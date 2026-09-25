"""Quality gate: fail the build when a committed run drops below its floor.

`check_results.py` proves the numbers match the predictions; it does not care
whether they are any good. This does. The floors live in eval/thresholds.json
and are deliberately a little below the current run — a gate set exactly at
today's number fires on noise and gets muted, which is worse than no gate.

  python -m src.gate                     # check runs/final/golden
  python -m src.gate --write             # re-baseline from the current run
"""
import argparse
import json
import sys

from src.config import ROOT

THRESHOLDS = ROOT / "eval" / "thresholds.json"
# How far below the current number a floor is set. Bootstrap CIs on 200 examples
# are roughly +/-7pp, so 5pp absorbs resampling noise without hiding a real drop.
SLACK = 0.05


def metrics_for(run: str, split: str) -> dict:
    path = ROOT / "runs" / run / split / "metrics.json"
    m = json.loads(path.read_text(encoding="utf-8"))["systems"]["agent"]
    esc = m.get("escalation", {})
    return {
        "intent_accuracy": m["intent_accuracy"][0],
        "escalation_recall": esc["recall"],
        "would_send": m["would_send"][0],
        "good_automation_rate": m["good_automation_rate"][0],
        "unsafe_auto_rate": esc["unsafe_auto_rate"],
    }


# Metrics where smaller is better get a ceiling instead of a floor.
UPPER_BOUND = {"unsafe_auto_rate"}


def write_baseline(run: str, split: str) -> dict:
    current = metrics_for(run, split)
    bounds = {k: round(v + SLACK if k in UPPER_BOUND else max(0.0, v - SLACK), 4)
              for k, v in current.items()}
    THRESHOLDS.write_text(json.dumps(
        {"run": run, "split": split, "slack": SLACK, "measured": current, "bounds": bounds},
        indent=1) + "\n", encoding="utf-8")
    return bounds


def check(run: str, split: str) -> int:
    if not THRESHOLDS.exists():
        print(f"no thresholds yet; run `python -m src.gate --write`")
        return 1
    spec = json.loads(THRESHOLDS.read_text(encoding="utf-8"))
    current = metrics_for(run, split)
    failures = []
    print(f"quality gate — {run}/{split}")
    for name, bound in spec["bounds"].items():
        value = current[name]
        ok = value <= bound if name in UPPER_BOUND else value >= bound
        arrow = "<=" if name in UPPER_BOUND else ">="
        print(f"  {'ok  ' if ok else 'FAIL'} {name}: {value:.1%} {arrow} {bound:.1%}")
        if not ok:
            failures.append(name)
    print("gate passed" if not failures else f"{len(failures)} metric(s) below floor")
    return 1 if failures else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="final")
    ap.add_argument("--split", default="golden")
    ap.add_argument("--write", action="store_true", help="re-baseline from this run")
    args = ap.parse_args()
    if args.write:
        print(json.dumps(write_baseline(args.run, args.split), indent=1))
        sys.exit(0)
    sys.exit(check(args.run, args.split))
