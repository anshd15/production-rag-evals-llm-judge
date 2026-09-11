"""The support agent: retrieve similar past cases -> one LLM call -> deterministic guardrails."""
import re

from src.llm import complete_batch, parse_json
from src.prompts import AGENT_SYSTEM, agent_user
from src.retrieval import Retriever
from src.taxonomy import ESCALATION_CODES, INTENT_KEYS

TOP_K = 5
MAX_LEN = 280

# Hard triggers the model is not trusted to catch on its own.
RISK_RE = re.compile(r"\b(lawyers?|sue|suing|lawsuit|attorney|legal action|trading standards|"
                     r"ombudsman|kill myself|suicid\w*|self[- ]harm)\b", re.I)


def truncate(reply: str, limit: int = MAX_LEN) -> str:
    if len(reply) <= limit:
        return reply
    cut = reply[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(",;:- ") + "…"


def guardrails(pred: dict | None, ex: dict) -> dict:
    """Validate the model output and apply non-negotiable routing rules."""
    if not pred or pred.get("intent") not in INTENT_KEYS or not isinstance(pred.get("escalate"), bool):
        return {"intent": "other", "confidence": 0.0, "escalate": True,
                "escalation_reason": "risk", "reason": "Fallback: model output was unusable.",
                "reply": "", "guardrail": "invalid_output"}
    out = {
        "intent": pred["intent"],
        "confidence": float(pred.get("confidence") or 0),
        "escalate": pred["escalate"],
        "escalation_reason": pred.get("escalation_reason") if pred["escalate"] else None,
        "reason": str(pred.get("reason", "")),
        "reply": truncate(str(pred.get("reply", "")).strip()),
        "guardrail": None,
    }
    if out["escalate"] and out["escalation_reason"] not in ESCALATION_CODES:
        out["escalation_reason"] = "account_specific"
    if RISK_RE.search(ex["text"]) and not out["escalate"]:
        out.update(escalate=True, escalation_reason="risk", guardrail="risk_keyword",
                   reason="Legal/safety keyword detected; routed to a human.")
    return out


def run(examples: list[dict], retriever: Retriever | None = None) -> list[dict | None]:
    """Returns one prediction per example (None while a stand-in LLM answer is pending)."""
    retriever = retriever or Retriever()
    similar = retriever.search_batch(examples, TOP_K)
    raw = complete_batch("agent", [{"system": AGENT_SYSTEM, "user": agent_user(ex, s)}
                                   for ex, s in zip(examples, similar)])
    preds = []
    for ex, sims, r in zip(examples, similar, raw):
        if r is None:
            preds.append(None)
            continue
        p = guardrails(parse_json(r), ex)
        p["retrieved"] = [s["msg_id"] for s in sims]
        preds.append(p)
    return preds
