import asyncio
import os
import sys
from dotenv import load_dotenv

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_server import ask_k8s_assistant

async def test():
    print("Testing MCP tool 'ask_k8s_assistant'...")
    query = "What is the status of the cluster?"
    print(f"Query: {query}")
    
    try:
        response = await ask_k8s_assistant(query)
        print("\n--- Response ---")
        print(response)
        print("----------------")
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test())
