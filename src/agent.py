"""The support agent: screen input -> retrieve similar cases -> one LLM call -> output policy.

Order matters. Screening runs first so that an instruction-override attempt never
reaches the model and PII never enters a prompt; the model sees the redacted text.
The output policy runs last and can overrule whatever the model decided.
"""
from src.guardrails import apply_output_policy, screen, truncate
from src.guardrails.output import unusable
from src.llm import complete_batch, parse_json
from src.prompts import AGENT_SYSTEM, agent_user
from src.retrieval import Retriever
from src.retrieval_qdrant import get_retriever

TOP_K = 5


def blocked_by_input_guard(flags: dict) -> dict:
    """An injection attempt is not a support request: escalate without asking the model."""
    return {"intent": "other", "confidence": 0.0, "escalate": True, "escalation_reason": "risk",
            "reason": "Message tries to override the agent's instructions; routed to a human.",
            "reply": "", "guardrail": "prompt_injection", "pii_detected": flags["pii"]}


def guardrails(pred: dict | None, ex: dict, flags: dict | None = None) -> dict:
    """Validate the model output and apply the non-negotiable routing rules.

    `flags` is the screening of the ORIGINAL text; `ex` may already be redacted,
    so re-screening it here would lose the PII finding.
    """
    flags = flags if flags is not None else screen(ex["text"])
    if flags["prompt_injection"]:
        return blocked_by_input_guard(flags)
    if unusable(pred):
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
    if flags["pii"]:
        out["pii_detected"] = flags["pii"]
    return apply_output_policy(out, ex["text"])


def run(examples: list[dict], retriever: Retriever | None = None) -> list[dict | None]:
    """Returns one prediction per example (None while a stand-in LLM answer is pending)."""
    retriever = retriever if retriever is not None else get_retriever()
    flags = [screen(ex["text"]) for ex in examples]
    # From here on the agent works on redacted text: retrieval, prompt and cache
    # never see a card number.
    safe = [ex | {"text": f["safe_text"]} for ex, f in zip(examples, flags)]

    asked = [i for i, f in enumerate(flags) if not f["prompt_injection"]]
    preds: list[dict | None] = [blocked_by_input_guard(f) for f in flags]
    if not asked:
        return preds

    similar = retriever.search_batch([safe[i] for i in asked], TOP_K)
    raw = complete_batch("agent", [{"system": AGENT_SYSTEM, "user": agent_user(safe[i], s)}
                                   for i, s in zip(asked, similar)])
    for i, sims, r in zip(asked, similar, raw):
        if r is None:
            preds[i] = None
            continue
        p = guardrails(parse_json(r), safe[i], flags[i])
        p["retrieved"] = [s["msg_id"] for s in sims]
        preds[i] = p
    return preds
