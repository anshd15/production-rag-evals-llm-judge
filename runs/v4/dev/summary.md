# v4 — dev split (n=250, provider=standin, agent=claude-haiku-standin, judge=claude-sonnet-standin)

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|---|
| agent | 76.4% [71%–82%] | 69.0% [61%–75%] | 83.8% [75%–92%] | 64.8% | 64.8% | 4.4% | 66.0% [60%–72%] | 64.8% | 39.6% [33%–46%] | 25.2% [20%–30%] |
| simple | 53.6% [47%–60%] | 30.9% [27%–36%] | 51.5% [40%–63%] | 67.3% | 79.2% | 13.2% | 50.8% [45%–57%] | 48.5% | 31.6% [27%–38%] | 47.6% [41%–53%] |
| trivial | 33.6% [28%–40%] | 4.6% [4%–5%] | 0.0% [0%–0%] | nan% | 100.0% | 27.2% | 6.4% [4%–9%] | 6.4% | 6.4% [4%–9%] | 93.6% [91%–96%] |

**Paired bootstrap, agent minus baseline (95% CI):**

- intent accuracy vs simple: +22.8% [+16.0%, +29.6%], P(agent not better) = 0.000
- intent accuracy vs trivial: +42.8% [+35.2%, +49.6%], P(agent not better) = 0.000
- would-send vs simple: +15.2% [+7.6%, +22.4%], P(agent not better) = 0.000

**Agent reply rubric pass rates:** addresses_issue 80%, grounded 87%, correct_next_step 68%, tone 100%, safe 99%, would_send 66%

| Intent | Support | Precision | Recall |
|---|---|---|---|
| billing_payment | 17 | 62% | 59% |
| subscription_plan | 19 | 57% | 63% |
| account_access | 18 | 67% | 89% |
| technical_issue | 84 | 85% | 88% |
| how_to_usage | 12 | 44% | 33% |
| content_availability | 24 | 79% | 92% |
| feedback_feature_request | 32 | 84% | 81% |
| artist_creator | 9 | 88% | 78% |
| dm_status_followup | 3 | 60% | 100% |
| praise_thanks | 21 | 93% | 67% |
| other | 11 | 50% | 27% |
