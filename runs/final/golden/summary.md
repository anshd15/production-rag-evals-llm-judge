# final — golden split (n=200, provider=standin, agent=claude-haiku-standin, judge=claude-sonnet-standin)

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|---|
| agent | 71.5% [65%–78%] | 70.6% [61%–75%] | 86.4% [78%–94%] | 75.0% | 62.0% | 4.5% | 73.0% [67%–79%] | 68.5% | 39.5% [33%–46%] | 22.5% [16%–28%] |
| simple | 51.5% [45%–58%] | 43.3% [36%–53%] | 57.6% [45%–70%] | 76.0% | 75.0% | 14.0% | 44.5% [38%–51%] | 40.7% | 25.0% [19%–31%] | 50.0% [43%–56%] |
| trivial | 23.0% [18%–29%] | 3.4% [3%–4%] | 0.0% [0%–0%] | nan% | 100.0% | 33.0% | 11.0% [7%–16%] | 11.0% | 10.5% [6%–16%] | 89.5% [84%–94%] |

**Paired bootstrap, agent minus baseline (95% CI):**

- intent accuracy vs simple: +20.0% [+12.0%, +28.0%], P(agent not better) = 0.000
- intent accuracy vs trivial: +48.5% [+41.0%, +56.0%], P(agent not better) = 0.000
- would-send vs simple: +28.5% [+21.0%, +36.5%], P(agent not better) = 0.000

**Agent reply rubric pass rates:** addresses_issue 84%, grounded 90%, correct_next_step 75%, tone 98%, safe 100%, would_send 73%

| Intent | Support | Precision | Recall |
|---|---|---|---|
| billing_payment | 17 | 83% | 88% |
| subscription_plan | 22 | 75% | 82% |
| account_access | 20 | 68% | 85% |
| technical_issue | 46 | 76% | 80% |
| how_to_usage | 14 | 21% | 21% |
| content_availability | 14 | 100% | 79% |
| feedback_feature_request | 36 | 85% | 61% |
| artist_creator | 9 | 67% | 44% |
| dm_status_followup | 1 | 100% | 100% |
| praise_thanks | 12 | 77% | 83% |
| other | 9 | 38% | 56% |
