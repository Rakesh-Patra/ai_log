import urllib.request
import json
import sys

print("Testing the /api/v1/query endpoint...")
print("This routes the HTTP request -> Temporal Workflow -> Agent Activity -> Gemini API")
try:
    url = "http://127.0.0.1:8000/api/v1/query"
    data = json.dumps({"query": "List all pods in the default namespace"}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))
        print("\n>>> SUCCESS! Received response from the Agent:")
        print(json.dumps(result, indent=2))
        sys.exit(0)
            
except Exception as e:
    print(f"\n>>> FAILED to query endpoint: {e}")
    sys.exit(1)
