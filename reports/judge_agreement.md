# Judge vs human agreement (2 drafts, run `final`)

| Criterion | Human pass | Judge pass | Agreement | Cohen's κ |
|---|---|---|---|---|
| addresses_issue | 100% | 100% | 100% | n/a |
| grounded | 100% | 50% | 50% | 0.00 |
| correct_next_step | 100% | 50% | 50% | 0.00 |
| tone | 100% | 100% | 100% | n/a |
| safe | 100% | 100% | 100% | n/a |
| would_send | 100% | 50% | 50% | 0.00 |

**would_send confusion (rows = human, cols = judge):**

| | judge yes | judge no |
|---|---|---|
| human yes | 1 | 1 |
| human no | 0 | 0 |

**would_send by system (human vs judge):** agent: 100% vs 0% (n=1), simple: 100% vs 100% (n=1)

## Disagreements on would_send

- **Tweet:** why isn’t star shopping by lil peep on spotify
  - Draft: Hey! We'd love to have all his music available. Sometimes content gets removed due to licensing, but hopefully we'll have it back soon: [link]
  - Human: send · Judge: edit — Makes an unfounded promise ('hopefully we'll have it back soon') and skips the country-clarifying question the reference uses to diagnose licensing.
