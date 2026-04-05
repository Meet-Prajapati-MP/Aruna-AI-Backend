"""
app/agents/router_crew.py
──────────────────────────────────────────────────────────────────
ROUTER AGENT SYSTEM — Click-by-click explanation + working code
──────────────────────────────────────────────────────────────────

HOW CrewAI AGENTS WORK (step by step):
═══════════════════════════════════════
1. AGENT  = An AI persona with a role, goal, and backstory.
            It uses an LLM under the hood and can have tools.

2. TASK   = A job description given TO an agent.
            It has a description (what to do) and
            expected_output (what the result should look like).

3. CREW   = A team of agents + tasks, wired together.
            Can run sequentially or in parallel.

4. KICKOFF = crew.kickoff() sends the tasks to agents and collects results.

ROUTER PATTERN (this file):
═══════════════════════════
┌─────────────────────────────────────────────────────────────────┐
│  User Question                                                  │
│        │                                                        │
│        ▼                                                        │
│  [Router Agent] ← classifies the question type                 │
│        │                                                        │
│        ├──► Coding?      → [Engineer Agent]                    │
│        ├──► Research?    → [Analyst Agent]                     │
│        ├──► Math?        → [Math Agent]                        │
│        ├──► Writing?     → [Writer Agent]                      │
│        └──► General?     → [General Agent]                     │
│                                 │                              │
│                                 ▼                              │
│                          Final Answer                          │
└─────────────────────────────────────────────────────────────────┘
"""

import os
from typing import Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────
# STEP 1 ─ LLM FACTORY
# Every agent needs an LLM.  We build one here from env vars.
# ─────────────────────────────────────────────────────────────────

def _make_llm(temperature: float = 0.3):
    """
    Build a CrewAI LLM.

    CLICK-BY-CLICK:
    ① Import crewai.LLM  (deferred so startup stays fast)
    ② Read API key from environment
    ③ Build LLM with model string + base URL for OpenRouter
    """
    from crewai import LLM  # ① deferred import

    api_key = os.environ.get("OPENROUTER_API_KEY", "")  # ②
    base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    return LLM(                                          # ③
        model="openrouter/anthropic/claude-3-haiku",    # fast + cheap for routing
        temperature=temperature,
        api_key=api_key,
        base_url=base_url,
    )


def _make_strong_llm(temperature: float = 0.5):
    """Stronger model for actual answering tasks."""
    from crewai import LLM

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    return LLM(
        model="openrouter/anthropic/claude-3-5-sonnet",
        temperature=temperature,
        api_key=api_key,
        base_url=base_url,
    )


# ─────────────────────────────────────────────────────────────────
# STEP 2 ─ DEFINE SPECIALIZED AGENTS
#
# Each agent is built with:
#   role      = "job title" — affects how the LLM responds
#   goal      = what the agent is trying to achieve
#   backstory = personality / expertise context
#   llm       = which model to use
#   tools     = list of callable tools (optional)
#   verbose   = print reasoning to console
# ─────────────────────────────────────────────────────────────────

def build_router_agent():
    """
    ROUTER AGENT — reads a question and outputs one category label.

    This is the meta-agent.  Its ONLY job is to classify.
    It does NOT answer the question itself.

    Categories it can output:
      coding | research | math | writing | general
    """
    from crewai import Agent

    return Agent(
        role="Question Router",
        goal=(
            "Classify incoming questions into exactly ONE of these categories: "
            "coding, research, math, writing, general. "
            "Output ONLY the category word — nothing else."
        ),
        backstory=(
            "You are a highly accurate classifier. You read a question and "
            "instantly know which expert should handle it. "
            "You never answer the question — you only label it."
        ),
        llm=_make_llm(temperature=0.0),   # low temp = deterministic classification
        verbose=True,
        allow_delegation=False,
        max_iter=1,                        # classifier needs only 1 pass
    )


def build_coding_agent():
    """
    CODING AGENT — answers programming questions, writes & explains code.
    """
    from crewai import Agent

    return Agent(
        role="Senior Software Engineer",
        goal=(
            "Answer coding questions with accurate, well-commented code examples. "
            "Explain the logic step by step. Prefer Python unless another language is asked."
        ),
        backstory=(
            "You are a senior engineer with 12 years of experience in Python, "
            "JavaScript, and system design. You write clean, secure code and "
            "always explain your reasoning."
        ),
        llm=_make_strong_llm(temperature=0.2),
        verbose=True,
        allow_delegation=False,
        max_iter=4,
    )


def build_research_agent():
    """
    RESEARCH AGENT — answers factual/research questions with sourced detail.
    """
    from crewai import Agent

    return Agent(
        role="Research Analyst",
        goal=(
            "Answer research questions with accurate, well-structured information. "
            "Always distinguish facts from opinions. "
            "Provide context and key sources when known."
        ),
        backstory=(
            "You are a meticulous researcher trained across science, history, "
            "technology, and current events. You never fabricate facts. "
            "You present information clearly and cite reasoning."
        ),
        llm=_make_strong_llm(temperature=0.4),
        verbose=True,
        allow_delegation=False,
        max_iter=4,
    )


def build_math_agent():
    """
    MATH AGENT — solves mathematical problems step by step.
    """
    from crewai import Agent

    return Agent(
        role="Mathematics Expert",
        goal=(
            "Solve mathematical problems step by step. "
            "Show all working. Verify the answer at the end. "
            "Use clear notation."
        ),
        backstory=(
            "You are a mathematics professor specialising in algebra, calculus, "
            "statistics, and discrete math. You always show your working "
            "and double-check answers."
        ),
        llm=_make_strong_llm(temperature=0.0),  # math needs no creativity
        verbose=True,
        allow_delegation=False,
        max_iter=4,
    )


def build_writer_agent():
    """
    WRITER AGENT — handles creative writing, emails, essays, summaries.
    """
    from crewai import Agent

    return Agent(
        role="Professional Writer",
        goal=(
            "Produce polished, well-structured written content. "
            "Match the tone and format the user needs: formal, casual, creative. "
            "Be concise and clear."
        ),
        backstory=(
            "You are an award-winning writer with experience in technical docs, "
            "creative fiction, business communication, and journalism. "
            "You adapt your voice to any context."
        ),
        llm=_make_strong_llm(temperature=0.8),  # writing benefits from creativity
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )


def build_general_agent():
    """
    GENERAL AGENT — fallback for everything else.
    """
    from crewai import Agent

    return Agent(
        role="General Assistant",
        goal=(
            "Answer any question helpfully, accurately, and concisely. "
            "If unsure, say so clearly rather than guessing."
        ),
        backstory=(
            "You are a knowledgeable, friendly assistant with broad expertise. "
            "You give honest, balanced answers and admit uncertainty when it exists."
        ),
        llm=_make_strong_llm(temperature=0.6),
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )


# ─────────────────────────────────────────────────────────────────
# STEP 3 ─ TASK FACTORY
#
# A Task tells an agent WHAT to do and WHAT format to return.
# context=[...] passes previous task outputs as input to this task.
# ─────────────────────────────────────────────────────────────────

def _make_classify_task(question: str, router_agent):
    """
    Task 1: give the question to the Router Agent.
    Its only job is to output a single category word.
    """
    from crewai import Task

    return Task(
        description=(
            f"Classify this question into one of: coding, research, math, writing, general.\n\n"
            f"Question: {question}\n\n"
            "Output ONLY the category word. No explanation, no punctuation."
        ),
        expected_output="One word: coding OR research OR math OR writing OR general",
        agent=router_agent,
    )


def _make_answer_task(question: str, category: str, answer_agent, classify_task):
    """
    Task 2: give the question + category to the specialist agent.
    context=[classify_task] means this task sees the router's output.
    """
    from crewai import Task

    return Task(
        description=(
            f"You are the {category.upper()} expert. Answer this question thoroughly:\n\n"
            f"Question: {question}\n\n"
            "Provide a clear, well-structured, accurate answer."
        ),
        expected_output="A complete, well-structured answer to the user's question.",
        agent=answer_agent,
        context=[classify_task],           # receives router output as context
    )


# ─────────────────────────────────────────────────────────────────
# STEP 4 ─ THE ROUTER CREW
#
# This function:
#  ① Runs the router agent to classify the question
#  ② Based on the label, picks the right specialist agent
#  ③ Runs the specialist to answer the question
#  ④ Returns the answer
# ─────────────────────────────────────────────────────────────────

# Map category → agent builder function
_AGENT_MAP = {
    "coding":   build_coding_agent,
    "research": build_research_agent,
    "math":     build_math_agent,
    "writing":  build_writer_agent,
    "general":  build_general_agent,
}


def run_router_crew(question: str) -> dict:
    """
    Main entry point.

    CLICK-BY-CLICK execution:
    ─────────────────────────
    1. Build the Router Agent
    2. Create the classify task
    3. Run a tiny 1-agent crew just for classification
    4. Parse the category from the result
    5. Build the correct specialist agent
    6. Create the answer task
    7. Run a 2-agent crew (router + specialist) sequentially
    8. Return the final answer

    Returns:
        {
            "question":  str,
            "category":  str,    ← which specialist handled it
            "answer":    str,    ← final response
        }
    """
    from crewai import Crew, Process

    logger.info("router_crew_start", question=question[:100])

    # ── 1. Build router agent ─────────────────────────────────────
    router_agent = build_router_agent()

    # ── 2. Create classify task ───────────────────────────────────
    classify_task = _make_classify_task(question, router_agent)

    # ── 3. Run classification crew (1 agent, 1 task) ──────────────
    classify_crew = Crew(
        agents=[router_agent],
        tasks=[classify_task],
        process=Process.sequential,
        verbose=True,
    )
    classify_result = classify_crew.kickoff()
    raw_category = str(classify_result).strip().lower().split()[0]

    # ── 4. Parse & validate the category ─────────────────────────
    category = raw_category if raw_category in _AGENT_MAP else "general"
    logger.info("question_classified", category=category)

    # ── 5. Build the right specialist agent ───────────────────────
    specialist_agent = _AGENT_MAP[category]()

    # ── 6. Create answer task ─────────────────────────────────────
    answer_task = _make_answer_task(question, category, specialist_agent, classify_task)

    # ── 7. Run the full 2-agent crew ──────────────────────────────
    answer_crew = Crew(
        agents=[router_agent, specialist_agent],
        tasks=[classify_task, answer_task],
        process=Process.sequential,   # router runs first, then specialist
        verbose=True,
    )
    final_result = answer_crew.kickoff()

    # ── 8. Return structured output ───────────────────────────────
    return {
        "question": question,
        "category": category,
        "answer":   str(final_result),
    }


# ─────────────────────────────────────────────────────────────────
# STEP 5 ─ QUICK TEST (run this file directly to test)
#
# From your backend folder:
#   python -m app.agents.router_crew
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_questions = [
        "How do I reverse a string in Python?",               # → coding
        "What caused World War 1?",                           # → research
        "What is 15% of 240?",                                # → math
        "Write a professional email declining a job offer.",  # → writing
        "What is the meaning of life?",                       # → general
    ]

    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        result = run_router_crew(q)
        print(f"Category: {result['category']}")
        print(f"Answer:\n{result['answer']}")
        print("="*60)
