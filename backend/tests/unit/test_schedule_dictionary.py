"""Проверки сохранения и ограниченной загрузки справочников расписания."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.schedule_dictionary import ScheduleDiscipline, ScheduleGroup, ScheduleRoom, ScheduleTeacher
from app.services.schedule_dictionary import (
    DictionarySyncError,
    save_schedule_dictionary_item,
    save_schedule_discipline,
    sync_dictionary_batch,
    sync_dictionary_page,
)
from app.source.tandem.dictionary_reader import Group, RegistryElement, Room, Teacher


async def test_dictionary_records_are_saved_and_updated():
    engine = create_engine("sqlite:///:memory:")
    for table in (
        ScheduleGroup.__table__,
        ScheduleRoom.__table__,
        ScheduleTeacher.__table__,
        ScheduleDiscipline.__table__,
    ):
        table.create(engine)
    with Session(engine) as db:

        class Adapter:
            async def merge(self, obj):
                return db.merge(obj)

        adapter = Adapter()
        await save_schedule_dictionary_item(adapter, Group("1", "Группа", None, False))
        await save_schedule_dictionary_item(adapter, Room("2", "101", None, "7"))
        await save_schedule_dictionary_item(adapter, Teacher("3", None, "Иванов", None, None, None))
        await save_schedule_discipline(adapter, RegistryElement("4", "Математика", None, None, None))
        db.flush()
        await save_schedule_dictionary_item(adapter, Group("1", "Новое название", None, False))
        db.flush()
        assert db.get(ScheduleGroup, "1").title == "Новое название"
        assert db.get(ScheduleRoom, "2").building_source_id == "7"
        assert db.get(ScheduleTeacher, "3").last_name == "Иванов"
        assert db.get(ScheduleDiscipline, "4").title == "Математика"
        assert db.query(ScheduleGroup).count() == 1
    engine.dispose()


async def test_sync_page_persists_and_returns_cursor():
    engine = create_engine("sqlite:///:memory:")
    ScheduleGroup.__table__.create(engine)
    with Session(engine) as db:

        class Adapter:
            @asynccontextmanager
            async def begin(self):
                with db.begin():
                    yield

            async def merge(self, obj):
                return db.merge(obj)

        reader = AsyncMock()
        reader.groups_page.return_value = [Group("10", "А", None, False), Group("11", "Б", None, False)]
        result = await sync_dictionary_page(reader, Adapter(), "group", after_id=9, limit=2)
        assert result == (2, 11)
        assert db.get(ScheduleGroup, "10").title == "А"
        reader.groups_page.assert_awaited_once_with(after_id=9, limit=2)
    engine.dispose()


async def test_invalid_page_is_not_saved():
    reader, session = AsyncMock(), AsyncMock()
    reader.groups_page.return_value = [Group("10", "А", None, False), Group("10", "Б", None, False)]
    with pytest.raises(ValueError):
        await sync_dictionary_page(reader, session, "group", limit=2)
    session.begin.assert_not_called()


async def test_batch_stops_at_page_limit_and_preserves_cursor(monkeypatch):
    page = AsyncMock(side_effect=[(2, 10), (2, 20)])
    monkeypatch.setattr("app.services.schedule_dictionary.sync_dictionary_page", page)
    progress = await sync_dictionary_batch(AsyncMock(), AsyncMock(), "group", page_size=2, max_pages=2)
    assert (progress.pages, progress.records, progress.next_after_id, progress.complete) == (2, 4, 20, False)
    assert page.await_args_list[1].kwargs["after_id"] == 10


async def test_batch_finishes_on_short_page(monkeypatch):
    page = AsyncMock(side_effect=[(2, 10), (1, None)])
    monkeypatch.setattr("app.services.schedule_dictionary.sync_dictionary_page", page)
    progress = await sync_dictionary_batch(AsyncMock(), AsyncMock(), "group", page_size=2)
    assert (progress.pages, progress.records, progress.next_after_id, progress.complete) == (2, 3, None, True)


async def test_batch_failure_reports_last_saved_cursor(monkeypatch):
    page = AsyncMock(side_effect=[(2, 10), RuntimeError("database error")])
    monkeypatch.setattr("app.services.schedule_dictionary.sync_dictionary_page", page)
    with pytest.raises(DictionarySyncError) as exc:
        await sync_dictionary_batch(AsyncMock(), AsyncMock(), "group", page_size=2)
    assert (exc.value.progress.pages, exc.value.progress.records, exc.value.progress.next_after_id) == (
        1,
        2,
        10,
    )
    assert isinstance(exc.value.__cause__, RuntimeError)
