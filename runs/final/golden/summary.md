# final — golden split (n=200, provider=standin, agent=claude-haiku-standin, judge=claude-sonnet-standin)

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|---|
| agent | — | — | — | — | — | — | 73.0% [67%–79%] | 68.5% | — | — |
| simple | — | — | — | — | — | — | 44.5% [38%–51%] | 40.7% | — | — |
| trivial | — | — | — | — | — | — | 11.0% [7%–16%] | 11.0% | — | — |

**Paired bootstrap, agent minus baseline (95% CI):**

- would-send vs simple: +28.5% [+21.0%, +36.5%], P(agent not better) = 0.000

**Agent reply rubric pass rates:** addresses_issue 84%, grounded 90%, correct_next_step 75%, tone 98%, safe 100%, would_send 73%
