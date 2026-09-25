"""The golden set as a versioned artifact: load it, and prove it hasn't drifted.

  python -m src.dataset verify     # checksums + schema, exit 1 on any mismatch

An evaluation set is only meaningful if everyone is scoring the same rows. The
manifest pins a sha256 per file and the row count; `verify` runs in CI, so a
stray re-sample or a hand-edited label fails the build instead of quietly
moving every number in the report.
"""
import hashlib
import json
import sys

from src.config import PROCESSED, ROOT
from src.make_eval_sets import read_jsonl
from src.taxonomy import ESCALATION_CODES, INTENT_KEYS

CRLF, LF = bytes([13, 10]), bytes([10])
MANIFEST = ROOT / "data" / "golden" / "v1" / "manifest.json"
REQUIRED_EXAMPLE_FIELDS = {"msg_id", "thread_id", "customer_id", "created_at", "is_opener",
                           "context", "text", "brand_reply", "stratum"}


def sha256(path) -> str:
    """Hash the content, not the line endings.

    .gitattributes normalises to LF in the repository, so a Windows checkout has
    CRLF on disk and a Linux one has LF. Hashing raw bytes makes the manifest
    fail on whichever platform did not create it — which is exactly what
    happened the first time CI ran this.
    """
    return hashlib.sha256(path.read_bytes().replace(CRLF, LF)).hexdigest()


def validate_examples(rows: list[dict]) -> list[str]:
    problems = []
    seen = set()
    for r in rows:
        missing = REQUIRED_EXAMPLE_FIELDS - set(r)
        if missing:
            problems.append(f"msg {r.get('msg_id')}: missing {sorted(missing)}")
        if r["msg_id"] in seen:
            problems.append(f"msg {r['msg_id']}: duplicate")
        seen.add(r["msg_id"])
        if not str(r.get("text", "")).strip():
            problems.append(f"msg {r['msg_id']}: empty text")
    return problems


def validate_labels(rows: list[dict], example_ids: set[int]) -> list[str]:
    problems = []
    for r in rows:
        if r["intent"] not in INTENT_KEYS:
            problems.append(f"msg {r['msg_id']}: unknown intent {r['intent']!r}")
        if not isinstance(r["escalate"], bool):
            problems.append(f"msg {r['msg_id']}: escalate is not a bool")
        if r["escalate"] and r["escalation_reason"] not in ESCALATION_CODES:
            problems.append(f"msg {r['msg_id']}: escalate without a valid reason")
        if r["escalate"] is False and r["escalation_reason"]:
            problems.append(f"msg {r['msg_id']}: auto-handle carries an escalation reason")
        if r["msg_id"] not in example_ids:
            problems.append(f"msg {r['msg_id']}: label for a message outside the set")
    return problems


def load(split: str = "golden") -> tuple[list[dict], dict[int, dict]]:
    """Returns (examples, labels-by-msg_id). Labels may be empty if unlabelled."""
    examples = read_jsonl(PROCESSED / f"{split}_set.jsonl")
    label_path = PROCESSED / f"{split}_labels.jsonl"
    labels = {r["msg_id"]: r for r in read_jsonl(label_path)} if label_path.exists() else {}
    return examples, labels


def verify() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    problems = []
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        if not path.exists():
            problems.append(f"{entry['path']}: missing")
            continue
        rows = read_jsonl(path)
        if len(rows) != entry["rows"]:
            problems.append(f"{entry['path']}: {len(rows)} rows, manifest says {entry['rows']}")
        digest = sha256(path)
        if digest != entry["sha256"]:
            problems.append(f"{entry['path']}: sha256 {digest[:12]}… != {entry['sha256'][:12]}…")

    examples, labels = load("golden")
    problems += validate_examples(examples)
    problems += validate_labels(list(labels.values()), {e["msg_id"] for e in examples})

    print(f"golden v{manifest['version']}: {len(examples)} messages, {len(labels)} labels")
    for p in problems[:15]:
        print("  FAIL", p)
    print("dataset verified" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(verify() if len(sys.argv) < 2 or sys.argv[1] == "verify" else 0)
