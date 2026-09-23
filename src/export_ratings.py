"""Export the reply-rating set for offline rating, and import the ratings back.

  python -m src.export_ratings export        -> labelling/drafts.json + ratings_template.json
  python -m src.export_ratings import labelling/ratings.json

Which system wrote each draft is withheld (that is the point of the exercise), and
so is the judge's verdict. The reply SpotifyCares actually sent IS shown, because
the judge sees it too — agreement is only meaningful on the same evidence.

Rating code: five pass/fail characters + a send decision, e.g. "11101 y".
"""
import json
import sys

from src.config import PROCESSED, ROOT
from src.label_app import RATING_SET, RATINGS
from src.make_eval_sets import read_jsonl

PACK = ROOT / "labelling"
DRAFTS = PACK / "drafts.json"
TEMPLATE = PACK / "ratings_template.json"
# item_id encodes the system ("93902:agent"), so the pack uses opaque ids and the
# mapping stays outside labelling/ — the rater must not know who wrote a draft.
ID_MAP = PROCESSED / "rating_id_map.json"
CRITERIA = ["addresses_issue", "grounded", "correct_next_step", "tone", "safe"]


def parse_code(code: str) -> dict | str:
    c = (code or "").strip().lower().replace(" ", "")
    if not c:
        return "empty"
    if len(c) != 6:
        return f"expected 5 pass/fail digits + y/n (e.g. '11101y'), got {code!r}"
    bits, send = c[:5], c[5]
    if any(ch not in "01" for ch in bits):
        return f"first five characters must be 0 or 1, got {bits!r}"
    if send not in "yn":
        return f"last character must be y or n, got {send!r}"
    return {k: bits[i] == "1" for i, k in enumerate(CRITERIA)} | {"would_send": send == "y"}


def export():
    PACK.mkdir(exist_ok=True)
    items = read_jsonl(RATING_SET)
    done = {r["item_id"]: r for r in read_jsonl(RATINGS)} if RATINGS.exists() else {}
    drafts, template, id_map = [], {}, {}
    for n, it in enumerate(items, 1):
        did = f"d{n:02d}"
        id_map[did] = it["item_id"]
        drafts.append({
            "n": n,
            "id": did,
            "thread_so_far": [{"who": "Customer" if t["role"] == "customer" else
                               ("SpotifyCares" if t["role"] == "Spotify" else "Someone else"),
                               "text": t["text"]} for t in it["context"]],
            "incoming_tweet": it["text"],
            "reference_reply_spotify_actually_sent": it["brand_reply"],
            "draft_to_rate": it["draft"],
        })
        prev = done.get(it["item_id"])
        template[did] = ("".join("1" if prev[k] else "0" for k in CRITERIA) +
                         ("y" if prev["would_send"] else "n")) if prev else ""
    ID_MAP.write_text(json.dumps(id_map, indent=1), encoding="utf-8")
    DRAFTS.write_text(json.dumps(drafts, ensure_ascii=False, indent=1), encoding="utf-8")
    TEMPLATE.write_text(json.dumps({"ratings": template}, ensure_ascii=False, indent=1), encoding="utf-8")
    filled = sum(1 for v in template.values() if v)
    print(f"{len(drafts)} drafts -> {DRAFTS}")
    print(f"ratings template -> {TEMPLATE}  ({filled} already done, {len(template) - filled} to fill)")


def import_ratings(path: str):
    data = json.loads(open(path, encoding="utf-8").read())
    ratings = data.get("ratings", data)
    items = {it["item_id"]: it for it in read_jsonl(RATING_SET)}
    id_map = json.loads(ID_MAP.read_text(encoding="utf-8"))
    valid, errors, blank = {}, [], 0
    for did, item_id in id_map.items():
        parsed = parse_code(ratings.get(did, ""))
        if parsed == "empty":
            blank += 1
        elif isinstance(parsed, str):
            errors.append(f"  {did}: {parsed}")
        else:
            valid[item_id] = parsed
    unknown = set(ratings) - set(id_map)
    if unknown:
        errors.append(f"  {len(unknown)} unknown draft ids: {sorted(unknown)[:5]}")
    for e in errors[:20]:
        print(e)
    if errors:
        print(f"{len(errors)} problem(s) — nothing written. Fix and re-run.")
        return
    with open(RATINGS, "w", encoding="utf-8") as f:
        for item_id, r in valid.items():
            f.write(json.dumps({"item_id": item_id, "msg_id": items[item_id]["msg_id"],
                                **r, "rater": "human"}, ensure_ascii=False) + "\n")
    print(f"wrote {len(valid)} ratings -> {RATINGS}  ({blank} blank)")
    if len(valid) < 30:
        print(f"⚠  {len(valid)} ratings is thin for a kappa; 40+ is much steadier.")
    print("Next:  python -m src.judge_agreement score --run final")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "export"
    export() if cmd == "export" else import_ratings(sys.argv[2])
