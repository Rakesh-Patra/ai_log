"""
FastAPI route definitions for the Kubernetes AI Agent API.
"""

import time
import uuid
from collections import defaultdict
from typing import AsyncGenerator
import asyncio

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from app.api.auth import require_api_key
from app.api.schemas import (
    ConversationHistory,
    ConversationMessage,
    ErrorResponse,
    GuardrailsReport,
    QueryRequest,
    QueryResponse,
)
from app.core.agent import create_k8s_agent
from app.core.mcp_client import create_mcp_client, get_mcp_session
from app.guardrails.validators import validate_input, validate_output
from app.utils.logging import get_logger
from app.utils.insforge import get_insforge_client

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Agent"],
    dependencies=[Depends(require_api_key)],
)


def _iter_exception_messages(exc: BaseException):
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
    markers = ("eof", "broken pipe", "connection reset", "stream closed")
    for message in _iter_exception_messages(exc):
        if any(marker in message for marker in markers):
            return True
    return False


def _is_quota_error(exc: BaseException) -> bool:
    markers = ("resourceexhausted", "quota exceeded", "429", "model_quota_exceeded")
    for message in _iter_exception_messages(exc):
        if any(marker in message for marker in markers):
            return True
    return False


def _is_kube_tls_error(exc: BaseException) -> bool:
    markers = (
        "kubernetes_tls_verification_failed",
        "certificate verify failed",
        "certificate signed by unknown authority",
        "x509",
        "tls",
    )
    for message in _iter_exception_messages(exc):
        if any(marker in message for marker in markers):
            return True
    return False


# ── Persistent conversation store (InsForge) ────────────────────────
# In-memory store removed in favor of InsForge PostgreSQL database.


# ═══════════════════════════════════════════════════════════════
#  POST /api/v1/query
# ═══════════════════════════════════════════════════════════════
from app.core.rate_limit import limiter

@router.post(
    "/query",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Guardrails validation failed"},
        500: {"model": ErrorResponse, "description": "Agent execution error"},
    },
    summary="Send a query to the Kubernetes agent",
    description="Processes a Kubernetes-related query through guardrails validation, "
    "invokes the AI agent, sanitizes the output, and returns the response.",
)
# Note: Limiter needs Request object
@limiter.limit("10/minute")
async def query_agent(request: Request, query_request: QueryRequest):
    start_time = time.time()
    conversation_id = query_request.conversation_id or str(uuid.uuid4())

    logger.info("query_received", query=query_request.query[:100], conversation_id=conversation_id)

    # ── Step 1: Input Guardrails ──────────────────────────────
    input_result = validate_input(query_request.query)
    if not input_result.is_valid:
        logger.warning("input_rejected", reason=input_result.message)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Input validation failed",
                "message": input_result.message,
                "violations": input_result.violations,
            },
        )

    # ── Step 2: Invoke Agent (direct, no Temporal) ──────────
    try:
        # Build conversation context from InsForge
        insforge = get_insforge_client()
        db_history = await insforge.get_history(conversation_id)

        # Convert DB rows to message tuples for LangGraph
        messages = [
            (msg["role"], msg["content"])
            for msg in db_history
        ]

        # Add new user message
        messages.append(("user", query_request.query))

        # Persist user message to InsForge
        await insforge.save_message(conversation_id, "user", query_request.query)

        # Invoke the agent directly via MCP (with retry for transient errors)
        max_attempts = 3
        agent_response = ""
        tools_used = []
        for attempt in range(1, max_attempts + 1):
            try:
                mcp = create_mcp_client()
                async with get_mcp_session(mcp) as tools_list:
                    agent = create_k8s_agent(tools_list)
                    result = await agent.ainvoke({"messages": messages})

                    # Extract final AI message
                    ai_messages = [
                        m for m in result["messages"]
                        if hasattr(m, "content") and getattr(m, "type", None) == "ai"
                    ]
                    agent_response = ai_messages[-1].content if ai_messages else ""

                    # Collect tool names used
                    tools_used = list({
                        m.name for m in result["messages"]
                        if hasattr(m, "name") and getattr(m, "type", None) == "tool"
                    })
                break  # success
            except Exception as inner_exc:
                if attempt < max_attempts and _is_transient_mcp_error(inner_exc):
                    logger.warning(
                        "query_transient_mcp_error_retrying",
                        attempt=attempt,
                        error=str(inner_exc),
                    )
                    await asyncio.sleep(0.4 * attempt)
                    continue
                raise  # re-raise on final attempt or non-transient error

    except BaseException as e:
        actual_error = e
        if isinstance(e, BaseExceptionGroup):
            if e.exceptions:
                actual_error = e.exceptions[0]

        error_msg = f"{type(actual_error).__name__}: {actual_error}"
        logger.error("agent_execution_failed", error=error_msg)

        if _is_quota_error(actual_error):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Model quota exceeded",
                    "message": "Gemini API quota exceeded. Please retry later or use a key/model with available quota.",
                },
            )

        if _is_kube_tls_error(actual_error):
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "Kubernetes TLS verification failed",
                    "message": (
                        "Unable to connect to the Kubernetes API due to certificate verification. "
                        "Verify kubeconfig server/certificate settings (for Kind in Docker, ensure the API server "
                        "address is reachable from the container and certificate trust settings are valid)."
                    ),
                },
            )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Agent execution failed",
                "message": error_msg,
            },
        )

    # ── Step 3: Output Guardrails ─────────────────────────────
    output_result = validate_output(agent_response)
    sanitized_response = output_result.sanitized_text or agent_response


    # Store assistant response in history (InsForge)
    await insforge.save_message(conversation_id, "assistant", sanitized_response)

    # ── Step 4: Build response ────────────────────────────────
    processing_time = (time.time() - start_time) * 1000

    guardrails_report = GuardrailsReport(
        input_valid=input_result.is_valid,
        input_message=input_result.message,
        input_violations=input_result.violations,
        output_violations=output_result.violations,
        pii_redacted=len(output_result.violations) > 0,
    )

    logger.info(
        "query_completed",
        conversation_id=conversation_id,
        processing_time_ms=round(processing_time, 2),
    )

    return QueryResponse(
        response=sanitized_response,
        conversation_id=conversation_id,
        tools_used=tools_used,
        guardrails_report=guardrails_report,
        processing_time_ms=round(processing_time, 2),
    )


# ═══════════════════════════════════════════════════════════════
#  POST /api/v1/query/stream
# ═══════════════════════════════════════════════════════════════
@router.post(
    "/query/stream",
    summary="Stream agent response via SSE",
    description="Sends a query and streams the agent's response token by token using Server-Sent Events.",
)
@limiter.limit("10/minute")
async def query_agent_stream(request: Request, query_request: QueryRequest):
    """Stream the agent response using Server-Sent Events."""

    # ── Input Guardrails ──────────────────────────────────────
    input_result = validate_input(query_request.query)
    if not input_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Input validation failed",
                "message": input_result.message,
                "violations": input_result.violations,
            },
        )

    async def event_generator() -> AsyncGenerator[dict, None]:
        conversation_id = query_request.conversation_id or str(uuid.uuid4())
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                client = create_mcp_client()
                async with get_mcp_session(client) as tools:
                    agent = create_k8s_agent(tools)
                    messages = [("user", query_request.query)]

                    async for event in agent.astream_events(
                        {"messages": messages}, version="v2"
                    ):
                        kind = event.get("event")
                        if kind == "on_chat_model_stream":
                            chunk = event["data"]["chunk"]
                            if hasattr(chunk, "content") and chunk.content:
                                # Apply output guardrails to each chunk
                                output_result = validate_output(chunk.content)
                                sanitized = output_result.sanitized_text or chunk.content
                                yield {
                                    "event": "token",
                                    "data": sanitized,
                                }

                yield {
                    "event": "done",
                    "data": f'{{"conversation_id": "{conversation_id}"}}',
                }
                return
            except Exception as e:
                if _is_quota_error(e):
                    logger.error("stream_quota_exceeded", error=str(e))
                    yield {
                        "event": "error",
                        "data": "Model quota exceeded. Please retry later or use a key/model with available quota.",
                    }
                    return
                if attempt < max_attempts and _is_transient_mcp_error(e):
                    logger.warning(
                        "stream_transient_mcp_error_retrying",
                        attempt=attempt,
                        max_attempts=max_attempts,
                        error=str(e),
                    )
                    await asyncio.sleep(0.4 * attempt)
                    continue
                logger.error("stream_error", error=str(e))
                yield {
                    "event": "error",
                    "data": str(e),
                }
                return

    return EventSourceResponse(event_generator())


# ═══════════════════════════════════════════════════════════════
#  GET /api/v1/history
# ═══════════════════════════════════════════════════════════════
@router.get(
    "/history/{conversation_id}",
    response_model=ConversationHistory,
    summary="Get conversation history",
    description="Retrieve the conversation history for a given conversation ID.",
)
async def get_history(conversation_id: str):
    insforge = get_insforge_client()
    db_history = await insforge.get_history(conversation_id)
    
    if not db_history:
        # Check if project exists but has no messages yet
        # Or return empty history
        return ConversationHistory(conversation_id=conversation_id, messages=[])
        
    messages = [
        ConversationMessage(role=msg["role"], content=msg["content"])
        for msg in db_history
    ]
    return ConversationHistory(conversation_id=conversation_id, messages=messages)


# ═══════════════════════════════════════════════════════════════
#  DELETE /api/v1/history
# ═══════════════════════════════════════════════════════════════
@router.delete(
    "/history/{conversation_id}",
    summary="Clear conversation history",
    description="Delete the conversation history for a given conversation ID.",
)
async def clear_history(conversation_id: str):
    insforge = get_insforge_client()
    if not insforge.base_url:
        raise HTTPException(
            status_code=503,
            detail="Conversation storage (InsForge) is not configured.",
        )
    url = f"{insforge.base_url}/database/records/conversations"
    params = {"session_id": f"eq.{conversation_id}"}
    
    async with httpx.AsyncClient(timeout=10.0) as client: # Modified httpx.AsyncClient with timeout
        try:
            # Delete all messages for this session
            response = await client.delete(url, params=params, headers=insforge.headers)
            response.raise_for_status()
            logger.info("conversation_cleared", conversation_id=conversation_id)
            return {"message": "Conversation history cleared", "conversation_id": conversation_id}
        except Exception as e:
            logger.error("insforge_clear_error", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to clear history from InsForge")
