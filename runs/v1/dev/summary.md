# v1 — dev split (n=250, provider=standin, agent=claude-haiku-standin, judge=claude-sonnet-standin)

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|---|
| agent | 82.0% [77%–87%] | 81.2% [75%–86%] | 82.0% [73%–92%] | 64.1% | 68.8% | 4.4% | 75.2% [69%–80%] | 75.6% | 49.2% [43%–55%] | 19.6% [15%–25%] |
| simple | 57.6% [51%–64%] | 40.2% [34%–46%] | 32.8% [22%–45%] | 43.5% | 81.6% | 16.4% | 50.8% [45%–57%] | 48.5% | 31.6% [26%–38%] | 50.0% [44%–56%] |
| trivial | 31.2% [26%–37%] | 4.3% [4%–5%] | 0.0% [0%–0%] | nan% | 100.0% | 24.4% | 6.4% [4%–9%] | 6.4% | 6.4% [4%–9%] | 93.6% [91%–96%] |

**Paired bootstrap, agent minus baseline (95% CI):**

- intent accuracy vs simple: +24.4% [+16.8%, +32.4%], P(agent not better) = 0.000
- intent accuracy vs trivial: +50.8% [+43.6%, +58.8%], P(agent not better) = 0.000
- would-send vs simple: +24.4% [+16.8%, +30.8%], P(agent not better) = 0.000

**Agent reply rubric pass rates:** addresses_issue 86%, grounded 90%, correct_next_step 76%, tone 99%, safe 99%, would_send 75%

| Intent | Support | Precision | Recall |
|---|---|---|---|
| billing_payment | 17 | 67% | 71% |
| subscription_plan | 20 | 81% | 65% |
| account_access | 18 | 75% | 100% |
| technical_issue | 78 | 89% | 85% |
| how_to_usage | 10 | 73% | 80% |
| content_availability | 24 | 88% | 96% |
| feedback_feature_request | 29 | 76% | 90% |
| artist_creator | 9 | 100% | 78% |
| dm_status_followup | 4 | 100% | 100% |
| praise_thanks | 23 | 100% | 83% |
| other | 18 | 53% | 50% |
