from src.agent import guardrails
from src.guardrails import MAX_LEN, truncate
from src.prompts import AGENT_SYSTEM, JUDGE_SYSTEM, LABELER_SYSTEM
from src.taxonomy import ESCALATION_CODES, INTENT_KEYS

EX = {"text": "my songs keep skipping", "context": []}
GOOD = {"intent": "technical_issue", "confidence": 0.9, "escalate": False,
        "escalation_reason": None, "reason": "generic bug", "reply": "Try logging out and back in!"}


def test_valid_prediction_passes_through():
    out = guardrails(GOOD, EX)
    assert out["intent"] == "technical_issue" and out["escalate"] is False and out["guardrail"] is None


def test_unusable_output_falls_back_to_escalation():
    for bad in [None, {}, {"intent": "made_up", "escalate": False}, {"intent": "other", "escalate": "no"}]:
        out = guardrails(bad, EX)
        assert out["escalate"] is True and out["guardrail"] == "invalid_output"


def test_risk_keyword_forces_escalation():
    out = guardrails(GOOD, {"text": "I will sue you if this isn't fixed", "context": []})
    assert out["escalate"] is True and out["escalation_reason"] == "risk"


def test_unknown_reason_is_normalised():
    out = guardrails(GOOD | {"escalate": True, "escalation_reason": "vibes"}, EX)
    assert out["escalation_reason"] in ESCALATION_CODES


def test_truncate():
    assert truncate("short") == "short"
    long = "word " * 100
    assert len(truncate(long)) <= MAX_LEN + 1


def test_prompts_mention_every_intent():
    for prompt in (AGENT_SYSTEM, LABELER_SYSTEM):
        for k in INTENT_KEYS:
            assert k in prompt
    assert "would_send" in JUDGE_SYSTEM
