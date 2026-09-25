"""Checks applied to the model's answer before anything is sent."""
import re

from src.taxonomy import ESCALATION_CODES, INTENT_KEYS

MAX_LEN = 280  # the channel's limit; a truncated apology is worse than a short one

# Hard triggers the model is not trusted to catch on its own.
RISK_RE = re.compile(r"\b(lawyers?|sue|suing|lawsuit|attorney|legal action|trading standards|"
                     r"ombudsman|kill myself|suicid\w*|self[- ]harm)\b", re.I)
# Claims about actions the agent cannot perform or verify. Human agents write these
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


def unusable(pred: dict | None) -> bool:
    return (not pred or pred.get("intent") not in INTENT_KEYS
            or not isinstance(pred.get("escalate"), bool))


def apply_output_policy(out: dict, customer_text: str) -> dict:
    """Mutate and return the prediction according to the non-negotiable rules."""
    if out["escalate"] and out["escalation_reason"] not in ESCALATION_CODES:
        out["escalation_reason"] = "account_specific"
    if RISK_RE.search(customer_text) and not out["escalate"]:
        out.update(escalate=True, escalation_reason="risk", guardrail="risk_keyword",
                   reason="Legal/safety keyword detected; routed to a human.")
    if UNVERIFIABLE_CLAIM_RE.search(out["reply"]):
        out.update(escalate=True, guardrail="unverifiable_claim",
                   escalation_reason=out["escalation_reason"] or "repeat_contact",
                   reason="Draft claims an action the agent cannot verify; human must confirm.")
    return out
