import httpx
from app.config import get_settings
from app.utils.logging import get_logger
import json

logger = get_logger(__name__)


def _preview(text: str, limit: int = 200) -> str:
    if not text:
        return ""
    text = text.strip().replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 3] + "..."


class InsForgeClient:
    def __init__(self):
        self.settings = get_settings()
        
        # Load from .insforge/project.json
        try:
            import os
            project_json_path = os.path.join(os.getcwd(), ".insforge", "project.json")
            with open(project_json_path, "r") as f:
                project_data = json.load(f)
                self.base_url = f"{project_data['oss_host']}/api"
                self.api_key = project_data["api_key"]
                logger.info("insforge_util_initialized", project_id=project_data["project_id"])
        except Exception as e:
            logger.error("insforge_config_load_failed", error=str(e))
            # Fallback (adjust as needed)
            self.base_url = None
            self.api_key = None

        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    async def save_message(self, session_id: str, role: str, content: str):
        if not self.base_url:
            logger.warning("insforge_not_configured_save_skipped")
            return None
        
        url = f"{self.base_url}/database/records/conversations"
        data = {
            "session_id": session_id,
            "role": role,
            "content": content
        }
        
        # Dual-header approach for maximum compatibility
        headers = {**self.headers, "apikey": self.api_key}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # Single object insert (more compatible than arrays in some configs)
                response = await client.post(url, json=data, headers=headers)
                response.raise_for_status()
                logger.info("insforge_save_success", session_id=session_id)
                return response.json()
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                log = logger.warning if 400 <= status < 500 else logger.error
                log(
                    "insforge_save_error",
                    status_code=status,
                    detail_preview=_preview(e.response.text or ""),
                    session_id=session_id,
                )
                return None
            except Exception as e:
                logger.error("insforge_save_error", error=str(e))
                return None

    async def get_history(self, session_id: str, limit: int = 20):
        if not self.base_url:
            logger.warning("insforge_not_configured_history_empty")
            return []
        # Query parameters for filtering
        url = f"{self.base_url}/database/records/conversations"
        params = {
            "session_id": f"eq.{session_id}",
            "order": "created_at.asc",
            "limit": limit
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, params=params, headers=self.headers)
                # No rows yet / unknown session: many APIs return 404; treat as empty history.
                if response.status_code == 404:
                    return []
                response.raise_for_status()
                data = response.json()
                return data if isinstance(data, list) else []
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 404:
                    return []
                # 401/403: bad or missing API key — still degrade gracefully for the request.
                log = logger.warning if 400 <= status < 500 else logger.error
                log(
                    "insforge_load_error",
                    status_code=status,
                    detail_preview=_preview(e.response.text or ""),
                    session_id=session_id,
                )
                return []
            except httpx.RequestError as e:
                logger.warning(
                    "insforge_load_unreachable",
                    error=str(e),
                    session_id=session_id,
                    hint="Check network and that oss_host in .insforge/project.json is reachable from this container.",
                )
                return []
            except Exception as e:
                logger.error("insforge_load_error", error=str(e), session_id=session_id)
                return []

_client = None

def get_insforge_client():
    global _client
    if _client is None:
        _client = InsForgeClient()
    return _client
