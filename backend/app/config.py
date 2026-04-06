import logging
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("playlist_saver.config")

_INSECURE_JWT_DEFAULTS = {"change-me", "secret", ""}
_INSECURE_ENC_PREFIX = "replace-with"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: Literal["development", "production"] = "development"
    log_level: str = "INFO"
    app_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"

    database_url: str = "postgresql+asyncpg://playlist_saver:playlist_saver@postgres:5432/playlist_saver"
    redis_url: str = "redis://redis:6379/0"
    skip_db_init: bool = False
    db_init_max_retries: int = 20
    db_init_retry_seconds: float = 1.5

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_expiration_minutes: int = 30
    jwt_refresh_expiration_days: int = 7
    encryption_key: str = "replace-with-generated-fernet-key"

    csrf_secret: str = ""

    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8000/api/auth/spotify/callback"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    email_provider: str = "resend"
    email_from: str = "notifications@playlistsaver.local"
    resend_api_key: str = ""

    def validate_production_secrets(self) -> None:
        is_prod = self.environment == "production"
        if self.jwt_secret_key in _INSECURE_JWT_DEFAULTS:
            if is_prod:
                raise ValueError(
                    "JWT_SECRET_KEY must be set to a strong random value in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            logger.warning("JWT_SECRET_KEY is using an insecure default — not suitable for production")

        if self.encryption_key.startswith(_INSECURE_ENC_PREFIX):
            if is_prod:
                raise ValueError(
                    "ENCRYPTION_KEY must be set to a valid Fernet key in production. "
                    "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                )
            logger.warning("ENCRYPTION_KEY is using a placeholder — OAuth tokens will NOT be encrypted")


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.validate_production_secrets()
    return s
