"""Circuit breaker and token accounting for the model dependency.

Without a breaker, every request retries a dead provider from scratch: latency
collapses to the timeout, workers fill up, and the queue stalls. The breaker
fails fast instead, so the service can shed load and keep escalating to humans
— which is the correct degraded mode for support, since a human can still work
the ticket without the model.
"""
import time

from src.observability import METRICS, log_event
from src.settings import settings


class CircuitOpen(RuntimeError):
    """Raised instead of calling a dependency that is known to be failing."""


class CircuitBreaker:
    def __init__(self, threshold: int | None = None, cooldown_s: int | None = None):
        # `or` would turn an explicit 0 into the default, which is exactly the value
        # a test (or an operator disabling the cooldown) is most likely to pass.
        self.threshold = settings.breaker_threshold if threshold is None else threshold
        self.cooldown_s = settings.breaker_cooldown_s if cooldown_s is None else cooldown_s
        self.failures = 0
        self.opened_at: float | None = None

    @property
    def state(self) -> str:
        if self.opened_at is None:
            return "closed"
        return "open" if time.time() - self.opened_at < self.cooldown_s else "half_open"

    def before_call(self):
        if self.state == "open":
            METRICS["breaker_rejected"] += 1
            raise CircuitOpen(f"circuit open, retry in "
                              f"{self.cooldown_s - (time.time() - self.opened_at):.0f}s")

    def record_success(self):
        if self.opened_at is not None:
            log_event("breaker_closed", after_failures=self.failures)
        self.failures, self.opened_at = 0, None

    def record_failure(self, error: str = ""):
        self.failures += 1
        if self.failures >= self.threshold and self.state != "open":
            self.opened_at = time.time()
            METRICS["breaker_opened"] += 1
            log_event("breaker_opened", failures=self.failures, error=error[:120],
                      cooldown_s=self.cooldown_s)


def record_usage(usage) -> dict:
    """Pull token counts off a provider response and price them if rates are set."""
    if usage is None:
        return {}
    prompt = getattr(usage, "prompt_token_count", None) or 0
    output = getattr(usage, "candidates_token_count", None) or 0
    METRICS["tokens_in"] += int(prompt)
    METRICS["tokens_out"] += int(output)
    cost = (prompt / 1e6) * settings.cost_per_mtok_in + (output / 1e6) * settings.cost_per_mtok_out
    if cost:
        METRICS["cost_micro_usd"] += int(round(cost * 1e6))
    return {"tokens_in": int(prompt), "tokens_out": int(output), "cost_usd": round(cost, 6)}


breaker = CircuitBreaker()
