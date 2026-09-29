"""Find similar past (customer tweet -> brand reply) pairs to ground the agent's reply.

Index = history messages sent strictly before EVAL_START, minus every customer who
appears in the golden or dev sets, so the agent can never see the answer to the
message it is evaluated on, or that same person's other threads.
"""
import json

import numpy as np
import pandas as pd

from src.config import EVAL_START, MESSAGES
from src.embeddings import embed
from src.make_eval_sets import DEV_FILE, GOLDEN_FILE, read_jsonl


def query_text(text: str, context: list[dict] | None) -> str:
    """Follow-ups like 'still not working' are ambiguous alone: prepend the previous turn."""
    if context:
        return f"{context[-1]['text']} || {text}"
    return text


def load_history() -> pd.DataFrame:
    m = pd.read_parquet(MESSAGES)
    hist = m[(m.split == "history") & (m.created_at < pd.Timestamp(EVAL_START, tz="UTC"))]
    excluded = {ex["customer_id"] for f in (GOLDEN_FILE, DEV_FILE) for ex in read_jsonl(f)}
    hist = hist[~hist.customer_id.isin(excluded)]
    return hist.reset_index(drop=True)


class Retriever:
    def __init__(self):
        self.rows = load_history()
        contexts = [json.loads(c) for c in self.rows.context]
        self.vecs = embed([query_text(t, c) for t, c in zip(self.rows.text, contexts)],
                          cache_name="history_index")

    def search_batch(self, examples: list[dict], k: int = 5) -> list[list[dict]]:
        q = embed([query_text(ex["text"], ex.get("context")) for ex in examples])
        sims = q @ self.vecs.T
        results = []
        ids = self.rows.msg_id.values
        for row in sims:
            # Ties are common here — the corpus contains near-duplicate tweets, so
            # several candidates land on the same cosine score. np.argsort defaults
            # to quicksort, which is NOT stable, so which of the tied cases made the
            # top-5 was not guaranteed across numpy versions or machines. The prompt
            # carries those cases and the LLM cache is keyed by a hash of the prompt,
            # so an unstable tie-break quietly weakens the reproducibility guarantee.
            # lexsort makes it total: score descending, then msg_id ascending.
            top = np.lexsort((ids, -row))[:k]
            results.append([{"msg_id": int(self.rows.msg_id[i]), "text": self.rows.text[i],
                             "brand_reply": self.rows.brand_reply[i], "score": round(float(row[i]), 3)}
                            for i in top])
        return results
