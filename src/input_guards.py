"""Screen the customer message BEFORE it reaches the model.

Public support channels are hostile input: people paste card numbers into
tweets, and anything that reaches a prompt can try to steer it. Two checks:

  prompt_injection  text trying to override the agent's instructions
  pii               payment-card or full email/phone data in a public tweet

Neither is fatal on its own — both force the case to a human, and PII is
redacted before the text is ever sent to a model or written to a log.
"""
import re

INJECTION_PATTERNS = [
    r"\bignore\b[^.!?]{0,30}\b(previous|prior|above|earlier)\b[^.!?]{0,20}\b(instruction|prompt|rule)",
    r"\bdisregard\b[^.!?]{0,30}\b(instruction|prompt|rule|system)",
    r"\b(you are|act as|pretend to be|roleplay as)\b[^.!?]{0,30}\b(now|a different|an?)\b[^.!?]{0,20}"
    r"\b(assistant|ai|bot|admin|developer)\b",
    r"\b(system|developer)\s*(prompt|message)\b",
    r"\b(reveal|show|print|repeat|output)\b[^.!?]{0,25}\b(prompt|instruction|system message)\b",
    r"\b(issue|approve|grant|give)\b[^.!?]{0,25}\b(refund|credit|premium|free)\b[^.!?]{0,25}"
    r"\b(immediately|without|no)\b",
    r"</?(system|instruction|admin)>",
]
INJECTION_RE = re.compile("|".join(INJECTION_PATTERNS), re.I)

CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+\d{1,3}[ -]?)?(?:\(\d{3}\)|\d{3})[ -]?\d{3}[ -]?\d{4}(?!\w)")
PII_PATTERNS = {"card": CARD_RE, "email": EMAIL_RE, "phone": PHONE_RE}


def luhn(digits: str) -> bool:
    """Real card numbers pass Luhn; order ids and tracking numbers usually don't."""
    ds = [int(c) for c in digits if c.isdigit()]
    if not 13 <= len(ds) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(ds)):
        if i % 2:
            d *= 2
            d -= 9 if d > 9 else 0
        total += d
    return total % 10 == 0


def find_pii(text: str) -> list[str]:
    found = []
    for kind, pattern in PII_PATTERNS.items():
        for m in pattern.finditer(text or ""):
            if kind != "card" or luhn(m.group(0)):
                found.append(kind)
                break
    return found


def redact(text: str) -> str:
    """Replace PII with placeholders before the text reaches a model or a log."""
    out = CARD_RE.sub(lambda m: "[card]" if luhn(m.group(0)) else m.group(0), text or "")
    out = EMAIL_RE.sub("[email]", out)
    return PHONE_RE.sub("[phone]", out)


def screen(text: str) -> dict:
    pii = find_pii(text)
    return {
        "prompt_injection": bool(INJECTION_RE.search(text or "")),
        "pii": pii,
        "safe_text": redact(text) if pii else (text or ""),
    }
