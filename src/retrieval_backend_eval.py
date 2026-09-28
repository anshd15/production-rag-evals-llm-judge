"""Does the vector DB earn its place? Measure it, don't assume it.

The honest case for Qdrant here is NOT speed: at 33.8k vectors a brute-force
matmul is already milliseconds, and an approximate index cannot beat that. The
case is cold start (the numpy index re-embeds the corpus on boot, which is fatal
on a host that scales to zero) and incremental updates.

So this measures the three things that actually decide it, and the one risk:

  parity        does exact search return the SAME top-k as numpy? If not, every
                committed LLM cache entry misses and the golden numbers die.
  quality       precedent@5 / route@1 per backend, via src.retrieval_eval
  search p50/p95 per-query latency once the index is warm
  cold start    time from process start to first answerable query

  python -m src.retrieval_backend_eval --backends numpy qdrant-exact qdrant-hnsw

Writes reports/retrieval_backends.md. Needs a reachable Qdrant for the qdrant
rows; the numpy row always works.
"""
import argparse
import json
import time

import numpy as np

from src.config import ROOT
from src.make_eval_sets import DEV_FILE, read_jsonl

BACKENDS = ["numpy", "qdrant-exact", "qdrant-hnsw"]


def _build(backend: str):
    """Returns (retriever, cold_start_seconds). Cold start is the whole point."""
    t0 = time.perf_counter()
    if backend == "numpy":
        from src.retrieval import Retriever
        r = Retriever()
    else:
        from src.retrieval_qdrant import QdrantRetriever
        r = QdrantRetriever(exact=backend.endswith("exact"))
    return r, time.perf_counter() - t0


def _latency(retriever, queries: list[dict], k: int) -> dict:
    """One query at a time: batching hides the per-request latency a service sees."""
    times = []
    for q in queries:
        t0 = time.perf_counter()
        retriever.search_batch([q], k)
        times.append((time.perf_counter() - t0) * 1000)
    return {"p50_ms": float(np.percentile(times, 50)),
            "p95_ms": float(np.percentile(times, 95)),
            "n": len(times)}


def _topk_ids(retriever, examples: list[dict], k: int) -> list[list[int]]:
    return [[c["msg_id"] for c in cases] for cases in retriever.search_batch(examples, k)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backends", nargs="*", default=BACKENDS)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--limit", type=int, default=100, help="queries for the latency sample")
    args = ap.parse_args()

    dev = read_jsonl(DEV_FILE)
    sample = dev[: args.limit]

    rows, reference, failures = {}, None, {}
    for backend in args.backends:
        try:
            retriever, cold = _build(backend)
            ids = _topk_ids(retriever, sample, args.k)
            row = {"cold_start_s": round(cold, 1), **_latency(retriever, sample, args.k)}
            if reference is None:
                reference = ids
                row["parity_vs_numpy"] = "reference"
            else:
                same = sum(a == b for a, b in zip(reference, ids))
                row["parity_vs_numpy"] = f"{same}/{len(ids)}"
                row["cache_valid"] = same == len(ids)
            rows[backend] = row
        except Exception as exc:  # a backend that isn't up is a row, not a crash
            failures[backend] = f"{type(exc).__name__}: {exc}"

    lines = [f"# Retrieval backends (n={len(sample)} queries, k={args.k})\n",
             "| Backend | cold start | search p50 | search p95 | same top-k as numpy | cache still valid |",
             "|---|---|---|---|---|---|"]
    for backend, r in rows.items():
        valid = r.get("cache_valid")
        lines.append(
            f"| {backend} | {r['cold_start_s']}s | {r['p50_ms']:.1f}ms | {r['p95_ms']:.1f}ms | "
            f"{r['parity_vs_numpy']} | {'—' if valid is None else ('yes' if valid else '**no**')} |")
    for backend, err in failures.items():
        lines.append(f"| {backend} | not reachable | — | — | — | — |")

    lines += [
        "",
        "**What decides this.** Speed is not the argument: a brute-force matmul over 33.8k",
        "vectors is already milliseconds, and an approximate index cannot beat exact search it",
        "is approximating. The argument is cold start — the numpy backend re-embeds the whole",
        "corpus on boot, which a scale-to-zero host pays on every request after an idle period.",
        "",
        "**Parity is the risk.** Every prompt contains the retrieved cases, and the committed LLM",
        "cache is keyed by a hash of the prompt. A backend that reorders neighbours invalidates",
        "the cache and voids the committed golden numbers until a full re-run against a live",
        "model. `exact` is expected to match numpy on every query; HNSW is expected not to, and",
        "the column above says how far off it is.",
    ]
    if failures:
        lines += ["", "**Not measured:**"] + [f"- `{b}`: {e}" for b, e in failures.items()]

    (ROOT / "reports" / "retrieval_backends.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "data" / "processed" / "retrieval_backends.json").write_text(
        json.dumps({"rows": rows, "failures": failures}, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
