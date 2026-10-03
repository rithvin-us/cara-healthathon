"""Application settings, read once from environment variables.

Every value has a safe local-development default so `uvicorn app.main:app`
works out of the box. Production deployments must set at least JWT_SECRET
and CORS_ORIGINS (see .env.example).
"""

import logging
import os
from functools import lru_cache

logger = logging.getLogger("cara.config")

_DEV_JWT_SECRET = "dev-only-insecure-secret-change-me"


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _list(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def _normalise_database_url(url: str) -> str:
    # Hosted Postgres providers hand out postgres:// URLs; SQLAlchemy 2 needs an
    # explicit driver, and we ship psycopg (v3).
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Settings:
    PROJECT_NAME: str = "Cara Postnatal Follow-Up Coordination Platform"
    VERSION: str = "1.1.0"
    API_V1_STR: str = "/api/v1"

    def __init__(self) -> None:
        self.ENVIRONMENT: str = os.getenv("CARA_ENV", "development").lower()

        # Security
        self.JWT_SECRET: str = os.getenv("JWT_SECRET", _DEV_JWT_SECRET)
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 12)))
        self.CORS_ORIGINS: list[str] = _list(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
        )

        # Demo mode enables one-click role sign-in and the demo-data reset endpoint.
        # Never enable it on a deployment that holds real patient data.
        self.DEMO_MODE: bool = _bool("CARA_DEMO_MODE", True)

        # Database (SQLite for zero-setup local runs; any SQLAlchemy URL in production)
        self.DATABASE_URL: str = _normalise_database_url(os.getenv("DATABASE_URL", "sqlite:///./cara.db"))

        # Facility-local calendar: visit "today" is computed in this timezone, not UTC.
        self.TIMEZONE: str = os.getenv("CARA_TIMEZONE", "Asia/Kolkata")

        # Messaging. "simulated" logs messages without sending; "twilio" sends for real.
        self.NUDGE_PROVIDER: str = os.getenv("NUDGE_PROVIDER", "simulated").lower()
        self.TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        self.TWILIO_SMS_NUMBER: str = os.getenv("TWILIO_SMS_NUMBER", "")
        self.TWILIO_STATUS_CALLBACK_URL: str = os.getenv("TWILIO_STATUS_CALLBACK_URL", "")

        # Shared secret for the scheduled daily job (Vercel Cron sends it as a Bearer token).
        self.CRON_SECRET: str = os.getenv("CRON_SECRET", "")

        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def twilio_enabled(self) -> bool:
        return self.NUDGE_PROVIDER == "twilio" and bool(self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN)

    def validate(self) -> None:
        if self.JWT_SECRET == _DEV_JWT_SECRET:
            if self.is_production:
                raise RuntimeError("JWT_SECRET must be set when CARA_ENV=production")
            logger.warning("Using the built-in development JWT secret. Set JWT_SECRET outside local development.")
        if self.NUDGE_PROVIDER == "twilio" and not self.twilio_enabled:
            raise RuntimeError("NUDGE_PROVIDER=twilio needs TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
