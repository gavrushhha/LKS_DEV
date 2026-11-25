"""Общие схемы ответов."""

from pydantic import BaseModel, Field


class PageMeta(BaseModel):
    next_cursor: str | None = None
    total: int | None = None
    limit: int = Field(default=50, ge=1, le=200)


class Ref(BaseModel):
    id: str
    name: str
