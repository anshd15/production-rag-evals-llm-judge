"""Export the golden set as an offline labelling pack, and import the answers back.

  python -m src.export_labelling export   -> labelling/questions.json + answers_template.json
  python -m src.export_labelling import labelling/answers.json

The questions file deliberately contains NO model suggestion and NOT the reply
SpotifyCares actually sent: the label has to come from what the agent sees.
Answers use a short code per message, e.g. "4a" (technical_issue, auto-handle) or
"1eb" (billing_payment, escalate, reason billing).
"""
import json
import sys

from src.config import PROCESSED, ROOT
from src.evaluate import GOLDEN_LABELS
from src.make_eval_sets import GOLDEN_FILE, read_jsonl
from src.taxonomy import ESCALATION_REASONS, INTENTS

PACK = ROOT / "labelling"
QUESTIONS = PACK / "questions.json"
TEMPLATE = PACK / "answers_template.json"

INTENT_CODES = {str((i + 1) % 10) if i < 10 else "x": it["key"] for i, it in enumerate(INTENTS)}
REASON_CODES = {"b": "billing", "s": "security", "c": "account_specific",
                "t": "troubleshooting_exhausted", "r": "repeat_contact", "k": "risk"}
CODE_OF_INTENT = {v: k for k, v in INTENT_CODES.items()}
CODE_OF_REASON = {v: k for k, v in REASON_CODES.items()}


def code_for(label: dict) -> str:
    code = CODE_OF_INTENT[label["intent"]]
    return code + ("e" + CODE_OF_REASON[label["escalation_reason"]] if label["escalate"] else "a")


def parse_code(code: str) -> dict | str:
    """Returns a label dict, or an error string."""
    c = (code or "").strip().lower().replace(" ", "")
    if not c:
        return "empty"
    if c[0] not in INTENT_CODES:
        return f"unknown intent code {c[0]!r} (use {'/'.join(INTENT_CODES)})"
    intent = INTENT_CODES[c[0]]
    rest = c[1:]
    if rest == "a":
        return {"intent": intent, "escalate": False, "escalation_reason": None}
    if rest.startswith("e"):
        r = rest[1:]
        if r not in REASON_CODES:
            return f"escalate needs a reason letter ({'/'.join(REASON_CODES)}), got {r!r}"
        return {"intent": intent, "escalate": True, "escalation_reason": REASON_CODES[r]}
    return f"second character must be 'a' or 'e', got {rest!r}"


def export():
    PACK.mkdir(exist_ok=True)
    golden = read_jsonl(GOLDEN_FILE)
    existing = {r["msg_id"]: r for r in read_jsonl(GOLDEN_LABELS)} if GOLDEN_LABELS.exists() else {}
    questions, answers = [], {}
    for n, ex in enumerate(golden, 1):
        questions.append({
            "n": n,
            "msg_id": ex["msg_id"],
            "thread_so_far": [{"who": "Customer" if t["role"] == "customer" else
                               ("SpotifyCares" if t["role"] == "Spotify" else "Someone else"),
                               "text": t["text"]} for t in ex["context"]],
            "incoming_tweet": ex["text"],
        })
        prev = existing.get(ex["msg_id"])
        # keep only labels made without a suggestion on screen
        answers[str(ex["msg_id"])] = code_for(prev) if prev and prev.get("source", "blind") == "blind" else ""
    QUESTIONS.write_text(json.dumps(questions, ensure_ascii=False, indent=1), encoding="utf-8")
    TEMPLATE.write_text(json.dumps({"labels": answers}, ensure_ascii=False, indent=1), encoding="utf-8")
    done = sum(1 for v in answers.values() if v)
    print(f"{len(questions)} questions -> {QUESTIONS}")
    print(f"answer template -> {TEMPLATE}  ({done} pre-filled from your blind labels, "
          f"{len(answers) - done} to fill)")


def import_answers(path: str):
    data = json.loads(open(path, encoding="utf-8").read())
    labels = data.get("labels", data)
    golden_ids = [e["msg_id"] for e in read_jsonl(GOLDEN_FILE)]
    valid, errors, blank = {}, [], 0
    for msg_id in golden_ids:
        raw = labels.get(str(msg_id), labels.get(msg_id, ""))
        parsed = parse_code(raw)
        if parsed == "empty":
            blank += 1
        elif isinstance(parsed, str):
            errors.append(f"  msg {msg_id}: {parsed}")
        else:
            valid[msg_id] = parsed
    unknown = set(map(str, labels)) - set(map(str, golden_ids))
    if unknown:
        errors.append(f"  {len(unknown)} ids not in the golden set: {sorted(unknown)[:5]}")
    for e in errors[:20]:
        print(e)
    if errors:
        print(f"{len(errors)} problem(s) — nothing was written. Fix them and re-run.")
        return
    with open(GOLDEN_LABELS, "w", encoding="utf-8") as f:
        for msg_id, lab in valid.items():
            f.write(json.dumps({"msg_id": msg_id, **lab, "note": "", "labeller": "human",
                                "source": "blind"}, ensure_ascii=False) + "\n")
    print(f"wrote {len(valid)} labels -> {GOLDEN_LABELS}  ({blank} left blank)")
    if len(valid) < 150:
        print(f"⚠  the brief asks for 150-250 labelled examples; you have {len(valid)}.")
    print("Next:  python -m src.finish")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "export"
    export() if cmd == "export" else import_answers(sys.argv[2])
