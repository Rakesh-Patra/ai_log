"""
Application configuration using pydantic-settings.
Loads settings from environment variables and .env file.
"""

import os
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── API Keys ──────────────────────────────────────────────
    google_api_key: str

    # ── Model Settings ────────────────────────────────────────
    model_name: str = "gemini-2.5-flash-lite"
    model_temperature: float = 0.0

    # ── Kubernetes / MCP ──────────────────────────────────────
    # Env: KUBECONFIG_PATH (pydantic-settings) or KUBECONFIG (kubectl standard).
    kubeconfig_path: str = "/home/rakesh_patra/.kube/config"
    npx_path: str = "npx"

    @model_validator(mode="before")
    @classmethod
    def _kubeconfig_from_env(cls, data: object) -> object:
        """Resolve kubeconfig from KUBECONFIG / KUBECONFIG_PATH; drop stray env keys."""
        if not isinstance(data, dict):
            return data
        out = dict(data)
        out.pop("KUBECONFIG_PATH", None)
        out.pop("KUBECONFIG", None)
        kc = os.environ.get("KUBECONFIG") or os.environ.get("KUBECONFIG_PATH")
        if kc:
            out["kubeconfig_path"] = kc
        return out

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

    # ── API Authentication ───────────────────────────────────
    api_auth_key: str | None = None  # Set API_AUTH_KEY in .env for production

    # ── CORS ─────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000"  # Comma-separated origins

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
