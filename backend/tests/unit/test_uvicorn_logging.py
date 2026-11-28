"""Проверка формата первого сообщения Uvicorn после загрузки приложения."""

import json
import subprocess
import sys


def test_uvicorn_startup_message_is_json() -> None:
    code = (
        "import logging, uvicorn; "
        "config = uvicorn.Config('app.main:app'); config.load(); "
        "logging.getLogger('uvicorn.error').info('Started server process [%d]', 123)"
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    record = json.loads(result.stdout.strip())
    assert record["event"] == "Started server process [123]"
    assert record["logger"] == "uvicorn.error"
