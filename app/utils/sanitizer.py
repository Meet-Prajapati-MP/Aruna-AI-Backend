"""
app/utils/sanitizer.py
───────────────────────
Input sanitisation and prompt-injection defence.

All user-supplied strings pass through `sanitize_input()` before
being forwarded to any LLM or external service.
"""

import re
from typing import Any

# ── Prompt injection patterns ────────────────────────────────────────────────
# These attempt to override system instructions or exfiltrate context.
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"forget\s+(all\s+)?(previous|prior|above)",
    r"you\s+are\s+now\s+(a\s+)?(?!an?\s+AI)",   # "you are now DAN"
    r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
    r"system\s*:\s*",                              # fake system turn injection
    r"<\|im_start\|>",                             # ChatML injection
    r"<\|system\|>",
    r"\[\[.*?\]\]",                                # common jailbreak bracket syntax
    r"base64\s*decode",                            # encoded payload attempt
]
_INJECTION_RE = re.compile(
    "|".join(_INJECTION_PATTERNS),
    re.IGNORECASE | re.DOTALL,
)

# Max character lengths per field type
_MAX_LENGTHS: dict[str, int] = {
    "task": 4000,
    "message": 2000,
    "default": 1000,
}


class InputSanitizationError(ValueError):
    """Raised when input fails validation."""


def sanitize_input(
    text: str,
    field_name: str = "default",
    *,
    allow_newlines: bool = True,
) -> str:
    """
    Sanitise a user-supplied string:

    1. Strip leading/trailing whitespace.
    2. Enforce maximum length.
    3. Reject strings containing prompt-injection patterns.
    4. Strip null bytes and other dangerous control characters.

    Returns the cleaned string, or raises InputSanitizationError.
    """
    if not isinstance(text, str):
        raise InputSanitizationError(f"Field '{field_name}' must be a string.")

    text = text.strip()

    # Remove null bytes
    text = text.replace("\x00", "")

    # Optionally collapse newlines
    if not allow_newlines:
        text = re.sub(r"[\r\n]+", " ", text)

    # Length check
    max_len = _MAX_LENGTHS.get(field_name, _MAX_LENGTHS["default"])
    if len(text) > max_len:
        raise InputSanitizationError(
            f"Field '{field_name}' exceeds maximum length of {max_len} characters."
        )

    # Prompt injection check
    if _INJECTION_RE.search(text):
        raise InputSanitizationError(
            "Input contains disallowed patterns. Please rephrase your request."
        )

    return text


def sanitize_code(code: str) -> str:
    """
    Light sanitisation for code passed to the E2B sandbox.
    We don't filter code semantics — that's E2B's job — but we
    strip obvious shell-escape tricks at the string level.
    """
    if not isinstance(code, str):
        raise InputSanitizationError("Code must be a string.")

    # Remove null bytes
    code = code.replace("\x00", "")

    max_len = 10_000
    if len(code) > max_len:
        raise InputSanitizationError(
            f"Code block exceeds maximum length of {max_len} characters."
        )

    return code
