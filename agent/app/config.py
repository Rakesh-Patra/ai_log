"""
Application configuration using pydantic-settings.
Loads settings from environment variables and .env file.
"""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── API Keys ──────────────────────────────────────────────
    google_api_key: str

    # ── Model Settings ────────────────────────────────────────
    model_name: str = "gemini-2.5-flash-lite"
    model_temperature: float = 0.0

    # ── Kubernetes / MCP ──────────────────────────────────────
    # KUBECONFIG (kubectl standard) and KUBECONFIG_PATH both accepted; prefer
    # explicit paths in Docker (e.g. /app/kubeconfig_agent).
    kubeconfig_path: str = Field(
        default="/home/rakesh_patra/.kube/config",
        validation_alias=AliasChoices("KUBECONFIG", "KUBECONFIG_PATH"),
    )
    npx_path: str = "/usr/bin/npx"

    # ── Server Settings ───────────────────────────────────────
    app_name: str = "Kubernetes AI Agent"
    app_version: str = "1.0.0"
    app_env: str = "dev"  # options: dev, staging, prod
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000
    # ── Temporal Settings ─────────────────────────────────────
    temporal_host: str = "127.0.0.1"
    temporal_port: int = 7233
    log_level: str = "INFO"

    # ── Production Safety ────────────────────────────────────
    protected_namespaces: list[str] = ["kube-system",  "kube-public", "kube-node-lease"]
    allow_destructive_actions: bool = False

    # ── LangSmith / Tracing ──────────────────────────────────
    langchain_tracing_v2: bool = True
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: str | None = None
    langchain_project: str = "k8s-ai-agent"

    # ── Guardrails Settings ───────────────────────────────────
    guardrails_enabled: bool = True
    allowed_topics: list[str] = [
        "kubernetes",
        "k8s",
        "pods",
        "deployments",
        "services",
        "namespaces",
        "nodes",
        "clusters",
        "containers",
        "docker",
        "helm",
        "ingress",
        "configmaps",
        "secrets",
        "volumes",
        "devops",
        "monitoring",
        "logging",
    ]


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
