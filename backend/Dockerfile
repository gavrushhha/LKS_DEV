FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PYTHONPATH=/app
WORKDIR /app

FROM base AS deps
COPY pyproject.toml ./
RUN mkdir app && touch app/__init__.py && pip install --upgrade pip && pip install .

FROM base AS runtime
RUN groupadd --system lks && useradd --system --gid lks --home-dir /app --no-create-home lks
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
USER lks
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-graceful-shutdown", "15"]
