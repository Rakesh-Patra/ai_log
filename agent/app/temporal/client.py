# app/temporal/client.py

import asyncio

from temporalio.client import Client
from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
temporal_client: Client = None

_MAX_CONNECT_ATTEMPTS = 15


async def get_temporal_client() -> Client:
    """
    Get or create a singleton Temporal client instance.
    Retries with backoff so the worker survives brief DNS / server startup races after compose starts.
    """
    global temporal_client
    if temporal_client is not None:
        return temporal_client

    settings = get_settings()
    target_host = f"{settings.temporal_host}:{settings.temporal_port}"
    last_err: Exception | None = None

    for attempt in range(1, _MAX_CONNECT_ATTEMPTS + 1):
        try:
            logger.info("connecting_to_temporal", target=target_host, attempt=attempt)
            temporal_client = await Client.connect(target_host)
            logger.info("temporal_connected", attempt=attempt)
            return temporal_client
        except Exception as e:
            last_err = e
            temporal_client = None
            if attempt >= _MAX_CONNECT_ATTEMPTS:
                break
            wait_s = min(2 ** min(attempt - 1, 5), 10)
            logger.warning(
                "temporal_connection_retry",
                target=target_host,
                attempt=attempt,
                wait_s=wait_s,
                error=str(e),
            )
            await asyncio.sleep(wait_s)

    logger.error("temporal_connection_failed", target=target_host, error=str(last_err))
    assert last_err is not None
    raise last_err