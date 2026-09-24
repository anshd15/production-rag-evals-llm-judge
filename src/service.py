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

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from src import agent
from src.feedback import ACTIONS, record_decision, record_outcome
from src.observability import METRICS, log_event, render_prometheus

app = FastAPI(title="Handoff", version="0.2.0")
_retriever = None


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
            "index_rows": len(_retriever.rows) if _retriever else 0}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return render_prometheus()


@app.post("/triage")
def triage(req: TriageRequest):
    request_id, t0 = str(uuid.uuid4())[:8], time.perf_counter()
    example = {"msg_id": request_id, "text": req.text,
               "context": [t.model_dump() for t in req.context], "brand_reply": ""}
    try:
        pred = agent.run([example], get_retriever())[0]
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
    record_decision(request_id, pred)
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
    from src.feedback import report
    return report()
