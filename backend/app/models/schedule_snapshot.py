"""Локальные снимки расписания в БД ЛКС; не модели БД Тандема."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ScheduleSnapshot(Base):
    """Одна попытка загрузки расписания для определённой области."""

    __tablename__ = "schedule_snapshot"
    __table_args__ = (
        CheckConstraint("status IN ('loading', 'ready', 'failed')", name="ck_schedule_snapshot_status"),
        UniqueConstraint("scope", "id", name="uq_schedule_snapshot_scope_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SnapshotScheduleEntry(Base):
    """Занятие в одной версии снимка; ID источника хранится без преобразования."""

    __tablename__ = "snapshot_schedule_entry"
    __table_args__ = (
        CheckConstraint("start_minutes IS NULL OR start_minutes BETWEEN 0 AND 1439", name="ck_entry_start"),
        CheckConstraint("end_minutes IS NULL OR end_minutes BETWEEN 0 AND 1439", name="ck_entry_end"),
        Index("ix_snapshot_entry_date", "snapshot_id", "lesson_date", "source_id"),
    )

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schedule_snapshot.id", ondelete="CASCADE"), primary_key=True
    )
    source_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lesson_date: Mapped[date] = mapped_column(Date, nullable=False)
    pair_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activity: Mapped[str | None] = mapped_column(String(255), nullable=True)
    place: Mapped[str | None] = mapped_column(String(255), nullable=True)
    teachers: Mapped[str | None] = mapped_column(String(255), nullable=True)
    groups: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)


class ActiveScheduleSnapshot(Base):
    """Указатель на активный снимок конкретной области."""

    __tablename__ = "active_schedule_snapshot"
    __table_args__ = (
        ForeignKeyConstraint(
            ["scope", "snapshot_id"],
            ["schedule_snapshot.scope", "schedule_snapshot.id"],
            name="fk_active_snapshot_scope",
            ondelete="RESTRICT",
        ),
    )

    scope: Mapped[str] = mapped_column(String(255), primary_key=True)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)


class SnapshotEntryTeacher(Base):
    """Связь занятия снимка с ID роли преподавателя в Тандеме."""

    __tablename__ = "snapshot_entry_teacher"
    __table_args__ = (
        ForeignKeyConstraint(
            ["snapshot_id", "entry_id"],
            ["snapshot_schedule_entry.snapshot_id", "snapshot_schedule_entry.source_id"],
            ondelete="CASCADE",
        ),
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    entry_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    teacher_id: Mapped[str] = mapped_column(String(64), primary_key=True)


class SnapshotEntryRoom(Base):
    """Связь занятия снимка с ID помещения в Тандеме."""

    __tablename__ = "snapshot_entry_room"
    __table_args__ = (
        ForeignKeyConstraint(
            ["snapshot_id", "entry_id"],
            ["snapshot_schedule_entry.snapshot_id", "snapshot_schedule_entry.source_id"],
            ondelete="CASCADE",
        ),
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    entry_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    room_id: Mapped[str] = mapped_column(String(64), primary_key=True)


class SnapshotEntryStudyGroup(Base):
    """Связь занятия с учебной группой Тандема; это не академическая группа."""

    __tablename__ = "snapshot_entry_study_group"
    __table_args__ = (
        ForeignKeyConstraint(
            ["snapshot_id", "entry_id"],
            ["snapshot_schedule_entry.snapshot_id", "snapshot_schedule_entry.source_id"],
            ondelete="CASCADE",
        ),
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    entry_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_group_id: Mapped[str] = mapped_column(String(64), primary_key=True)


class SnapshotEntryDiscipline(Base):
    """Связь занятия снимка с дисциплиной реестра источника."""

    __tablename__ = "snapshot_entry_discipline"
    __table_args__ = (
        ForeignKeyConstraint(
            ["snapshot_id", "entry_id"],
            ["snapshot_schedule_entry.snapshot_id", "snapshot_schedule_entry.source_id"],
            ondelete="CASCADE",
        ),
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    entry_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    discipline_id: Mapped[str] = mapped_column(String(64), primary_key=True)
