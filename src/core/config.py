from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"  # подстройте parents[*], если структура иная


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(default="<API_KEY_PLACEHOLDER>", alias="API_KEY")

    database_url: str = Field(
        default="postgresql+asyncpg://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>",
        alias="DATABASE_URL",
    )


settings = Settings()
