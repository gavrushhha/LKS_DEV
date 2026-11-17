"""Ведомости (ТЗ, раздел 7)."""

from fastapi import APIRouter

router = APIRouter(prefix="/statements", tags=["Statements"])


@router.post("", status_code=201, summary="Сформировать ведомость")
async def create_statement() -> dict[str, object]:
    """TODO(T12.2)."""
    raise NotImplementedError


@router.get("/{statement_id}", summary="Получить ведомость")
async def get_statement(statement_id: str) -> dict[str, object]:
    """TODO(T12.1)."""
    raise NotImplementedError(statement_id)


@router.get("/{statement_id}/pdf", summary="Скачать ведомость в PDF")
async def download_statement_pdf(statement_id: str) -> bytes:
    """TODO(T12.3)."""
    raise NotImplementedError(statement_id)


@router.post("/{statement_id}/close", summary="Закрыть ведомость")
async def close_statement(statement_id: str) -> dict[str, object]:
    """TODO(T12.4): блокировка правок, событие statement.closed."""
    raise NotImplementedError(statement_id)
