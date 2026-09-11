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
                       "follow-ups in a troubleshooting thread ('Android 7.0', 'still not working') "
                       "and vague breakage complaints ('is this thing broken??', 'sort your app out').",
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
        "description": "Only when you cannot tell what the message is about or what it needs: "
                       "off-topic, spam, jokes, non-English, a bare link/image with no complaint. "
                       "A vague complaint that something is broken is technical_issue, not other.",
        "examples": ["[link]", "lol", "what's everyone listening to?"],
    },
]
INTENT_KEYS = [i["key"] for i in INTENTS]

ESCALATION_REASONS = [
    {"code": "billing", "rule": "A disputed, unexpected or failed charge, or a refund request."},
    {"code": "security", "rule": "Hacked/compromised account, credentials changed by someone "
                                 "else, or locked out after the self-service reset failed."},
    {"code": "account_specific", "rule": "THIS customer's own account or subscription state must "
                                         "be inspected — even when the only sensible public reply "
                                         "is 'DM us your account email'. E.g. can't log in, "
                                         "Premium not activating, Family invite failing, Student "
                                         "verification stuck, cancelling an account they can't "
                                         "access. A general question about how a plan works ('do "
                                         "I have to cancel Premium before joining a Family plan?') "
                                         "is NOT account_specific — that is how_to_usage, "
                                         "auto-handle."},
    {"code": "troubleshooting_exhausted", "rule": "The customer explicitly says they ALREADY did "
                                                  "at least one standard fix (logged out/in, "
                                                  "restarted the device, reinstalled the app, "
                                                  "cleared cache) and it still fails. Narrowing "
                                                  "the problem down (works on another device, only "
                                                  "over Bluetooth, only on WiFi) or answering "
                                                  "diagnostic questions (device, OS, version) is "
                                                  "diagnosis, NOT exhaustion — keep diagnosing."},
    {"code": "repeat_contact", "rule": "Chasing an earlier DM/ticket, or says they already "
                                       "contacted support without an answer."},
    {"code": "risk", "rule": "Legal/regulatory threat, safety or self-harm, harassment, "
                             "discrimination, press, or an explicit request for a human."},
]
ESCALATION_CODES = [r["code"] for r in ESCALATION_REASONS]

ESCALATION_POLICY = """\
ROUTING — who owns the case once the reply is sent?

THE TEST: after this reply goes out, does a human at Spotify still have to do something for this
customer? If yes -> ESCALATE. Asking them to DM their account email so the account can be checked
means yes: the reply is a safe holding message, but a human still works the case.

ESCALATE (routed to a human agent; your reply is a draft they review) if ANY rule applies:
{rules}

AUTO-HANDLE otherwise — your reply alone settles it and no human follow-up is implied: how-to
answers, first-line troubleshooting steps or diagnostic questions, content/country availability,
acknowledging feedback, artist referral to Spotify for Artists, thanks, or a clarifying question
for a vague message. Anger alone is NOT a reason to escalate if the answer is standard.\
""".format(rules="\n".join(f"- {r['code']}: {r['rule']}" for r in ESCALATION_REASONS))


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
