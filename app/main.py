"""
app/main.py
────────────
FastAPI application entry point.

Responsibilities:
  - Create and configure the FastAPI app
  - Register CORS middleware
  - Mount all API routers
  - Attach the rate limiter
  - Configure structured logging
  - Expose a health-check endpoint
  - Handle errors without leaking stack traces
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import agents, auth, tasks
from app.config import get_settings
from app.middleware.rate_limiter import limiter
from app.utils.logger import configure_logging, get_logger

# Configure basic logging immediately so startup errors are visible in Railway logs.
# This runs before settings are loaded so we always get log output.
configure_logging(is_production=False)
logger = get_logger(__name__)


# ── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # Re-configure logging now that we know the environment
    configure_logging(is_production=settings.is_production)
    logger.info("startup", env=settings.APP_ENV)
    yield
    logger.info("shutdown")


# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    # Validate settings eagerly so missing env-vars produce a clear error in logs
    # rather than a cryptic crash mid-request.
    try:
        settings = get_settings()
    except Exception as exc:
        logger.error(
            "startup_failed",
            error=str(exc),
            hint=(
                "One or more required environment variables are not set. "
                "Set them in Railway → Project → Variables. "
                "Required: APP_SECRET_KEY, OPENROUTER_API_KEY, SUPABASE_URL, "
                "SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, "
                "SUPABASE_JWT_SECRET, E2B_API_KEY, COMPOSIO_API_KEY"
            ),
        )
        raise

    app = FastAPI(
        title="Multi-Agent AI Platform",
        description=(
            "Production-ready backend for a multi-agent AI SaaS platform. "
            "LLM calls are routed through OpenRouter. "
            "Agents are powered by CrewAI."
        ),
        version="1.0.0",
        # Hide /docs and /openapi.json in production
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=lifespan,
    )

    # ── Rate limiter ──────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth.router)
    app.include_router(tasks.router)
    app.include_router(agents.router)

    # ── Global exception handler (no stack trace leakage) ────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("unhandled_exception", path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal error occurred. Please try again later."},
        )

    # ── Root ──────────────────────────────────────────────────────────────────
    @app.get("/", tags=["System"], include_in_schema=False)
    async def root():
        return {"status": "ok", "message": "Multi-Agent AI Platform is running", "version": "1.0.0"}

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["System"], include_in_schema=False)
    async def health():
        return {"status": "ok", "version": "1.0.0"}

    return app


app = create_app()
