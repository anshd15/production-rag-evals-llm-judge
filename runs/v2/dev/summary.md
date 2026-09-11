# v2 — dev split (n=250, provider=standin, agent=claude-haiku-standin, judge=claude-sonnet-standin)

| System | Intent acc | Macro-F1 | Esc. recall | Esc. precision | Automation | Unsafe auto | Would-send (all) | Would-send (auto-sent) | Good automation | Bad auto-send |
|---|---|---|---|---|---|---|---|---|---|---|
| agent | 84.4% [80%–89%] | 78.0% [70%–84%] | 81.7% [72%–90%] | 70.7% | 67.2% | 5.2% | 74.0% [68%–79%] | 77.4% | 48.4% [42%–55%] | 18.8% [14%–24%] |
| simple | 56.4% [50%–62%] | 35.1% [29%–41%] | 56.3% [44%–68%] | 72.7% | 78.0% | 12.4% | 50.8% [45%–57%] | 49.2% | 31.2% [26%–37%] | 46.8% [40%–53%] |
| trivial | 35.6% [30%–42%] | 4.8% [4%–6%] | 0.0% [0%–0%] | nan% | 100.0% | 28.4% | 6.4% [4%–9%] | 6.4% | 6.4% [4%–9%] | 93.6% [91%–96%] |

**Paired bootstrap, agent minus baseline (95% CI):**

- intent accuracy vs simple: +28.0% [+20.8%, +34.4%], P(agent not better) = 0.000
- intent accuracy vs trivial: +48.8% [+40.8%, +55.6%], P(agent not better) = 0.000
- would-send vs simple: +23.2% [+16.0%, +30.0%], P(agent not better) = 0.000

**Agent reply rubric pass rates:** addresses_issue 86%, grounded 89%, correct_next_step 76%, tone 99%, safe 98%, would_send 74%

| Intent | Support | Precision | Recall |
|---|---|---|---|
| billing_payment | 16 | 69% | 56% |
| subscription_plan | 18 | 70% | 78% |
| account_access | 20 | 66% | 95% |
| technical_issue | 89 | 95% | 88% |
| how_to_usage | 11 | 100% | 36% |
| content_availability | 26 | 96% | 92% |
| feedback_feature_request | 28 | 80% | 100% |
| artist_creator | 9 | 100% | 89% |
| dm_status_followup | 3 | 60% | 100% |
| praise_thanks | 20 | 95% | 95% |
| other | 10 | 56% | 50% |
