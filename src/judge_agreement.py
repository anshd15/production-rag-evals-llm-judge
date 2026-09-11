"""How much should we trust the LLM judge? Compare it with a human on the same drafts.

  python -m src.judge_agreement make  --run <run>   # sample drafts to rate -> data/processed/rating_set.jsonl
  (rate them in the labelling tool, tab 2)
  python -m src.judge_agreement score --run <run>   # -> reports/judge_agreement.md

Drafts are a mix of agent and baseline replies so the human sees both good and bad
ones (agreement on an all-good set is uninformative), shown without the system name.
"""
import argparse
import json
import random

import numpy as np

from src.config import PROCESSED, ROOT, SEED
from src.evaluate import JUDGE_KEYS, judge
from src.label_app import RATING_SET, RATINGS
from src.make_eval_sets import GOLDEN_FILE, read_jsonl
from src.metrics import kappa

MIX = {"agent": 30, "simple": 20, "trivial": 10}


def make(run: str):
    rows = read_jsonl(ROOT / "runs" / run / "golden" / "predictions.jsonl")
    examples = {e["msg_id"]: e for e in read_jsonl(GOLDEN_FILE)}
    rng = random.Random(SEED)
    items = []
    for system, n in MIX.items():
        pool = [r for r in rows if r[system] and r[system]["reply"]]
        for r in rng.sample(pool, min(n, len(pool))):
            ex = examples[r["msg_id"]]
            items.append({"item_id": f"{r['msg_id']}:{system}", "msg_id": r["msg_id"], "system": system,
                          "context": ex["context"], "text": ex["text"],
                          "brand_reply": ex["brand_reply"], "draft": r[system]["reply"]})
    rng.shuffle(items)
    with open(RATING_SET, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"{len(items)} drafts to rate -> {RATING_SET}")


def score(run: str):
    items = {it["item_id"]: it for it in read_jsonl(RATING_SET)}
    human = {r["item_id"]: r for r in read_jsonl(RATINGS)} if RATINGS.exists() else {}
    rated = [items[k] for k in items if k in human]
    if not rated:
        print("No human ratings yet.")
        return
    examples = {e["msg_id"]: e for e in read_jsonl(GOLDEN_FILE)}
    verdicts = judge([examples[it["msg_id"]] for it in rated], [it["draft"] for it in rated])
    pairs = [(human[it["item_id"]], v, it) for it, v in zip(rated, verdicts) if v]
    lines = [f"# Judge vs human agreement ({len(pairs)} drafts, run `{run}`)\n",
             "| Criterion | Human pass | Judge pass | Agreement | Cohen's κ |", "|---|---|---|---|---|"]
    out = {}
    for k in JUDGE_KEYS:
        h = [bool(p[0][k]) for p in pairs]
        j = [bool(p[1][k]) for p in pairs]
        agree = float(np.mean(np.array(h) == np.array(j)))
        kap = kappa(h, j)
        out[k] = {"human_pass": float(np.mean(h)), "judge_pass": float(np.mean(j)),
                  "agreement": agree, "kappa": kap}
        lines.append(f"| {k} | {np.mean(h):.0%} | {np.mean(j):.0%} | {agree:.0%} | "
                     f"{'n/a' if kap != kap else f'{kap:.2f}'} |")
    hw = [p[0]["would_send"] for p in pairs]
    jw = [p[1]["would_send"] for p in pairs]
    lines += ["\n**would_send confusion (rows = human, cols = judge):**\n",
              "| | judge yes | judge no |", "|---|---|---|",
              f"| human yes | {sum(h and j for h, j in zip(hw, jw))} | {sum(h and not j for h, j in zip(hw, jw))} |",
              f"| human no | {sum(not h and j for h, j in zip(hw, jw))} | {sum(not h and not j for h, j in zip(hw, jw))} |"]
    by_sys = {}
    for h, v, it in pairs:
        by_sys.setdefault(it["system"], []).append((h["would_send"], v["would_send"]))
    lines.append("\n**would_send by system (human vs judge):** " + ", ".join(
        f"{s}: {np.mean([a for a, _ in xs]):.0%} vs {np.mean([b for _, b in xs]):.0%} (n={len(xs)})"
        for s, xs in by_sys.items()))
    disagreements = [(h, v, it) for h, v, it in pairs if h["would_send"] != v["would_send"]]
    if disagreements:
        lines.append("\n## Disagreements on would_send\n")
        for h, v, it in disagreements[:15]:
            lines.append(f"- **Tweet:** {it['text'][:160]}\n  - Draft: {it['draft'][:200]}\n"
                         f"  - Human: {'send' if h['would_send'] else 'edit'} · Judge: "
                         f"{'send' if v['would_send'] else 'edit'} — {v.get('rationale', '')[:200]}")
    (ROOT / "reports" / "judge_agreement.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (PROCESSED / "judge_agreement.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("\n".join(lines[:4 + len(JUDGE_KEYS)]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["make", "score"])
    ap.add_argument("--run", default="final")
    a = ap.parse_args()
    make(a.run) if a.cmd == "make" else score(a.run)
