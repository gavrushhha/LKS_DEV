from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.schedule_dictionary import ScheduleDiscipline, ScheduleGroup, ScheduleRoom, ScheduleTeacher
from app.services.schedule_dictionary import save_schedule_dictionary_item, save_schedule_discipline
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
