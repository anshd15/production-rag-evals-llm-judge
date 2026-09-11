"""Intent taxonomy + escalation policy for SpotifyCares.

Single source of truth: the same text is shown to the human labeller, the silver
labeller and the agent, so disagreements are about judgment, not definitions.
Derived from reports/intent_discovery.md (30 KMeans clusters over history tweets).
"""

INTENTS = [
    {
        "key": "billing_payment",
        "name": "Billing & payment problem",
        "description": "Money has moved or failed to move: unexpected/double charges, refund "
                       "requests, payment declined, charged but Premium not active, charged the "
                       "wrong price (e.g. full price on Student).",
        "examples": ["I was charged twice this month", "paid for premium but my account still says free",
                     "my card keeps getting declined when I try to pay"],
    },
    {
        "key": "subscription_plan",
        "name": "Plan & subscription management",
        "description": "Changing, cancelling or joining a plan with no disputed charge: cancel "
                       "Premium, Family plan invites/members, Student discount eligibility or "
                       "renewal, trials, promo offers, gift cards.",
        "examples": ["how do I cancel premium?", "can't add my wife to our family plan",
                     "is the student discount available in Canada?"],
    },
    {
        "key": "account_access",
        "name": "Account access & security",
        "description": "Can't log in, password reset email not arriving, hacked/compromised "
                       "account, email changed by someone else, merging or deleting accounts, "
                       "Facebook-login problems.",
        "examples": ["someone changed the email on my account", "reset password email never arrives",
                     "I have two accounts, can you merge them?"],
    },
    {
        "key": "technical_issue",
        "name": "App / playback technical issue",
        "description": "Something is broken: app crashes, songs won't play or skip, web player "
                       "down, device/Connect/Chromecast/car problems, downloads or saved music "
                       "disappearing, ads malfunctioning (e.g. ad-free time resetting). Includes "
                       "follow-ups in a troubleshooting thread ('Android 7.0', 'still not working').",
        "examples": ["my downloaded songs keep disappearing", "web player not working in Chrome",
                     "iPhone 7, iOS 11.1, Spotify 8.4.25"],
    },
    {
        "key": "how_to_usage",
        "name": "How-to / product question",
        "description": "Asks how to do something or whether something is possible, nothing is "
                       "broken: import local files/iTunes, collaborative playlists, lyrics, "
                       "change country, pay annually, sort playlists.",
        "examples": ["how can I import my iTunes library?", "is it possible to pay annually?",
                     "how do I make a collaborative playlist?"],
    },
    {
        "key": "content_availability",
        "name": "Content or service availability",
        "description": "A song/album/artist/podcast is missing, removed, greyed out or region-"
                       "locked; when a release will land; when Spotify launches in a country.",
        "examples": ["when will Reputation be on Spotify?", "why was this album removed?",
                     "when is Spotify coming to India?"],
    },
    {
        "key": "feedback_feature_request",
        "name": "Feedback & feature request",
        "description": "Opinions about how the product is designed (working as intended): "
                       "feature requests, complaints about ads frequency, shuffle, the 10k library "
                       "limit, removed features, UI changes, 'when will you support iPhone X?'.",
        "examples": ["please bring back touch preview", "too many ads on free",
                     "you should add an Apple Watch app"],
    },
    {
        "key": "artist_creator",
        "name": "Artist / creator support",
        "description": "Artists, labels or curators: artist profile verification, music on the "
                       "wrong artist page, playlist submission, getting music onto Spotify.",
        "examples": ["my song is showing under another artist", "how do I get added to your playlists?"],
    },
    {
        "key": "dm_status_followup",
        "name": "DM / status follow-up",
        "description": "Chasing support rather than describing an issue: 'I sent you a DM', "
                       "'please check my DM', 'still waiting for a reply', 'nobody responded'.",
        "examples": ["hello I sent you a DM please check", "still waiting for help on my issue"],
    },
    {
        "key": "praise_thanks",
        "name": "Praise, thanks & resolved",
        "description": "Compliments, gratitude, or confirming the problem is fixed.",
        "examples": ["thank you, it works now!", "love the new Wrapped feature"],
    },
    {
        "key": "other",
        "name": "Other / unclear",
        "description": "Off-topic, spam, jokes, non-English, a bare link/image with no context, "
                       "or too vague to tell what is needed.",
        "examples": ["[link]", "lol", "what's everyone listening to?"],
    },
]
INTENT_KEYS = [i["key"] for i in INTENTS]

ESCALATION_REASONS = [
    {"code": "billing", "rule": "A disputed, unexpected or failed charge, or a refund request."},
    {"code": "security", "rule": "Hacked/compromised account, credentials changed by someone "
                                 "else, or locked out after the self-service reset failed."},
    {"code": "account_specific", "rule": "Can only be resolved by looking up THIS customer's "
                                         "account/subscription (e.g. Premium not activating, "
                                         "Family invite failing, cancelling an account they "
                                         "can't access, Student verification stuck)."},
    {"code": "troubleshooting_exhausted", "rule": "The customer says standard fixes (log out/"
                                                  "restart/reinstall/clear cache) already failed."},
    {"code": "repeat_contact", "rule": "Chasing an earlier DM/ticket, or says they already "
                                       "contacted support without an answer."},
    {"code": "risk", "rule": "Legal/regulatory threat, safety or self-harm, harassment, "
                             "discrimination, press, or an explicit request for a human."},
]
ESCALATION_CODES = [r["code"] for r in ESCALATION_REASONS]

ESCALATION_POLICY = """\
ESCALATE (a human agent must handle it) if ANY rule applies:
{rules}

AUTO-HANDLE otherwise — i.e. the right reply is standard guidance anyone on the team would give
without looking at the account: how-to answers, first-line troubleshooting steps, content/country
availability, acknowledging feedback, artist referral to Spotify for Artists, thanks, or asking a
clarifying question for vague messages. Anger alone is NOT a reason to escalate if the answer is
standard.""".format(rules="\n".join(f"- {r['code']}: {r['rule']}" for r in ESCALATION_REASONS))


def intents_block() -> str:
    lines = []
    for i in INTENTS:
        ex = "; ".join(f'"{e}"' for e in i["examples"])
        lines.append(f"- {i['key']}: {i['description']} e.g. {ex}")
    return "\n".join(lines)


LABELING_GUIDE = f"""\
You label ONE incoming customer tweet to SpotifyCares (with earlier turns for context).

INTENT — what the customer needs right now. Use the earlier turns to interpret short replies
('Android 7.0' in a troubleshooting thread is technical_issue; 'thanks!' is praise_thanks).
If several apply, pick the one that decides what the reply must do. Money involved beats plan;
security beats access how-to.
{intents_block()}

{ESCALATION_POLICY}
"""
