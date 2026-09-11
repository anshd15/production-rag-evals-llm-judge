# v1b (predictions from v1, current labels) — dev split (n=250, provider=standin, agent=claude-haiku-standin, judge=claude-sonnet-standin)

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|---|
| agent | 82.4% [78%–87%] | 80.4% [74%–85%] | 85.9% [78%–93%] | 78.2% | 68.8% | 4.0% | 75.2% [69%–80%] | 75.6% | 49.2% [43%–55%] | 19.6% [15%–25%] |
| simple | 59.2% [53%–66%] | 39.8% [33%–46%] | 39.4% [29%–51%] | 60.9% | 81.6% | 17.2% | 50.8% [45%–57%] | 48.5% | 30.4% [25%–36%] | 51.2% [45%–57%] |
| trivial | 35.6% [30%–42%] | 4.8% [4%–6%] | 0.0% [0%–0%] | nan% | 100.0% | 28.4% | 6.4% [4%–9%] | 6.4% | 6.4% [4%–9%] | 93.6% [91%–96%] |

**Paired bootstrap, agent minus baseline (95% CI):**

- intent accuracy vs simple: +23.2% [+15.6%, +31.2%], P(agent not better) = 0.000
- intent accuracy vs trivial: +46.8% [+38.4%, +54.8%], P(agent not better) = 0.000
- would-send vs simple: +24.4% [+16.8%, +30.8%], P(agent not better) = 0.000

**Agent reply rubric pass rates:** addresses_issue 86%, grounded 90%, correct_next_step 76%, tone 99%, safe 99%, would_send 75%

| Intent | Support | Precision | Recall |
|---|---|---|---|
| billing_payment | 16 | 61% | 69% |
| subscription_plan | 18 | 75% | 67% |
| account_access | 20 | 79% | 95% |
| technical_issue | 89 | 95% | 79% |
| how_to_usage | 11 | 91% | 91% |
| content_availability | 26 | 92% | 92% |
| feedback_feature_request | 28 | 76% | 93% |
| artist_creator | 9 | 100% | 78% |
| dm_status_followup | 3 | 75% | 100% |
| praise_thanks | 20 | 95% | 90% |
| other | 10 | 35% | 60% |
