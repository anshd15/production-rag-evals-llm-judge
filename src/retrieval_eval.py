"""Does retrieval surface a useful precedent? Nothing else in the repo asks.

End-to-end metrics can't separate a bad answer from five irrelevant examples in
the prompt. These isolate the retriever and need no LLM call, so a retrieval
change is measurable in seconds instead of a full re-run.

The history has no relevance judgements, so the proxy is the brand's own reply:
a retrieved case is useful if the reply it carries resembles the reply
SpotifyCares actually sent to the query message. That reply is never shown to
the agent — it is held out exactly for this.

  precedent@k   best cosine between a retrieved reply and the true reply
  mean@k        same, averaged over all k (how much of the prompt is on-topic)
  route@1       top case's reply takes the same next step (DM ask vs not)

  python -m src.retrieval_eval --methods dense tfidf hybrid
"""
import argparse
import json

import numpy as np

from src.config import ROOT, SEED
from src.embeddings import embed
from src.make_eval_sets import DEV_FILE, read_jsonl
from src.retrieval import Retriever


def evaluate(dense: Retriever, method: str, dev: list[dict], ks: list[int]) -> dict:
    retriever = dense
    if method != "dense":
        from src.retrieval_hybrid import HybridRetriever
        retriever = HybridRetriever(dense, method)

    kmax = max(ks)
    hits = retriever.search_batch(dev, kmax)
    dm_of = dict(zip(dense.rows.msg_id.astype(int), dense.rows.reply_asks_dm.astype(bool)))

    true_vecs = embed([e["brand_reply"] for e in dev], cache_name=f"rq_true_{len(dev)}")
    flat = [c["brand_reply"] for cases in hits for c in cases[:kmax]]
    flat_vecs = embed(flat, cache_name=f"rq_{method}_{len(dev)}_{kmax}")
    per_example = np.split(flat_vecs, np.cumsum([len(c[:kmax]) for c in hits])[:-1])

    out = {"method": method, "n": len(dev), "k": {}, "per_example": {}}
    for k in ks:
        best, mean = [], []
        for tv, cand in zip(true_vecs, per_example):
            if len(cand) == 0:
                continue
            sims = cand[:k] @ tv
            best.append(float(sims.max()))
            mean.append(float(sims.mean()))
        out["k"][k] = {"precedent": float(np.mean(best)), "mean": float(np.mean(mean))}
        out["per_example"][k] = best
    route = [dm_of.get(cases[0]["msg_id"], False) == bool(e["reply_asks_dm"])
             for e, cases in zip(dev, hits) if cases]
    out["route_at_1"] = float(np.mean(route))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", nargs="*", default=["dense", "tfidf", "hybrid"])
    ap.add_argument("--k", type=int, nargs="*", default=[1, 3, 5, 10])
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    dev = read_jsonl(DEV_FILE)
    dev = dev[: args.limit] if args.limit else dev
    dense = Retriever()

    results = [evaluate(dense, m, dev, args.k) for m in args.methods]
    baseline = next((r for r in results if r["method"] == "dense"), None)
    comparisons = {}
    if baseline:
        rng = np.random.default_rng(SEED)
        base = np.array(baseline["per_example"][5])
        idx = [rng.integers(0, len(base), len(base)) for _ in range(1000)]
        for r in results:
            if r["method"] == "dense":
                continue
            other = np.array(r["per_example"][5])
            diffs = np.array([other[i].mean() - base[i].mean() for i in idx])
            comparisons[r["method"]] = {
                "diff": float(other.mean() - base.mean()),
                "lo": float(np.percentile(diffs, 2.5)), "hi": float(np.percentile(diffs, 97.5)),
                "p_not_better": float((diffs <= 0).mean())}
    lines = [f"# Retrieval quality (n={len(dev)} dev messages, proxy = the reply the brand "
             f"actually sent)\n",
             "| Method | " + " | ".join(f"precedent@{k}" for k in args.k) + " | mean@5 | route@1 |",
             "|---" * (len(args.k) + 3) + "|"]
    for r in results:
        lines.append(f"| {r['method']} | " +
                     " | ".join(f"{r['k'][k]['precedent']:.3f}" for k in args.k) +
                     f" | {r['k'][max(5, min(args.k))]['mean']:.3f} | {r['route_at_1']:.1%} |")
    if comparisons:
        lines.append("")
        lines.append("**Paired bootstrap on precedent@5, method minus dense:**")
        lines.append("")
        for m, c in comparisons.items():
            lines.append(f"- {m}: {c['diff']:+.3f} [{c['lo']:+.3f}, {c['hi']:+.3f}], "
                         f"P(not better) = {c['p_not_better']:.3f}")
    lines += ["\nCosine between MiniLM embeddings of the retrieved reply and the true reply; the",
              "true reply is held out from the agent. `route@1` asks whether the top case took the",
              "same next step (ask for a DM, or not) as the real agent did.\n",
              "Dense remains the shipped default: switching would change every prompt and void the",
              "committed golden numbers until a full re-run with a live model."]
    (ROOT / "reports" / "retrieval_quality.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "data" / "processed" / "retrieval_quality.json").write_text(
        json.dumps({"results": [{k: v for k, v in r.items() if k != "per_example"} for r in results],
                    "comparisons": comparisons}, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
