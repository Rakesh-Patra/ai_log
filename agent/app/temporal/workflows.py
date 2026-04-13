from temporalio import workflow
from datetime import timedelta
from temporalio.common import RetryPolicy

@workflow.defn
class AgentQAWorkflow:
    @workflow.run
    async def run(self, messages: list) -> dict:
        return await workflow.execute_activity(
            "run_agent_activity",
            messages,
            start_to_close_timeout=timedelta(seconds=180),
            retry_policy=RetryPolicy(maximum_attempts=1),
        )
