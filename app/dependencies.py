"""
app/dependencies.py
────────────────────
FastAPI dependency injectors.

`require_auth` is the JWT guard used on all protected routes.
It validates the Supabase JWT and returns the user_id.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import TokenValidationError, extract_user_id

_bearer_scheme = HTTPBearer(auto_error=False)


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """
    FastAPI dependency that:
      1. Extracts the Bearer token from the Authorization header.
      2. Validates and decodes the Supabase JWT.
      3. Returns the user UUID (sub claim).

    Raises HTTP 401 on any failure.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = extract_user_id(credentials.credentials)
        return user_id
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
