"""
app/core/security.py
─────────────────────
JWT validation helpers for Supabase-issued tokens.

Uses the Supabase Admin SDK to verify tokens — this avoids any
JWT-secret mismatch issues and always stays in sync with Supabase.
"""

from typing import Any, Optional

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TokenValidationError(Exception):
    """Raised when a JWT cannot be validated."""


def decode_supabase_jwt(token: str) -> dict[str, Any]:
    """
    Validate a Supabase-issued JWT via the Supabase Auth API.

    Returns a payload-like dict with at least a 'sub' (user UUID).
    Raises TokenValidationError on any failure.
    """
    from supabase import create_client
    settings = get_settings()
    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        response = client.auth.get_user(token)
        if response.user is None:
            raise TokenValidationError("Invalid token.")
        return {"sub": response.user.id, "email": response.user.email}
    except TokenValidationError:
        raise
    except Exception as exc:
        logger.warning("jwt_validation_failed", error=str(exc))
        raise TokenValidationError("Invalid token.")


def extract_user_id(token: str) -> str:
    """
    Returns the Supabase user UUID from the token.
    Raises TokenValidationError on failure.
    """
    payload = decode_supabase_jwt(token)
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise TokenValidationError("Token missing subject claim.")
    return user_id


def extract_bearer_token(authorization: Optional[str]) -> str:
    """
    Parse 'Bearer <token>' header value.
    Raises TokenValidationError if header is malformed.
    """
    if not authorization:
        raise TokenValidationError("Missing Authorization header.")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise TokenValidationError("Authorization header must be 'Bearer <token>'.")
    return parts[1]
