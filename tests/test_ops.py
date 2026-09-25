import time

import pytest

from src.gate import UPPER_BOUND, metrics_for
from src.resilience import CircuitBreaker, CircuitOpen
from src.settings import Settings, _clean, _int


def test_env_values_survive_inline_comments_and_quotes(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini   # the one with the key")
    monkeypatch.setenv("GEMINI_RPM", "'15'")
    assert _clean("LLM_PROVIDER") == "gemini"
    assert _int("GEMINI_RPM", 10, 1, 1000) == 15


def test_bad_numbers_fail_at_startup_not_mid_request(monkeypatch):
    monkeypatch.setenv("GEMINI_RPM", "banana")
    with pytest.raises(ValueError, match="not a number"):
        _int("GEMINI_RPM", 10, 1, 1000)
    monkeypatch.setenv("GEMINI_RPM", "99999")
    with pytest.raises(ValueError, match="outside"):
        _int("GEMINI_RPM", 10, 1, 1000)


def test_provider_falls_back_to_standin_without_a_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    assert Settings().resolved_provider() == "standin"
    monkeypatch.setenv("GEMINI_API_KEY", "abc123")
    assert Settings().resolved_provider() == "gemini"


def test_summary_never_leaks_the_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "super-secret")
    summary = Settings().summary()
    assert summary["has_key"] is True
    assert "super-secret" not in str(summary)


def test_breaker_opens_after_repeated_failures_and_sheds_load():
    b = CircuitBreaker(threshold=3, cooldown_s=60)
    for _ in range(2):
        b.record_failure("boom")
    assert b.state == "closed"
    b.before_call()  # still allowed
    b.record_failure("boom")
    assert b.state == "open"
    with pytest.raises(CircuitOpen):
        b.before_call()


def test_breaker_half_opens_after_cooldown_and_closes_on_success():
    b = CircuitBreaker(threshold=1, cooldown_s=0)
    b.record_failure("boom")
    time.sleep(0.01)
    assert b.state == "half_open"
    b.before_call()  # a half-open circuit lets one request through
    b.record_success()
    assert b.state == "closed" and b.failures == 0


def test_gate_reads_the_committed_run():
    m = metrics_for("final", "golden")
    assert 0 <= m["intent_accuracy"] <= 1 and 0 <= m["unsafe_auto_rate"] <= 1
    assert "unsafe_auto_rate" in UPPER_BOUND  # smaller is better, so it gets a ceiling
