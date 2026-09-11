from src.agent import UNVERIFIABLE_CLAIM_RE, guardrails

EX = {"text": "any update on my issue?", "context": []}
BASE = {"intent": "dm_status_followup", "confidence": 0.9, "escalate": False,
        "escalation_reason": None, "reason": "", "reply": ""}


def test_catches_claims_the_agent_cannot_verify():
    for reply in ["Hi! We've just replied to your DM 🙂",
                  "We have responded to your direct message, let's chat there",
                  "We've just sent a DM your way. Let's carry on chatting there",
                  "Good news — we've refunded the charge!",
                  "We've updated your account, all set"]:
        assert UNVERIFIABLE_CLAIM_RE.search(reply), reply


def test_allows_honest_phrasings():
    for reply in ["Can you DM us your account's email address? We'll take a look backstage [link]",
                  "Sorry for the wait! Our team will pick this up in your DM as soon as they can",
                  "Refunds usually take 5-7 days to show up — can you DM us your account email?"]:
        assert not UNVERIFIABLE_CLAIM_RE.search(reply), reply


def test_unverifiable_claim_forces_escalation():
    out = guardrails(BASE | {"reply": "We've just replied to your DM!"}, EX)
    assert out["escalate"] is True and out["guardrail"] == "unverifiable_claim"


def test_clean_reply_is_untouched():
    out = guardrails(BASE | {"reply": "Can you DM us your account's email? We'll check [link]"}, EX)
    assert out["escalate"] is False and out["guardrail"] is None
