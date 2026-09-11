# Decision log

Non-obvious decisions, in the order they were made, with the reason. (Bullets, per the brief.)

## Data & scope

1. **Brand = SpotifyCares.** A digital subscription product is the closest analogue to Hiver's SaaS/e-commerce customers; ~27k threads; replies mix concrete troubleshooting ("log out > restart > log back in") with account-specific routing ("DM us your email"), so *both* auto-handling and escalation occur naturally. Airlines (Delta, BA) were the runner-up: higher stakes, but replies are mostly "DM your confirmation code", which makes "grounded reply" nearly trivial.
2. **Unit of work = every inbound customer tweet the brand answered, not only thread openers.** Follow-ups ("still not working", "Android 7.0", "thanks!") are ~30% of traffic and are exactly where escalation decisions get hard. The agent sees up to 4 previous turns.
3. **Time-based split, not random.** Threads starting on/after 2017-11-25 form the evaluation pool; everything earlier is history. A random split would let the agent retrieve replies written *after* the message it is answering.
4. **Strict retrieval cutoff on top of the thread split.** 566 "history" messages were sent after the cutoff (follow-ups in threads that started earlier). The retrieval index only uses messages sent before 2017-11-25.
5. **Customers in the golden/dev sets are removed from the retrieval index entirely.** Otherwise the agent could retrieve the same person's other thread about the same problem.
6. **Multi-part brand replies are merged** ("1/2 … 2/2" self-replies) and agent sign-offs (`/JN`, `^Kev`) stripped, so the reference replies are complete and the agent doesn't learn to invent agent initials.
7. **URLs become `[link]`.** t.co links are dead/opaque; the agent is told to write `[link]` where the brand linked an article, and never to invent URLs.
8. **Eval sets are frozen once sampled.** A later fix to the English filter would have reshuffled them; instead the sets were kept (1 non-English tweet remains in each — realistic traffic, labelled `other`) and `make_eval_sets` refuses to overwrite without `--force`, because human labels are keyed to those exact messages.

## Taxonomy & labels

9. **11 intents derived from 30 KMeans clusters** (MiniLM embeddings, 6k history tweets), merged by *what the reply has to do*, not by topic. E.g. "charged but no Premium" (billing) vs "can't join Family plan" (plan) are separate because only the first involves a money dispute.
10. **Escalation is a policy with 6 named reasons**, not a vibe: billing, security, account_specific, troubleshooting_exhausted, repeat_contact, risk. "Anger alone is not a reason to escalate" — otherwise half of Twitter gets escalated.
11. **One guideline text for everyone.** The human labeller, the silver labeller and the agent prompt all read the same taxonomy/policy text (`src/taxonomy.py`), so disagreements are about judgment, not definitions.
12. **The golden set is labelled blind to the brand's actual reply.** The labeller sees exactly what the agent sees; showing "SpotifyCares asked for a DM" would leak the answer into the escalation label.
13. **Golden = 150 random + 50 coverage picks.** Random keeps headline numbers honest (natural class mix); the 50 picks from the smallest clusters give rare intents enough support for per-class metrics. Strata are recorded so results can be reported on the random subset alone.
14. **Dev set gets LLM "silver" labels and drives all iteration; the golden set is touched only for final numbers.** Tuning prompts against the golden set would turn it into a training set.

## System

15. **Retrieval-augmented single LLM call** (intent + routing + reply in one JSON). One call is cheaper and keeps the routing reason consistent with the reply; the loop can split it if routing suffers.
16. **Deterministic guardrails after the LLM**: unparseable output → escalate; legal/self-harm keywords → escalate regardless of the model; replies truncated to 280 chars. The model is not trusted with the non-negotiables.
17. **The agent may not claim actions it cannot verify** ("we've replied to your DM", "refund issued") — even though SpotifyCares' real replies often do. A bot saying that without checking the DM inbox is a lie.
18. **Every LLM call is cached by hash(model, system, user).** Reproduction needs no API key and costs nothing; `LLM_OFFLINE=1` guarantees no new calls.
19. **Every improvement is one change, measured on dev, kept only if the paired bootstrap says it isn't noise.** Each iteration is a separate `runs/<name>/` with its own predictions, judgements and metrics, so any claim in the report can be traced to a file.
20. **v2: the escalation definition was the bug, not the prompt.** v1 looked like it over-escalated (precision 64%): 19 of 28 "needless" escalations were ordinary login/account problems where the agent said "needs an account lookup" and the labeller said "auto-handle" — while SpotifyCares itself had replied "DM us your account email". The guideline never said whether *asking for a DM* counts as handling it. Resolved with an explicit test — *after this reply is sent, does a human still have to do something for this customer?* — which makes "automation rate" mean "tickets closed without a human", the number a support team actually budgets around. Re-scoring the **unchanged v1 predictions** against the re-labelled dev set moved escalation precision 64.1% → 78.2% and recall 82.0% → 85.9%: ~14 points of apparent model error was really definitional disagreement. Reported as a measurement fix, not a model win.
21. **`other` was tightened at the same time**: vague breakage complaints ("sort your app out", "is this thing broken??") are `technical_issue`; `other` is only for messages whose domain is unclear. `other` was the worst class (P/R ≈ 50%) and half its errors were this.
22. **Stand-in provider while no API key existed.** Prompts were answered by fresh Claude sub-agents that never saw labels or results (Haiku for the agent, Sonnet for the judge/labeller) — not by the developer, who knows which examples fail. Stand-in results are reported separately from Gemini results.
