"""
app/agents/definitions.py
──────────────────────────
CrewAI Agent definitions.

Each agent is assigned:
  - A role, goal, and backstory (drives LLM behaviour)
  - A tiered OpenRouter model via LiteLLM's 'openrouter/' prefix
  - Composio tools where applicable

Model assignment:
  Architect  → COMPLEX  (needs deep reasoning for planning)
  Analyst    → MEDIUM   (research tasks, balanced cost/quality)
  Writer     → MEDIUM   (writing, doesn't need max capability)
  Engineer   → COMPLEX  (code generation + E2B execution)
"""

import os

# crewai (Agent, LLM) is intentionally NOT imported at module level —
# see crew.py for the explanation.  All crewai symbols are imported
# inside the functions that use them so startup stays lightweight.

from app.config import get_settings
from app.core.model_router import TaskComplexity, get_crewai_llm_string
from app.integrations.composio_client import get_tools_for_agent
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _make_llm(complexity: TaskComplexity, temperature: float = 0.7):
    """
    Build a CrewAI LLM object pointing at OpenRouter.
    LiteLLM resolves 'openrouter/<model>' to the correct endpoint.
    """
    from crewai import LLM  # noqa: PLC0415  deferred import
    settings = get_settings()
    # ── LiteLLM needs the OpenRouter key in the environment ──────────────────
    # CrewAI/LiteLLM reads OPENROUTER_API_KEY automatically when the model
    # string is prefixed with 'openrouter/'.
    os.environ.setdefault("OPENROUTER_API_KEY", settings.OPENROUTER_API_KEY)
    model_string = get_crewai_llm_string(complexity)
    return LLM(
        model=model_string,
        temperature=temperature,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        extra_headers={
            "HTTP-Referer": settings.OPENROUTER_APP_URL,
            "X-Title": settings.OPENROUTER_APP_NAME,
        },
    )


def build_architect_agent():
    """
    Architect Agent — decomposes the user task into a structured plan.
    Uses a complex model to ensure high-quality planning.
    """
    from crewai import Agent  # noqa: PLC0415  deferred import
    tools = get_tools_for_agent("architect")
    return Agent(
        role="Architect",
        goal=(
            "Analyse the user's task and produce a clear, step-by-step execution plan. "
            "Identify which sub-tasks require research, writing, or code execution. "
            "Be concise and precise."
        ),
        backstory=(
            "You are a senior solutions architect with 15 years of experience decomposing "
            "complex technical problems into actionable plans. You excel at identifying "
            "dependencies, risks, and the optimal sequence of work."
        ),
        llm=_make_llm(TaskComplexity.COMPLEX, temperature=0.3),
        tools=tools,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )


def build_analyst_agent():
    """
    Analyst Agent — performs research and gathers information.
    """
    from crewai import Agent  # noqa: PLC0415  deferred import
    tools = get_tools_for_agent("analyst")
    return Agent(
        role="Analyst",
        goal=(
            "Research and synthesise information relevant to the task. "
            "Provide accurate, well-sourced summaries that other agents can act on."
        ),
        backstory=(
            "You are a meticulous research analyst. You separate facts from opinions, "
            "identify primary sources, and present findings in a structured format. "
            "You never fabricate information."
        ),
        llm=_make_llm(TaskComplexity.MEDIUM, temperature=0.5),
        tools=tools,
        verbose=True,
        allow_delegation=False,
        max_iter=4,
    )


def build_writer_agent():
    """
    Writer Agent — produces polished final output.
    Optionally sends reports via Gmail through Composio.
    """
    from crewai import Agent  # noqa: PLC0415  deferred import
    tools = get_tools_for_agent("writer")
    return Agent(
        role="Writer",
        goal=(
            "Transform the architect's plan and analyst's research into a clear, "
            "well-structured final response. Adapt tone and format to the task type."
        ),
        backstory=(
            "You are a professional technical writer with experience producing "
            "documentation, reports, and blog posts. You write clearly and concisely, "
            "adapting style from formal reports to casual summaries as needed."
        ),
        llm=_make_llm(TaskComplexity.MEDIUM, temperature=0.8),
        tools=tools,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )


def build_engineer_agent():
    """
    Engineer Agent — writes and executes code via E2B sandbox.
    Also has access to GitHub tools via Composio.
    """
    from crewai import Agent  # noqa: PLC0415  deferred import
    tools = get_tools_for_agent("engineer")
    return Agent(
        role="Engineer",
        goal=(
            "Write production-quality code to solve technical sub-tasks. "
            "Ensure all code is correct, secure, and well-commented. "
            "When code needs to run, delegate execution to the E2B sandbox tool."
        ),
        backstory=(
            "You are a senior software engineer fluent in Python, JavaScript, "
            "and systems design. You write clean, testable code and never "
            "hardcode secrets. You always validate inputs and handle errors."
        ),
        llm=_make_llm(TaskComplexity.COMPLEX, temperature=0.2),
        tools=tools,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )
