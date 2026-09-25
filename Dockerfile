FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# Offline by default: the image ships the response cache, so it serves
# reproducible answers with no key. Override to call a live provider.
ENV LLM_OFFLINE=1 LLM_PROVIDER=standin
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY data/processed/ data/processed/
COPY llm_cache/ llm_cache/

RUN useradd --create-home app && chown -R app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/healthz')"

CMD ["uvicorn", "src.service:app", "--host", "0.0.0.0", "--port", "8000"]
