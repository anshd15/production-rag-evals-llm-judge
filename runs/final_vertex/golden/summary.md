# final_vertex — golden split (n=200, provider=vertex, agent=gemini-3.5-flash-lite, judge=gemini-3.1-flash-lite)

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|---|
| agent | 75.5% [69%–81%] | 71.5% [65%–79%] | 81.8% [72%–91%] | 79.4% | 66.0% | 6.0% | 81.4% [76%–86%] | 75.0% | 46.2% [39%–53%] | 20.1% [15%–26%] |
| simple | 51.5% [45%–58%] | 43.3% [36%–53%] | 57.6% [45%–70%] | 76.0% | 75.0% | 14.0% | 44.5% [37%–51%] | 37.3% | 23.0% [18%–28%] | 52.0% [45%–59%] |
| trivial | 23.0% [18%–29%] | 3.4% [3%–4%] | 0.0% [0%–0%] | nan% | 100.0% | 33.0% | 7.0% [4%–11%] | 7.0% | 7.0% [4%–11%] | 93.0% [89%–96%] |

**Paired bootstrap, agent minus baseline (95% CI):**

- intent accuracy vs simple: +24.0% [+15.5%, +32.5%], P(agent not better) = 0.000
- intent accuracy vs trivial: +52.5% [+44.0%, +60.5%], P(agent not better) = 0.000
- would-send vs simple: +36.7% [+29.6%, +44.7%], P(agent not better) = 0.000

**Agent reply rubric pass rates:** addresses_issue 96%, grounded 98%, correct_next_step 86%, tone 100%, safe 100%, would_send 81%

| Intent | Support | Precision | Recall |
|---|---|---|---|
| billing_payment | 17 | 65% | 100% |
| subscription_plan | 22 | 68% | 68% |
| account_access | 20 | 78% | 90% |
| technical_issue | 46 | 89% | 74% |
| how_to_usage | 14 | 44% | 29% |
| content_availability | 14 | 64% | 100% |
| feedback_feature_request | 36 | 87% | 72% |
| artist_creator | 9 | 89% | 89% |
| dm_status_followup | 1 | 50% | 100% |
| praise_thanks | 12 | 79% | 92% |
| other | 9 | 60% | 33% |
