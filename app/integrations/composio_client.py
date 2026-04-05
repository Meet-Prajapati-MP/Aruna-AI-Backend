"""
app/integrations/composio_client.py
─────────────────────────────────────
Composio tool integration for CrewAI agents.

Composio provides pre-built connectors for Gmail, GitHub, Slack,
Google Sheets, and 100+ other services. Agents call these tools
through the standard CrewAI tool interface — no custom HTTP code needed.

Manual setup required:
  1. Create an account at https://app.composio.dev
  2. Connect the services you want (GitHub, Gmail, etc.)
  3. Set COMPOSIO_API_KEY in .env
"""

from typing import List

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# NOTE: composio_crewai is intentionally NOT imported at module level.
# composio-core 0.6.x initialises grpc and reads ~/.composio/ at import
# time, which crashes the process before FastAPI even starts.
# All imports are deferred to the point of first use inside each function.

_toolset = None  # module-level cache (lazy)


def _get_toolset():
    """Lazy singleton for ComposioToolSet — imported and created on first call."""
    global _toolset
    if _toolset is None:
        from composio_crewai import ComposioToolSet  # deferred import
        settings = get_settings()
        _toolset = ComposioToolSet(api_key=settings.COMPOSIO_API_KEY)
    return _toolset


def get_github_tools() -> List:
    """
    Returns CrewAI-compatible tools for GitHub operations.
    Requires a GitHub connection in the Composio dashboard.
    """
    try:
        from composio_crewai import Action  # deferred import
        toolset = _get_toolset()
        tools = toolset.get_tools(
            actions=[
                Action.GITHUB_CREATE_AN_ISSUE,
                Action.GITHUB_LIST_OPEN_PULL_REQUESTS,
                Action.GITHUB_STAR_A_REPOSITORY_FOR_THE_AUTHENTICATED_USER,
            ]
        )
        logger.info("composio_github_tools_loaded", count=len(tools))
        return tools
    except Exception as exc:
        logger.error("composio_github_tools_error", error=str(exc))
        return []


def get_gmail_tools() -> List:
    """
    Returns CrewAI-compatible tools for Gmail operations.
    Requires a Gmail connection in the Composio dashboard.
    """
    try:
        from composio_crewai import Action  # deferred import
        toolset = _get_toolset()
        tools = toolset.get_tools(
            actions=[
                Action.GMAIL_SEND_EMAIL,
                Action.GMAIL_FETCH_EMAILS,
            ]
        )
        logger.info("composio_gmail_tools_loaded", count=len(tools))
        return tools
    except Exception as exc:
        logger.error("composio_gmail_tools_error", error=str(exc))
        return []


def get_tools_for_agent(agent_role: str) -> List:
    """
    Maps agent roles to the appropriate Composio tool sets.

    The Engineer agent gets GitHub tools (create issues, PRs).
    The Writer agent gets Gmail tools (send reports).
    Other agents get no external tools by default.
    """
    role_lower = agent_role.lower()
    if "engineer" in role_lower:
        return get_github_tools()
    if "writer" in role_lower:
        return get_gmail_tools()
    return []
