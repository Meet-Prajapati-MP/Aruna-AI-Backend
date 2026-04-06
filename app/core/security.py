"""
app/core/security.py
─────────────────────
JWT validation helpers for Supabase-issued tokens.

Supabase signs its JWTs with the project's JWT secret.
We verify them locally — no round-trip to Supabase on every request.
"""

import base64
from datetime import datetime, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Supabase uses HS256 for its JWTs
_ALGORITHM = "HS256"


class TokenValidationError(Exception):
    """Raised when a JWT cannot be validated."""


def decode_supabase_jwt(token: str) -> dict[str, Any]:
    """
    Decode and validate a Supabase-issued JWT.

    Returns the decoded payload dict on success.
    Raises TokenValidationError on any failure.
    """
    settings = get_settings()
    # Supabase stores the JWT secret as a base64-encoded string in the dashboard.
    # GoTrue signs tokens using the decoded bytes, so we try decoded first.
    raw_secret = settings.SUPABASE_JWT_SECRET
    try:
        secret = base64.b64decode(raw_secret + '==')
    except Exception:
        secret = raw_secret.encode('utf-8')
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[_ALGORITHM],
            options={"verify_aud": False},  # Supabase sets 'authenticated' as audience
        )
        return payload
    except ExpiredSignatureError:
        raise TokenValidationError("Token has expired.")
    except JWTError as exc:
        logger.warning("jwt_validation_failed", error=str(exc))
        raise TokenValidationError("Invalid token.")


def extract_user_id(token: str) -> str:
    """
    Convenience wrapper — returns the Supabase user UUID from the token.
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
