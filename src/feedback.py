"""Capture what the human did with the agent's draft — the flywheel.

Every decision the agent makes is written to data/feedback/decisions.jsonl.
When an agent accepts, edits or rejects a draft, that outcome is appended too.
Two things fall out of the pairing, and neither is available offline:

  - edit rate and rejection reasons per intent: live quality, no judge needed
  - every edited draft is a labelled example for the next golden set

Run `python -m src.feedback report` for the current picture.
"""
import json
import sys
import time
from collections import Counter

from src.config import ROOT

STORE = ROOT / "data" / "feedback"
DECISIONS = STORE / "decisions.jsonl"
OUTCOMES = STORE / "outcomes.jsonl"
ACTIONS = ("accepted", "edited", "rejected", "escalated_by_human")


def _append(path, rec):
    STORE.mkdir(parents=True, exist_ok=True)
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def record_decision(request_id: str, prediction: dict, example: dict | None = None,
                    evidence: list[dict] | None = None):
    """Store enough for a human to review the decision later without re-running anything."""
    _append(DECISIONS, {"request_id": request_id, "intent": prediction["intent"],
                        "escalate": prediction["escalate"],
                        "escalation_reason": prediction.get("escalation_reason"),
                        "confidence": prediction.get("confidence"),
                        "reason": prediction.get("reason", ""),
                        "reply": prediction["reply"],
                        "guardrail": prediction.get("guardrail"),
                        "pii_detected": prediction.get("pii_detected"),
                        "text": (example or {}).get("text", ""),
                        "context": (example or {}).get("context", []),
                        "evidence": evidence or []})


def record_outcome(request_id: str, action: str, final_reply: str = "", note: str = ""):
    if action not in ACTIONS:
        raise ValueError(f"action must be one of {ACTIONS}")
    _append(OUTCOMES, {"request_id": request_id, "action": action,
                       "final_reply": final_reply, "note": note})


def _read(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")] if path.exists() else []


def pending_review() -> list[dict]:
    """Decisions a human has not acted on yet.

    Escalations sort first because somebody is waiting on them; auto-handled drafts
    stay in the queue too, so quality is sampled rather than assumed.
    """
    reviewed = {o["request_id"] for o in _read(OUTCOMES)}
    waiting = [d for d in _read(DECISIONS) if d["request_id"] not in reviewed]
    return sorted(waiting, key=lambda d: (not d["escalate"], d["ts"]))


def report() -> dict:
    decisions = {d["request_id"]: d for d in _read(DECISIONS)}
    outcomes = _read(OUTCOMES)
    actions = Counter(o["action"] for o in outcomes)
    reviewed = len(outcomes)
    by_intent = Counter(decisions[o["request_id"]]["intent"] for o in outcomes
                        if o["action"] in ("edited", "rejected") and o["request_id"] in decisions)
    return {
        "decisions": len(decisions),
        "reviewed": reviewed,
        "actions": dict(actions),
        "accept_rate": round(actions["accepted"] / reviewed, 3) if reviewed else None,
        "most_edited_intents": by_intent.most_common(5),
    }


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        print(json.dumps(report(), indent=1))
    else:
        print(__doc__)
