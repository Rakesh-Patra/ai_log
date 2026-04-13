#!/bin/bash
curl -s -X POST http://127.0.0.1:8000/api/v1/query -H "Content-Type: application/json" -d '{"query": "List all pods in the default namespace"}' > final_result_ok.json
