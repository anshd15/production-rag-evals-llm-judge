"""Paired comparison of two runs on the same split — the loop's keep-or-revert test.

Both runs must have been scored against the same labels. Differences are computed on
the same bootstrap resamples of the examples, so the CI accounts for the fact that
both systems saw the same messages.

  python -m src.compare_runs --a v2 --b v1b --split dev
"""
import argparse

import numpy as np

from src.config import ROOT, SEED
from src.make_eval_sets import read_jsonl
from src.metrics import N_BOOT

METRICS = {
    "intent accuracy": lambda lab, p, j: float(lab["intent"] == p["intent"]),
    "escalation recall": lambda lab, p, j: float(p["escalate"]) if lab["escalate"] else np.nan,
    "escalation precision": lambda lab, p, j: float(lab["escalate"]) if p["escalate"] else np.nan,
    "automation rate": lambda lab, p, j: float(not p["escalate"]),
    "unsafe auto (lower=better)": lambda lab, p, j: float(lab["escalate"] and not p["escalate"]),
    "would-send": lambda lab, p, j: float(j["would_send"]) if j else np.nan,
    "good automation": lambda lab, p, j: float(
        not p["escalate"] and not lab["escalate"] and bool(j and j["would_send"])),
    "bad auto-send (lower=better)": lambda lab, p, j: float(
        not p["escalate"] and (lab["escalate"] or not j or not j["safe"] or not j["would_send"])),
}


def load(run: str, split: str, system: str = "agent"):
    rows = read_jsonl(ROOT / "runs" / run / split / "predictions.jsonl")
    return {r["msg_id"]: (r["label"], r[system], r["judge"][system]) for r in rows if r["label"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True, help="new run")
    ap.add_argument("--b", required=True, help="baseline run")
    ap.add_argument("--split", default="dev")
    ap.add_argument("--system", default="agent")
    args = ap.parse_args()
    A, B = load(args.a, args.split, args.system), load(args.b, args.split, args.system)
    ids = sorted(set(A) & set(B))
    print(f"{args.a} vs {args.b} on {len(ids)} shared labelled examples ({args.split})\n")
    print(f"| Metric | {args.a} | {args.b} | diff | 95% CI | P(no better) |")
    print("|---|---|---|---|---|---|")
    rng = np.random.default_rng(SEED)
    boot_idx = [rng.integers(0, len(ids), len(ids)) for _ in range(N_BOOT)]
    for name, fn in METRICS.items():
        a = np.array([fn(*A[i]) for i in ids], dtype=float)
        b = np.array([fn(*B[i]) for i in ids], dtype=float)
        pa, pb = np.nanmean(a), np.nanmean(b)
        diffs = []
        for idx in boot_idx:
            with np.errstate(invalid="ignore"):
                d = np.nanmean(a[idx]) - np.nanmean(b[idx])
            if d == d:
                diffs.append(d)
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        lower_better = "lower=better" in name
        worse = np.mean(np.array(diffs) >= 0) if lower_better else np.mean(np.array(diffs) <= 0)
        print(f"| {name} | {pa:.1%} | {pb:.1%} | {100 * (pa - pb):+.1f}pp | "
              f"[{lo:+.1%}, {hi:+.1%}] | {worse:.2f} |")


if __name__ == "__main__":
    main()
