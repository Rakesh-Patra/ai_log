"""
API Key authentication middleware for the Kubernetes AI Agent API.
Uses a simple Bearer token from environment variable API_AUTH_KEY.
"""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str = Security(_api_key_header)) -> str:
    """
    FastAPI dependency that validates the X-API-Key header.
    Skips validation in dev mode if API_AUTH_KEY is not set.
    """
    settings = get_settings()
    expected_key = settings.api_auth_key

    # In dev mode, if no key is configured, skip auth
    if not expected_key:
        if settings.app_env == "dev":
            return "dev-bypass"
        raise HTTPException(
            status_code=500,
            detail="API_AUTH_KEY is not configured on the server.",
        )

    if not api_key or api_key != expected_key:
        # Do not log any part of secrets provided by clients.
        logger.warning("auth_failed", provided_key_present=bool(api_key))
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Provide X-API-Key header.",
        )

    return api_key
