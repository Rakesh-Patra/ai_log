#!/bin/bash
cd /mnt/c/ai_log/k8s-kind-voting-app/agent
source venv/bin/activate
python test_temporal_import.py
