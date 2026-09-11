"""Silver labels for the dev set, produced by an LLM with the human labelling guide.

The dev set drives the improvement loop; the hand-labelled golden set is kept for
the final numbers only. Silver != gold: agreement between the two is reported.

Run:  python -m src.silver_label [dev|golden]
"""
import json
import sys

from src.config import PROCESSED
from src.llm import complete_batch, parse_json
from src.make_eval_sets import DEV_FILE, GOLDEN_FILE, read_jsonl
from src.prompts import LABELER_SYSTEM, labeler_user
from src.taxonomy import ESCALATION_CODES, INTENT_KEYS


def silver_path(name: str):
    return PROCESSED / f"{name}_silver_labels.jsonl"


def validate(lab: dict | None) -> dict | None:
    if not lab or lab.get("intent") not in INTENT_KEYS or not isinstance(lab.get("escalate"), bool):
        return None
    reason = lab.get("escalation_reason")
    return {"intent": lab["intent"], "escalate": lab["escalate"],
            "escalation_reason": reason if lab["escalate"] and reason in ESCALATION_CODES else None}


def main(name: str = "dev"):
    examples = read_jsonl(DEV_FILE if name == "dev" else GOLDEN_FILE)
    raw = complete_batch("labeler", [{"system": LABELER_SYSTEM, "user": labeler_user(ex)}
                                     for ex in examples])
    labels = {ex["msg_id"]: validate(parse_json(r)) for ex, r in zip(examples, raw)}
    done = {k: v for k, v in labels.items() if v}
    print(f"{len(done)}/{len(examples)} {name} examples labelled "
          f"({sum(r is None for r in raw)} pending, "
          f"{sum(r is not None and labels[ex['msg_id']] is None for ex, r in zip(examples, raw))} invalid)")
    with open(silver_path(name), "w", encoding="utf-8") as f:
        for msg_id, lab in done.items():
            f.write(json.dumps({"msg_id": msg_id, **lab}) + "\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dev")
