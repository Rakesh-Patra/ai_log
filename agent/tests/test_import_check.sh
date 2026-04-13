#!/bin/bash
cd /mnt/c/ai_log/k8s-kind-voting-app/agent
source venv/bin/activate

# Check if port is in use
echo "=== Checking port 8000 ==="
ss -tlnp 2>/dev/null | grep 8000 || echo "Port 8000 is free"

# Try running on a different port with full error output
echo "=== Starting server on port 8001 ==="
timeout 8 uvicorn app.main:app --host 0.0.0.0 --port 8001 2>&1
echo "Exit code: $?"
