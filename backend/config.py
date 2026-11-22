"""Application configuration, read from environment variables (.env in dev)."""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """Raised when a required setting is missing or unsafe."""


def load_config():
    database_url = os.environ.get("DATABASE_URL")
    jwt_secret = os.environ.get("JWT_SECRET")

    if not database_url:
        raise ConfigError("DATABASE_URL is not set")
    if not jwt_secret or len(jwt_secret) < 32:
        raise ConfigError("JWT_SECRET must be set and at least 32 characters long")

    return {
        "SQLALCHEMY_DATABASE_URI": database_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {"pool_pre_ping": True},
        "JWT_SECRET_KEY": jwt_secret,
        "JWT_ACCESS_TOKEN_EXPIRES": timedelta(
            hours=int(os.environ.get("JWT_EXPIRES_HOURS", "12"))
        ),
        "SAMPLE_INTERVAL_SECONDS": int(os.environ.get("SAMPLE_INTERVAL_SECONDS", "10")),
        "RETENTION_DAYS": int(os.environ.get("RETENTION_DAYS", "7")),
        "START_COLLECTOR": True,
    }
