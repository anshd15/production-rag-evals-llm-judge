"""LLM access: one batch API, a disk cache, and pluggable providers.

Every response is cached in llm_cache/<provider>__<model>.jsonl keyed by a hash of
(model, system, user). Re-running the pipeline therefore costs nothing and gives
identical numbers — which is what makes the README's 15-minute reproduction possible.

Providers (env LLM_PROVIDER):
  gemini   Google Gemini via google-genai. Needs GEMINI_API_KEY.
  standin  No API. Cache misses are written to llm_queue/<role>/ as JSON batches and
           answered offline by a separate Claude session acting as the model, then
           loaded with `python -m src.llm ingest`. Used during development before an
           API key existed; results are reported separately from Gemini results.
Set LLM_OFFLINE=1 to forbid any new calls (cache only) — used for reproduction.

Run:  python -m src.llm ingest       # load stand-in answers into the cache
      python -m src.llm status       # show cache sizes and pending queue items
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from src.config import ROOT

load_dotenv(ROOT / ".env")

CACHE_DIR = ROOT / "llm_cache"
QUEUE_DIR = ROOT / "llm_queue"
STANDIN_BATCH = 25

MODELS = {
    "gemini": {
        "agent": os.getenv("GEMINI_AGENT_MODEL", "gemini-3.5-flash"),
        "judge": os.getenv("GEMINI_JUDGE_MODEL", "gemini-3.5-flash"),
        "labeler": os.getenv("GEMINI_LABELER_MODEL", "gemini-3.5-flash"),
    },
    # Same models, reached through Vertex AI on a GCP project instead of an AI
    # Studio key. Two reasons to prefer it: nothing secret is ever written down
    # (it authenticates with Application Default Credentials from `gcloud auth
    # application-default login`), and it bills the project rather than sharing
    # the AI Studio free tier's 500-requests-per-day-per-model cap, which is what
    # stalled the first golden run.
    "vertex": {
        "agent": os.getenv("VERTEX_AGENT_MODEL", "gemini-2.5-flash"),
        "judge": os.getenv("VERTEX_JUDGE_MODEL", "gemini-2.5-flash"),
        "labeler": os.getenv("VERTEX_LABELER_MODEL", "gemini-2.5-flash"),
    },
    "standin": {
        "agent": "claude-haiku-standin",
        "judge": "claude-sonnet-standin",
        "labeler": "claude-sonnet-standin",
    },
}


def provider() -> str:
    # tolerate "gemini   # comment" and stray quotes coming from .env
    p = (os.getenv("LLM_PROVIDER") or "").split("#")[0].strip().strip("'\"").lower()
    if not p:
        p = "gemini" if os.getenv("GEMINI_API_KEY") else "standin"
    if p not in MODELS:
        raise ValueError(f"LLM_PROVIDER must be one of {list(MODELS)}, got {p!r}")
    return p


def model_for(role: str) -> str:
    return MODELS[provider()][role]


def cache_key(model: str, system: str, user: str) -> str:
    return hashlib.sha256(json.dumps([model, system, user]).encode("utf-8")).hexdigest()[:24]


class Cache:
    def __init__(self, prov: str, model: str):
        self.path = CACHE_DIR / f"{prov}__{model}.jsonl"
        self.data: dict[str, str] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self.data[rec["key"]] = rec["response"]

    def get(self, key):
        return self.data.get(key)

    def put(self, key, response):
        if key in self.data:
            return
        self.data[key] = response
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"key": key, "response": response}, ensure_ascii=False) + "\n")


def complete_batch(role: str, requests: list[dict]) -> list[str | None]:
    """requests: [{"system": str, "user": str}, ...] -> responses (None = pending in stand-in mode)."""
    prov, model = provider(), model_for(role)
    cache = Cache(prov, model)
    keys = [cache_key(model, r["system"], r["user"]) for r in requests]
    out = [cache.get(k) for k in keys]
    missing = [i for i, o in enumerate(out) if o is None]
    if not missing:
        return out
    if os.getenv("LLM_OFFLINE") == "1":
        raise RuntimeError(f"{len(missing)} {role} calls not in cache and LLM_OFFLINE=1")
    if prov in ("gemini", "vertex"):
        for i in missing:
            out[i] = _gemini_call(model, requests[i]["system"], requests[i]["user"], prov)
            cache.put(keys[i], out[i])
    else:
        _enqueue(role, model, [(keys[i], requests[i]) for i in missing])
    return out


# ---------------------------------------------------------------- gemini
_client = None
_last_call = [0.0]
_spent = [0]


class BudgetExhausted(RuntimeError):
    """Raised instead of making a paid call once LLM_MAX_CALLS is reached."""


def calls_made() -> int:
    return _spent[0]


def _charge_budget():
    """Count every live call and stop at the cap.

    A full re-run is thousands of calls, so a loop that retries forever is
    indistinguishable from normal traffic at the provider. The cap turns a
    runaway into a crash with a number attached instead of a bill.
    """
    from src.settings import settings
    limit = settings.llm_max_calls
    if limit and _spent[0] >= limit:
        raise BudgetExhausted(
            f"LLM_MAX_CALLS={limit} reached ({_spent[0]} live calls this process). "
            f"Cached responses are already on disk; re-run to continue, or raise the cap.")
    _spent[0] += 1


def _gemini_call(model: str, system: str, user: str, prov: str = "gemini") -> str:
    """One model call: rate-paced, deadline-bound, retried with jitter, breaker-guarded.

    `prov` picks how the client authenticates, not what it does: "gemini" uses an
    AI Studio API key, "vertex" uses Application Default Credentials against a GCP
    project. Everything downstream — pacing, retries, the breaker, the cache — is
    identical, which is the point of keeping them one code path.
    """
    global _client
    import random

    from google import genai
    from google.genai import types

    from src.resilience import breaker, record_usage
    from src.settings import settings

    if _client is None:
        if prov == "vertex":
            if not settings.gcp_project:
                raise RuntimeError(
                    "LLM_PROVIDER=vertex needs GCP_PROJECT set, and credentials from "
                    "`gcloud auth application-default login`")
            _client = genai.Client(vertexai=True, project=settings.gcp_project,
                                   location=settings.gcp_location)
        else:
            _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    min_gap = 60.0 / settings.gemini_rpm
    config = types.GenerateContentConfig(
        system_instruction=system, temperature=0, response_mime_type="application/json",
        http_options=types.HttpOptions(timeout=settings.llm_timeout_s * 1000))
    last_error = None
    for attempt in range(settings.llm_max_attempts):
        breaker.before_call()  # fail fast while the provider is known to be down
        _charge_budget()       # a retry costs the same as a first attempt
        wait = _last_call[0] + min_gap - time.time()
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.time()
        try:
            resp = _client.models.generate_content(model=model, contents=user, config=config)
            record_usage(getattr(resp, "usage_metadata", None))
            breaker.record_success()
            return resp.text
        except Exception as e:  # rate limits / timeouts / transient server errors
            last_error = e
            breaker.record_failure(f"{e.__class__.__name__}: {e}")
            if attempt == settings.llm_max_attempts - 1:
                raise
            # Jitter matters: without it, every worker retries in lockstep and
            # re-creates the spike that caused the failure.
            backoff = min(60, 5 * 2 ** attempt) * (0.5 + random.random())
            print(f"  gemini error ({e.__class__.__name__}: {str(e)[:120]}), "
                  f"retry in {backoff:.1f}s", file=sys.stderr)
            time.sleep(backoff)
    raise last_error


# ---------------------------------------------------------------- stand-in queue
def _enqueue(role: str, model: str, items: list[tuple[str, dict]]):
    """Write cache misses as batch files; identical system prompts are stored once per batch."""
    qdir = QUEUE_DIR / role
    qdir.mkdir(parents=True, exist_ok=True)
    queued = set()
    for p in qdir.glob("*.json"):
        queued.update(it["key"] for it in json.loads(p.read_text(encoding="utf-8"))["items"])
    by_system: dict[str, list] = {}
    for key, req in items:
        if key not in queued:
            by_system.setdefault(req["system"], []).append({"key": key, "user": req["user"]})
    n_existing = len(list(qdir.glob("*.json")))
    for system, its in by_system.items():
        for start in range(0, len(its), STANDIN_BATCH):
            n_existing += 1
            batch = {"role": role, "model": model, "system": system,
                     "items": its[start:start + STANDIN_BATCH]}
            (qdir / f"batch_{n_existing:04d}.json").write_text(
                json.dumps(batch, ensure_ascii=False, indent=1), encoding="utf-8")


def pending_batches(role: str | None = None) -> list[Path]:
    roles = [role] if role else [p.name for p in QUEUE_DIR.glob("*") if p.is_dir()]
    out = []
    for r in roles:
        for p in sorted((QUEUE_DIR / r).glob("batch_*.json")):
            if not p.with_suffix(".responses.jsonl").exists():
                out.append(p)
    return out


def ingest(role: str | None = None) -> int:
    """Move stand-in answers (batch_X.responses.jsonl) into the cache; delete consumed files."""
    n = 0
    for batch_path in sorted(QUEUE_DIR.glob(f"{role or '*'}/batch_*.json")):
        resp_path = batch_path.with_suffix(".responses.jsonl")
        if not resp_path.exists():
            continue
        batch = json.loads(batch_path.read_text(encoding="utf-8"))
        cache = Cache("standin", batch["model"])
        wanted = {it["key"] for it in batch["items"]}
        got = {}
        for line in resp_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                if rec.get("key") in wanted:
                    resp = rec["response"]
                    got[rec["key"]] = resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)
        for k, v in got.items():
            cache.put(k, v)
        n += len(got)
        missing = wanted - set(got)
        if not got:
            # Nothing usable — most likely the answer file is still being written.
            # Leave the batch in place instead of throwing the work away.
            print(f"  {batch_path.name}: no matching answers yet, leaving queued")
            continue
        batch_path.unlink()
        resp_path.unlink()
        if missing:
            print(f"  {batch_path.name}: {len(missing)} items unanswered (will be re-queued on next run)")
    return n


def parse_json(text: str | None) -> dict | None:
    """Tolerant JSON-object parsing: strips code fences / prose around the object."""
    if not text:
        return None
    t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "ingest":
        print(f"ingested {ingest(sys.argv[2] if len(sys.argv) > 2 else None)} responses")
    for p in sorted(CACHE_DIR.glob("*.jsonl")):
        print(f"cache {p.name}: {sum(1 for _ in open(p, encoding='utf-8'))} responses")
    pend = pending_batches()
    print(f"pending stand-in batches: {len(pend)}", *[f"  {p.relative_to(ROOT)}" for p in pend], sep="\n")
