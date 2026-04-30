import subprocess
import json
import time

def test_mcp():
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    process = subprocess.Popen(
        [r"venv_win\Scripts\python.exe", "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="c:\\ai_log\\k8s-kind-voting-app\\agent"
    )
    
    stdout_data, stderr_data = process.communicate(input=json.dumps(req) + "\n", timeout=10)
    
    print("STDOUT:")
    print(repr(stdout_data))
    print("\nSTDERR:")
    print(stderr_data)

if __name__ == "__main__":
    test_mcp()
