"""
MCP (Model Context Protocol) client setup and session management.
Handles the Kubernetes MCP server connection lifecycle.

After a successful agent run, closing the stdio session can raise benign EOF-style errors;
we suppress only those on normal teardown so real failures still propagate.
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _is_benign_mcp_stdio_eof(exc: BaseException) -> bool:
    """True when stderr/pipe closed after successful work (not a cluster outage)."""
    if isinstance(exc, EOFError):
        return True
    nested = getattr(exc, "exceptions", None)
    if nested:
        return all(_is_benign_mcp_stdio_eof(e) for e in nested)
    msg = str(exc).lower()
    if "eof" not in msg:
        return False
    return "read" in msg or "stream" in msg or "pipe" in msg or "broken" in msg


def create_mcp_client() -> MultiServerMCPClient:
    """Create a configured MultiServerMCPClient for the Kubernetes MCP server."""
    settings = get_settings()

    client = MultiServerMCPClient(
        {
            "kubernetes": {
                "command": settings.npx_path,
                "args": [
                    "-y",
                    "kubernetes-mcp-server",
                    "--cluster-provider",
                    "kubeconfig",
                    "--kubeconfig",
                    settings.kubeconfig_path,
                ],
                "transport": "stdio",
                "env": os.environ.copy(),
            }
        }
    )

    logger.info(
        "mcp_client_created",
        kubeconfig=settings.kubeconfig_path,
        npx_path=settings.npx_path,
    )
    return client


@asynccontextmanager
async def get_mcp_session(
    client: MultiServerMCPClient,
) -> AsyncGenerator:
    """
    Async context manager that opens a Kubernetes MCP session,
    loads tools, and yields them.

    Usage:
        async with get_mcp_session(client) as tools:
            # use tools with the agent
    """
    cm = client.session("kubernetes")
    session = await cm.__aenter__()
    try:
        logger.info("mcp_session_opened")
        tools = await load_mcp_tools(session)
        logger.info("mcp_tools_loaded", tool_count=len(tools))
        yield tools
    except BaseException:
        await cm.__aexit__(*sys.exc_info())
        raise
    else:
        try:
            await cm.__aexit__(None, None, None)
        except BaseException as e:
            if _is_benign_mcp_stdio_eof(e):
                logger.debug("mcp_session_close_eof_suppressed", detail=str(e))
                return
            raise
