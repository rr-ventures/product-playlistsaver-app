from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    jwt_expiration_minutes: int = 1440
    encryption_key: str = "replace-with-generated-fernet-key"

    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_redirect_uri: str = "http://localhost:8000/api/auth/spotify/callback"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    stripe_secret_key: str = "disabled"
    stripe_publishable_key: str = "disabled"
    stripe_webhook_secret: str = "disabled"
    stripe_price_monthly: str = "disabled"
    stripe_price_annual: str = "disabled"
    payments_enabled: bool = False

    email_provider: str = "resend"
    email_from: str = "notifications@playlistsaver.local"
    resend_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
