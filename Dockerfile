FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# Offline by default: the image ships the response cache, so it serves
# reproducible answers with no key. Override to call a live provider.
ENV LLM_OFFLINE=1 LLM_PROVIDER=standin
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake the embedding model into the image.
#
# Without this the container fetches all-MiniLM-L6-v2 from huggingface.co on
# the FIRST REQUEST of every cold start, unauthenticated. On Cloud Run that
# meant a 429 from the HF Hub and a request that never returned -- a hard
# runtime dependency on a third party, paid on every scale-from-zero.
# HF_HUB_OFFLINE then guarantees it can never reach for the network again:
# if the weights are missing the container fails loudly at startup instead of
# hanging on a download mid-request.
ENV HF_HOME=/opt/hf
RUN mkdir -p /opt/hf && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')"
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

COPY src/ src/
COPY data/processed/ data/processed/
COPY llm_cache/ llm_cache/

RUN useradd --create-home app && chown -R app /app /opt/hf
USER app

# The host decides the port. Cloud Run injects PORT=8080 and fails the startup
# probe when nothing is listening there, so it cannot be hardcoded -- and exec
# form does no variable expansion, hence sh -c. `exec` keeps uvicorn as PID 1 so
# it still receives SIGTERM and drains instead of being killed after the grace
# period.
ENV PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s \
  CMD python -c "import os,urllib.request;urllib.request.urlopen('http://localhost:'+os.environ.get('PORT','8000')+'/healthz')"

# --proxy-headers: behind Cloud Run the peer is always Google's front end, so
# request.client.host is the SAME address for every visitor on earth and a
# "per-client" rate limit silently becomes one shared bucket. The real address
# is in X-Forwarded-For, which uvicorn ignores unless told to read it -- the
# default is cautious because that header is attacker-writable in general. It
# is not here: the container is only reachable through the front end, which
# overwrites it.
CMD ["sh", "-c", "exec uvicorn src.service:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=*"]
