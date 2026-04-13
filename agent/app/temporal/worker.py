# app/temporal/worker.py

import sys
import os
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

from temporalio.worker import Worker
from app.temporal.client import get_temporal_client
from app.temporal.activities import run_agent_activity
from app.temporal.workflows import AgentQAWorkflow
from app.temporal.constants import TASK_QUEUE
from app.utils.logging import setup_logging, get_logger


async def start_worker():
    setup_logging()
    log = get_logger(__name__)
    client = await get_temporal_client()

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[AgentQAWorkflow],
        activities=[run_agent_activity],
    )

    log.info("temporal_worker_started", task_queue=TASK_QUEUE)
    await worker.run()
if __name__ == "__main__":
    import asyncio
    asyncio.run(start_worker())