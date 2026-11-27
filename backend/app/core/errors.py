"""Единый формат ошибок: RFC 9457 (application/problem+json)."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_CONTENT_TYPE = "application/problem+json"


class ProblemError(BaseModel):
    field: str | None = None
    message: str | None = None
    code: str | None = None


class Problem(BaseModel):
    type: str
    title: str
    status: int
    code: str
    detail: str | None = None
    instance: str | None = None
    trace_id: str | None = None
    errors: list[ProblemError] | None = None
    checks: dict[str, str] | None = None


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
    trace_id: str | None = None,
    checks: dict[str, str] | None = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "type": f"https://api.lks.local/errors/{code.replace('_', '-')}",
        "title": title,
        "status": status_code,
        "code": code,
    }
    if trace_id:
        payload["trace_id"] = trace_id
    if checks is not None:
        payload["checks"] = checks
    if detail:
        payload["detail"] = detail
    if errors:
        payload["errors"] = errors
    return JSONResponse(status_code=status_code, content=payload, media_type=PROBLEM_CONTENT_TYPE)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        return problem_response(
            exc.status_code,
            exc.code,
            exc.title,
            exc.detail,
            exc.errors,
            trace_id=getattr(request.state, "trace_id", None),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        problems = {
            400: ("bad_request", "Неверный запрос"),
            401: ("unauthorized", "Требуется аутентификация"),
            403: ("forbidden", "Доступ запрещён"),
            404: ("not_found", "Ресурс не найден"),
            405: ("method_not_allowed", "Метод не разрешён"),
            429: ("too_many_requests", "Слишком много запросов"),
        }
        code, title = problems.get(exc.status_code, ("http_error", "Ошибка запроса"))
        response = problem_response(
            exc.status_code,
            code,
            title,
            detail=str(exc.detail),
            trace_id=getattr(request.state, "trace_id", None),
        )
        if exc.headers:
            response.headers.update(exc.headers)
        return response

    @app.exception_handler(NotImplementedError)
    async def _not_implemented(request: Request, exc: NotImplementedError) -> JSONResponse:
        return problem_response(
            status.HTTP_501_NOT_IMPLEMENTED,
            "not_implemented",
            "Операция ещё не реализована",
            detail=str(exc) or None,
            trace_id=getattr(request.state, "trace_id", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        return problem_response(
            status.HTTP_400_BAD_REQUEST,
            "validation_error",
            "Ошибка валидации",
            trace_id=getattr(request.state, "trace_id", None),
            errors=[
                {"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"], "code": e["type"]}
                for e in exc.errors()
            ],
        )
