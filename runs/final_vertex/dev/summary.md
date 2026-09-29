# final_vertex — dev split (n=250, provider=vertex, agent=gemini-3.5-flash-lite, judge=gemini-3.1-flash-lite)

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|---|
| agent | 82.0% [77%–86%] | 74.9% [66%–81%] | 79.4% [69%–89%] | 79.4% | 72.8% | 5.6% | 87.2% [83%–91%] | 84.6% | 58.0% [52%–64%] | 14.8% [11%–20%] |
| simple | 53.6% [47%–60%] | 30.9% [27%–36%] | 51.5% [40%–63%] | 67.3% | 79.2% | 13.2% | 43.2% [37%–49%] | 41.9% | 26.4% [22%–32%] | 52.8% [47%–59%] |
| trivial | 33.6% [28%–40%] | 4.6% [4%–5%] | 0.0% [0%–0%] | nan% | 100.0% | 27.2% | 8.8% [6%–12%] | 8.8% | 8.8% [6%–12%] | 91.2% [88%–94%] |

**Paired bootstrap, agent minus baseline (95% CI):**

- intent accuracy vs simple: +28.4% [+21.2%, +35.6%], P(agent not better) = 0.000
- intent accuracy vs trivial: +48.4% [+40.8%, +55.2%], P(agent not better) = 0.000
- would-send vs simple: +44.0% [+37.6%, +50.8%], P(agent not better) = 0.000

**Agent reply rubric pass rates:** addresses_issue 96%, grounded 98%, correct_next_step 90%, tone 100%, safe 100%, would_send 87%

| Intent | Support | Precision | Recall |
|---|---|---|---|
| billing_payment | 17 | 79% | 65% |
| subscription_plan | 19 | 76% | 68% |
| account_access | 18 | 64% | 89% |
| technical_issue | 84 | 93% | 90% |
| how_to_usage | 12 | 55% | 50% |
| content_availability | 24 | 85% | 96% |
| feedback_feature_request | 32 | 75% | 84% |
| artist_creator | 9 | 88% | 78% |
| dm_status_followup | 3 | 60% | 100% |
| praise_thanks | 21 | 95% | 95% |
| other | 11 | 75% | 27% |
