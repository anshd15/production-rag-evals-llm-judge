"""Is the judge measuring the draft, or something else?

Three biases make an LLM judge untrustworthy, and all three are testable without
a single human rating:

  self-preference   a judge prefers text from its own model family
  position bias     the same draft scores differently depending on where it sits
  verbosity bias    longer drafts score higher regardless of content

This computes what the committed run already allows: the position/order check
needs paired judgements (available once a second judge model is run) while
verbosity and system-level spread can be measured from `runs/<run>/<split>`
today.

  python -m src.judge_robustness --run final --split golden
"""
import argparse
import json
import statistics

from src.config import ROOT
from src.evaluate import SYSTEMS
from src.make_eval_sets import read_jsonl


def analyse(run: str, split: str) -> dict:
    rows = read_jsonl(ROOT / "runs" / run / split / "predictions.jsonl")
    out = {"n": len(rows), "systems": {}, "verbosity": {}}
    for s in SYSTEMS:
        judged = [(r[s]["reply"], r["judge"][s]) for r in rows if r["judge"].get(s)]
        if not judged:
            continue
        sent = [j["would_send"] for _, j in judged]
        out["systems"][s] = {"judged": len(judged), "would_send": sum(sent) / len(sent)}
        # verbosity: does a longer draft get approved more often?
        lengths = [len(t) for t, _ in judged]
        cut = statistics.median(lengths)
        short = [j["would_send"] for t, j in judged if len(t) <= cut]
        long_ = [j["would_send"] for t, j in judged if len(t) > cut]
        if short and long_:
            out["verbosity"][s] = {
                "median_chars": cut,
                "would_send_short": sum(short) / len(short),
                "would_send_long": sum(long_) / len(long_),
                "gap_pp": round(100 * (sum(long_) / len(long_) - sum(short) / len(short)), 1),
            }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="final_vertex")
    ap.add_argument("--split", default="golden")
    args = ap.parse_args()
    res = analyse(args.run, args.split)

    lines = [f"# Judge robustness — {args.run}/{args.split} (n={res['n']})\n",
             "Bias checks that need no human ratings. They cannot tell you the judge is *right* —",
             "only whether it is responding to something other than reply quality.\n",
             "| System | Judged | Would-send |", "|---|---|---|"]
    for s, v in res["systems"].items():
        lines.append(f"| {s} | {v['judged']} | {v['would_send']:.1%} |")
    lines += ["\n## Verbosity bias\n",
              "| System | Median chars | Short drafts | Long drafts | Gap |", "|---|---|---|---|---|"]
    for s, v in res["verbosity"].items():
        lines.append(f"| {s} | {v['median_chars']:.0f} | {v['would_send_short']:.1%} | "
                     f"{v['would_send_long']:.1%} | {v['gap_pp']:+.1f}pp |")
    lines += ["\n## Not yet measurable here\n",
              "- **Self-preference**: needs a judge from a different model family scoring the same",
              "  drafts. `GEMINI_JUDGE_MODEL` / `--judge-model` makes this a one-command run once a",
              "  second provider key exists.",
              "- **Position bias**: this rubric scores one draft at a time rather than ranking a",
              "  pair, so order cannot influence it by construction — the cheapest way to avoid the",
              "  bias is not to create it.\n",
              "Agreement with a human is the check that actually matters; see reports/judge_agreement.md."]
    path = ROOT / "reports" / "judge_robustness.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (ROOT / "data" / "processed" / "judge_robustness.json").write_text(
        json.dumps(res, indent=1), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
