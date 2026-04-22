#!/bin/bash
# run-hardened.sh — Step 6: Hardened Runtime (Defense in Depth)
# 
# Use this instead of plain `docker run` for production deployments.
# Each flag adds a layer of runtime security.

IMAGE="${1:-patracoder/k8s-ai-agent:v1.0}"
PORT="${2:-8000}"

echo "🛡️  Starting $IMAGE with hardened runtime flags..."

# Security Features Enabled:
# - Read-only root filesystem
# - Tmpfs mounted for temporary writes only (noexec, nosuid)
# - Dropped ALL Linux capabilities, re-adding only NET_BIND_SERVICE
# - Blocked privilege escalation (no-new-privileges)
# - Unconfined seccomp (custom profile recommended for prod)
# - Process limits (150 pids)
# - Memory limits (512m, no swap)
# - CPU limits (1.0 cores)
# - Explicit non-root user execution (10001:10001)

docker run \
  --rm \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --security-opt no-new-privileges \
  --security-opt seccomp=unconfined \
  --pids-limit 150 \
  --memory 512m \
  --memory-swap 512m \
  --cpus 1.0 \
  --user 10001:10001 \
  -e API_AUTH_KEY=patra-dev-key-12345 \
  --env-file agent/.env \
  --network bridge \
  -p "$PORT:$PORT" \
  "$IMAGE"
