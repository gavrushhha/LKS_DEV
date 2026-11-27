"""Проверки постраничного чтения локальных справочников."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.schedule_dictionary import ScheduleDiscipline, ScheduleGroup, ScheduleRoom, ScheduleTeacher
from app.services.dictionary_read import read_dictionary_item, read_dictionary_page


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    for model in (ScheduleGroup, ScheduleRoom, ScheduleTeacher, ScheduleDiscipline):
        model.__table__.create(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


class Adapter:
    def __init__(self, session):
        self.session = session

    async def scalars(self, statement):
        return self.session.scalars(statement)

    async def get(self, model, source_id):
        return self.session.get(model, source_id)


async def test_pages_use_stable_string_id_and_do_not_omit_entries(db):
    db.add_all([ScheduleGroup(source_id="10"), ScheduleGroup(source_id="2"), ScheduleGroup(source_id="30")])
    db.commit()
    first, cursor = await read_dictionary_page(Adapter(db), "group", limit=2)
    second, last_cursor = await read_dictionary_page(Adapter(db), "group", after_id=cursor, limit=2)
    assert [x.source_id for x in first] == ["10", "2"]
    assert [x.source_id for x in second] == ["30"]
    assert cursor == "2" and last_cursor is None


@pytest.mark.parametrize(
    "kind,model", [("room", ScheduleRoom), ("teacher", ScheduleTeacher), ("discipline", ScheduleDiscipline)]
)
async def test_each_dictionary_reads_its_own_table(db, kind, model):
    db.add(model(source_id="123"))
    db.commit()
    page, cursor = await read_dictionary_page(Adapter(db), kind)
    assert len(page) == 1 and page[0].source_id == "123" and cursor is None


async def test_invalid_arguments_rejected_before_query():
    class NeverQuery:
        async def scalars(self, statement):
            raise AssertionError("Запрос не должен выполняться")

    for kwargs in ({"limit": 0}, {"limit": 201}, {"after_id": ""}):
        with pytest.raises(ValueError):
            await read_dictionary_page(NeverQuery(), "group", **kwargs)


async def test_find_dictionary_item_or_missing(db):
    db.add(ScheduleRoom(source_id="12", number="101"))
    db.commit()
    room = await read_dictionary_item(Adapter(db), "room", "12")
    assert room is not None and room.number == "101"
    assert await read_dictionary_item(Adapter(db), "room", "13") is None
