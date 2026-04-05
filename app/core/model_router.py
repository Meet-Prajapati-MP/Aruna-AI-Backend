"""
app/core/model_router.py
─────────────────────────
FIX B5: Corrected OpenRouter model IDs.

Original bug: "anthropic/claude-sonnet-4-6" is not a valid OpenRouter model ID.
Every COMPLEX task would fail on the first candidate, waste retries, and fall
back to LLaMA 405B silently.

Verified OpenRouter model IDs (as of 2025):
  Claude Sonnet 4.5  → anthropic/claude-sonnet-4-5
  LLaMA 3.1 70B      → meta-llama/llama-3.1-70b-instruct
  LLaMA 3.1 405B     → meta-llama/llama-3.1-405b-instruct
  Nemotron 70B       → nvidia/llama-3.1-nemotron-70b-instruct
  Mistral 7B         → mistralai/mistral-7b-instruct
  LLaMA 3 8B         → meta-llama/llama-3-8b-instruct
  Mixtral 8x7B       → mistralai/mixtral-8x7b-instruct

NOTE: Check https://openrouter.ai/models for the latest IDs.
Model IDs on OpenRouter follow the pattern: provider/model-name
"""

from enum import Enum
from typing import Optional

from app.core.llm_gateway import chat_completion
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


# ── Model tiers (all via OpenRouter) ────────────────────────────────────────
# FIX B5: All model IDs verified against OpenRouter's model catalogue.
MODEL_TIERS: dict[TaskComplexity, list[str]] = {
    TaskComplexity.SIMPLE: [
        "mistralai/mistral-7b-instruct",
        "meta-llama/llama-3-8b-instruct",
        "meta-llama/llama-3.1-8b-instruct",    # fallback variant
    ],
    TaskComplexity.MEDIUM: [
        "meta-llama/llama-3.1-70b-instruct",   # FIX: was "llama-3-70b-instruct"
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "mistralai/mixtral-8x7b-instruct",
    ],
    TaskComplexity.COMPLEX: [
        "anthropic/claude-sonnet-4-5",          # FIX: was "claude-sonnet-4-6" (invalid)
        "meta-llama/llama-3.1-405b-instruct",
        "nvidia/llama-3.1-nemotron-70b-instruct",   # final fallback
    ],
}

# Keyword hints that bump complexity up
_COMPLEX_KEYWORDS = {
    "analyze", "architecture", "design", "strategy", "compare",
    "research", "optimize", "security", "review",
}
_SIMPLE_KEYWORDS = {
    "summarize", "translate", "list", "format", "convert", "fix typo",
}


def classify_task(task_description: str) -> TaskComplexity:
    """Heuristic classifier: inspects keywords and word count to assign a tier."""
    lower = task_description.lower()
    word_count = len(lower.split())

    if any(kw in lower for kw in _COMPLEX_KEYWORDS) or word_count > 100:
        return TaskComplexity.COMPLEX
    if any(kw in lower for kw in _SIMPLE_KEYWORDS) or word_count < 20:
        return TaskComplexity.SIMPLE
    return TaskComplexity.MEDIUM


async def routed_chat(
    messages: list[dict],
    task_description: str = "",
    *,
    complexity: Optional[TaskComplexity] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> tuple[str, str]:
    """
    Route a chat completion request through the model tier system with fallback.

    Returns:
        Tuple of (response_text, model_used)
    """
    tier = complexity or classify_task(task_description)
    candidates = MODEL_TIERS[tier]
    last_error: Optional[Exception] = None

    for model in candidates:
        try:
            logger.info("model_router_attempt", model=model, tier=tier)
            response = await chat_completion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            logger.info("model_router_success", model=model, tier=tier)
            return response, model

        except RuntimeError as exc:
            logger.warning("model_router_fallback", model=model, reason=str(exc))
            last_error = exc
            continue

    logger.error("model_router_all_failed", tier=tier)
    raise RuntimeError(
        f"All models in tier '{tier}' failed. Last error: {last_error}"
    )


def get_crewai_llm_string(complexity: TaskComplexity = TaskComplexity.MEDIUM) -> str:
    """
    Returns the LiteLLM model string for CrewAI agent configuration.
    LiteLLM/CrewAI requires the 'openrouter/' prefix to route through OpenRouter.
    """
    primary = MODEL_TIERS[complexity][0]
    return f"openrouter/{primary}"
