import asyncio
import os
import sys

# Force unbuffered output so prints show immediately (even in WSL pipes)
os.environ["PYTHONUNBUFFERED"] = "1"

from dotenv import load_dotenv

load_dotenv()

print("[init] Loading libraries...", flush=True)
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
print("[init] Libraries loaded.", flush=True)


# ── Read config from .env ─────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite")
KUBECONFIG = os.getenv("KUBECONFIG_PATH", "/home/rakesh_patra/.kube/config")
NPX_PATH = os.getenv("NPX_PATH", "npx")
AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT", "120"))  # seconds


async def main():
    # ── Pre-flight checks ─────────────────────────────────────
    if not GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY is not set in .env", flush=True)
        sys.exit(1)

    print(f"[config] Model      : {MODEL_NAME}", flush=True)
    print(f"[config] Kubeconfig : {KUBECONFIG}", flush=True)
    print(f"[config] NPX path   : {NPX_PATH}", flush=True)
    print(f"[config] Timeout    : {AGENT_TIMEOUT}s", flush=True)
    print(flush=True)

    # ── Create MCP client ─────────────────────────────────────
    client = MultiServerMCPClient(
        {
            "kubernetes": {
                "command": NPX_PATH,
                "args": [
                    "-y",
                    "kubernetes-mcp-server",
                    "--cluster-provider",
                    "kubeconfig",
                    "--kubeconfig",
                    KUBECONFIG,
                ],
                "transport": "stdio",
                "env": os.environ.copy(),
            }
        }
    )

    print("[step 1/4] Connecting to Kubernetes MCP server...", flush=True)
    try:
        async with client.session("kubernetes") as session:
            print("[step 2/4] Session established. Loading tools...", flush=True)

            tools = await load_mcp_tools(session)
            print(f"[step 2/4] Loaded {len(tools)} tools: {[t.name for t in tools]}", flush=True)

            # ── Build model & agent ───────────────────────────
            print(f"[step 3/4] Initializing model ({MODEL_NAME})...", flush=True)
            model = ChatGoogleGenerativeAI(
                model=MODEL_NAME,
                temperature=0,
                google_api_key=GOOGLE_API_KEY,
            )

            agent = create_react_agent(
                model=model,
                tools=tools,
                prompt=(
                    "You are a Kubernetes assistant. Use the available tools to "
                    "inspect and manage the Kubernetes cluster. Always explain what "
                    "you are doing and summarize the results clearly."
                ),
            )

            # ── Run the agent ─────────────────────────────────
            print("[step 4/4] Running agent query...\n", flush=True)
            print("=" * 60, flush=True)

            inputs = {
                "messages": [
                    ("user", "List all pods across all namespaces and tell me if any are not running.")
                ]
            }

            try:
                result = await asyncio.wait_for(
                    agent.ainvoke(inputs),
                    timeout=AGENT_TIMEOUT,
                )
                print("\n--- Agent Response ---", flush=True)
                print(result["messages"][-1].content, flush=True)
            except asyncio.TimeoutError:
                print(f"\nERROR: Agent did not respond within {AGENT_TIMEOUT}s. "
                      "Try increasing AGENT_TIMEOUT in .env or check your network/API key.",
                      flush=True)
            except Exception as e:
                print(f"\nERROR during agent execution: {type(e).__name__}: {e}", flush=True)
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"\nERROR: Failed to connect to MCP server: {type(e).__name__}: {e}", flush=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())