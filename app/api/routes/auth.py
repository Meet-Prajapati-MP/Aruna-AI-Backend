"""
app/api/routes/auth.py
───────────────────────
Authentication endpoints:
  POST /auth/signup  — register a new user
  POST /auth/login   — authenticate and receive JWT tokens
"""

from fastapi import APIRouter, HTTPException, Request, status

from app.integrations.supabase_client import AuthError, sign_in, sign_up
from app.middleware.rate_limiter import limiter
from app.models.auth import AuthResponse, LoginRequest, SignupRequest
from app.utils.logger import get_logger
from app.utils.sanitizer import InputSanitizationError, sanitize_input

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
@limiter.limit("5/minute")
async def signup(request: Request, body: SignupRequest) -> AuthResponse:
    """
    Register a new user account using Supabase Auth.

    - Email must be valid.
    - Password must be ≥8 chars, contain uppercase and a digit.
    - After signup, Supabase may send a confirmation email depending
      on your project's email settings.
    """
    try:
        # Sanitise email string (Pydantic already validated format)
        sanitize_input(body.email, field_name="default", allow_newlines=False)
    except InputSanitizationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    try:
        result = sign_up(email=body.email, password=body.password)
        return AuthResponse(
            user_id=result["user_id"],
            email=result["email"],
            access_token=result.get("access_token") or "",
            refresh_token=result.get("refresh_token"),
            message="Account created successfully.",
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in and receive JWT tokens",
)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest) -> AuthResponse:
    """
    Authenticate with email and password.

    Returns Supabase-issued access_token and refresh_token.
    Include the access_token as `Authorization: Bearer <token>` on
    all protected requests.
    """
    try:
        sanitize_input(body.email, field_name="default", allow_newlines=False)
    except InputSanitizationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    try:
        result = sign_in(email=body.email, password=body.password)
        return AuthResponse(
            user_id=result["user_id"],
            email=result["email"],
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token"),
            expires_in=result.get("expires_in"),
            message="Login successful.",
        )
    except AuthError as exc:
        # Return a generic message — don't reveal whether email or password was wrong
        logger.warning("login_failed", email=body.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )
