"""Smoke + load check against a running service.

  python -m src.smoke --url http://localhost:8000 --n 20 --concurrency 4

Sends real golden-set tweets, asserts the contract holds on every response
(intent in the taxonomy, a reason whenever it escalates, reply within 280
chars), and reports p50/p95 latency. Exit code 1 if any check fails, so it
works as a deploy gate.
"""
import argparse
import concurrent.futures as futures
import json
import statistics
import sys
import time
import urllib.error
import urllib.request

from src.make_eval_sets import GOLDEN_FILE, read_jsonl
from src.taxonomy import ESCALATION_CODES, INTENT_KEYS


def post(url: str, payload: dict, timeout: float = 120) -> tuple[dict, float]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read()), (time.perf_counter() - t0) * 1000


def check(pred: dict) -> list[str]:
    problems = []
    if pred.get("intent") not in INTENT_KEYS:
        problems.append(f"intent not in taxonomy: {pred.get('intent')!r}")
    if pred.get("escalate") and pred.get("escalation_reason") not in ESCALATION_CODES:
        problems.append(f"escalated without a valid reason: {pred.get('escalation_reason')!r}")
    if len(pred.get("reply", "")) > 280:
        problems.append(f"reply is {len(pred['reply'])} chars")
    if not pred.get("request_id"):
        problems.append("no request id")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--concurrency", type=int, default=4)
    args = ap.parse_args()

    examples = read_jsonl(GOLDEN_FILE)[: args.n]
    payloads = [{"text": e["text"], "context": e["context"]} for e in examples]
    failures, latencies, escalated = [], [], 0

    with futures.ThreadPoolExecutor(args.concurrency) as pool:
        jobs = [pool.submit(post, f"{args.url}/triage", p) for p in payloads]
        for payload, job in zip(payloads, jobs):
            try:
                pred, ms = job.result()
            except urllib.error.HTTPError as exc:
                failures.append(f"{payload['text'][:60]!r} -> HTTP {exc.code}")
                continue
            latencies.append(ms)
            escalated += bool(pred.get("escalate"))
            failures += [f"{payload['text'][:60]!r} -> {p}" for p in check(pred)]

    print(f"sent {len(payloads)}, answered {len(latencies)}, escalated {escalated}")
    if latencies:
        ordered = sorted(latencies)
        print(f"latency p50 {statistics.median(ordered):.0f} ms · "
              f"p95 {ordered[int(len(ordered) * 0.95) - 1]:.0f} ms · max {ordered[-1]:.0f} ms")
    for f in failures[:10]:
        print("FAIL", f)
    print("contract holds on every response" if not failures else f"{len(failures)} failure(s)")
    return 1 if failures or not latencies else 0


if __name__ == "__main__":
    sys.exit(main())
