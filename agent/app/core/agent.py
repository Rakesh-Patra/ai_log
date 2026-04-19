"""
LangGraph ReAct agent factory.
Creates the Kubernetes assistant agent with the SAME model as the original.
Loads the kubernetes skill from skills/kubernetes.md for CLI guidance.
"""

import asyncio
from pathlib import Path
import shlex

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# ── Skill Loading ─────────────────────────────────────────────
_SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"

def _load_skills() -> str:
    """Load all relevant skill files from the skills directory."""
    skill_contents = []
    
    # List of skills to load
    skill_files = ["kubernetes.md", "insforge.md"]
    
    for filename in skill_files:
        path = _SKILLS_DIR / filename
        try:
            content = path.read_text(encoding="utf-8")
            skill_contents.append(content)
            logger.info("skill_loaded", file=filename)
        except FileNotFoundError:
            logger.warning("skill_not_found", file=filename)
            
    return "\n\n---\n\n".join(skill_contents)


# ── Shell Tool ────────────────────────────────────────────────
ALLOWED_COMMANDS = {
    # Keep this list intentionally small. Anything here is executable by the agent.
    "kubectl",
    "helm",
    "kind",
}

@tool
async def shell(command: str, is_approved: bool = False) -> str:
    """Run a shell command on the host. Use for kubectl, helm, and other CLI operations.

    Args:
        command: The shell command to execute, e.g. 'kubectl get pods -A'.
        is_approved: Set to True ONLY if the user has explicitly approved this specific command.
    """
    command = (command or "").strip()
    if not command:
        return "ERROR: Empty command"

    # Human-in-the-loop: Block destructive commands unless explicitly approved
    destructive_verbs = {"delete", "apply", "patch", "edit", "scale", "create", "exec", "replace", "rollout"}
    command_parts = set(command.lower().split())
    is_destructive = any(verb in command_parts for verb in destructive_verbs)
    
    if is_destructive and not is_approved:
        return (
            f"ACTION BLOCKED: The command '{command}' is destructive. "
            f"You MUST reply to the user, explain exactly what this command will do, "
            f"and ask for their explicit approval before you run it again with is_approved=True."
        )

    # Security: block shell metacharacters to avoid injection.
    # (Even with an allowlist, `kubectl ...; <anything>` would run if we used a shell.)
    forbidden = (";", "&&", "||", "|", ">", "<", "$(", "`", "\n", "\r")
    if any(tok in command for tok in forbidden):
        return "ERROR: Command contains forbidden shell operators"

    # Parse into argv safely (no shell).
    try:
        argv = shlex.split(command, posix=True)
    except ValueError:
        return "ERROR: Failed to parse command"

    if not argv:
        return "ERROR: Empty command"

    base_cmd = argv[0].rsplit("/", 1)[-1]
    if base_cmd not in ALLOWED_COMMANDS:
        return (
            f"ERROR: Command '{base_cmd}' is not allowed. "
            f"Permitted commands: {', '.join(sorted(ALLOWED_COMMANDS))}"
        )

    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        out = stdout.decode().strip()
        err = stderr.decode().strip()
        if proc.returncode != 0:
            return f"ERROR (exit {proc.returncode}):\n{err}\n{out}".strip()
        return out or "(no output)"
    except asyncio.TimeoutError:
        return "ERROR: Command timed out after 30s"


# ── System Prompt ─────────────────────────────────────────────
_BASE_PROMPT = (
    "You are a Kubernetes assistant. Use the available tools to "
    "inspect and manage the Kubernetes cluster. Always explain what "
    "you are doing and summarize the results clearly.\n\n"
    "Guidelines:\n"
    "- Always verify the cluster context before making changes\n"
    "- Provide clear, structured output with resource names and statuses\n"
    "- For destructive commands (delete, patch, etc), the shell tool will block you and request user approval.\n"
    "- When blocked, explain the command to the user and ask them to approve it. ONLY proceed with `is_approved=True` once they say yes.\n"
    "- If a tool call fails, explain the error and suggest alternatives\n"
    "- Format output using markdown tables when listing resources\n"
    "- CRITICAL: To run `kubectl` or `helm` commands, you MUST call the tool named `shell` and pass your command as the argument."
)

_all_skills = _load_skills()
SYSTEM_PROMPT = f"{_BASE_PROMPT}\n\n{_all_skills}" if _all_skills else _BASE_PROMPT


def get_model() -> ChatGoogleGenerativeAI:
    """
    Create the LLM instance.
    Model is NOT changed – uses the same gemini-3-flash-preview.
    """
    settings = get_settings()

    model = ChatGoogleGenerativeAI(
        model=settings.model_name,
        temperature=settings.model_temperature,
        google_api_key=settings.google_api_key,
        max_retries=1,
    )

    logger.info(
        "model_initialized",
        model=settings.model_name,
        temperature=settings.model_temperature,
    )
    return model


def create_k8s_agent(tools: list):
    """
    Create a LangGraph ReAct agent for Kubernetes operations.

    Args:
        tools: List of MCP tools loaded from the Kubernetes MCP session.
              ShellTool is automatically appended.

    Returns:
        A LangGraph ReAct agent ready for invocation.
    """
    model = get_model()

    # Append shell tool to the MCP tools list
    all_tools = [*tools, shell]

    agent = create_react_agent(
        model=model,
        tools=all_tools,
        prompt=SYSTEM_PROMPT,
    )

    logger.info("k8s_agent_created", tool_count=len(all_tools), shell_enabled=True)
    return agent
