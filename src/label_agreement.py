"""Human (golden) vs LLM (silver) labels on the same 200 messages.

Answers two questions the report needs:
  - how much of the agent's remaining error could be label noise?
  - could the cheap LLM labels have replaced the hand-labelling?

  python -m src.label_agreement    ->  reports/label_agreement.md
"""
import collections
import json

from src.config import PROCESSED, ROOT
from src.evaluate import GOLDEN_LABELS
from src.make_eval_sets import GOLDEN_FILE, read_jsonl
from src.metrics import kappa
from src.silver_label import silver_path


def main():
    if not GOLDEN_LABELS.exists():
        print("No human labels yet — label the golden set first (python -m src.label_app).")
        return
    human = {r["msg_id"]: r for r in read_jsonl(GOLDEN_LABELS)}
    silver = {r["msg_id"]: r for r in read_jsonl(silver_path("golden"))}
    texts = {e["msg_id"]: e["text"] for e in read_jsonl(GOLDEN_FILE)}
    ids = [i for i in human if i in silver]
    if not ids:
        print("No overlap between human and silver labels.")
        return

    hi = [human[i]["intent"] for i in ids]
    si = [silver[i]["intent"] for i in ids]
    he = [bool(human[i]["escalate"]) for i in ids]
    se = [bool(silver[i]["escalate"]) for i in ids]
    intent_agree = sum(a == b for a, b in zip(hi, si)) / len(ids)
    esc_agree = sum(a == b for a, b in zip(he, se)) / len(ids)

    lines = [f"# Human vs LLM labels ({len(ids)} golden messages)\n",
             "| | Agreement | Cohen's κ |", "|---|---|---|",
             f"| intent (11 classes) | {intent_agree:.0%} | {kappa(hi, si):.2f} |",
             f"| escalate (binary) | {esc_agree:.0%} | {kappa(he, se):.2f} |",
             f"\nHuman escalate rate {sum(he) / len(he):.0%} vs LLM {sum(se) / len(se):.0%}.\n",
             "## Where they disagree on intent\n"]
    pairs = collections.Counter((h, s) for h, s in zip(hi, si) if h != s)
    lines += [f"- human **{h}** vs LLM **{s}**: {n}" for (h, s), n in pairs.most_common(10)]
    lines.append("\n## Examples (human vs LLM)\n")
    shown = 0
    for i in ids:
        if human[i]["intent"] != silver[i]["intent"] or human[i]["escalate"] != silver[i]["escalate"]:
            lines.append(f"- {texts[i][:180]}\n  - human: {human[i]['intent']} / "
                         f"{'escalate' if human[i]['escalate'] else 'auto'}"
                         f"{' — ' + human[i]['note'] if human[i].get('note') else ''}\n"
                         f"  - LLM: {silver[i]['intent']} / "
                         f"{'escalate' if silver[i]['escalate'] else 'auto'}")
            shown += 1
            if shown >= 15:
                break
    (ROOT / "reports" / "label_agreement.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (PROCESSED / "label_agreement.json").write_text(json.dumps(
        {"n": len(ids), "intent_agreement": intent_agree, "intent_kappa": kappa(hi, si),
         "escalate_agreement": esc_agree, "escalate_kappa": kappa(he, se)}, indent=1), encoding="utf-8")
    print("\n".join(lines[:6]))


if __name__ == "__main__":
    main()
