# ════════════════════════════════════════════════════════════
# Result Dockerfile  — Hardened (Multi-Stage + Non-Root)
# Steps applied:
#   ✅ Step 2: Non-root user
#   ✅ Step 3: .dockerignore (at repo root)
#   ✅ Step 4: Multi-stage build (deps + runtime)
#   ✅ Step 5: Slim runtime image (no build tools in prod)
#   ✅ Step 6: Healthcheck + tini PID1
# ════════════════════════════════════════════════════════════

# ── Stage 1: Dependency installer ───────────────────────────
FROM node:18-slim AS deps

WORKDIR /build

# Install only production dependencies
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force

# ── Stage 2: Runtime ─────────────────────────────────────────
FROM node:18-slim AS runtime

# Install only minimal runtime tools
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/app

# ── Step 2: Non-root user ─────────────────────────────────────
RUN groupadd -r app && useradd -r -g app app

# Copy only app source + pre-built deps from builder (no devDependencies)
COPY --from=deps --chown=app:app /build/node_modules /node_modules
COPY --chown=app:app . .

# ── Healthcheck ───────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

USER app

ENV PORT=80
EXPOSE 80

# tini as PID 1 — proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["node", "server.js"]
