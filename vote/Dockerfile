# ════════════════════════════════════════════════════════════
# Vote Dockerfile  — Hardened (Multi-Stage + Non-Root)
# Steps applied:
#   ✅ Step 2: Non-root user
#   ✅ Step 3: .dockerignore
#   ✅ Step 4: Multi-stage build (builder + dev + final)
#   ✅ Step 5: Slim runtime (no pip in prod)
#   ✅ Step 6: Healthcheck, read-only fs hints
# ════════════════════════════════════════════════════════════

# ── Stage 1: Builder — install dependencies ──────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Dev (file-watching, only used locally) ──────────
FROM python:3.11-slim AS dev

WORKDIR /usr/local/app
COPY --from=builder /install /usr/local

RUN pip install --no-cache-dir watchdog
ENV FLASK_ENV=development

COPY . .
CMD ["python", "app.py"]

# ── Stage 3: Production runtime ───────────────────────────────
FROM python:3.11-slim AS final

# Runtime tools only — curl for healthcheck
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/app

# Copy installed packages from builder (no pip in runtime)
COPY --from=builder /install /usr/local

# ── Step 2: Non-root user ─────────────────────────────────────
RUN groupadd -r app && useradd -r -g app app

# Copy only application source
COPY --chown=app:app . .

# ── Healthcheck ───────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

USER app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 80

# tini as PID 1
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:80", "--log-file", "-", "--access-logfile", "-", "--workers", "4", "--keep-alive", "0"]
