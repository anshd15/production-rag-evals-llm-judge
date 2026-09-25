"""Guardrails: what the model is not trusted to decide.

Two sides, deliberately separate:

  input   runs BEFORE the prompt is built (src/guardrails/input.py). Instruction-
          override attempts never reach the model at all; PII is redacted so it
          never enters a prompt, a cache file or a log.
  output  runs AFTER the model answers (src/guardrails/output.py). Unusable JSON,
          legal/self-harm keywords, and claims the agent cannot verify all force
          the case to a human; replies are capped at the channel limit.

Everything here is deterministic and unit-tested. Prompt instructions were tried
for this job and measured worse (decision log #24): the model followed them most
of the time, and "most of the time" is not a guardrail.
"""
from src.guardrails.input import redact, screen
from src.guardrails.output import (MAX_LEN, RISK_RE, UNVERIFIABLE_CLAIM_RE, apply_output_policy,
                                   truncate)

__all__ = ["screen", "redact", "apply_output_policy", "truncate", "MAX_LEN", "RISK_RE",
           "UNVERIFIABLE_CLAIM_RE"]
