#!/bin/bash
cd /mnt/c/ai_log/k8s-kind-voting-app/agent
source venv/bin/activate

LOGFILE="/mnt/c/ai_log/k8s-kind-voting-app/agent/uvicorn_debug.log"
RESULTFILE="/mnt/c/ai_log/k8s-kind-voting-app/agent/test_results.txt"

# Use python -u for unbuffered output
python -u -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > "$LOGFILE" 2>&1 &
SERVER_PID=$!

# Wait for Temporal timeout (3s) + uvicorn boot
sleep 12

echo "=== Health Endpoint ===" > "$RESULTFILE"
curl -s http://127.0.0.1:8000/health >> "$RESULTFILE" 2>&1
echo "" >> "$RESULTFILE"

echo "=== Root Endpoint ===" >> "$RESULTFILE"
curl -s http://127.0.0.1:8000/ >> "$RESULTFILE" 2>&1
echo "" >> "$RESULTFILE"

echo "=== Swagger Docs Status ===" >> "$RESULTFILE"
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/docs >> "$RESULTFILE" 2>&1
echo "" >> "$RESULTFILE"

kill $SERVER_PID 2>/dev/null
echo "DONE" >> "$RESULTFILE"
