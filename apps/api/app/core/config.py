from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://honeypot:honeypot@postgres:5432/honeypot"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: SecretStr = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    password_reset_minutes: int = 30
    password_reset_webhook_url: str | None = None
    sensor_api_key: SecretStr = Field(min_length=24)
    bootstrap_admin_email: str | None = None
    cors_origins: str = "http://localhost:3000"
    max_event_body_bytes: int = 262_144
    ingestion_rate_limit_per_minute: int = 600
    threat_intel_provider_url: str | None = None
    threat_intel_api_key: SecretStr | None = None
    threat_intel_timeout_seconds: float = 3.0
    ai_provider_url: str | None = None
    ai_api_key: SecretStr | None = None
    ai_model: str | None = None
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
