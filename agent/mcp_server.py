import os
import asyncio
import sys
import warnings

# Suppress warnings that might pollute stdio/stderr and break MCP protocol
warnings.filterwarnings("ignore")

# Initialize logging FIRST before any other app imports
from app.utils.logging import setup_logging, get_logger
setup_logging()
logger = get_logger("mcp_server")

from dotenv import load_dotenv
from fastmcp import FastMCP

# Add the project root to sys.path so we can import 'app'
# Since this file is in 'agent/', we add the 'agent/' directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.mcp_client import create_mcp_client, get_mcp_session
from app.core.agent import create_k8s_agent

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP(
    "K8s-Assistant",
)

@mcp.tool()
async def ask_k8s_assistant(query: str) -> str:
    """
    Ask the Kubernetes AI assistant to inspect or manage the cluster.
    
    Args:
        query: The natural language query or command for Kubernetes (e.g., 'list all pods', 'check node health').
    """
    logger.info("mcp_query_received", query=query)
    
    try:
        # 1. Create the underlying Kubernetes MCP client
        client = create_mcp_client()
        
        # 2. Start a session and load tools
        async with get_mcp_session(client) as tools:
            # 3. Create the LangGraph agent
            agent = create_k8s_agent(tools)
            
            # 4. Invoke the agent
            inputs = {"messages": [("user", query)]}
            
            # Use wait_for to prevent hanging
            result = await asyncio.wait_for(
                agent.ainvoke(inputs),
                timeout=120 # 2 minute timeout for complex operations
            )
            
            # 5. Extract the final response
            response = result["messages"][-1].content
            logger.info("mcp_query_completed")
            return response
            
    except asyncio.TimeoutError:
        logger.error("mcp_query_timeout")
        return "ERROR: The agent took too long to respond. Please try a simpler query."
    except Exception as e:
        logger.error("mcp_query_failed", error=str(e))
        return f"ERROR: Failed to process query: {type(e).__name__}: {e}"

if __name__ == "__main__":
    # When run directly, start the MCP server
    mcp.run()
