# Judge robustness — final_vertex/golden (n=200)

Bias checks that need no human ratings. They cannot tell you the judge is *right* —
only whether it is responding to something other than reply quality.

| System | Judged | Would-send |
|---|---|---|
| agent | 199 | 81.4% |
| simple | 200 | 44.5% |
| trivial | 200 | 7.0% |

## Verbosity bias

| System | Median chars | Short drafts | Long drafts | Gap |
|---|---|---|---|---|
| agent | 121 | 80.8% | 82.1% | +1.3pp |
| simple | 107 | 42.2% | 46.9% | +4.8pp |

## Not yet measurable here

- **Self-preference**: needs a judge from a different model family scoring the same
  drafts. `GEMINI_JUDGE_MODEL` / `--judge-model` makes this a one-command run once a
  second provider key exists.
- **Position bias**: this rubric scores one draft at a time rather than ranking a
  pair, so order cannot influence it by construction — the cheapest way to avoid the
  bias is not to create it.

Agreement with a human is the check that actually matters; see reports/judge_agreement.md.
