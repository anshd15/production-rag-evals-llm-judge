"""Local labelling tool (stdlib only): golden-set labels + human reply ratings.

Run:  python -m src.label_app        then open http://localhost:8765

Labels are appended to data/processed/golden_labels.jsonl and ratings to
data/processed/human_reply_ratings.jsonl as you go (later lines win), so you can
stop and resume at any time. The brand's real reply is deliberately hidden while
labelling: you label from exactly what the agent sees.
"""
import json
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from src.config import PROCESSED
from src.make_eval_sets import GOLDEN_FILE, read_jsonl
from src.taxonomy import ESCALATION_REASONS, INTENTS, LABELING_GUIDE

PORT = 8765
LABELS = PROCESSED / "golden_labels.jsonl"
RATING_SET = PROCESSED / "rating_set.jsonl"
RATINGS = PROCESSED / "human_reply_ratings.jsonl"
HTML = Path(__file__).with_name("label_app.html")


def _latest(path: Path, key: str) -> dict:
    return {str(r[key]): r for r in read_jsonl(path)} if path.exists() else {}


def _append(path: Path, rec: dict):
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, body: bytes, ctype: str, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            return self._send(HTML.read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/state":
            golden = [{k: ex[k] for k in ("msg_id", "context", "text")} for ex in read_jsonl(GOLDEN_FILE)]
            state = {
                "golden": golden,
                "labels": _latest(LABELS, "msg_id"),
                "intents": INTENTS,
                "reasons": ESCALATION_REASONS,
                "guide": LABELING_GUIDE,
                "rating_items": read_jsonl(RATING_SET) if RATING_SET.exists() else [],
                "ratings": _latest(RATINGS, "item_id"),
            }
            return self._send(json.dumps(state, ensure_ascii=False).encode("utf-8"), "application/json")
        self._send(b"not found", "text/plain", 404)

    def do_POST(self):
        rec = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path == "/api/label":
            _append(LABELS, {"msg_id": int(rec["msg_id"]), "intent": rec["intent"],
                             "escalate": bool(rec["escalate"]),
                             "escalation_reason": rec.get("escalation_reason") if rec["escalate"] else None,
                             "note": rec.get("note", ""), "labeller": "human"})
        elif self.path == "/api/rating":
            _append(RATINGS, rec | {"rater": "human"})
        else:
            return self._send(b"not found", "text/plain", 404)
        self._send(b'{"ok":true}', "application/json")


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"Labelling tool running at {url}  (Ctrl+C to stop)")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    server.serve_forever()


if __name__ == "__main__":
    main()
