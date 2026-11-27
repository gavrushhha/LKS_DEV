"""Локальные справочники расписания; идентификаторы сохраняются как строки."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ScheduleGroup(Base):
    """Академическая группа, полученная из источника."""

    __tablename__ = "schedule_group"
    source_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str | None] = mapped_column(Text)
    short_title: Mapped[str | None] = mapped_column(Text)
    archived: Mapped[bool | None] = mapped_column(Boolean)


class ScheduleRoom(Base):
    """Помещение и идентификатор здания из источника."""

    __tablename__ = "schedule_room"
    source_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    number: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    building_source_id: Mapped[str | None] = mapped_column(String(64))


class ScheduleTeacher(Base):
    """Роль преподавателя и подтверждённые поля человека."""

    __tablename__ = "schedule_teacher"
    source_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    role_guid: Mapped[str | None] = mapped_column(String(64))
    last_name: Mapped[str | None] = mapped_column(Text)
    first_name: Mapped[str | None] = mapped_column(Text)
    middle_name: Mapped[str | None] = mapped_column(Text)
    removal_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))


class ScheduleDiscipline(Base):
    """Дисциплина реестра, связанная с таблицей дисциплин источника."""

    __tablename__ = "schedule_discipline"
    source_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str | None] = mapped_column(Text)
    number: Mapped[str | None] = mapped_column(Text)
    user_code: Mapped[str | None] = mapped_column(Text)
    source_guid: Mapped[str | None] = mapped_column(String(64))
