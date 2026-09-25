import pytest

from src import feedback


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(feedback, "STORE", tmp_path)
    monkeypatch.setattr(feedback, "DECISIONS", tmp_path / "decisions.jsonl")
    monkeypatch.setattr(feedback, "OUTCOMES", tmp_path / "outcomes.jsonl")


def decide(rid, escalate, text="help"):
    feedback.record_decision(rid, {"intent": "technical_issue", "escalate": escalate,
                                   "escalation_reason": "account_specific" if escalate else None,
                                   "confidence": 0.8, "reason": "because", "reply": "draft"},
                             {"text": text, "context": []},
                             [{"text": "past case", "brand_reply": "past reply"}])


def test_escalations_are_queued_before_auto_handled(store):
    decide("auto-1", False)
    decide("esc-1", True)
    assert [d["request_id"] for d in feedback.pending_review()] == ["esc-1", "auto-1"]


def test_reviewed_items_leave_the_queue(store):
    decide("r1", True)
    decide("r2", True)
    feedback.record_outcome("r1", "accepted")
    assert [d["request_id"] for d in feedback.pending_review()] == ["r2"]


def test_queue_carries_what_a_reviewer_needs(store):
    decide("r1", True, text="charged twice")
    item = feedback.pending_review()[0]
    for field in ("text", "context", "reply", "reason", "escalation_reason", "confidence", "evidence"):
        assert field in item, field
    assert item["evidence"][0]["brand_reply"] == "past reply"
