"""Настройки приложения (pydantic-settings)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", secrets_dir="/run/secrets", extra="ignore"
    )

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

    redis_dsn: SecretStr = SecretStr("redis://localhost:6379/0")
    rabbitmq_dsn: SecretStr = SecretStr("amqp://guest:guest@localhost:5672/")
    schedule_cache_ttl_seconds: int = 60

    identity_jwks_url: str = ""
    access_base_url: str = ""
    files_base_url: str = ""

    allowed_period_days: int = Field(default=92, description="Максимальный период выборки расписания")

    @model_validator(mode="after")
    def validate_environment(self) -> "Settings":
        if self.app_env in {"stage", "prod"}:
            dsn = self.lks_db_dsn.get_secret_value()
            if not dsn or "localhost" in dsn or ":lks@" in dsn:
                raise ValueError("Для stage/prod необходимо настроить LKS_DB_DSN")
        if self.app_env == "prod" and not self.tandem_db_dsn.get_secret_value():
            raise ValueError("Для prod необходимо настроить TANDEM_DB_DSN")
        if self.app_env == "prod" and not self.identity_jwks_url.strip():
            raise ValueError("Для prod необходимо настроить IDENTITY_JWKS_URL")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
