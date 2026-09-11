"""Failure analysis for one run: where does the agent go wrong, with real examples.

  python -m src.analyze --run v1 --split dev   -> runs/<run>/<split>/failures.md
"""
import argparse
from collections import Counter

from src.config import ROOT
from src.make_eval_sets import DEV_FILE, GOLDEN_FILE, read_jsonl
from src.prompts import JUDGE_CRITERIA


def show(ex, row, extra="") -> str:
    a = row["agent"]
    ctx = f" _(after: {ex['context'][-1]['text'][:90]})_" if ex["context"] else ""
    lab = row["label"] or {}
    return (f"- **{ex['text'][:220]}**{ctx}\n"
            f"  - gold: {lab.get('intent')} / {'ESC:' + str(lab.get('escalation_reason')) if lab.get('escalate') else 'auto'}"
            f" · agent: {a['intent']} ({a['confidence']:.2f}) / "
            f"{'ESC:' + str(a['escalation_reason']) if a['escalate'] else 'auto'}\n"
            f"  - agent reply: {a['reply'][:240]}\n"
            f"  - brand reply: {ex['brand_reply'][:200]}" + (f"\n  - {extra}" if extra else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--n", type=int, default=8)
    args = ap.parse_args()
    run_dir = ROOT / "runs" / args.run / args.split
    rows = read_jsonl(run_dir / "predictions.jsonl")
    examples = {e["msg_id"]: e for e in read_jsonl(DEV_FILE if args.split == "dev" else GOLDEN_FILE)}
    labelled = [r for r in rows if r["label"]]
    out = [f"# Failure analysis — {args.run} / {args.split}\n"]

    pairs = Counter((r["label"]["intent"], r["agent"]["intent"]) for r in labelled
                    if r["label"]["intent"] != r["agent"]["intent"])
    out.append(f"## Intent confusions ({sum(pairs.values())} errors / {len(labelled)})\n")
    out += [f"- gold **{g}** → predicted **{p}**: {n}" for (g, p), n in pairs.most_common(12)]
    for (g, p), _ in pairs.most_common(4):
        out.append(f"\n### {g} → {p}\n")
        out += [show(examples[r["msg_id"]], r) for r in labelled
                if r["label"]["intent"] == g and r["agent"]["intent"] == p][:3]

    fn = [r for r in labelled if r["label"]["escalate"] and not r["agent"]["escalate"]]
    fp = [r for r in labelled if not r["label"]["escalate"] and r["agent"]["escalate"]]
    out.append(f"\n## Missed escalations — auto-sent but should escalate ({len(fn)})\n")
    out.append("By gold reason: " + ", ".join(
        f"{k}: {v}" for k, v in Counter(r["label"]["escalation_reason"] for r in fn).most_common()))
    out += [show(examples[r["msg_id"]], r) for r in fn[:args.n]]
    out.append(f"\n## Needless escalations ({len(fp)})\n")
    out.append("By agent reason: " + ", ".join(
        f"{k}: {v}" for k, v in Counter(r["agent"]["escalation_reason"] for r in fp).most_common()))
    out += [show(examples[r["msg_id"]], r, f"agent reason: {r['agent']['reason']}") for r in fp[:args.n]]

    judged = [r for r in rows if r["judge"]["agent"]]
    out.append(f"\n## Reply failures by rubric criterion ({len(judged)} judged)\n")
    for k in list(JUDGE_CRITERIA) + ["would_send"]:
        fails = [r for r in judged if not r["judge"]["agent"][k]]
        out.append(f"- {k}: {len(fails)} fails ({len(fails) / max(1, len(judged)):.0%})")
    for k in JUDGE_CRITERIA:
        fails = [r for r in judged if not r["judge"]["agent"][k]]
        if fails:
            out.append(f"\n### Fails `{k}`\n")
            out += [show(examples[r["msg_id"]], r, "judge: " + r["judge"]["agent"]["rationale"][:220])
                    for r in fails[:5]]
    guard = Counter(r["agent"].get("guardrail") for r in rows if r["agent"].get("guardrail"))
    out.append(f"\n## Guardrail triggers: {dict(guard) or 'none'}")
    lengths = [len(r["agent"]["reply"]) for r in rows]
    out.append(f"\nReply length: median {sorted(lengths)[len(lengths) // 2]}, max {max(lengths)}")
    (run_dir / "failures.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {run_dir / 'failures.md'}")


if __name__ == "__main__":
    main()
