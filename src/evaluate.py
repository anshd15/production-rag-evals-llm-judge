"""Run agent + baselines on a split, judge every reply, score against labels.

  python -m src.evaluate --split dev --run agent_v1      # silver labels, used by the loop
  python -m src.evaluate --split golden --run final      # human labels, final numbers

Writes runs/<run>/<split>/{predictions.jsonl, judgements.jsonl, metrics.json, summary.md}.
Re-entrant: with the stand-in provider it stops after queuing missing LLM calls;
answer them, run `python -m src.llm ingest`, and re-run (cached calls are free).
"""
import argparse
import json
import os
import sys

import numpy as np

from src import agent
from src.baselines import Baselines
from src.config import PROCESSED, ROOT
from src.llm import complete_batch, model_for, parse_json, provider
from src.make_eval_sets import DEV_FILE, GOLDEN_FILE, read_jsonl
from src.metrics import (bootstrap_ci, confusion, escalation_stats, intent_accuracy,
                         intent_macro_f1, paired_bootstrap_diff)
from src.prompts import JUDGE_CRITERIA, JUDGE_SYSTEM, judge_user
from src.silver_label import silver_path
from src.taxonomy import INTENT_KEYS

GOLDEN_LABELS = PROCESSED / "golden_labels.jsonl"
SYSTEMS = ["agent", "simple", "trivial"]
JUDGE_KEYS = list(JUDGE_CRITERIA) + ["would_send"]


def load_labels(split: str) -> dict[int, dict]:
    path = silver_path("dev") if split == "dev" else GOLDEN_LABELS
    if not path.exists():
        return {}
    labels = {}
    for rec in read_jsonl(path):  # later lines override earlier ones (re-labelling)
        labels[int(rec["msg_id"])] = rec
    return labels


def judge(examples, replies) -> list[dict | None]:
    reqs = [{"system": JUDGE_SYSTEM, "user": judge_user(ex, r)} for ex, r in zip(examples, replies)]
    out = []
    for raw in complete_batch("judge", reqs):
        j = parse_json(raw)
        out.append({k: bool(j.get(k)) for k in JUDGE_KEYS} | {"rationale": j.get("rationale", "")}
                   if j and all(k in j for k in JUDGE_KEYS) else None)
    return out


def score_system(examples, preds, labels, judgements) -> dict:
    ids = [ex["msg_id"] for ex in examples]
    have = [i for i, m in enumerate(ids) if m in labels]
    res = {"n_labelled": len(have)}
    if have:
        yt = [labels[ids[i]]["intent"] for i in have]
        yp = [preds[i]["intent"] for i in have]
        res["intent_accuracy"] = bootstrap_ci(intent_accuracy, yt, yp)
        res["intent_macro_f1"] = bootstrap_ci(lambda a, b: intent_macro_f1(a, b, INTENT_KEYS), yt, yp)
        et = [labels[ids[i]]["escalate"] for i in have]
        ep = [preds[i]["escalate"] for i in have]
        res["escalation"] = escalation_stats(et, ep)
        res["escalation_recall_ci"] = bootstrap_ci(
            lambda a, b: escalation_stats(a, b)["recall"], et, ep)
        res["confusion"] = confusion(yt, yp, INTENT_KEYS)
        per_class = {}
        for k in INTENT_KEYS:
            tp = sum(t == k and p == k for t, p in zip(yt, yp))
            n_true, n_pred = yt.count(k), yp.count(k)
            per_class[k] = {"support": n_true, "precision": tp / n_pred if n_pred else None,
                            "recall": tp / n_true if n_true else None}
        res["per_class"] = per_class

    ok = [j for j in judgements if j]
    if ok:
        res["judged"] = len(ok)
        res["reply_pass_rates"] = {k: float(np.mean([j[k] for j in ok])) for k in JUDGE_KEYS}
        ws = [bool(j["would_send"]) for j in ok]
        res["would_send"] = bootstrap_ci(lambda x: float(np.mean(x.astype(bool))), ws)
        auto = [j["would_send"] for p, j in zip(preds, judgements) if j and not p["escalate"]]
        res["would_send_on_auto_sent"] = float(np.mean(auto)) if auto else None
        if have:
            # Of ALL messages: auto-sent AND should be auto AND reply approved
            good, harmful = [], []
            for i in have:
                j, p, lab = judgements[i], preds[i], labels[ids[i]]
                if j is None:
                    continue
                auto_sent = not p["escalate"]
                good.append(auto_sent and not lab["escalate"] and j["would_send"])
                harmful.append(auto_sent and (lab["escalate"] or not j["safe"] or not j["would_send"]))
            res["good_automation_rate"] = bootstrap_ci(lambda x: float(np.mean(x.astype(bool))), good)
            res["bad_auto_send_rate"] = bootstrap_ci(lambda x: float(np.mean(x.astype(bool))), harmful)
    res["reply_over_280"] = float(np.mean([len(p["reply"]) > 280 for p in preds]))
    return res


def fmt(ci) -> str:
    if ci is None:
        return "—"
    if isinstance(ci, (list, tuple)):
        return f"{ci[0]:.1%} [{ci[1]:.0%}–{ci[2]:.0%}]"
    return f"{ci:.1%}"


def summary_md(split, run, metrics, comparisons, n) -> str:
    lines = [f"# {run} — {split} split (n={n}, provider={provider()}, agent={model_for('agent')}, "
             f"judge={model_for('judge')})\n",
             "| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | "
             "Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s, m in metrics.items():
        e = m.get("escalation", {})
        lines.append(" | ".join([
            f"| {s}", fmt(m.get("intent_accuracy")), fmt(m.get("intent_macro_f1")),
            fmt(m.get("escalation_recall_ci")), fmt(e.get("precision")), fmt(e.get("automation_rate")),
            fmt(e.get("unsafe_auto_rate")), fmt(m.get("would_send")),
            fmt(m.get("would_send_on_auto_sent")), fmt(m.get("good_automation_rate")),
            fmt(m.get("bad_auto_send_rate"))]) + " |")
    if comparisons:
        lines.append("\n**Paired bootstrap, agent minus baseline (95% CI):**\n")
        for name, c in comparisons.items():
            lines.append(f"- {name}: {c['diff']:+.1%} [{c['lo']:+.1%}, {c['hi']:+.1%}], "
                         f"P(agent not better) = {c['p_not_better']:.3f}")
    a = metrics.get("agent", {})
    if a.get("reply_pass_rates"):
        lines.append("\n**Agent reply rubric pass rates:** " + ", ".join(
            f"{k} {v:.0%}" for k, v in a["reply_pass_rates"].items()))
    if a.get("per_class"):
        lines.append("\n| Intent | Support | Precision | Recall |\n|---|---|---|---|")
        for k, v in a["per_class"].items():
            if v["support"] or v["precision"] is not None:
                p = "—" if v["precision"] is None else f"{v['precision']:.0%}"
                r = "—" if v["recall"] is None else f"{v['recall']:.0%}"
                lines.append(f"| {k} | {v['support']} | {p} | {r} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "golden"], default="dev")
    ap.add_argument("--run", default="scratch")
    args = ap.parse_args()

    examples = read_jsonl(DEV_FILE if args.split == "dev" else GOLDEN_FILE)
    labels = load_labels(args.split)
    dev_examples = read_jsonl(DEV_FILE)
    dev_labels = load_labels("dev")
    train = [(e, dev_labels[e["msg_id"]]) for e in dev_examples if e["msg_id"] in dev_labels]
    base = Baselines([e for e, _ in train], [l for _, l in train])

    preds = {"agent": agent.run(examples)}
    if args.split == "dev":  # baselines are trained on dev: use out-of-fold predictions there
        train_ids = [e["msg_id"] for e, _ in train]
        oof = dict(zip(train_ids, base.simple([e for e, _ in train], in_sample=True)))
        preds["simple"] = [oof.get(e["msg_id"]) or base.simple([e])[0] for e in examples]
    else:
        preds["simple"] = base.simple(examples)
    preds["trivial"] = base.trivial(examples)

    pending = sum(p is None for p in preds["agent"])
    judgements = {}
    for s in SYSTEMS:
        idx = [i for i, p in enumerate(preds[s]) if p is not None and p["reply"]]
        js = judge([examples[i] for i in idx], [preds[s][i]["reply"] for i in idx])
        judgements[s] = [None] * len(examples)
        for i, j in zip(idx, js):
            judgements[s][i] = j
    pending_judge = sum(1 for s in SYSTEMS for i, p in enumerate(preds[s])
                        if p is not None and p["reply"] and judgements[s][i] is None)
    if pending or pending_judge:
        print(f"PENDING: {pending} agent calls, {pending_judge} judge calls queued. "
              "Answer them, run `python -m src.llm ingest`, then re-run this command.")
        sys.exit(3)

    out_dir = ROOT / "runs" / args.run / args.split
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "predictions.jsonl", "w", encoding="utf-8") as f:
        for i, ex in enumerate(examples):
            f.write(json.dumps({"msg_id": ex["msg_id"], "text": ex["text"],
                                "label": labels.get(ex["msg_id"]),
                                **{s: preds[s][i] for s in SYSTEMS},
                                "judge": {s: judgements[s][i] for s in SYSTEMS}},
                               ensure_ascii=False) + "\n")

    metrics = {s: score_system(examples, preds[s], labels, judgements[s]) for s in SYSTEMS}
    comparisons = {}
    ids = [e["msg_id"] for e in examples]
    have = [i for i, m in enumerate(ids) if m in labels]
    if have:
        yt = [labels[ids[i]]["intent"] for i in have]
        for b in ["simple", "trivial"]:
            comparisons[f"intent accuracy vs {b}"] = paired_bootstrap_diff(
                intent_accuracy, yt, [preds["agent"][i]["intent"] for i in have],
                [preds[b][i]["intent"] for i in have])
    both = [i for i in range(len(examples)) if judgements["agent"][i] and judgements["simple"][i]]
    if both:
        comparisons["would-send vs simple"] = paired_bootstrap_diff(
            lambda y, p: float(np.mean(p.astype(bool))), [0] * len(both),
            [judgements["agent"][i]["would_send"] for i in both],
            [judgements["simple"][i]["would_send"] for i in both])
    meta = {"split": args.split, "run": args.run, "n": len(examples), "provider": provider(),
            "agent_model": model_for("agent"), "judge_model": model_for("judge"),
            "label_source": "silver (LLM)" if args.split == "dev" else "human (golden)"}
    (out_dir / "metrics.json").write_text(json.dumps(
        {"meta": meta, "systems": metrics, "comparisons": comparisons}, indent=1), encoding="utf-8")
    md = summary_md(args.split, args.run, metrics, comparisons, len(examples))
    (out_dir / "summary.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
