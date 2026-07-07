"""
Tests for utils.help_kb's retrieval logic — pure-function, no Flask/network,
same style as tests/test_circuit_engine.py.

A small synthetic fixture matrix is monkeypatched directly into the module's
internal state (the same state utils/kb_build.py's real output populates at
import time), so ranking/re-rank/threshold behavior can be asserted against
known vectors instead of live embeddings.
"""

import numpy as np
import pytest

from utils import help_kb


def _make_chunk(id, project_key=None, step_index=None, source="auto", title="", text=""):
    return {
        "id": id,
        "source": source,
        "project_key": project_key,
        "step_index": step_index,
        "tab_key": None,
        "title": title,
        "text": text,
        "tags": [],
    }


def _unit(v):
    v = np.array(v, dtype=np.float32)
    return v / np.linalg.norm(v)


@pytest.fixture
def fixture_index(monkeypatch):
    vectors = np.array([
        [1.0, 0.0, 0.0],   # c0: project_a, step 0
        [0.9, 0.1, 0.0],   # c1: project_b, step 0
        [0.0, 1.0, 0.0],   # c2: project_a, step 1
        [0.0, 0.0, 1.0],   # c3: global (no project)
        [0.5, 0.5, 0.0],   # c4: project_a, step 0
    ], dtype=np.float32)
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    chunks = [
        _make_chunk("c0", project_key="project_a", step_index=0, title="A0", text="alpha text"),
        _make_chunk("c1", project_key="project_b", step_index=0, title="B0", text="beta text"),
        _make_chunk("c2", project_key="project_a", step_index=1, title="A1", text="gamma text"),
        _make_chunk("c3", project_key=None,        step_index=None, title="G", text="glossary text"),
        _make_chunk("c4", project_key="project_a", step_index=0, title="A0b", text="delta text"),
    ]

    monkeypatch.setattr(help_kb, "_MATRIX", vectors)
    monkeypatch.setattr(help_kb, "_CHUNKS", chunks)
    monkeypatch.setattr(help_kb, "_META", {"embedding_model": "text-embedding-3-small", "dimension": 3})
    return vectors, chunks


# ── is_available ────────────────────────────────────────────────────────────

def test_is_available_true_with_loaded_index(fixture_index):
    assert help_kb.is_available() is True


def test_is_available_false_without_index(monkeypatch):
    monkeypatch.setattr(help_kb, "_MATRIX", None)
    assert help_kb.is_available() is False


# ── retrieve: ranking ────────────────────────────────────────────────────────

def test_retrieve_ranks_by_cosine_similarity(fixture_index):
    query = _unit([1.0, 0.0, 0.0])
    results = help_kb.retrieve(query, k=5)
    assert results[0].chunk_id == "c0"
    assert results[0].similarity == pytest.approx(1.0, abs=1e-5)
    sims = [r.similarity for r in results]
    assert sims == sorted(sims, reverse=True)


def test_retrieve_returns_empty_when_unavailable(monkeypatch):
    monkeypatch.setattr(help_kb, "_MATRIX", None)
    assert help_kb.retrieve(_unit([1, 0, 0]), k=5) == []


def test_retrieve_returns_empty_for_none_query_vector(fixture_index):
    assert help_kb.retrieve(None, k=5) == []


def test_retrieve_respects_k(fixture_index):
    results = help_kb.retrieve(_unit([1, 0, 0]), k=2)
    assert len(results) == 2


# ── retrieve: re-rank grouping (exact > same-project > other) ───────────────

def test_retrieve_project_rerank_promotes_same_project(fixture_index):
    # Query points closest to c1 (project_b), but the caller is asking in the
    # context of project_a — same-project chunks should still be grouped
    # ahead of higher-raw-similarity chunks from a different project.
    query = _unit([0.9, 0.1, 0.0])
    results = help_kb.retrieve(query, project_key="project_a", step_index=None, k=5)
    project_a_positions = [i for i, r in enumerate(results) if r.project_key == "project_a"]
    other_positions = [i for i, r in enumerate(results) if r.project_key != "project_a"]
    assert project_a_positions and other_positions
    assert max(project_a_positions) < min(other_positions)


def test_retrieve_exact_step_match_ranks_above_same_project_other_step(fixture_index):
    query = _unit([0.6, 0.6, 0.0])
    results = help_kb.retrieve(query, project_key="project_a", step_index=0, k=5)
    step0_ids = {"c0", "c4"}
    step0_positions = [i for i, r in enumerate(results) if r.chunk_id in step0_ids]
    step1_position = next(i for i, r in enumerate(results) if r.chunk_id == "c2")
    assert step0_positions
    assert max(step0_positions) < step1_position


def test_retrieve_without_project_key_keeps_pure_similarity_order(fixture_index):
    query = _unit([0.9, 0.1, 0.0])
    results = help_kb.retrieve(query, project_key=None, step_index=None, k=5)
    sims = [r.similarity for r in results]
    assert sims == sorted(sims, reverse=True)


# ── embed_query ──────────────────────────────────────────────────────────────

def test_embed_query_returns_none_on_client_exception(fixture_index):
    class BoomClient:
        class embeddings:
            @staticmethod
            def create(*a, **kw):
                raise RuntimeError("network exploded")

    assert help_kb.embed_query("hello", BoomClient()) is None


def test_embed_query_returns_none_for_empty_text(fixture_index):
    assert help_kb.embed_query("", object()) is None
    assert help_kb.embed_query("   ", object()) is None


def test_embed_query_returns_none_when_index_unavailable(monkeypatch):
    monkeypatch.setattr(help_kb, "_META", None)
    assert help_kb.embed_query("hello", object()) is None


def test_embed_query_normalizes_and_returns_vector(fixture_index):
    class FakeEmbeddingItem:
        embedding = [3.0, 4.0, 0.0]  # norm = 5

    class FakeResponse:
        data = [FakeEmbeddingItem()]

    class FakeClient:
        class embeddings:
            @staticmethod
            def create(*a, **kw):
                return FakeResponse()

    vec = help_kb.embed_query("some query", FakeClient())
    assert vec is not None
    assert np.linalg.norm(vec) == pytest.approx(1.0, abs=1e-5)
