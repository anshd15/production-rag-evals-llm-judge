import json

import pytest

from src import llm


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(llm, "QUEUE_DIR", tmp_path / "queue")
    monkeypatch.setenv("LLM_PROVIDER", "standin")
    monkeypatch.delenv("LLM_OFFLINE", raising=False)
    return tmp_path


def test_parse_json_tolerates_fences_and_prose():
    assert llm.parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert llm.parse_json('Sure! {"a": 2} hope that helps') == {"a": 2}
    assert llm.parse_json("not json") is None
    assert llm.parse_json(None) is None


def test_cache_key_depends_on_all_inputs():
    k = llm.cache_key("m", "s", "u")
    assert k == llm.cache_key("m", "s", "u")
    assert k != llm.cache_key("m2", "s", "u") and k != llm.cache_key("m", "s", "u2")


def test_standin_roundtrip(sandbox):
    reqs = [{"system": "sys", "user": f"q{i}"} for i in range(3)]
    assert llm.complete_batch("agent", reqs) == [None, None, None]
    batches = llm.pending_batches("agent")
    assert len(batches) == 1
    batch = json.loads(batches[0].read_text(encoding="utf-8"))
    assert batch["system"] == "sys" and len(batch["items"]) == 3
    # re-running does not queue duplicates
    llm.complete_batch("agent", reqs)
    assert len(llm.pending_batches("agent")) == 1
    # answer two of three, ingest, re-run
    lines = [json.dumps({"key": it["key"], "response": {"answer": it["user"]}})
             for it in batch["items"][:2]]
    batches[0].with_suffix(".responses.jsonl").write_text("\n".join(lines), encoding="utf-8")
    assert llm.ingest() == 2
    out = llm.complete_batch("agent", reqs)
    assert [llm.parse_json(o) for o in out[:2]] == [{"answer": "q0"}, {"answer": "q1"}]
    assert out[2] is None  # unanswered item re-queued
    assert len(llm.pending_batches("agent")) == 1


def test_offline_mode_refuses_new_calls(sandbox, monkeypatch):
    monkeypatch.setenv("LLM_OFFLINE", "1")
    with pytest.raises(RuntimeError):
        llm.complete_batch("agent", [{"system": "s", "user": "u"}])


def test_parse_json_returns_an_object_or_nothing():
    """A live Vertex run died here: the model answered with a JSON array and
    `unusable()` called .get() on a list. Valid JSON is not a valid prediction."""
    # The models intermittently wrap the object in a one-element array.
    assert llm.parse_json('[{"intent": "billing_payment"}]') == {"intent": "billing_payment"}
    # Everything else is not a prediction, and must not reach the caller as one.
    for bad in ('[{"a": 1}, {"b": 2}]', "[1, 2, 3]", '"a string"', "null", "[]", "42"):
        assert llm.parse_json(bad) is None, bad
