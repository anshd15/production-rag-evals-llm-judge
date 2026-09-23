# How to rate the 60 drafts

Two files in this folder:

- **`drafts.json`** — 60 drafts. Each has `id` (`d01`…`d60`), the thread, the incoming tweet,
  **the reply SpotifyCares actually sent** (the reference), and the **`draft_to_rate`**.
- **`ratings_template.json`** — one slot per id. 2 are filled from the ones you did in the tool.

Fill in the rest, save as **`labelling/ratings.json`**, and tell me.

You are not told which system wrote each draft — some are the agent's, some come from the two
baselines. That's deliberate: if you knew, your ratings would drift toward the agent.

---

## The rating code

Six characters: **five 0/1 flags** then **`y` or `n`**.

```
"11101y"  →  passes 1,2,3 and 5, fails 4 (tone), and you'd send it
"10010n"  →  passes 1 and 4 only, and you would not send it
```

### The five flags, in order

| # | Criterion | Mark `1` when… |
|---|---|---|
| 1 | **addresses_issue** | It engages with what *this* customer asked. Generic boilerplate that would fit any tweet is `0` |
| 2 | **grounded** | Nothing invented: no made-up policies, prices, dates, features or promises. Plausible for Spotify support in late 2017 and consistent with the reference |
| 3 | **correct_next_step** | The action is right: asks for a DM when the account must be checked; gives troubleshooting for a bug; acknowledges feedback; asks a clarifying question when the tweet is vague. Doesn't send the customer in circles |
| 4 | **tone** | Friendly, concise, on-brand, tweet-length. Not robotic, rude or grovelling |
| 5 | **safe** | Doesn't ask for passwords/card numbers in public, doesn't claim things it can't have done ("we've replied to your DM", "refund issued"), nothing harmful |

### The last character

**`y`** = you'd approve sending this draft **as-is**, no edits. **`n`** = it needs edits.

A draft can pass all five and still be `n` if it's weak overall — and it can fail `tone` but still
be `y` if you'd send it anyway. Trust your judgement; that gap between flags and the send decision
is part of what's being measured.

---

## How to judge against the reference

The reference shows what the real agent did, so it tells you the correct information and the
right resolution path. But **a differently-worded draft can be just as good, or better**.

- Don't mark a draft down for not using the customer's name, or for missing the agent's initials.
- Do mark it down if it contradicts the reference's facts, or takes an action that can't work.
- If the reference asks for a DM because the account must be looked at, a draft that gives generic
  troubleshooting instead is a `0` on **correct_next_step**.

## Ground rules

- Rate them in order; 20–30 seconds each is about right (~25 minutes total).
- Some drafts are deliberately terrible — that's the point, the spread is what makes the
  agreement number meaningful. Don't soften a bad one.
- Leave `""` if you truly can't decide. Aim for **40+** filled; fewer makes the kappa jumpy.
- These must be your own judgements. This file is the *only* human check on the AI grader — if a
  model fills it in, we're measuring one model against another and the 73% "send-ready" figure
  loses its meaning.

## When you're done

Save as `labelling/ratings.json`:

```json
{ "ratings": { "d01": "11101y", "d02": "10010n", "...": "..." } }
```

Then say it's ready. I'll validate it, compute agreement and Cohen's kappa per criterion, and
write `reports/judge_agreement.md`.
