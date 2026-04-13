"""
Pydantic request and response schemas for the API.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Request Schemas ───────────────────────────────────────────
class QueryRequest(BaseModel):
    """User query sent to the Kubernetes agent."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The Kubernetes-related question or command.",
        examples=["List all pods in the default namespace"],
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation ID for multi-turn context.",
    )


# ── Response Schemas ──────────────────────────────────────────
class GuardrailsReport(BaseModel):
    """Report of guardrails validation results."""

    input_valid: bool = True
    input_message: str = ""
    input_violations: list[str] = []
    output_violations: list[str] = []
    pii_redacted: bool = False


class QueryResponse(BaseModel):
    """Response returned after processing a user query."""

    response: str = Field(..., description="The agent's response text.")
    conversation_id: str = Field(..., description="Conversation tracking ID.")
    tools_used: list[str] = Field(
        default_factory=list,
        description="Names of tools the agent called (e.g. 'shell', MCP tool names).",
    )
    guardrails_report: GuardrailsReport = Field(
        default_factory=GuardrailsReport,
        description="Guardrails validation report.",
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_ms: float = Field(
        default=0.0, description="Time taken to process the query in milliseconds."
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mcp_connected: bool = False


class ErrorResponse(BaseModel):
    """Standardized error response."""

    error: str
    detail: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Conversation History ─────────────────────────────────────
class ConversationMessage(BaseModel):
    """A single message in the conversation history."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationHistory(BaseModel):
    """Full conversation history for a session."""

    conversation_id: str
    messages: list[ConversationMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
