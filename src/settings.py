"""One typed place for every knob, validated at import.

Env vars were read ad-hoc across the codebase, so a typo in a name silently
became a default and a bad value failed deep inside a request. This reads them
once, checks them, and fails loudly at startup instead.
"""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

from src.config import ROOT

load_dotenv(ROOT / ".env")


def _clean(name: str, default: str = "") -> str:
    """Env values from a .env often carry an inline comment or stray quotes."""
    return (os.getenv(name) or default).split("#")[0].strip().strip("'\"")


def _int(name: str, default: int, low: int, high: int) -> int:
    raw = _clean(name) or str(default)
    try:
        value = int(float(raw))
    except ValueError:
        raise ValueError(f"{name}={raw!r} is not a number")
    if not low <= value <= high:
        raise ValueError(f"{name}={value} outside {low}..{high}")
    return value


@dataclass(frozen=True)
class Settings:
    provider: str = field(default_factory=lambda: _clean("LLM_PROVIDER").lower())
    offline: bool = field(default_factory=lambda: _clean("LLM_OFFLINE") == "1")
    gemini_key: str = field(default_factory=lambda: _clean("GEMINI_API_KEY"))
    gemini_rpm: int = field(default_factory=lambda: _int("GEMINI_RPM", 10, 1, 1000))
    # A hung model call holds a worker forever; this is the deadline per attempt.
    llm_timeout_s: int = field(default_factory=lambda: _int("LLM_TIMEOUT_S", 45, 5, 300))
    llm_max_attempts: int = field(default_factory=lambda: _int("LLM_MAX_ATTEMPTS", 4, 1, 10))
    # Open the circuit after this many consecutive failures; stop trying for this long.
    breaker_threshold: int = field(default_factory=lambda: _int("BREAKER_THRESHOLD", 5, 1, 100))
    breaker_cooldown_s: int = field(default_factory=lambda: _int("BREAKER_COOLDOWN_S", 30, 1, 600))
    # Service limits. 0 disables.
    api_key: str = field(default_factory=lambda: _clean("API_KEY"))
    rate_limit_per_min: int = field(default_factory=lambda: _int("RATE_LIMIT_PER_MIN", 60, 0, 10000))
    # Cost accounting, USD per million tokens; defaults are deliberately 0 so no
    # invented prices end up in a report.
    cost_per_mtok_in: float = field(
        default_factory=lambda: float(_clean("COST_PER_MTOK_IN", "0") or 0))
    cost_per_mtok_out: float = field(
        default_factory=lambda: float(_clean("COST_PER_MTOK_OUT", "0") or 0))

    def resolved_provider(self) -> str:
        return self.provider or ("gemini" if self.gemini_key else "standin")

    def summary(self) -> dict:
        """Safe to log: no secrets, just the shape of the configuration."""
        return {"provider": self.resolved_provider(), "offline": self.offline,
                "has_key": bool(self.gemini_key), "llm_timeout_s": self.llm_timeout_s,
                "llm_max_attempts": self.llm_max_attempts,
                "breaker_threshold": self.breaker_threshold,
                "rate_limit_per_min": self.rate_limit_per_min,
                "auth_required": bool(self.api_key)}


settings = Settings()
