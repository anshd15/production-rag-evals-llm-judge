import pytest

from src import feedback


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(feedback, "STORE", tmp_path)
    monkeypatch.setattr(feedback, "DECISIONS", tmp_path / "decisions.jsonl")
    monkeypatch.setattr(feedback, "OUTCOMES", tmp_path / "outcomes.jsonl")


def test_empty_report(store):
    assert feedback.report() == {"decisions": 0, "reviewed": 0, "actions": {},
                                 "accept_rate": None, "most_edited_intents": []}


def test_accept_rate_and_most_edited_intent(store):
    for i, intent in enumerate(["billing_payment", "technical_issue", "technical_issue"]):
        feedback.record_decision(f"r{i}", {"intent": intent, "escalate": False,
                                           "reply": "hi", "guardrail": None})
    feedback.record_outcome("r0", "accepted")
    feedback.record_outcome("r1", "edited", final_reply="better wording")
    feedback.record_outcome("r2", "rejected", note="wrong next step")
    rep = feedback.report()
    assert rep["reviewed"] == 3 and rep["accept_rate"] == pytest.approx(0.333, abs=1e-3)
    assert rep["most_edited_intents"][0] == ("technical_issue", 2)


def test_unknown_action_is_refused(store):
    with pytest.raises(ValueError):
        feedback.record_outcome("r0", "ignored")
