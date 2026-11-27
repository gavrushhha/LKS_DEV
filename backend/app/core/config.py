"""Настройки приложения (pydantic-settings)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения и подключений."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["dev", "stage", "prod"] = "dev"
    app_name: str = "lks-education"
    log_level: str = "INFO"

    lks_db_dsn: SecretStr = SecretStr("postgresql+asyncpg://lks:lks@localhost:5432/lks")

    # Источник расписания: только чтение (ТЗ, 2.2)
    tandem_mode: Literal["replica", "snapshot"] = "replica"
    tandem_db_dsn: SecretStr = SecretStr("")
    tandem_pool_min: int = 1
    tandem_pool_max: int = 10
    tandem_statement_timeout_ms: int = 5000
    tandem_budget_rpm: int = 60

    nsi_basic_username: str = ""
    nsi_basic_password: SecretStr = SecretStr("")
    nsi_destination_id: str = "dev_api"

    redis_dsn: SecretStr = SecretStr("redis://localhost:6379/0")
    schedule_cache_ttl_seconds: int = 60

    identity_jwks_url: str = ""
    access_base_url: str = ""
    files_base_url: str = ""

    allowed_period_days: int = Field(default=92, description="Максимальный период выборки расписания")


@lru_cache
def get_settings() -> Settings:
    """Получить настройки приложения."""
    return Settings()


settings = get_settings()
