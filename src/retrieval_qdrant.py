"""Qdrant-backed retrieval, with the same interface as the numpy Retriever.

Why this exists is NOT speed. At 33.8k vectors a brute-force matmul is already a
few milliseconds, and an approximate index cannot beat that. It exists because
the numpy index is rebuilt from scratch on first request (~2 min of embedding),
which is fatal on any host that scales to zero. Qdrant holds the vectors, so a
cold start is just loading the encoder.

Two search modes, and the difference is measurable (`python -m src.retrieval_eval
--backends`):
  exact   full scan, identical results to the numpy retriever. The committed LLM
          cache stays valid, because every prompt is byte-identical.
  hnsw    approximate. Neighbours may differ, which changes prompts, which
          invalidates the cache and voids the committed golden numbers until a
          full re-run. Opt in deliberately.

  python -m src.retrieval_qdrant upsert    # build the collection (once)
  python -m src.retrieval_qdrant status
"""
import sys

import numpy as np

from src.embeddings import embed
from src.retrieval import load_history, query_text
from src.settings import settings

BATCH = 256


def _client():
    """Imported lazily: the repo must run with no qdrant-client installed."""
    try:
        from qdrant_client import QdrantClient
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise RuntimeError(
            "RETRIEVAL_BACKEND=qdrant needs `pip install qdrant-client`") from exc
    kwargs = {"url": settings.qdrant_url}
    if settings.qdrant_api_key:
        kwargs["api_key"] = settings.qdrant_api_key
    return QdrantClient(timeout=settings.qdrant_timeout_s, **kwargs)


class QdrantRetriever:
    """Drop-in replacement for src.retrieval.Retriever.

    Holds `rows` for the same reason the numpy one does: /triage and the review
    console look up a retrieved message's text by msg_id. The vectors are what
    moves to Qdrant, not the corpus metadata.
    """

    def __init__(self, exact: bool | None = None):
        self.exact = settings.qdrant_exact if exact is None else exact
        self.collection = settings.qdrant_collection
        self.client = _client()
        self.rows = load_history()

    # ---------------------------------------------------------------- build
    @staticmethod
    def build(recreate: bool = False) -> int:
        """Embed the history once and upsert it. Safe to re-run."""
        from qdrant_client import models

        rows = load_history()
        import json
        contexts = [json.loads(c) for c in rows.context]
        vecs = embed([query_text(t, c) for t, c in zip(rows.text, contexts)],
                     cache_name="history_index")
        client = _client()
        name = settings.qdrant_collection
        exists = client.collection_exists(name)
        if recreate and exists:
            client.delete_collection(name)
            exists = False
        if not exists:
            client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=int(vecs.shape[1]), distance=models.Distance.COSINE))
        for start in range(0, len(rows), BATCH):
            stop = min(start + BATCH, len(rows))
            client.upsert(collection_name=name, points=models.Batch(
                ids=[int(m) for m in rows.msg_id[start:stop]],
                vectors=[v.tolist() for v in vecs[start:stop]],
                payloads=[{"created_at": str(c)} for c in rows.created_at[start:stop]]))
            print(f"  upserted {stop}/{len(rows)}", file=sys.stderr)
        return len(rows)

    # ---------------------------------------------------------------- search
    def search_batch(self, examples: list[dict], k: int = 5) -> list[list[dict]]:
        from qdrant_client import models

        q = embed([query_text(ex["text"], ex.get("context")) for ex in examples])
        params = models.SearchParams(exact=True) if self.exact else None
        by_id = self.rows.set_index("msg_id")
        results = []
        for vec in q:
            hits = self.client.query_points(
                collection_name=self.collection, query=vec.tolist(), limit=k,
                search_params=params, with_payload=False).points
            cases = []
            for h in hits:
                mid = int(h.id)
                if mid not in by_id.index:
                    continue  # corpus changed under the collection; skip rather than crash
                cases.append({"msg_id": mid, "text": by_id.text[mid],
                              "brand_reply": by_id.brand_reply[mid],
                              "score": round(float(h.score), 3)})
            results.append(cases)
        return results


def get_retriever(backend: str | None = None):
    """The one place that decides which retriever the agent and service use."""
    backend = (backend or settings.retrieval_backend).lower()
    if backend == "qdrant":
        return QdrantRetriever()
    if backend == "numpy":
        from src.retrieval import Retriever
        return Retriever()
    raise ValueError(f"RETRIEVAL_BACKEND must be numpy or qdrant, got {backend!r}")


def _cosine_topk(vecs: np.ndarray, q: np.ndarray, k: int) -> list[list[int]]:
    """Reference implementation used by the parity test."""
    sims = q @ vecs.T
    return [list(np.argsort(-row)[:k]) for row in sims]


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "upsert":
        n = QdrantRetriever.build(recreate="--recreate" in sys.argv)
        print(f"upserted {n} vectors into {settings.qdrant_collection}")
    else:
        c = _client()
        name = settings.qdrant_collection
        if not c.collection_exists(name):
            print(f"collection {name!r} does not exist — run `python -m src.retrieval_qdrant upsert`")
            sys.exit(1)
        info = c.get_collection(name)
        print(f"collection {name}: {info.points_count} points, status {info.status}")
