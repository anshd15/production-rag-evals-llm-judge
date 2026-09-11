"""Integrity checks that need no LLM and no embeddings (run in CI).

1. Golden and dev sets share no thread and no customer.
2. No example the agent retrieved is itself an evaluation message.
3. Every committed runs/*/*/metrics.json is reproduced exactly from its predictions.jsonl.

Run:  python -m src.check_results
"""
import json
import math
import sys

from src.config import ROOT
from src.make_eval_sets import DEV_FILE, GOLDEN_FILE, read_jsonl


def _close(a, b) -> bool:
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_close(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_close(a[k], b[k]) for k in a)
    if isinstance(a, float) and isinstance(b, float):
        return (math.isnan(a) and math.isnan(b)) or abs(a - b) < 1e-9
    return a == b


def main() -> int:
    from src.evaluate import SYSTEMS, score_system

    errors = []
    golden, dev = read_jsonl(GOLDEN_FILE), read_jsonl(DEV_FILE)
    for field in ("thread_id", "customer_id"):
        overlap = {e[field] for e in golden} & {e[field] for e in dev}
        if overlap:
            errors.append(f"golden/dev share {len(overlap)} {field}s")
    eval_ids = {e["msg_id"] for e in golden + dev}

    for metrics_path in sorted((ROOT / "runs").glob("*/*/metrics.json")):
        pred_path = metrics_path.with_name("predictions.jsonl")
        rows = read_jsonl(pred_path)
        leaked = {r for row in rows if row["agent"] for r in row["agent"].get("retrieved", [])} & eval_ids
        if leaked:
            errors.append(f"{pred_path}: retrieved {len(leaked)} evaluation messages")
        split = metrics_path.parent.name
        examples = {e["msg_id"]: e for e in (dev if split == "dev" else golden)}
        exs = [examples[r["msg_id"]] for r in rows]
        labels = {r["msg_id"]: r["label"] for r in rows if r["label"]}
        stored = json.loads(metrics_path.read_text(encoding="utf-8"))["systems"]
        for s in SYSTEMS:
            recomputed = json.loads(json.dumps(score_system(
                exs, [r[s] for r in rows], labels, [r["judge"][s] for r in rows])))
            if not _close(recomputed, stored[s]):
                errors.append(f"{metrics_path}: {s} metrics do not match predictions")
        print(f"ok  {metrics_path.relative_to(ROOT)}")

    for e in errors:
        print("FAIL", e)
    print("all checks passed" if not errors else f"{len(errors)} check(s) failed")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
