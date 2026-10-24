from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "detection-agent"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"

    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-5.5"

    database_url: str = "sqlite+aiosqlite:///./discovery.db"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
