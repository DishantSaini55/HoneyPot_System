from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
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
    password_reset_webhook_secret: SecretStr | None = None
    password_reset_webhook_max_age_seconds: int = 300
    auth_rate_limit_window_seconds: int = 900
    login_rate_limit: int = 10
    password_reset_request_rate_limit: int = 5
    password_reset_confirm_rate_limit: int = 10
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

    @model_validator(mode="after")
    def validate_production_webhook(self) -> "Settings":
        if self.environment == "production" and self.password_reset_webhook_url:
            if not self.password_reset_webhook_secret:
                raise ValueError("PASSWORD_RESET_WEBHOOK_SECRET is required for production webhook delivery")
            if not self.password_reset_webhook_url.startswith("https://"):
                raise ValueError("PASSWORD_RESET_WEBHOOK_URL must use HTTPS in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
