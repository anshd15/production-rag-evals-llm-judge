"""Structured logs and in-process counters.

One JSON object per line on stdout (what a log shipper expects) and a counter
map exposed at /metrics. No PII reaches either: text is never logged, only the
decision about it.
"""
import collections
import json
import sys
import time

METRICS = collections.Counter()
BOOT = time.time()


def log_event(event: str, **fields):
    print(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **fields}),
          file=sys.stdout, flush=True)


def render_prometheus() -> str:
    lines = [f"rag_uptime_seconds {round(time.time() - BOOT, 1)}"]
    for key, value in sorted(METRICS.items()):
        lines.append(f"rag_{key} {value}")
    served = METRICS["requests"]
    if served:
        lines.append(f"rag_latency_ms_avg {METRICS['latency_ms_total'] / served:.1f}")
        lines.append(f"rag_automation_rate {METRICS['auto_handled'] / served:.3f}")
    return "\n".join(lines) + "\n"
