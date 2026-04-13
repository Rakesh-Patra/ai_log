"""
Guardrails AI input and output validators.
Uses the Guardrails AI framework to validate and sanitize user queries and agent responses.
"""

import re
from typing import Any, Dict, Optional

from guardrails import Guard, Validator, register_validator
from guardrails.validator_base import (
    FailResult,
    PassResult,
    ValidationResult as GuardValidationResult,
)

# NOTE: These hub validators require installation: 
# guardrails-hub-install detect_prompt_injection detect_pii toxic_language
try:
    from guardrails.hub import DetectPII, ToxicLanguage, DetectPromptInjection
except ImportError:
    # Fallback to local mocks or placeholders if not installed
    DetectPII = None
    ToxicLanguage = None
    DetectPromptInjection = None

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════
#  Legacy Patterns (Kept for custom validators)
# ═══════════════════════════════════════════════════════════════
DESTRUCTIVE_PATTERNS = [
    re.compile(r"\b(delete|remove|terminate|uninstall|purge|destroy)\b", re.IGNORECASE),
]

# ═══════════════════════════════════════════════════════════════
#  Custom Guardrails Validators
# ═══════════════════════════════════════════════════════════════

@register_validator(name="k8s/destructive_action", data_type="string")
class K8sDestructiveAction(Validator):
    """Guardrails validator to block destructive Kubernetes actions."""

    def validate(self, value: Any, metadata: Dict) -> GuardValidationResult:
        settings = get_settings()
        if settings.allow_destructive_actions:
            return PassResult()

        query_lower = str(value).lower()
        
        for pattern in DESTRUCTIVE_PATTERNS:
            if pattern.search(query_lower):
                k8s_resources = ["pod", "service", "deployment", "namespace", "pvc", "pv", "ingress", "configmap", "secret"]
                if any(res in query_lower for res in k8s_resources) or any(ns in query_lower for ns in settings.protected_namespaces):
                    return FailResult(
                        error_message="Destructive actions (like delete or uninstall) are disabled for production safety.",
                        fix_value=None,
                    )
        return PassResult()


@register_validator(name="k8s/topic_relevance", data_type="string")
class K8sTopicRelevance(Validator):
    """Guardrails validator to ensure query is K8s/DevOps related."""

    def validate(self, value: Any, metadata: Dict) -> GuardValidationResult:
        settings = get_settings()
        query_lower = str(value).lower()

        # Check allowed topics from config
        if any(topic in query_lower for topic in settings.allowed_topics):
            return PassResult()

        # Kubernetes-specific indicators
        k8s_indicators = [
            "kubectl", "pod", "deploy", "scale", "rollout", "port-forward",
            "apply", "delete", "describe", "logs", "exec", "namespace",
            "configmap", "persistent", "pvc", "pv", "daemonset", "statefulset",
            "replicaset", "cronjob", "job", "hpa", "vpa", "network policy",
            "service account", "role", "clusterrole", "kustomize", "kind",
            "minikube", "cluster", "node", "workload", "manifest", "yaml",
            "resource", "replica", "container", "image", "registry",
            "endpoint", "label", "annotation", "taint", "toleration",
            "affinity", "probe", "liveness", "readiness", "startup",
        ]

        if any(indicator in query_lower for indicator in k8s_indicators):
            return PassResult()

        return FailResult(
            error_message="Your query does not appear to be related to Kubernetes or DevOps.",
            fix_value=None,
        )


# ═══════════════════════════════════════════════════════════════
#  Compatibility Layer (Matches existing ValidationResult in routes.py)
# ═══════════════════════════════════════════════════════════════

class ValidationResult:
    """Legacy compatibility result of a guardrails validation check."""
    def __init__(
        self,
        is_valid: bool,
        message: str = "",
        violations: list[str] | None = None,
        sanitized_text: str | None = None,
    ):
        self.is_valid = is_valid
        self.message = message
        self.violations = violations or []
        self.sanitized_text = sanitized_text

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "message": self.message,
            "violations": self.violations,
            "sanitized_text": self.sanitized_text,
        }


# ═══════════════════════════════════════════════════════════════
#  Guards Initialization
# ═══════════════════════════════════════════════════════════════

def get_input_guard() -> Guard:
    """Initialize the input validation guard based on environment."""
    settings = get_settings()
    guard = Guard()
    
    # K8s Specific Guards (Dynamic based on Environment)
    if settings.app_env == "prod":
        # Production: Strict blocking for destructive actions and off-topic
        guard.use(K8sDestructiveAction(on_fail="exception"))
        guard.use(K8sTopicRelevance(on_fail="exception"))
    elif settings.app_env == "staging":
        # Staging: Block destructive, but maybe just log topic relevance?
        guard.use(K8sDestructiveAction(on_fail="exception"))
        guard.use(K8sTopicRelevance(on_fail="nothing"))
    else: # dev / local
        # Development: Allow everything for testing, or just use minimal guards
        if not settings.allow_destructive_actions:
            guard.use(K8sDestructiveAction(on_fail="exception"))
        # Topic relevance is often annoying in dev, so we skip it
    
    # General AI Safety Guards
    if DetectPromptInjection:
        # Always run prompt injection in prod/staging
        if settings.app_env in ["prod", "staging"]:
            guard.use(DetectPromptInjection(on_fail="exception"))
            
    if ToxicLanguage:
        if settings.app_env == "prod":
            guard.use(ToxicLanguage(on_fail="exception"))
        
    return guard


def get_output_guard() -> Guard:
    """Initialize the output validation guard (Redaction)."""
    settings = get_settings()
    guard = Guard()
    
    if DetectPII:
        # Always redact PII in production and staging
        if settings.app_env in ["prod", "staging"]:
            guard.use(DetectPII(entities=["EMAIL_ADDRESS", "IP_ADDRESS", "PHONE_NUMBER"], on_fail="fix"))
        
    return guard


# ═══════════════════════════════════════════════════════════════
#  Public Interface
# ═══════════════════════════════════════════════════════════════

def validate_input(query: str) -> ValidationResult:
    """Run Guardrails AI on user input."""
    settings = get_settings()
    if not settings.guardrails_enabled:
        return ValidationResult(is_valid=True, message="Guardrails disabled.")

    try:
        guard = get_input_guard()
        guard.validate(query)
        return ValidationResult(is_valid=True, message="Input validation passed.")
    except Exception as e:
        logger.warning("input_validation_failed", error=str(e))
        return ValidationResult(
            is_valid=False,
            message=str(e),
            violations=[type(e).__name__]
        )


def validate_output(response: str) -> ValidationResult:
    """Run Guardrails AI on agent response for PII redaction."""
    settings = get_settings()
    if not settings.guardrails_enabled:
        return ValidationResult(is_valid=True, message="Guardrails disabled.", sanitized_text=response)

    try:
        guard = get_output_guard()
        # This will return the sanitized text if 'fix' is used on failure
        res = guard.validate(response)
        
        # Guardrails 0.5+ returns a validation response object
        sanitized = res.validated_output if hasattr(res, 'validated_output') else response
        
        return ValidationResult(
            is_valid=True,
            message="Output validation completed.",
            violations=[],
            sanitized_text=sanitized
        )
    except Exception as e:
        logger.error("output_validation_error", error=str(e))
        return ValidationResult(
            is_valid=True, # We usually don't block entire output unless extreme
            message="Error in output validation, falling back to raw response.",
            sanitized_text=response
        )
