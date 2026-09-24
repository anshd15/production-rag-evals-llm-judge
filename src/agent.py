"""The support agent: retrieve similar past cases -> one LLM call -> deterministic guardrails."""
import re

from src.input_guards import screen
from src.llm import complete_batch, parse_json
from src.prompts import AGENT_SYSTEM, agent_user
from src.retrieval import Retriever
from src.taxonomy import ESCALATION_CODES, INTENT_KEYS

TOP_K = 5
MAX_LEN = 280

# Hard triggers the model is not trusted to catch on its own.
RISK_RE = re.compile(r"\b(lawyers?|sue|suing|lawsuit|attorney|legal action|trading standards|"
                     r"ombudsman|kill myself|suicid\w*|self[- ]harm)\b", re.I)
# Claims about actions the agent cannot perform or verify. SpotifyCares agents write these
# ("we've just replied to your DM") because they can see the DM inbox; the agent cannot.
UNVERIFIABLE_CLAIM_RE = re.compile(
    r"we(?:'ve| have|'ll| will)?\s*(?:just\s+)?(?:replied|responded|sent|answered|got back)"
    r"[^.!?]{0,40}\b(?:dm|direct message|inbox)|"
    r"we(?:'ve| have)\s*(?:just\s+)?(?:refunded|issued (?:a|the) refund|cancelled your|"
    r"canceled your|updated your account|fixed (?:it|this) for you)", re.I)


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
    flags = screen(ex["text"])
    if flags["prompt_injection"]:
        # Someone is steering the agent, not asking for support.
        out.update(escalate=True, escalation_reason="risk", guardrail="prompt_injection",
                   reason="Message tries to override the agent's instructions; routed to a human.")
    if flags["pii"]:
        out["pii_detected"] = flags["pii"]
    if UNVERIFIABLE_CLAIM_RE.search(out["reply"]):
        # Never auto-send a claim about something we cannot check (DM replies, refunds).
        out.update(escalate=True, guardrail="unverifiable_claim",
                   escalation_reason=out["escalation_reason"] or "repeat_contact",
                   reason="Draft claims an action the agent cannot verify; human must confirm.")
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
