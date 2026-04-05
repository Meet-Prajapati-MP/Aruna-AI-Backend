"""
app/integrations/supabase_client.py
─────────────────────────────────────
Supabase client wrapper for authentication and database operations.

Two clients are maintained:
  - anon_client  : uses the anon key (safe for per-user operations)
  - admin_client : uses the service-role key (server-side only,
                   NEVER expose to frontend)
"""

from functools import lru_cache
from typing import Optional

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@lru_cache
def get_supabase_anon() -> Client:
    """Public client — mirrors what the frontend SDK would use."""
    s = get_settings()
    return create_client(s.SUPABASE_URL, s.SUPABASE_ANON_KEY)


@lru_cache
def get_supabase_admin() -> Client:
    """
    Service-role client — bypasses Row Level Security.
    Use only for server-side admin operations.
    """
    s = get_settings()
    return create_client(
        s.SUPABASE_URL,
        s.SUPABASE_SERVICE_ROLE_KEY,
        options=ClientOptions(auto_refresh_token=False, persist_session=False),
    )


# ── Auth helpers ──────────────────────────────────────────────────────────────

class AuthError(Exception):
    """Raised when a Supabase auth operation fails."""


def sign_up(email: str, password: str) -> dict:
    """
    Register a new user with Supabase Auth.
    Returns the session dict on success.
    Raises AuthError on failure.
    """
    try:
        client = get_supabase_anon()
        response = client.auth.sign_up({"email": email, "password": password})
        if response.user is None:
            raise AuthError("Signup failed: no user returned.")
        logger.info("user_signed_up", user_id=response.user.id)
        return {
            "user_id": response.user.id,
            "email": response.user.email,
            "access_token": response.session.access_token if response.session else None,
            "refresh_token": response.session.refresh_token if response.session else None,
        }
    except AuthError:
        raise
    except Exception as exc:
        logger.error("signup_error", error=str(exc))
        raise AuthError("Signup failed. Please check your credentials.")


def sign_in(email: str, password: str) -> dict:
    """
    Authenticate a user.
    Returns access_token and refresh_token on success.
    Raises AuthError on failure.
    """
    try:
        client = get_supabase_anon()
        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        if response.session is None:
            raise AuthError("Login failed: no session returned.")
        logger.info("user_signed_in", user_id=response.user.id)
        return {
            "user_id": response.user.id,
            "email": response.user.email,
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "expires_in": response.session.expires_in,
        }
    except AuthError:
        raise
    except Exception as exc:
        logger.error("signin_error", error=str(exc))
        raise AuthError("Login failed. Invalid credentials.")


def get_user_by_id(user_id: str) -> Optional[dict]:
    """Fetch user profile using the admin client."""
    try:
        admin = get_supabase_admin()
        response = admin.auth.admin.get_user_by_id(user_id)
        if response.user:
            return {"user_id": response.user.id, "email": response.user.email}
        return None
    except Exception as exc:
        logger.error("get_user_error", user_id=user_id, error=str(exc))
        return None
