"""HTTP service around the agent.

  uvicorn src.service:app --port 8000

POST /triage   {"text": "...", "context": [{"role": "customer", "text": "..."}]}
               -> {intent, escalate, escalation_reason, reply, retrieved, request_id, latency_ms}
GET  /healthz  liveness; never loads the model
GET  /readyz   readiness; reports whether the retrieval index is warm
GET  /metrics  counters since boot (Prometheus text format)

The retrieval index takes ~2 min to build, so it loads lazily on first use and
/readyz stays false until it is warm. Any failure below the API returns 503 with
a request id rather than a stack trace — a support queue would rather wait than
receive a wrong answer.
"""
import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from src import agent
from src.feedback import (ACTIONS, pending_review, record_decision, record_outcome,
                          report)
from src.observability import METRICS, log_event, render_prometheus
from src.resilience import CircuitOpen, breaker
from src.settings import settings

app = FastAPI(title="Production RAG with Evals and LLM as a Judge", version="0.3.0")
_retriever = None
_hits: dict[str, list[float]] = {}


def require_key(x_api_key: str = Header(default="")):
    """Off by default so the repo runs out of the box; set API_KEY to require it."""
    if settings.api_key and x_api_key != settings.api_key:
        METRICS["auth_rejected"] += 1
        raise HTTPException(status_code=401, detail="invalid or missing X-API-Key")


def rate_limit(request: Request):
    """Per-client sliding window. In-process on purpose: one instance, one limiter;
    a multi-instance deployment needs a shared store, and pretending otherwise
    would be worse than saying so."""
    if not settings.rate_limit_per_min:
        return
    who = request.client.host if request.client else "unknown"
    now = time.time()
    recent = [t for t in _hits.get(who, []) if now - t < 60]
    if len(recent) >= settings.rate_limit_per_min:
        METRICS["rate_limited"] += 1
        raise HTTPException(status_code=429, detail="rate limit exceeded, retry in a minute")
    recent.append(now)
    _hits[who] = recent


class Outcome(BaseModel):
    request_id: str
    action: str = Field(description=" | ".join(ACTIONS))
    final_reply: str = ""
    note: str = ""


class Turn(BaseModel):
    role: str = "customer"
    text: str


class TriageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    context: list[Turn] = Field(default_factory=list)


def get_retriever():
    global _retriever
    if _retriever is None:
        t0 = time.perf_counter()
        _retriever = agent.Retriever()
        log_event("index_loaded", rows=len(_retriever.rows),
                  ms=round((time.perf_counter() - t0) * 1000))
    return _retriever


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready" if _retriever is not None else "cold",
            "index_rows": len(_retriever.rows) if _retriever else 0,
            "breaker": breaker.state, "config": settings.summary()}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return render_prometheus()


@app.post("/triage", dependencies=[Depends(require_key), Depends(rate_limit)])
def triage(req: TriageRequest):
    request_id, t0 = str(uuid.uuid4())[:8], time.perf_counter()
    example = {"msg_id": request_id, "text": req.text,
               "context": [t.model_dump() for t in req.context], "brand_reply": ""}
    retrieved_cases: list[dict] = []
    try:
        retriever = get_retriever()
        pred = agent.run([example], retriever)[0]
        if pred and pred.get("retrieved"):
            rows = retriever.rows.set_index("msg_id")
            retrieved_cases = [{"text": rows.text[m], "brand_reply": rows.brand_reply[m]}
                               for m in pred["retrieved"] if m in rows.index]
    except CircuitOpen as exc:
        # The provider is known to be failing: say so immediately instead of
        # holding the worker for a timeout that will fail anyway.
        log_event("triage_shed", request_id=request_id, breaker=breaker.state)
        raise HTTPException(status_code=503, headers={"Retry-After": str(settings.breaker_cooldown_s)},
                            detail={"request_id": request_id, "error": str(exc)})
    except Exception as exc:
        METRICS["errors"] += 1
        log_event("triage_failed", request_id=request_id, error=type(exc).__name__)
        raise HTTPException(status_code=503, detail={"request_id": request_id,
                                                     "error": "agent unavailable"})
    if pred is None:  # stand-in provider: the answer is queued, not ready
        METRICS["pending"] += 1
        raise HTTPException(status_code=503, detail={"request_id": request_id,
                                                     "error": "model answer pending"})
    latency_ms = round((time.perf_counter() - t0) * 1000)
    METRICS["requests"] += 1
    METRICS["escalated" if pred["escalate"] else "auto_handled"] += 1
    if pred.get("guardrail"):
        METRICS[f"guardrail_{pred['guardrail']}"] += 1
    METRICS["latency_ms_total"] += latency_ms
    record_decision(request_id, pred, example, retrieved_cases)
    log_event("triage", request_id=request_id, intent=pred["intent"],
              escalate=pred["escalate"], guardrail=pred.get("guardrail"), ms=latency_ms)
    return pred | {"request_id": request_id, "latency_ms": latency_ms}


@app.post("/feedback")
def feedback(outcome: Outcome):
    """What the human agent did with the draft. This is the only signal that
    tells us whether quality is holding up in production."""
    try:
        record_outcome(outcome.request_id, outcome.action, outcome.final_reply, outcome.note)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    METRICS[f"outcome_{outcome.action}"] += 1
    log_event("feedback", request_id=outcome.request_id, action=outcome.action)
    return {"recorded": True}


@app.get("/feedback/report")
def feedback_report():
    return report()


@app.get("/review", response_class=FileResponse)
def review_console():
    """A queue a human can actually work: the draft, why it routed that way, the past
    cases it was built from, and accept / edit / reject in one keypress."""
    return FileResponse(Path(__file__).with_name("review_app.html"))


@app.get("/review/state")
def review_state():
    return {"queue": pending_review(), "report": report()}
