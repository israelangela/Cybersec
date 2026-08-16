from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://cybersec:cybersec_dev_password@localhost:5432/cybersec"
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    collector_scheduler_enabled: bool = False
    collector_interval_minutes: int = 30
    collector_request_timeout_seconds: float = 20.0
    collector_max_response_bytes: int = 5_000_000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
