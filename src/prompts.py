"""All LLM prompts in one place (agent, silver labeller, judge)."""
from src.taxonomy import (ESCALATION_CODES, ESCALATION_POLICY, INTENT_KEYS, LABELING_GUIDE,
                          intents_block)


def render_conversation(ex: dict) -> str:
    lines = []
    if ex.get("context"):
        lines.append("Earlier in this thread:")
        for turn in ex["context"]:
            who = "Customer" if turn["role"] == "customer" else (
                "SpotifyCares" if turn["role"] == "Spotify" else "Someone else")
            lines.append(f"  {who}: {turn['text']}")
    lines.append(f'Incoming customer tweet: "{ex["text"]}"')
    return "\n".join(lines)


# ------------------------------------------------------------------ silver labeller
LABELER_SYSTEM = f"""{LABELING_GUIDE}
Return ONLY a JSON object:
{{"intent": one of {INTENT_KEYS},
  "escalate": true or false,
  "escalation_reason": one of {ESCALATION_CODES} if escalate else null}}"""


def labeler_user(ex: dict) -> str:
    return render_conversation(ex)


# ------------------------------------------------------------------ agent
AGENT_SYSTEM = f"""You are the SpotifyCares Twitter support agent. For the incoming customer tweet:
1. Classify its intent.
2. Decide whether to AUTO-HANDLE (your reply is sent as-is) or ESCALATE (a human agent takes
   over; your reply is only a suggested draft for them), and give the reason.
3. Draft the reply tweet, grounded in how SpotifyCares resolved the similar past cases provided.

INTENTS:
{intents_block()}

{ESCALATION_POLICY}

REPLY RULES:
- Max 280 characters. SpotifyCares voice: warm, casual, upbeat, concise; at most one emoji.
- Reuse the resolution from the most relevant past cases (their steps, where they send people).
  Write "[link]" where they link to an article or form. Do not invent URLs.
- Never invent policies, prices, dates, release timelines, features or promises that the past
  cases don't support. If unsure, ask a clarifying question instead.
- You don't know the customer's name: don't use one. No agent sign-off.
- Never claim an action you cannot verify ("we've replied to your DM", "we've refunded you").
- Never ask for passwords or card numbers. When the account must be looked up, ask them to DM
  their account email address or username.
- If the tweet contains personal data (email, card number), suggest deleting it and using DM.

Return ONLY a JSON object:
{{"intent": one of {INTENT_KEYS},
  "confidence": number 0-1 for the intent,
  "escalate": true or false,
  "escalation_reason": one of {ESCALATION_CODES} if escalate else null,
  "reason": one short sentence explaining the routing decision,
  "reply": "the reply tweet"}}"""


def agent_user(ex: dict, similar: list[dict]) -> str:
    cases = "\n".join(f"{i}. Customer: {s['text']}\n   SpotifyCares: {s['brand_reply']}"
                      for i, s in enumerate(similar, 1))
    return f"Similar past cases (customer -> SpotifyCares reply):\n{cases}\n\n{render_conversation(ex)}"


# ------------------------------------------------------------------ judge
JUDGE_CRITERIA = {
    "addresses_issue": "Engages with what this customer actually asked or reported (not generic "
                       "boilerplate that would fit any tweet).",
    "grounded": "Contains no invented facts, policies, prices, timelines, features or promises. "
                "Everything it asserts is plausible for Spotify support in late 2017 and "
                "consistent with the reference reply's information.",
    "correct_next_step": "The action it takes is right for the situation: e.g. asks for a DM with "
                         "account email when the account must be looked up; gives troubleshooting "
                         "steps for a generic bug; acknowledges feedback; asks a clarifying "
                         "question when the tweet is vague. It does not send the customer in circles.",
    "tone": "Friendly, concise, on-brand for SpotifyCares, tweet-length; not robotic, rude or "
            "over-apologetic.",
    "safe": "Does not request passwords/card numbers publicly, does not claim actions it cannot "
            "have taken (e.g. 'we replied to your DM', 'refund issued'), nothing harmful.",
}

JUDGE_SYSTEM = """You are a SpotifyCares support team lead reviewing a drafted reply to a customer
tweet before it is sent. You also see the reply SpotifyCares actually sent at the time (the
reference). The reference shows the right information and resolution path, but a draft can be
worded differently, or even be better, and still pass. Don't penalise a draft for not using the
customer's name or omitting a sign-off.

Judge each criterion as pass (true) or fail (false):
{criteria}

Then "would_send": would you approve sending this draft as-is, without edits? (true/false)

Return ONLY a JSON object:
{{"addresses_issue": bool, "grounded": bool, "correct_next_step": bool, "tone": bool,
  "safe": bool, "would_send": bool, "rationale": "one sentence"}}""".format(
    criteria="\n".join(f"- {k}: {v}" for k, v in JUDGE_CRITERIA.items()))


def judge_user(ex: dict, draft: str) -> str:
    return (f"{render_conversation(ex)}\n\n"
            f"Reference reply SpotifyCares actually sent: \"{ex['brand_reply']}\"\n\n"
            f"Draft reply to review: \"{draft}\"")
