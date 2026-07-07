"""
CI staleness guard for the help-chat RAG index.

Recomputes the corpus hashes from the *live* utils.project_registry.PROJECTS
and utils/kb_*.py modules and asserts they match what's recorded in
data/help_index_meta.json. Zero embedding calls — this only catches
"someone edited lesson/KB content but forgot to rerun utils/kb_build.py",
not embedding-quality regressions (that's a manual calibration concern,
not something a hash comparison can detect).
"""

import json
import os

import numpy as np
import pytest

from utils.kb_build import collect_auto_chunks, collect_authored_chunks, corpus_hash
from utils.project_registry import PROJECTS

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_META_PATH = os.path.join(_REPO_ROOT, "data", "help_index_meta.json")
_NPZ_PATH = os.path.join(_REPO_ROOT, "data", "help_index.npz")


def _load_meta():
    if not os.path.exists(_META_PATH):
        pytest.fail(
            f"{_META_PATH} not found — run `python -m utils.kb_build` to build the "
            "help index before running this test."
        )
    with open(_META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_auto_derived_corpus_matches_built_index():
    meta = _load_meta()
    current_hash = corpus_hash(collect_auto_chunks(PROJECTS))
    assert current_hash == meta["corpus_hash_auto"], (
        "Lesson drawer content has changed since the help index was last built "
        "(auto-derived corpus hash mismatch) — run `python -m utils.kb_build` and "
        "commit the updated data/help_index.npz + data/help_index_meta.json."
    )


def test_authored_corpus_matches_built_index():
    meta = _load_meta()
    current_hash = corpus_hash(collect_authored_chunks())
    assert current_hash == meta["corpus_hash_authored"], (
        "A utils/kb_*.py module has changed since the help index was last built "
        "(hand-authored corpus hash mismatch) — run `python -m utils.kb_build` and "
        "commit the updated data/help_index.npz + data/help_index_meta.json."
    )


def test_index_row_count_matches_chunk_count():
    meta = _load_meta()
    if not os.path.exists(_NPZ_PATH):
        pytest.fail(f"{_NPZ_PATH} not found — run `python -m utils.kb_build`.")
    archive = np.load(_NPZ_PATH)
    assert len(archive["ids"]) == len(meta["chunks"])
    assert archive["vectors"].shape[0] == len(meta["chunks"])
    assert archive["vectors"].shape[1] == meta["dimension"]
