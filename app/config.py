"""
app/config.py
─────────────
Central configuration loaded from environment variables.
Pydantic-Settings validates every value at startup — the app will
refuse to start if a required secret is missing.
"""

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_SECRET_KEY: str
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # ── OpenRouter ───────────────────────────────────────────
    OPENROUTER_API_KEY: str
    OPENROUTER_APP_NAME: str = "MultiAgent AI Platform"
    OPENROUTER_APP_URL: str = "https://localhost"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # ── Supabase ─────────────────────────────────────────────
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    # ── E2B ──────────────────────────────────────────────────
    E2B_API_KEY: str

    # ── Composio ─────────────────────────────────────────────
    COMPOSIO_API_KEY: str

    # ── Rate Limiting ────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 20

    # ── Derived helpers ──────────────────────────────────────
    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Use this everywhere instead of instantiating Settings() directly.
    """
    return Settings()
