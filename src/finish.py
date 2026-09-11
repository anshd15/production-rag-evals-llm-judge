"""Everything that depends on the human labels, in one command.

  python -m src.finish

Runs (all from cached LLM responses — no API key needed):
  1. golden evaluation           -> runs/final/golden/{metrics.json,summary.md}
  2. failure analysis            -> runs/final/golden/failures.md
  3. judge vs human agreement    -> reports/judge_agreement.md
  4. human vs LLM label noise    -> reports/label_agreement.md
  5. integrity checks
"""
import os
import subprocess
import sys

from src.config import ROOT
from src.evaluate import GOLDEN_LABELS
from src.label_app import RATINGS
from src.make_eval_sets import GOLDEN_FILE, read_jsonl

STEPS = [
    ("golden evaluation", [sys.executable, "-m", "src.evaluate", "--split", "golden", "--run", "final"]),
    ("failure analysis", [sys.executable, "-m", "src.analyze", "--run", "final", "--split", "golden"]),
    ("judge vs human", [sys.executable, "-m", "src.judge_agreement", "score", "--run", "final"]),
    ("human vs LLM labels", [sys.executable, "-m", "src.label_agreement"]),
    ("integrity checks", [sys.executable, "-m", "src.check_results"]),
]


def main():
    n_labels = len({r["msg_id"] for r in read_jsonl(GOLDEN_LABELS)}) if GOLDEN_LABELS.exists() else 0
    n_golden = len(read_jsonl(GOLDEN_FILE))
    n_ratings = len({r["item_id"] for r in read_jsonl(RATINGS)}) if RATINGS.exists() else 0
    print(f"golden labels: {n_labels}/{n_golden} · reply ratings: {n_ratings}/60\n")
    if n_labels < n_golden:
        print(f"⚠  {n_golden - n_labels} messages still unlabelled — run `python -m src.label_app` "
              "first, or continue to see partial results.\n")

    env = os.environ | {"LLM_OFFLINE": "1", "PYTHONIOENCODING": "utf-8"}
    for name, cmd in STEPS:
        print(f"\n{'=' * 70}\n== {name}\n{'=' * 70}")
        r = subprocess.run(cmd, cwd=ROOT, env=env)
        if r.returncode not in (0, 3):
            print(f"!! {name} failed (exit {r.returncode})")
    print("\nDone. Report numbers live in runs/final/golden/summary.md and reports/.")


if __name__ == "__main__":
    main()
