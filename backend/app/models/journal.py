"""Модели журнала (ТЗ, 4.2). Реализация — T6.1.

Черновик описан полями, миграции создаются в T6.1.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Offering(Base):
    __tablename__ = "offering"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curriculum_unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    grading_scale_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


class Lesson(Base):
    __tablename__ = "lesson"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offering_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("offering.id"))
    schedule_entry_external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    date: Mapped[date] = mapped_column(Date)
    pair_number: Mapped[int]
    lesson_type: Mapped[str] = mapped_column(String(32))
    topic: Mapped[str | None] = mapped_column(String(500), nullable=True)
    homework: Mapped[str | None] = mapped_column(String(5000), nullable=True)
    extra: Mapped[bool] = mapped_column(default=False)


class Grade(Base):
    __tablename__ = "grade"
    __table_args__ = (UniqueConstraint("offering_id", "student_id", "lesson_id", "grade_type"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offering_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("offering.id"))
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("lesson.id"), nullable=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    value: Mapped[str] = mapped_column(String(10))
    grade_type: Mapped[str] = mapped_column(String(32))
    weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1.0)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
