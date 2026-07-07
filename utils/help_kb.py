"""Runtime retrieval for the help-chat RAG index.

Loads the pre-built data/help_index.npz + data/help_index_meta.json pair
(produced offline by utils/kb_build.py) once at import time, into a
module-level singleton — mirroring utils/project_registry.py's pattern of
loading everything once and never touching disk again per-request.

Only routes/help.py should import this module. It never imports the
utils/kb_*.py content modules directly — those are build-time only.

Any load failure (missing file, corrupt archive, dimension mismatch
against the recorded embedding model) disables retrieval silently rather
than raising — the caller falls back to today's exact-key-only behavior,
never a 500.
"""

import json
import os
import traceback
from dataclasses import dataclass

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(_HERE), "data")
_INDEX_PATH = os.path.join(_DATA_DIR, "help_index.npz")
_META_PATH = os.path.join(_DATA_DIR, "help_index_meta.json")

_MATRIX = None          # (N, D) float32, L2-normalized rows
_CHUNKS = None          # list[dict], same row order as _MATRIX
_META = None
_LOAD_ERROR = None


@dataclass
class RetrievedChunk:
    chunk_id: str
    similarity: float
    title: str
    text: str
    project_key: str | None
    step_index: int | None
    source: str


def _load():
    global _MATRIX, _CHUNKS, _META, _LOAD_ERROR
    try:
        with open(_META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
        archive = np.load(_INDEX_PATH, allow_pickle=False)
        vectors = archive["vectors"]
        ids = archive["ids"]
        chunks = meta.get("chunks", [])

        if not (len(vectors) == len(ids) == len(chunks)):
            raise ValueError(
                f"help index row-count mismatch: vectors={len(vectors)} "
                f"ids={len(ids)} chunks={len(chunks)}"
            )
        if vectors.shape[1] != meta.get("dimension"):
            raise ValueError(
                f"help index dimension mismatch: vectors have {vectors.shape[1]} "
                f"dims, metadata recorded {meta.get('dimension')}"
            )
        for i, chunk in enumerate(chunks):
            if chunk.get("id") != ids[i]:
                raise ValueError(f"help index id ordering mismatch at row {i}")

        _MATRIX = vectors.astype(np.float32)
        _CHUNKS = chunks
        _META = meta
    except FileNotFoundError:
        _LOAD_ERROR = "help index not built yet"
    except Exception as exc:
        traceback.print_exc()
        _LOAD_ERROR = str(exc)


_load()


def is_available() -> bool:
    return _MATRIX is not None


def embedding_model() -> str | None:
    return (_META or {}).get("embedding_model")


def embed_query(text: str, client, timeout: float = 4.0) -> "np.ndarray | None":
    """Embed a query string for retrieval. Returns None on any failure
    (timeout, network error, API error) — callers must treat None as
    'retrieval unavailable this request' and fall back gracefully.
    """
    if not text or not text.strip():
        return None
    model = embedding_model()
    if not model:
        return None
    try:
        response = client.embeddings.create(model=model, input=[text], timeout=timeout)
        vector = np.array(response.data[0].embedding, dtype=np.float32)
        norm = np.linalg.norm(vector)
        if norm == 0:
            return None
        return vector / norm
    except Exception:
        return None


def retrieve(query_vector, project_key=None, step_index=None, k: int = 5) -> list[RetrievedChunk]:
    """Pure function, no I/O: rank chunks by cosine similarity (dot product,
    both sides pre-normalized), then re-rank as stable-sorted groups —
    exact project+step match first, same-project next, everything else
    last — rather than blending a score bonus into the similarity itself.
    """
    if not is_available() or query_vector is None:
        return []

    sims = _MATRIX @ query_vector
    overfetch = min(len(sims), max(k * 3, k))
    order = np.argsort(-sims)[:overfetch]

    exact, same_project, other = [], [], []
    for idx in order:
        chunk = _CHUNKS[idx]
        entry = (idx, float(sims[idx]))
        if project_key is not None and chunk.get("project_key") == project_key:
            if step_index is not None and chunk.get("step_index") == step_index:
                exact.append(entry)
            else:
                same_project.append(entry)
        else:
            other.append(entry)

    ranked = (exact + same_project + other)[:k]
    results = []
    for idx, sim in ranked:
        chunk = _CHUNKS[idx]
        results.append(RetrievedChunk(
            chunk_id=chunk["id"],
            similarity=sim,
            title=chunk.get("title", ""),
            text=chunk.get("text", ""),
            project_key=chunk.get("project_key"),
            step_index=chunk.get("step_index"),
            source=chunk.get("source", ""),
        ))
    return results
