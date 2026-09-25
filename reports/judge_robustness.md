# Judge robustness — final/golden (n=200)

Bias checks that need no human ratings. They cannot tell you the judge is *right* —
only whether it is responding to something other than reply quality.

| System | Judged | Would-send |
|---|---|---|
| agent | 200 | 73.0% |
| simple | 200 | 44.5% |
| trivial | 200 | 11.0% |

## Verbosity bias

| System | Median chars | Short drafts | Long drafts | Gap |
|---|---|---|---|---|
| agent | 80 | 69.0% | 77.0% | +8.0pp |
| simple | 107 | 43.1% | 45.9% | +2.8pp |

## Not yet measurable here

- **Self-preference**: needs a judge from a different model family scoring the same
  drafts. `GEMINI_JUDGE_MODEL` / `--judge-model` makes this a one-command run once a
  second provider key exists.
- **Position bias**: this rubric scores one draft at a time rather than ranking a
  pair, so order cannot influence it by construction — the cheapest way to avoid the
  bias is not to create it.

Agreement with a human is the check that actually matters; see reports/judge_agreement.md.
