# How to label the golden set

You have two files in this folder:

- **`questions.json`** — 200 customer tweets. Each item has `n` (1–200), `msg_id`,
  `thread_so_far` (earlier turns, may be empty) and `incoming_tweet` (the one you label).
- **`answers_template.json`** — one slot per `msg_id`. 50 are already filled in from the labels
  you did blind; the other 150 are `""`.

Fill in the blanks, save the file as **`labelling/answers.json`**, and say it's ready.

---

## The answer code

Each answer is a short string: **intent digit** + **`a` or `e`** (+ **reason letter** if `e`).

```
"4a"    technical issue, bot can handle it
"1eb"   billing problem, escalate, reason = billing
"3ec"   account access, escalate, reason = needs an account lookup
```

### 1. Intent — what does the customer need?

| Code | Intent | Use it when |
|---|---|---|
| `1` | Billing & payment | Money moved or failed: charged twice, refund, payment declined, paid but still on Free |
| `2` | Plan & subscription | Changing/cancelling/joining a plan, Family invites, Student discount, trials, offers, gift cards — **no disputed charge** |
| `3` | Account access & security | Can't log in, password reset email missing, hacked, email changed by someone else, merging/deleting accounts |
| `4` | App / playback technical issue | Something is broken: crashes, songs won't play, web player down, downloads vanish, device/Bluetooth/car problems. Also vague breakage ("sort your app out") and follow-ups in a troubleshooting thread ("Android 7.0", "still not working") |
| `5` | How-to / product question | Asks how to do something or whether it's possible; nothing is broken |
| `6` | Content or service availability | A song/album/artist is missing, removed or region-locked; when a release lands; when Spotify launches in a country |
| `7` | Feedback & feature request | Opinions about how the product is designed *as intended*: feature requests, ad frequency, shuffle, removed features, "when will you support iPhone X?" |
| `8` | Artist / creator support | Artist profile, verification, wrong artist page, playlist submission, getting music on Spotify |
| `9` | DM / status follow-up | Chasing support, not describing an issue: "I sent a DM", "check my DM", "still waiting" |
| `0` | Praise, thanks & resolved | Compliments, thanks, or confirming it's fixed |
| `x` | Other / unclear | Only if you can't tell what it's about: spam, jokes, non-English, a bare link with no complaint |

**If two fit, pick the one that decides what the reply must do.** Money involved beats plan.
Security beats a how-to about accounts. A vague "it's broken" is `4`, not `x`.

### 2. Route — `a` or `e`

> **The test: after the reply is sent, does someone at Spotify still have to do something for this customer?**
> Yes → `e` (escalate). No → `a` (auto-handle).

Asking the customer to "DM us your account email" counts as **yes** — a human still works the case.

`a` is for replies that settle it on their own: how-to answers, first-line troubleshooting steps or
diagnostic questions, content/country availability, acknowledging feedback, pointing artists to
Spotify for Artists, thanks, or a clarifying question for a vague tweet.

**Anger alone is not a reason to escalate** if the answer is standard.

### 3. Reason letter (only when you chose `e`)

| Letter | Reason | Meaning |
|---|---|---|
| `b` | billing | Disputed, unexpected or failed charge, or a refund request |
| `s` | security | Hacked/compromised account, credentials changed by someone else, locked out after a failed reset |
| `c` | account_specific | This customer's account must be inspected — can't log in, Premium not activating, Family invite failing, Student verification stuck. A *general* question about how a plan works is **not** this: that's `5a` |
| `t` | troubleshooting_exhausted | They say they already tried a standard fix (logged out/in, restarted, reinstalled, cleared cache) and it still fails. Narrowing the problem down ("only over Bluetooth") is diagnosis, **not** exhaustion |
| `r` | repeat_contact | Chasing an earlier DM/ticket, or says they contacted support with no answer |
| `k` | risk | Legal threat, safety/self-harm, harassment, discrimination, press, or explicitly asking for a human |

---

## Worked examples (made up, not from your set)

| Tweet | Answer | Why |
|---|---|---|
| "how do I make a playlist collaborative?" | `5a` | How-to; the answer settles it |
| "charged £9.99 twice this month, sort it out" | `1eb` | Money dispute; a human must check billing |
| "can't log in, reset email never arrives" | `3ec` | Needs this account looked at |
| "reinstalled twice, songs still won't download" | `4et` | Standard fixes already tried and failed |
| "when is the new Taylor Swift album coming?" | `6a` | Standard "as soon as it's available to us" answer |
| "third time I'm asking, check my DM" | `9er` | Chasing an earlier contact |
| "your app is garbage, fix the shuffle" | `7a` | Opinion about intended behaviour; anger isn't escalation |
| "thanks, working now!" | `0a` | Nothing left to do |
| "iOS 11.2, Spotify 8.4.27" (after Spotify asked for versions) | `4a` | Follow-up in a bug thread; keep diagnosing |

---

## Ground rules

- **Label from the tweet only.** You don't get to see what SpotifyCares actually replied — neither
  does the agent. That's the point.
- **These must be your own judgements.** If an AI fills them in, the test set and the thing being
  tested are the same model, and every number in the report becomes meaningless. Your blind labels
  disagreed with the AI on 36% of intents, which is exactly why this set has to be human.
- Aim for 20–30 seconds each. First instinct is usually right.
- Leave an item `""` if you truly can't decide — blanks are skipped, not guessed. Keep the total
  filled at **150 or more** (that's the brief's minimum).

## When you're done

Save as `labelling/answers.json` with the same shape as the template:

```json
{ "labels": { "572664": "5a", "521815": "1eb", "...": "..." } }
```

Then say it's ready. I'll validate it (bad codes are reported per message, nothing is written until
it's clean), load it, and run the final scoring.
