# v5 — dev split (n=250, provider=standin, agent=claude-haiku-standin, judge=claude-sonnet-standin)

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|---|
| agent | 82.0% [77%–87%] | 74.8% [67%–81%] | 83.8% [74%–92%] | 73.1% | 68.8% | 4.4% | 71.6% [66%–77%] | 69.8% | 45.6% [40%–52%] | 23.2% [18%–28%] |
| simple | 53.6% [47%–60%] | 30.9% [27%–36%] | 51.5% [40%–63%] | 67.3% | 79.2% | 13.2% | 50.8% [45%–57%] | 48.5% | 31.6% [27%–38%] | 47.6% [41%–53%] |
| trivial | 33.6% [28%–40%] | 4.6% [4%–5%] | 0.0% [0%–0%] | nan% | 100.0% | 27.2% | 6.4% [4%–9%] | 6.4% | 6.4% [4%–9%] | 93.6% [91%–96%] |

**Paired bootstrap, agent minus baseline (95% CI):**

- intent accuracy vs simple: +28.4% [+21.6%, +35.2%], P(agent not better) = 0.000
- intent accuracy vs trivial: +48.4% [+41.6%, +55.6%], P(agent not better) = 0.000
- would-send vs simple: +20.8% [+13.2%, +27.6%], P(agent not better) = 0.000

**Agent reply rubric pass rates:** addresses_issue 84%, grounded 89%, correct_next_step 72%, tone 98%, safe 99%, would_send 72%

| Intent | Support | Precision | Recall |
|---|---|---|---|
| billing_payment | 17 | 67% | 71% |
| subscription_plan | 19 | 92% | 58% |
| account_access | 18 | 73% | 89% |
| technical_issue | 84 | 93% | 90% |
| how_to_usage | 12 | 67% | 50% |
| content_availability | 24 | 85% | 96% |
| feedback_feature_request | 32 | 84% | 81% |
| artist_creator | 9 | 100% | 89% |
| dm_status_followup | 3 | 43% | 100% |
| praise_thanks | 21 | 87% | 95% |
| other | 11 | 36% | 36% |
