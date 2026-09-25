"""Lexical + dense retrieval fused by reciprocal rank.

Dense embeddings miss exact strings that matter in support ("error 3", "8.4.27",
"CarPlay"); TF-IDF misses paraphrase. Reciprocal rank fusion combines the two
orderings without needing the scores to be on the same scale:

    score(doc) = sum over retrievers of 1 / (RRF_K + rank(doc))

Opt-in: the shipped agent still uses dense-only, because switching the default
would change every prompt, invalidate the cached model responses and void the
committed golden numbers until a full re-run. Measure first, switch later.
"""
import json

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from src.retrieval import Retriever, query_text

RRF_K = 60  # standard damping; larger = flatter weighting of deep ranks


class HybridRetriever:
    def __init__(self, dense: Retriever, method: str = "hybrid"):
        self.dense = dense
        self.method = method
        self.rows = dense.rows
        contexts = [json.loads(c) for c in self.rows.context]
        corpus = [query_text(t, c) for t, c in zip(self.rows.text, contexts)]
        # min_df=2 drops hapaxes on the real 34k corpus; on a tiny one it would prune
        # the whole vocabulary, so it scales with the corpus.
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True,
                                   min_df=2 if len(corpus) >= 50 else 1)
        self.matrix = self.vec.fit_transform(corpus)

    def _lexical_ranks(self, examples, k):
        sims = self.vec.transform([query_text(e["text"], e.get("context")) for e in examples]) @ self.matrix.T
        sims = np.asarray(sims.todense())
        return [np.argsort(-row)[:k] for row in sims]

    def search_batch(self, examples: list[dict], k: int = 5) -> list[list[dict]]:
        pool = max(k * 4, 20)  # fuse over a deeper pool than we return
        lexical = self._lexical_ranks(examples, pool)
        if self.method == "tfidf":
            return [[self._row(i) for i in idx[:k]] for idx in lexical]

        dense_hits = self.dense.search_batch(examples, pool)
        out = []
        for lex_idx, dense_cases in zip(lexical, dense_hits):
            scores: dict[int, float] = {}
            for rank, i in enumerate(lex_idx):
                scores[int(i)] = scores.get(int(i), 0.0) + 1 / (RRF_K + rank + 1)
            by_msg = {int(self.rows.msg_id[i]): int(i) for i in lex_idx}
            for rank, case in enumerate(dense_cases):
                i = by_msg.get(case["msg_id"], self._index_of(case["msg_id"]))
                scores[i] = scores.get(i, 0.0) + 1 / (RRF_K + rank + 1)
            best = sorted(scores, key=scores.get, reverse=True)[:k]
            out.append([self._row(i, round(scores[i], 4)) for i in best])
        return out

    def _index_of(self, msg_id: int) -> int:
        return int(np.flatnonzero(self.rows.msg_id.values == msg_id)[0])

    def _row(self, i: int, score: float | None = None) -> dict:
        return {"msg_id": int(self.rows.msg_id[i]), "text": self.rows.text[i],
                "brand_reply": self.rows.brand_reply[i], "score": score}
