"""Build the brand's conversation table from the raw Kaggle dump.

One output row = one inbound customer tweet that the brand replied to, with
  - the cleaned customer text
  - up to MAX_CONTEXT_TURNS previous turns of the same thread
  - the brand's reply (multi-part replies merged)
  - split: "history" (older threads) or "eval_pool" (newest threads)

Run:  python -m src.data_prep
"""
import html
import json
import re

import pandas as pd

from src.config import BRAND, BRAND_NAME, EVAL_START, MAX_CONTEXT_TURNS, MESSAGES, RAW_CSV

URL_RE = re.compile(r"https?://\S+")
LEADING_MENTIONS_RE = re.compile(r"^(\s*\.?@\w+[:,]?)+\s*")
MENTION_RE = re.compile(r"@\w+")
# Agent sign-offs at the end of brand tweets: "/JN", "^Kev", "*HJH" (optionally followed by links)
SIGNATURE_RE = re.compile(r"\s+[/^*]\s?[A-Z][A-Za-z]{0,7}(?=(\s*\[link\])*\s*$)")
# Multi-part markers: "1/2", "(2/2)" at the end, "1: " at the start
PART_SUFFIX_RE = re.compile(r"\s*\(?\d/\d\)?\s*$")
PART_PREFIX_RE = re.compile(r"^\d:\s*")
DM_RE = re.compile(r"\b(?:dm|dms|direct message|private message)\b", re.I)

# Words that are function words in English but not in Spanish/Portuguese/French/German
# ("me", "no", "a" are ambiguous, so they are left out).
EN_FUNCTION_WORDS = set(
    "the an im i'm my you your it its it's is are was were to of and on for with "
    "this that not can can't cant why how what when do does don't dont have has be been "
    "just all get got but if there".split()
)
NON_EN_FUNCTION_WORDS = set(
    "de la el que en y los las por para con una un mi es se lo como pero muy ya gracias hola "
    "ayuda não você obrigado est le les des et je pas ich und nicht der die das ist "
    "een het ik niet van mijn hoe saya mau tidak yang dan ini itu kok dari".split()
)


def clean_text(text: str, is_brand: bool = False) -> str:
    t = html.unescape(text or "")
    t = URL_RE.sub("[link]", t)
    t = LEADING_MENTIONS_RE.sub("", t)
    t = MENTION_RE.sub("@user", t)
    if is_brand:
        t = PART_PREFIX_RE.sub("", t)
        t = PART_SUFFIX_RE.sub("", t)
        t = SIGNATURE_RE.sub("", t)
        t = PART_SUFFIX_RE.sub("", t)
    return re.sub(r"\s+", " ", t).strip()


def looks_english(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    if sum(ord(c) > 127 for c in letters) / len(letters) > 0.3:
        return False
    words = re.findall(r"[a-zà-ÿ']+", text.lower().replace("’", "'"))
    en = sum(w in EN_FUNCTION_WORDS for w in words)
    non_en = sum(w in NON_EN_FUNCTION_WORDS for w in words)
    # English unless there is positive evidence of another language
    return non_en == 0 if len(words) <= 3 else non_en <= en


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_CSV, dtype={"author_id": "string", "text": "string",
                                     "response_tweet_id": "string"})
    df["created_at"] = pd.to_datetime(df.created_at, format="%a %b %d %H:%M:%S %z %Y")
    df["parent_id"] = df.in_response_to_tweet_id.astype("Int64")
    return df


def build_messages(df: pd.DataFrame) -> pd.DataFrame:
    tweets = {
        tid: (author, inbound, text, parent, ts)
        for tid, author, inbound, text, parent, ts in zip(
            df.tweet_id, df.author_id, df.inbound, df.text, df.parent_id, df.created_at)
    }
    brand = df[df.author_id == BRAND].sort_values("created_at")

    # parent tweet id -> brand tweets replying to it (in time order)
    brand_children: dict[int, list[int]] = {}
    for tid, parent in zip(brand.tweet_id, brand.parent_id):
        if pd.notna(parent):
            brand_children.setdefault(int(parent), []).append(tid)

    def parent_of(tid):
        p = tweets[tid][3]
        return int(p) if pd.notna(p) and int(p) in tweets else None

    def merged_reply(first_id: int) -> str:
        """Brand reply plus up to 2 self-continuations (the "1/2 ... 2/2" pattern)."""
        parts, cur = [tweets[first_id][2]], first_id
        for _ in range(2):
            nxt = brand_children.get(cur)
            if not nxt:
                break
            cur = nxt[0]
            parts.append(tweets[cur][2])
        return " ".join(clean_text(p, is_brand=True) for p in parts)

    def root_of(tid):
        seen = 0
        while (p := parent_of(tid)) is not None and seen < 50:
            tid, seen = p, seen + 1
        return tid

    rows = []
    for cust_id, replies in brand_children.items():
        if cust_id not in tweets:
            continue
        author, inbound, text, _, ts = tweets[cust_id]
        if not inbound or pd.isna(text):
            continue

        context, cur = [], parent_of(cust_id)
        while cur is not None and len(context) < MAX_CONTEXT_TURNS:
            c_author, c_inbound, c_text, _, _ = tweets[cur]
            role = "customer" if c_inbound else (BRAND_NAME if c_author == BRAND else "other")
            context.append({"role": role, "text": clean_text(c_text, is_brand=not c_inbound)})
            cur = parent_of(cur)
        context.reverse()

        root = root_of(cust_id)
        reply = merged_reply(replies[0])
        rows.append({
            "msg_id": int(cust_id),
            "thread_id": int(root),
            "thread_start": tweets[root][4],
            "customer_id": author,
            "created_at": ts,
            "is_opener": parent_of(cust_id) is None,
            "context": json.dumps(context, ensure_ascii=False),
            "text_raw": text,
            "text": clean_text(text),
            "brand_reply": reply,
            "reply_asks_dm": bool(DM_RE.search(reply)),
        })

    out = pd.DataFrame(rows)
    keep = out.text.str.count(r"\w") >= 3
    keep &= out.text.map(looks_english)
    keep &= out.brand_reply.str.len() > 0
    out = out[keep].copy()
    out["split"] = (out.thread_start >= pd.Timestamp(EVAL_START, tz="UTC")).map(
        {True: "eval_pool", False: "history"})
    return out.sort_values("created_at").reset_index(drop=True)


def main():
    df = load_raw()
    msgs = build_messages(df)
    MESSAGES.parent.mkdir(parents=True, exist_ok=True)
    msgs.to_parquet(MESSAGES, index=False)
    print(f"{len(msgs)} messages -> {MESSAGES}")
    print(msgs.groupby("split").agg(n=("msg_id", "size"), openers=("is_opener", "mean"),
                                    asks_dm=("reply_asks_dm", "mean"),
                                    start=("created_at", "min"), end=("created_at", "max")))


if __name__ == "__main__":
    main()
