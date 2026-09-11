# v2c (predictions from v2, current labels) — dev split (n=250, provider=standin, agent=claude-haiku-standin, judge=claude-sonnet-standin)

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|---|
| agent | 82.4% [78%–87%] | 75.8% [68%–81%] | 80.9% [71%–90%] | 67.1% | 67.2% | 5.2% | 74.0% [68%–79%] | 77.4% | 48.4% [42%–54%] | 18.8% [14%–24%] |
| simple | 56.8% [50%–63%] | 37.1% [31%–43%] | 57.4% [45%–69%] | 70.9% | 78.0% | 11.6% | 50.8% [45%–57%] | 49.2% | 32.0% [27%–38%] | 46.0% [40%–52%] |
| trivial | 33.6% [28%–40%] | 4.6% [4%–5%] | 0.0% [0%–0%] | nan% | 100.0% | 27.2% | 6.4% [4%–9%] | 6.4% | 6.4% [4%–9%] | 93.6% [91%–96%] |

**Paired bootstrap, agent minus baseline (95% CI):**

- intent accuracy vs simple: +25.6% [+18.4%, +32.4%], P(agent not better) = 0.000
- intent accuracy vs trivial: +48.8% [+42.0%, +56.0%], P(agent not better) = 0.000
- would-send vs simple: +23.2% [+16.0%, +30.0%], P(agent not better) = 0.000

**Agent reply rubric pass rates:** addresses_issue 86%, grounded 89%, correct_next_step 76%, tone 99%, safe 98%, would_send 74%

| Intent | Support | Precision | Recall |
|---|---|---|---|
| billing_payment | 17 | 77% | 59% |
| subscription_plan | 19 | 70% | 74% |
| account_access | 18 | 59% | 94% |
| technical_issue | 84 | 91% | 89% |
| how_to_usage | 12 | 100% | 33% |
| content_availability | 24 | 92% | 96% |
| feedback_feature_request | 32 | 83% | 91% |
| artist_creator | 9 | 100% | 89% |
| dm_status_followup | 3 | 60% | 100% |
| praise_thanks | 21 | 95% | 90% |
| other | 11 | 44% | 36% |
