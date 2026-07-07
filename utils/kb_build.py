"""Offline build script for the help-chat RAG index.

Run manually (or in CI) whenever lesson drawer content or a utils/kb_*.py
module changes:

    python -m utils.kb_build

Never imported by the running Flask app — routes/help.py and
utils/help_kb.py only ever read the two files this script produces:

    data/help_index.npz        vectors (float32, L2-normalized) + ids
    data/help_index_meta.json  chunk metadata + corpus hashes (diffable)

Auto-derived chunks are read directly from utils.project_registry.PROJECTS
(the same object the running app uses), so lesson content never needs to
be duplicated here. Hand-authored chunks come from any utils/kb_*.py
module exporting a module-level CHUNKS list, discovered the same way
utils/project_registry.py discovers utils/project_*.py modules.
"""

import datetime
import hashlib
import importlib
import json
import os
import pkgutil
import re
import traceback

import numpy as np

import utils
from config import OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL

EMBED_BATCH_SIZE = 100

# Tabs that should never be embedded: raw sketch code (reads too differently
# from troubleshooting prose, see plan decision) and "sim" tabs, which hold a
# sim_config dict rather than a content string and are skipped generically
# below anyway.
EXCLUDED_TAB_KEYS = {"code"}


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _step_chunks(project_key, title, step_index, step, out):
    step_title = step.get("title", "") if isinstance(step, dict) else ""
    tabs = step.get("tabs") or {} if isinstance(step, dict) else {}
    for tab_key, tab in tabs.items():
        if tab_key in EXCLUDED_TAB_KEYS:
            continue
        content = tab.get("content") if isinstance(tab, dict) else None
        if not isinstance(content, str) or not content.strip():
            continue
        text = _strip_html(content)
        if not text:
            continue
        label = tab.get("label", tab_key)
        out.append({
            "id": f"{project_key}:step{step_index}:{tab_key}",
            "source": "auto",
            "project_key": project_key,
            "step_index": step_index,
            "tab_key": tab_key,
            "title": f"{title} — {step_title} ({label})" if step_title else f"{title} ({label})",
            "text": text,
            "tags": [],
        })


def collect_auto_chunks(projects: dict) -> list[dict]:
    """Walk utils.project_registry.PROJECTS and emit one chunk per drawer tab
    that has non-empty string content. Schema-tolerant: three drawer shapes
    were found via direct inspection across the 19 project_*.py modules plus
    block_builder_tutorial.py —
      A) drawer[key]["tabs"][tab_key]                (project-level, no steps)
      B) drawer[key]["steps"][i]["tabs"][tab_key]     (per-step, wrapped)
      C) drawer[key] is itself a list of step dicts   (per-step, unwrapped —
         only block_builder_tutorial.py uses this)
    """
    chunks = []
    for project_key, project in projects.items():
        drawer = project.get("drawer") or {}
        if not drawer:
            continue
        drawer_entry = drawer.get(project_key)
        if drawer_entry is None and len(drawer) == 1:
            drawer_entry = next(iter(drawer.values()))
        if not drawer_entry:
            continue

        meta = project.get("meta") or {}
        title = meta.get("title", project_key)

        if isinstance(drawer_entry, list):
            for step_index, step in enumerate(drawer_entry):
                _step_chunks(project_key, title, step_index, step, chunks)
        elif isinstance(drawer_entry, dict) and "steps" in drawer_entry:
            for step_index, step in enumerate(drawer_entry["steps"] or []):
                _step_chunks(project_key, title, step_index, step, chunks)
        elif isinstance(drawer_entry, dict) and "tabs" in drawer_entry:
            tabs = drawer_entry["tabs"] or {}
            for tab_key, tab in tabs.items():
                if tab_key in EXCLUDED_TAB_KEYS:
                    continue
                content = tab.get("content") if isinstance(tab, dict) else None
                if not isinstance(content, str) or not content.strip():
                    continue
                text = _strip_html(content)
                if not text:
                    continue
                chunks.append({
                    "id": f"{project_key}:{tab_key}",
                    "source": "auto",
                    "project_key": project_key,
                    "step_index": None,
                    "tab_key": tab_key,
                    "title": f"{title} ({tab.get('label', tab_key)})",
                    "text": text,
                    "tags": [],
                })
        # else: shape not recognized — skip rather than guess.
    return chunks


def collect_authored_chunks() -> list[dict]:
    """Discover utils/kb_*.py modules and merge their CHUNKS lists.

    One bad module is logged and skipped rather than aborting the build,
    mirroring utils/project_registry.py's defensive per-module handling.
    """
    chunks = []
    for _, module_name, _ in pkgutil.iter_modules(utils.__path__):
        if not module_name.startswith("kb_"):
            continue
        try:
            module = importlib.import_module(f"utils.{module_name}")
            for entry in getattr(module, "CHUNKS", []) or []:
                chunk = dict(entry)
                chunk["source"] = module_name
                chunk["project_key"] = None
                chunk["step_index"] = None
                chunk["tab_key"] = None
                chunk.setdefault("tags", [])
                chunks.append(chunk)
        except Exception as exc:
            traceback.print_exc()
            print(f"Error loading KB module {module_name}: {exc}")
    return chunks


def corpus_hash(chunks: list[dict]) -> str:
    """Sha256 over sorted id+text pairs — insensitive to dict/module ordering,
    sensitive to any content or id change.
    """
    digest = hashlib.sha256()
    for part in sorted(f"{c['id']}\x00{c['text']}" for c in chunks):
        digest.update(part.encode("utf-8"))
        digest.update(b"\x01")
    return digest.hexdigest()


def _embed_all(texts: list[str], client) -> np.ndarray:
    vectors = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i:i + EMBED_BATCH_SIZE]
        response = client.embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=batch)
        vectors.extend(item.embedding for item in response.data)
    matrix = np.array(vectors, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def build(output_dir: str = "data") -> None:
    from openai import OpenAI
    from utils.project_registry import PROJECTS

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY must be set to build the help index")

    auto_chunks = collect_auto_chunks(PROJECTS)
    authored_chunks = collect_authored_chunks()
    all_chunks = auto_chunks + authored_chunks

    seen_ids = set()
    for chunk in all_chunks:
        if chunk["id"] in seen_ids:
            raise ValueError(f"Duplicate chunk id: {chunk['id']}")
        seen_ids.add(chunk["id"])

    if not all_chunks:
        raise RuntimeError("No chunks collected — refusing to write an empty index")

    client = OpenAI(api_key=OPENAI_API_KEY)
    matrix = _embed_all([c["text"] for c in all_chunks], client)
    ids = np.array([c["id"] for c in all_chunks])

    os.makedirs(output_dir, exist_ok=True)
    np.savez(os.path.join(output_dir, "help_index.npz"), vectors=matrix, ids=ids)

    meta = {
        "embedding_model": OPENAI_EMBEDDING_MODEL,
        "dimension": int(matrix.shape[1]),
        "built_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "corpus_hash_auto": corpus_hash(auto_chunks),
        "corpus_hash_authored": corpus_hash(authored_chunks),
        "chunks": all_chunks,
    }
    with open(os.path.join(output_dir, "help_index_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print(
        f"Built help index: {len(all_chunks)} chunks "
        f"({len(auto_chunks)} auto, {len(authored_chunks)} authored), "
        f"dim={matrix.shape[1]}"
    )


if __name__ == "__main__":
    build()
