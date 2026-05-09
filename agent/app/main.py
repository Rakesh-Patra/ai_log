"""
WHY THIS EXISTS:
This FastAPI entry point now includes a production-grade webhook receiver 
for Alertmanager. This bridges the gap between 'Detection' (Prometheus) 
and 'Action' (AI Agent). In a high-scale environment, manual intervention 
for every OOMKill or Idle Resource is impossible. This automation 
ensures immediate triage.
"""

import asyncio
import warnings
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

# Suppress harmless guardrails event loop warning
warnings.filterwarnings("ignore", message="Could not obtain an event loop.*", category=UserWarning)

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

from app.api.routes import router as api_router
from app.api.schemas import HealthResponse
from app.config import get_settings
from app.temporal.client import get_temporal_client
from app.core.rate_limit import limiter
from app.utils.logging import setup_logging, get_logger
from app.bot import sentinel_app
from langchain_core.messages import HumanMessage

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = get_logger(__name__)
    settings = get_settings()

    logger.info(
        "app_starting",
        app_name=settings.app_name,
        version=settings.app_version,
    )

    # 🟢 Connect Temporal client and start Worker
    async def run_worker():
        from app.temporal.worker import start_worker
        try:
            await start_worker()
        except Exception as e:
            logger.error("temporal_worker_failed", error=str(e))

    asyncio.create_task(run_worker())
    yield
    logger.info("app_shutting_down")

# ── Create the FastAPI app ────────────────────────────────────
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Sentinel-Ops: Autonomous K8s SRE & FinOps Agent.",
    version=settings.app_version,
    lifespan=lifespan,
    root_path="/agent",
    openapi_url="/openapi.json",
    servers=[{"url": "/agent"}]
)

# ── Rate Limiting ─────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS Middleware ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Alertmanager Webhook ─────────────────────────────────────
@app.post("/webhook/alertmanager", tags=["Automations"])
async def alertmanager_webhook(data: Dict[str, Any]):
    """
    WHY THIS EXISTS:
    Receives alerts from Alertmanager and triggers the Sentinel-Ops
    agent to investigate and remediate issues autonomously.
    """
    logger = get_logger(__name__)
    alerts = data.get('alerts', [])
    
    results = []
    for alert in alerts:
        alert_name = alert.get('labels', {}).get('alertname')
        pod = alert.get('labels', {}).get('pod', 'unknown')
        namespace = alert.get('labels', {}).get('namespace', 'default')
        
        logger.info("webhook_received_alert", alert_name=alert_name, pod=pod, namespace=namespace)
        
        # Trigger the Sentinel-Ops LangGraph agent
        input_message = HumanMessage(content=f"ALERT TRIGGERED: {alert_name} on pod {pod} in namespace {namespace}. Please investigate and act.")
        
        # Execute the agent workflow
        final_state = sentinel_app.invoke({"messages": [input_message]})
        
        # Get the last message (the agent's report)
        agent_report = final_state["messages"][-1].content
        results.append({
            "alert": alert_name,
            "status": "triaged",
            "agent_report": agent_report
        })
        
    return {"status": "success", "triaged_alerts": results}

# ── Mount API routes & Health ────────────────────────────────
app.include_router(api_router)

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        mcp_connected=True,
    )

@app.get("/", tags=["System"])
async def root():
    return {
        "app": settings.app_name,
        "webhook_url": "/webhook/alertmanager",
        "health": "/health",
    }
