"""
app/core/llm_gateway.py
────────────────────────
OpenRouter is the SINGLE entry point for every LLM call.

We wrap the OpenAI-compatible SDK pointed at OpenRouter's base URL.
All agents, routes, and tools use `openrouter_client` from this module —
never import openai directly anywhere else.
"""

import httpx
from openai import AsyncOpenAI, APIConnectionError, APIStatusError, RateLimitError

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _get_openrouter_client() -> AsyncOpenAI:
    """Lazy singleton — created on first use, not at import time."""
    settings = get_settings()
    return AsyncOpenAI(
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": settings.OPENROUTER_APP_URL,
            "X-Title": settings.OPENROUTER_APP_NAME,
        },
        timeout=httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0),
    )


_openrouter_client: AsyncOpenAI | None = None


def _client() -> AsyncOpenAI:
    global _openrouter_client
    if _openrouter_client is None:
        _openrouter_client = _get_openrouter_client()
    return _openrouter_client


async def chat_completion(
    model: str,
    messages: list[dict],
    *,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    stream: bool = False,
) -> str:
    """
    Send a chat completion request through OpenRouter.

    Args:
        model:       Full OpenRouter model string, e.g.
                     "meta-llama/llama-3-70b-instruct"
        messages:    OpenAI-format message list.
        temperature: Sampling temperature.
        max_tokens:  Max response tokens.
        stream:      Whether to stream (returns generator when True).

    Returns:
        The assistant message content as a string.

    Raises:
        RuntimeError on unrecoverable errors (message is safe for clients).
    """
    logger.info("llm_request", model=model, message_count=len(messages))
    try:
        response = await _client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        logger.info(
            "llm_response",
            model=model,
            prompt_tokens=response.usage.prompt_tokens if response.usage else None,
            completion_tokens=response.usage.completion_tokens if response.usage else None,
        )
        return content

    except RateLimitError:
        logger.warning("openrouter_rate_limited", model=model)
        raise RuntimeError("LLM rate limit reached. Please retry shortly.")

    except APIStatusError as exc:
        logger.error("openrouter_api_error", status=exc.status_code, model=model)
        raise RuntimeError(f"LLM provider error (status {exc.status_code}).")

    except APIConnectionError:
        logger.error("openrouter_connection_error", model=model)
        raise RuntimeError("Cannot reach LLM gateway. Check connectivity.")

    except Exception as exc:
        # Never leak internal details to callers
        logger.exception("llm_unexpected_error", model=model)
        raise RuntimeError("Unexpected LLM error. Please try again.")
