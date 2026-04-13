"""Quick smoke test to verify temporal_agent module imports cleanly."""
try:
    from app.temporal_agent import init_temporal, close_temporal, AgentQAWorkflow, TASK_QUEUE
    print("OK: temporal_agent imports successfully")
    print(f"  TASK_QUEUE = {TASK_QUEUE}")
    print(f"  AgentQAWorkflow = {AgentQAWorkflow}")
except Exception as e:
    print(f"FAIL: {e}")

try:
    from app.main import app
    print("OK: app.main imports successfully")
except Exception as e:
    print(f"FAIL: app.main import error: {e}")
