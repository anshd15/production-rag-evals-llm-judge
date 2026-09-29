# final_gemini — golden split (n=200, provider=gemini, agent=gemini-3.5-flash-lite, judge=gemini-3.1-flash-lite)

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|---|
| agent | 74.5% [68%–80%] | 70.6% [63%–78%] | 81.8% [72%–90%] | 81.8% | 67.0% | 6.0% | — | — | — | — |
| simple | 51.5% [45%–58%] | 43.3% [36%–53%] | 57.6% [45%–70%] | 76.0% | 75.0% | 14.0% | — | — | — | — |
| trivial | 23.0% [18%–29%] | 3.4% [3%–4%] | 0.0% [0%–0%] | nan% | 100.0% | 33.0% | — | — | — | — |

**Paired bootstrap, agent minus baseline (95% CI):**

- intent accuracy vs simple: +23.0% [+15.0%, +31.0%], P(agent not better) = 0.000
- intent accuracy vs trivial: +51.5% [+43.5%, +59.0%], P(agent not better) = 0.000

| Intent | Support | Precision | Recall |
|---|---|---|---|
| billing_payment | 17 | 64% | 94% |
| subscription_plan | 22 | 71% | 77% |
| account_access | 20 | 71% | 85% |
| technical_issue | 46 | 92% | 74% |
| how_to_usage | 14 | 40% | 29% |
| content_availability | 14 | 65% | 93% |
| feedback_feature_request | 36 | 84% | 72% |
| artist_creator | 9 | 86% | 67% |
| dm_status_followup | 1 | 50% | 100% |
| praise_thanks | 12 | 79% | 92% |
| other | 9 | 67% | 44% |
