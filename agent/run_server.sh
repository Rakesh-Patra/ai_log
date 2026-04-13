#!/bin/bash
cd /mnt/c/ai_log/k8s-kind-voting-app/agent
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 | tee /tmp/server_output.txt
