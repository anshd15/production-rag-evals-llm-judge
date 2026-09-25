import json

import pandas as pd
import pytest

from src.retrieval_hybrid import RRF_K, HybridRetriever


class FakeDense:
    """Stands in for the embedding retriever: returns a fixed ranking."""

    def __init__(self, rows, order):
        self.rows = rows
        self.order = order

    def search_batch(self, examples, k):
        return [[{"msg_id": int(self.rows.msg_id[i]), "text": self.rows.text[i],
                  "brand_reply": self.rows.brand_reply[i], "score": 1.0}
                 for i in self.order[:k]] for _ in examples]


@pytest.fixture
def dense():
    rows = pd.DataFrame({
        "msg_id": [10, 11, 12, 13],
        "text": ["error 3 on checkout", "cannot pay for premium", "playlist gone", "album missing"],
        "brand_reply": ["DM us", "DM us", "try reinstalling", "licensing"],
        "context": [json.dumps([])] * 4,
    })
    return FakeDense(rows, order=[2, 3, 0, 1])


def test_tfidf_mode_ranks_by_exact_wording(dense):
    hits = HybridRetriever(dense, "tfidf").search_batch([{"text": "error 3 on checkout",
                                                          "context": []}], k=2)[0]
    assert hits[0]["msg_id"] == 10


def test_hybrid_prefers_a_case_both_retrievers_rank_highly(dense):
    dense.order = [1, 0, 2, 3]  # 11 is also dense's top hit
    hits = HybridRetriever(dense, "hybrid").search_batch(
        [{"text": "cannot pay for premium", "context": []}], k=4)[0]
    assert [h["msg_id"] for h in hits][0] == 11
    assert hits[0]["score"] == pytest.approx(2 / (RRF_K + 1), abs=1e-4)


def test_one_strong_ranking_can_outweigh_a_slightly_better_one(dense):
    """RRF is rank-based, so a first place in one list beats a fourth in the other
    even when the second retriever disagrees — worth pinning down, because it is
    the behaviour that surprises people reading the fused order."""
    hits = HybridRetriever(dense, "hybrid").search_batch(
        [{"text": "cannot pay for premium", "context": []}], k=4)[0]
    ids = [h["msg_id"] for h in hits]
    assert ids[0] == 12          # dense rank 1 + lexical rank 3
    assert ids[1] == 11          # lexical rank 1 + dense rank 4
    assert set(ids) == {10, 11, 12, 13}


def test_fusion_scores_are_reciprocal_ranks(dense):
    hits = HybridRetriever(dense, "hybrid").search_batch([{"text": "playlist gone",
                                                           "context": []}], k=1)[0]
    # top of both lists => 1/(K+1) twice
    assert hits[0]["score"] == pytest.approx(2 / (RRF_K + 1), abs=1e-4)
