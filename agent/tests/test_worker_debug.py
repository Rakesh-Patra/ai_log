import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker
import sys
import os

# Add the current directory to sys.path to allow importing app
sys.path.append(os.getcwd())

from app.temporal_workflows import AgentQAWorkflow
from app.temporal_agent import run_agent_activity, TASK_QUEUE

async def main():
    logging.basicConfig(level=logging.INFO)
    try:
        client = await Client.connect("127.0.0.1:7233")
        worker = Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[AgentQAWorkflow],
            activities=[run_agent_activity],
        )
        print("Worker initialized successfully")
        # We don't actually need to run it, just initialize it to check validation
    except Exception as e:
        logging.exception("Failed to initialize worker")

if __name__ == "__main__":
    asyncio.run(main())
