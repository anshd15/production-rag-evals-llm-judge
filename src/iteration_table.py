"""Markdown table of every run's headline dev metrics, built from runs/*/dev/metrics.json.

  python -m src.iteration_table [--split dev] [--runs v1c v2c v3 v4 v5]
"""
import argparse
import json

from src.config import ROOT

COLS = [("intent_accuracy", "Intent acc"), ("escalation_recall_ci", "Esc. recall"),
        ("would_send", "Would-send"), ("good_automation_rate", "Good autom."),
        ("bad_auto_send_rate", "Bad auto-send")]


def cell(v):
    if isinstance(v, list):
        return f"{v[0]:.1%}"
    return "—" if v is None else f"{v:.1%}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev")
    ap.add_argument("--runs", nargs="*")
    args = ap.parse_args()
    runs = args.runs or sorted(p.parent.parent.name for p in (ROOT / "runs").glob(f"*/{args.split}/metrics.json"))
    print("| Run | " + " | ".join(t for _, t in COLS) + " | Esc. precision | Automation | Unsafe auto |")
    print("|---" * (len(COLS) + 4) + "|")
    for run in runs:
        path = ROOT / "runs" / run / args.split / "metrics.json"
        if not path.exists():
            continue
        m = json.loads(path.read_text(encoding="utf-8"))["systems"]["agent"]
        esc = m.get("escalation", {})
        print(f"| {run} | " + " | ".join(cell(m.get(k)) for k, _ in COLS) +
              f" | {cell(esc.get('precision'))} | {cell(esc.get('automation_rate'))} | "
              f"{cell(esc.get('unsafe_auto_rate'))} |")


if __name__ == "__main__":
    main()
