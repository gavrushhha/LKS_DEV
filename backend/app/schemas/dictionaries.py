"""Формат записи справочника."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, StrictStr

DictionaryKind = Literal["groups", "teachers", "rooms"]


class DictionaryItem(BaseModel):
    id: UUID
    code: StrictStr | None = None
    name: StrictStr
    source_system: StrictStr
    extra: dict[str, object] = Field(default_factory=dict)
