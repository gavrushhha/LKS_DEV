"""Базовый класс моделей."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Все модели ЛКС наследуются от этого класса."""
