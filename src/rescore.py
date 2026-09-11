"""Re-score an existing run's saved predictions against the current labels.

No model calls: this isolates the effect of a *label/definition* change from the
effect of an agent change.

  python -m src.rescore --run v1 --split dev --out v1b
"""
import argparse
import json

import numpy as np

from src.config import ROOT
from src.evaluate import SYSTEMS, load_labels, summary_md
from src.make_eval_sets import DEV_FILE, GOLDEN_FILE, read_jsonl
from src.metrics import intent_accuracy, paired_bootstrap_diff


def rescore(run: str, split: str, out: str) -> str:
    rows = read_jsonl(ROOT / "runs" / run / split / "predictions.jsonl")
    examples = {e["msg_id"]: e for e in read_jsonl(DEV_FILE if split == "dev" else GOLDEN_FILE)}
    labels = load_labels(split)
    exs = [examples[r["msg_id"]] for r in rows]
    preds = {s: [r[s] for r in rows] for s in SYSTEMS}
    judgements = {s: [r["judge"][s] for r in rows] for s in SYSTEMS}

    from src.evaluate import score_system
    metrics = {s: score_system(exs, preds[s], labels, judgements[s]) for s in SYSTEMS}
    ids = [e["msg_id"] for e in exs]
    have = [i for i, m in enumerate(ids) if m in labels]
    comparisons = {}
    if have:
        yt = [labels[ids[i]]["intent"] for i in have]
        for b in ["simple", "trivial"]:
            comparisons[f"intent accuracy vs {b}"] = paired_bootstrap_diff(
                intent_accuracy, yt, [preds["agent"][i]["intent"] for i in have],
                [preds[b][i]["intent"] for i in have])
    both = [i for i in range(len(exs)) if judgements["agent"][i] and judgements["simple"][i]]
    if both:
        comparisons["would-send vs simple"] = paired_bootstrap_diff(
            lambda y, p: float(np.mean(p.astype(bool))), [0] * len(both),
            [judgements["agent"][i]["would_send"] for i in both],
            [judgements["simple"][i]["would_send"] for i in both])

    out_dir = ROOT / "runs" / out / split
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "predictions.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r | {"label": labels.get(r["msg_id"])}, ensure_ascii=False) + "\n")
    meta = json.loads((ROOT / "runs" / run / split / "metrics.json").read_text(encoding="utf-8"))["meta"]
    meta |= {"run": out, "rescored_from": run}
    (out_dir / "metrics.json").write_text(json.dumps(
        {"meta": meta, "systems": metrics, "comparisons": comparisons}, indent=1), encoding="utf-8")
    md = summary_md(split, f"{out} (predictions from {run}, current labels)", metrics, comparisons, len(exs))
    (out_dir / "summary.md").write_text(md, encoding="utf-8")
    return md


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print(rescore(a.run, a.split, a.out))
