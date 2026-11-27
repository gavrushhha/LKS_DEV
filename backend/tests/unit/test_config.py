"""Проверка защиты настроек для рабочих окружений."""

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings


def test_stage_rejects_local_development_dsn() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="stage", _env_file=None)


def test_prod_requires_tandem_dsn() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="prod",
            lks_db_dsn=SecretStr("postgresql+asyncpg://user:password@database/lks"),
            tandem_db_dsn=SecretStr(""),
            _env_file=None,
        )


def test_secret_is_masked() -> None:
    settings = Settings(lks_db_dsn=SecretStr("postgresql+asyncpg://user:password@database/lks"))
    assert "password" not in repr(settings)


def test_prod_requires_identity_url() -> None:
    with pytest.raises(ValidationError, match="IDENTITY_JWKS_URL"):
        Settings(
            app_env="prod",
            lks_db_dsn=SecretStr("postgresql+asyncpg://user:password@database/lks"),
            tandem_db_dsn=SecretStr("postgresql+asyncpg://user:password@source/tandem"),
            identity_jwks_url="",
            _env_file=None,
        )


def test_docs_disabled_in_production() -> None:
    import os
    import subprocess
    import sys

    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "prod",
            "LKS_DB_DSN": "postgresql+asyncpg://user:test@database/lks",
            "TANDEM_DB_DSN": "postgresql+asyncpg://readonly:test@source/tandem",
            "IDENTITY_JWKS_URL": "https://identity.example/.well-known/jwks.json",
        }
    )
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-c",
            "from app.main import app; assert app.docs_url is None and app.openapi_url is None",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
