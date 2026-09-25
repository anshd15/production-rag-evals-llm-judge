import pytest

from src.dataset import validate_examples, validate_labels

GOOD_EX = {"msg_id": 1, "thread_id": 1, "customer_id": "c1", "created_at": "2017-12-01",
           "is_opener": True, "context": [], "text": "help", "brand_reply": "hi",
           "stratum": "random"}


def test_valid_example_passes():
    assert validate_examples([GOOD_EX]) == []


def test_missing_field_and_duplicates_are_caught():
    assert "missing" in validate_examples([{k: v for k, v in GOOD_EX.items() if k != "text"}])[0]
    problems = validate_examples([GOOD_EX, GOOD_EX])
    assert any("duplicate" in p for p in problems)


def test_empty_text_is_caught():
    assert any("empty text" in p for p in validate_examples([GOOD_EX | {"text": "   "}]))


@pytest.mark.parametrize("label,expected", [
    ({"msg_id": 1, "intent": "billing_payment", "escalate": True, "escalation_reason": "billing"}, 0),
    ({"msg_id": 1, "intent": "nonsense", "escalate": False, "escalation_reason": None}, 1),
    ({"msg_id": 1, "intent": "other", "escalate": True, "escalation_reason": None}, 1),
    ({"msg_id": 1, "intent": "other", "escalate": False, "escalation_reason": "billing"}, 1),
    ({"msg_id": 99, "intent": "other", "escalate": False, "escalation_reason": None}, 1),
])
def test_label_validation(label, expected):
    assert len(validate_labels([label], {1})) == expected
