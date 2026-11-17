"""Единый формат ошибок: RFC 9457 (application/problem+json)."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

PROBLEM_CONTENT_TYPE = "application/problem+json"


class ApiError(Exception):
    """Доменная ошибка с машиночитаемым кодом (ТЗ, 3.4)."""

    def __init__(
        self,
        status_code: int,
        code: str,
        title: str,
        detail: str | None = None,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.title = title
        self.detail = detail
        self.errors = errors or []


def problem_response(
    status_code: int,
    code: str,
    title: str,
    detail: str | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "type": f"https://api.lks.local/errors/{code.replace('_', '-')}",
        "title": title,
        "status": status_code,
        "code": code,
    }
    if detail:
        payload["detail"] = detail
    if errors:
        payload["errors"] = errors
    return JSONResponse(status_code=status_code, content=payload, media_type=PROBLEM_CONTENT_TYPE)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return problem_response(exc.status_code, exc.code, exc.title, exc.detail, exc.errors)

    @app.exception_handler(NotImplementedError)
    async def _not_implemented(_: Request, exc: NotImplementedError) -> JSONResponse:
        return problem_response(
            status.HTTP_501_NOT_IMPLEMENTED,
            "not_implemented",
            "Операция ещё не реализована",
            detail=str(exc) or None,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return problem_response(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "Ошибка валидации",
            errors=[
                {"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"], "code": e["type"]}
                for e in exc.errors()
            ],
        )
