"""The parity contract between the two retrieval backends.

The committed LLM cache is keyed by a hash of the prompt, and the prompt contains
the retrieved cases. So `exact` search in Qdrant must return the same top-k, in
the same order, as the numpy matmul — otherwise every cached response misses and
the committed golden numbers cannot be reproduced without a live model.

These run with no Qdrant and no qdrant-client installed: they pin the ranking
contract that the Qdrant path has to satisfy, and assert the backend selector
fails loudly rather than silently falling back.
"""
import numpy as np
import pytest

from src.retrieval_qdrant import _cosine_topk, get_retriever


def _unit(rng, n, d):
    v = rng.normal(size=(n, d))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def test_cosine_topk_is_descending_by_similarity():
    rng = np.random.default_rng(0)
    vecs, q = _unit(rng, 200, 16), _unit(rng, 5, 16)
    for qi, idx in zip(q, _cosine_topk(vecs, q, 5)):
        sims = [float(vecs[i] @ qi) for i in idx]
        assert sims == sorted(sims, reverse=True)
        assert len(set(idx)) == 5


def test_cosine_topk_matches_exhaustive_ranking():
    """Exact search has no tolerance: it is argsort, or it is not exact."""
    rng = np.random.default_rng(1)
    vecs, q = _unit(rng, 120, 8), _unit(rng, 3, 8)
    for qi, idx in zip(q, _cosine_topk(vecs, q, 10)):
        expected = list(np.argsort(-(vecs @ qi))[:10])
        assert list(idx) == expected


def test_unknown_backend_is_rejected():
    with pytest.raises(ValueError, match="numpy or qdrant"):
        get_retriever("pinecone")


def test_qdrant_backend_does_not_silently_fall_back():
    """A typo'd URL must raise, not quietly serve numpy results.

    A fallback here would be the worst kind of bug: the service would look
    healthy while answering from an index nobody thinks is in use.
    """
    pytest.importorskip("qdrant_client", reason="qdrant-client not installed")
    import src.settings as s
    original = s.settings.qdrant_url
    object.__setattr__(s.settings, "qdrant_url", "http://127.0.0.1:1")
    try:
        with pytest.raises(Exception):
            get_retriever("qdrant").search_batch([{"text": "hi", "context": []}], 5)
    finally:
        object.__setattr__(s.settings, "qdrant_url", original)
