# v1c (predictions from v1, current labels) — dev split (n=250, provider=standin, agent=claude-haiku-standin, judge=claude-sonnet-standin)

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|---|
| agent | 79.6% [74%–85%] | 76.8% [70%–82%] | 82.4% [73%–91%] | 71.8% | 68.8% | 4.8% | 75.2% [69%–80%] | 75.6% | 48.4% [42%–54%] | 20.4% [16%–26%] |
| simple | 59.6% [53%–66%] | 41.5% [35%–47%] | 38.2% [27%–50%] | 56.5% | 81.6% | 16.8% | 50.8% [45%–57%] | 48.5% | 31.2% [26%–37%] | 50.4% [44%–56%] |
| trivial | 33.6% [28%–40%] | 4.6% [4%–5%] | 0.0% [0%–0%] | nan% | 100.0% | 27.2% | 6.4% [4%–9%] | 6.4% | 6.4% [4%–9%] | 93.6% [91%–96%] |

**Paired bootstrap, agent minus baseline (95% CI):**

- intent accuracy vs simple: +20.0% [+13.2%, +27.6%], P(agent not better) = 0.000
- intent accuracy vs trivial: +46.0% [+38.4%, +54.0%], P(agent not better) = 0.000
- would-send vs simple: +24.4% [+16.8%, +30.8%], P(agent not better) = 0.000

**Agent reply rubric pass rates:** addresses_issue 86%, grounded 90%, correct_next_step 76%, tone 99%, safe 99%, would_send 75%

| Intent | Support | Precision | Recall |
|---|---|---|---|
| billing_payment | 17 | 67% | 71% |
| subscription_plan | 19 | 75% | 63% |
| account_access | 18 | 71% | 94% |
| technical_issue | 84 | 91% | 80% |
| how_to_usage | 12 | 73% | 67% |
| content_availability | 24 | 88% | 96% |
| feedback_feature_request | 32 | 79% | 84% |
| artist_creator | 9 | 100% | 78% |
| dm_status_followup | 3 | 75% | 100% |
| praise_thanks | 21 | 95% | 86% |
| other | 11 | 29% | 45% |
