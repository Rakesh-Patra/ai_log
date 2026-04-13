"""Temporal activities for running the Kubernetes agent."""

import asyncio
from temporalio import activity
from temporalio.exceptions import ApplicationError

from app.core.agent import create_k8s_agent
from app.core.mcp_client import create_mcp_client, get_mcp_session
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _iter_exception_messages(exc: BaseException):
    """Yield message strings from the exception and nested causes/groups."""
    stack = [exc]
    seen = set()
    while stack:
        current = stack.pop()
        key = id(current)
        if key in seen:
            continue
        seen.add(key)
        yield str(current).lower()
        cause = getattr(current, "__cause__", None)
        context = getattr(current, "__context__", None)
        if cause is not None:
            stack.append(cause)
        if context is not None:
            stack.append(context)
        nested = getattr(current, "exceptions", None)
        if nested:
            stack.extend(nested)


def _is_transient_mcp_error(exc: BaseException) -> bool:
    """Detect transient MCP transport disconnects such as EOF."""
    markers = ("eof", "broken pipe", "connection reset", "stream closed")
    for message in _iter_exception_messages(exc):
        if any(marker in message for marker in markers):
            return True
    return False


def _is_quota_error(exc: BaseException) -> bool:
    """Detect upstream model quota exhaustion errors."""
    markers = ("resourceexhausted", "quota exceeded", "429", "rate limit")
    for message in _iter_exception_messages(exc):
        if any(marker in message for marker in markers):
            return True
    return False


def _is_kube_tls_error_text(text: str) -> bool:
    """Detect Kubernetes TLS/x509 verification failures from model/tool output."""
    lowered = text.lower()
    markers = (
        "tls",
        "certificate",
        "x509",
        "certificate signed by unknown authority",
        "certificate verify failed",
    )
    return any(marker in lowered for marker in markers)


async def _invoke_agent_once(messages: list) -> dict:
    """Run one agent invocation with a fresh MCP client/session."""
    client = create_mcp_client()
    async with get_mcp_session(client) as tools:
        agent = create_k8s_agent(tools)
        return await agent.ainvoke({"messages": messages})

@activity.defn(name="run_agent_activity")
async def run_agent_activity(messages: list) -> dict:
    max_attempts = 3
    result = None
    for attempt in range(1, max_attempts + 1):
        try:
            result = await _invoke_agent_once(messages)
            break
        except Exception as exc:
            # MCP stdio can occasionally disconnect with EOF; retry with a
            # brand new client/session to recover transparently.
            if _is_transient_mcp_error(exc) and attempt < max_attempts:
                logger.warning(
                    "mcp_transient_error_retrying",
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=str(exc),
                )
                await asyncio.sleep(0.4 * attempt)
                continue
            if _is_quota_error(exc):
                raise ApplicationError(
                    "MODEL_QUOTA_EXCEEDED: Gemini API quota exceeded",
                    non_retryable=True,
                ) from exc
            raise

    raw_content = result["messages"][-1].content

    if isinstance(raw_content, list):
        agent_response = "\n".join(
            block.get("text", str(block)) if isinstance(block, dict) else str(block)
            for block in raw_content
        )
    else:
        agent_response = str(raw_content)

    # Surface cluster connectivity/config failures as hard API errors instead of
    # successful responses containing model-generated fallback text.
    if _is_kube_tls_error_text(agent_response):
        raise ApplicationError(
            "KUBERNETES_TLS_VERIFICATION_FAILED: Kubernetes API TLS verification failed. "
            "Check kubeconfig server address and certificate settings.",
            non_retryable=True,
        )

    tools_used = [
        msg.name for msg in result["messages"]
        if hasattr(msg, "name") and hasattr(msg, "tool_call_id")
    ]

    return {
        "agent_response": agent_response,
        "tools_used": tools_used
    }