# ════════════════════════════════════════════════════════════
# Worker Dockerfile  — Hardened (.NET Multi-Stage + Non-Root)
# Steps applied:
#   ✅ Step 2: Non-root user (appuser)
#   ✅ Step 3: .dockerignore
#   ✅ Step 4: Multi-stage build (SDK build → runtime only)
#   ✅ Step 5: Minimal runtime image (dotnet/runtime, no SDK)
#   ✅ Step 6: Read-only fs compatible, no new privileges
# ════════════════════════════════════════════════════════════

# dotnet doesn't support QEMU for building or running.
# hadolint ignore=DL3029
FROM --platform=${BUILDPLATFORM} mcr.microsoft.com/dotnet/sdk:8.0 AS build

ARG TARGETPLATFORM
ARG TARGETARCH
ARG BUILDPLATFORM
RUN echo "Building on $BUILDPLATFORM for $TARGETPLATFORM ($TARGETARCH)"

WORKDIR /source

# Restore dependencies first (layer caching)
COPY *.csproj .
RUN dotnet restore -a $TARGETARCH

# Build & publish — self-contained=false keeps image smaller
COPY . .
RUN dotnet publish -c Release -o /app -a $TARGETARCH \
    --self-contained false \
    --no-restore \
    /p:TreatWarningsAsErrors=false

# ── Runtime Stage ─────────────────────────────────────────────
# Only the .NET runtime — no SDK, compiler, or build tools remain
FROM mcr.microsoft.com/dotnet/runtime:8.0 AS runtime

WORKDIR /app

# Copy only the published output
COPY --from=build /app .

# ── Step 2: Non-root user ─────────────────────────────────────
RUN adduser --disabled-password --gecos "" --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

# Metadata labels
LABEL org.opencontainers.image.description="Voting App Worker — .NET background processor" \
      org.opencontainers.image.source="https://github.com/patracoder/k8s-kind-voting-app"

ENTRYPOINT ["dotnet", "Worker.dll"]