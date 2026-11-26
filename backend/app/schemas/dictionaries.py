"""Формат записи справочника."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, StrictStr
from pydantic.json_schema import SkipJsonSchema

DictionaryKind = Literal["groups", "teachers", "rooms"]


class DictionaryItem(BaseModel):
    id: UUID
    # Старый кэш может содержать null, но HTTP-ответ опускает это поле.
    code: StrictStr | SkipJsonSchema[None] = Field(default_factory=lambda: None)
    name: StrictStr
    source_system: StrictStr
    extra: dict[str, object] = Field(default_factory=dict)


class BrsThreshold(BaseModel):
    min_points: float
    grade: str


class GradingScale(BaseModel):
    id: UUID
    name: str
    values: list[str]
    pass_value: str | None = None
    brs_thresholds: list[BrsThreshold] | None = None
