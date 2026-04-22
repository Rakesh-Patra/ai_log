# ════════════════════════════════════════════════════════════
# Agent Dockerfile  — Hardened (Multi-Stage + Non-Root + Read-only)
# Steps applied:
#   ✅ Step 2: Non-root user
#   ✅ Step 3: .dockerignore
#   ✅ Step 4: Multi-stage build (builder + runtime)
#   ✅ Step 5: Minimal slim runtime image
#   ✅ Step 6: Read-only filesystem (HEALTHCHECK + env hints)
# ════════════════════════════════════════════════════════════

# ── Stage 1: Builder ─────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build-time system deps only — NOT carried into runtime
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl (pinned) in the builder stage
ARG KUBECTL_VERSION=v1.29.2
RUN ARCH=$(dpkg --print-architecture) && \
    curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${ARCH}/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl

# Use uv for fast, reproducible dependency install
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Install only runtime system deps (node/npm for npx MCP server + curl for healthcheck)
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Copy kubectl from builder
COPY --from=builder /usr/local/bin/kubectl /usr/local/bin/kubectl

# Copy installed Python packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

# ── Step 2: Non-root user ─────────────────────────────────────
RUN groupadd -r app && \
    useradd -m -r -g app app && \
    mkdir -p /home/app/.kube && \
    chown -R app:app /home/app/.kube

# Copy only application source (not venv, not .env, not tests)
COPY --chown=app:app app/ ./app/
COPY --chown=app:app skills/ ./skills/
COPY --chown=app:app mcp_server.py main.py ./

# Create tmp dir for runtime writes (for read-only fs compatibility)
RUN mkdir -p /tmp/agent && chown app:app /tmp/agent

USER app

# ── Environment ───────────────────────────────────────────────
ENV HOST=0.0.0.0 \
    PORT=8000 \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ── Healthcheck ───────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# tini as PID 1 — proper signal handling, no zombie processes
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
