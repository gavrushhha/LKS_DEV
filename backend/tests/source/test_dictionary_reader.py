from unittest.mock import AsyncMock

import pytest

from app.source.tandem import queries
from app.source.tandem.client import TandemClient
from app.source.tandem.dictionary_reader import Group, RegistryElement, Room, TandemDictionaryReader, Teacher


async def test_group_by_id_returns_group_with_source_id():
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = [{"id": 123, "title_p": "ИТ-1", "shorttitle_p": None, "archival_p": False}]
    result = await TandemDictionaryReader(client).group_by_id(123)
    assert result == Group("123", "ИТ-1", None, False)
    client.fetch.assert_awaited_once_with(queries.GROUP_BY_ID, 123)


async def test_room_by_id_allows_missing_building():
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = [{"id": 456, "number_p": "101", "title_p": None, "cachedbuilding_id": None}]
    assert await TandemDictionaryReader(client).room_by_id(456) == Room("456", "101", None, None)


@pytest.mark.parametrize("method", ["group_by_id", "room_by_id"])
async def test_not_found_and_invalid_ids(method):
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = []
    reader = TandemDictionaryReader(client)
    fn = getattr(reader, method)
    assert await fn(1) is None
    client.fetch.reset_mock()
    for invalid in (0, -1, True, 2**63):
        with pytest.raises(ValueError):
            await fn(invalid)
    client.fetch.assert_not_awaited()


async def test_groups_page_passes_cursor_and_limit():
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = [{"id": 123, "title_p": "ИТ-1", "shorttitle_p": None, "archival_p": False}]
    assert await TandemDictionaryReader(client).groups_page(after_id=100, limit=20) == [
        Group("123", "ИТ-1", None, False)
    ]
    client.fetch.assert_awaited_once_with(queries.GROUPS_PAGE, 100, 20)


async def test_rooms_page_preserves_building_id():
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = [{"id": 456, "number_p": "101", "title_p": None, "cachedbuilding_id": 789}]
    assert await TandemDictionaryReader(client).rooms_page() == [Room("456", "101", None, "789")]
    client.fetch.assert_awaited_once_with(queries.ROOMS_PAGE, None, 100)


@pytest.mark.parametrize("method", ["groups_page", "rooms_page"])
async def test_pages_reject_invalid_input_without_query(method):
    client = AsyncMock(spec=TandemClient)
    fn = getattr(TandemDictionaryReader(client), method)
    for kwargs in ({"after_id": 0}, {"limit": 201}, {"limit": True}):
        with pytest.raises(ValueError):
            await fn(**kwargs)
    client.fetch.assert_not_awaited()


async def test_teacher_by_id_returns_separate_name_parts_and_role_guid():
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = [
        {
            "id": 123,
            "guid_p": "test-guid",
            "lastname_p": "Иванов",
            "firstname_p": "Иван",
            "middlename_p": None,
            "removaldate_p": None,
        }
    ]
    result = await TandemDictionaryReader(client).teacher_by_id(123)
    assert result == Teacher("123", "test-guid", "Иванов", "Иван", None, None)
    client.fetch.assert_awaited_once_with(queries.TEACHER_BY_ID, 123)


async def test_teachers_page_keeps_missing_names():
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = [
        {
            "id": 1,
            "guid_p": None,
            "lastname_p": None,
            "firstname_p": None,
            "middlename_p": None,
            "removaldate_p": None,
        }
    ]
    result = await TandemDictionaryReader(client).teachers_page(limit=5)
    assert result == [Teacher("1", None, None, None, None, None)]
    client.fetch.assert_awaited_once_with(queries.TEACHERS_PAGE, None, 5)


async def test_teachers_by_name_returns_all_matches_and_passes_parameters():
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = [
        {
            "id": 1,
            "guid_p": None,
            "lastname_p": "Иванов",
            "firstname_p": "Иван",
            "middlename_p": None,
            "removaldate_p": None,
        },
        {
            "id": 2,
            "guid_p": None,
            "lastname_p": "Иванов",
            "firstname_p": "Иван",
            "middlename_p": "Иванович",
            "removaldate_p": None,
        },
    ]
    result = await TandemDictionaryReader(client).teachers_by_name(" Иван ", " Иванов ", limit=2)
    assert [teacher.id for teacher in result] == ["1", "2"]
    client.fetch.assert_awaited_once_with(queries.TEACHERS_BY_NAME, "Иван", "Иванов", None, 2)


async def test_teachers_by_name_rejects_blank_name_without_query():
    client = AsyncMock(spec=TandemClient)
    with pytest.raises(ValueError):
        await TandemDictionaryReader(client).teachers_by_name(" ", "Иванов")
    client.fetch.assert_not_awaited()


async def test_registry_page_preserves_distinct_source_codes():
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = [
        {"id": 7, "title_p": "Математика", "number_p": "01", "usercode_p": "МАТ", "guid_p": None}
    ]
    result = await TandemDictionaryReader(client).registry_elements_page(after_id=2, limit=10)
    assert result == [RegistryElement("7", "Математика", "01", "МАТ", None)]
    client.fetch.assert_awaited_once_with(queries.REGISTRY_ELEMENTS_PAGE, 2, 10)


async def test_registry_page_rejects_invalid_limit_without_query():
    client = AsyncMock(spec=TandemClient)
    with pytest.raises(ValueError):
        await TandemDictionaryReader(client).registry_elements_page(limit=0)
    client.fetch.assert_not_awaited()


async def test_disciplines_page_uses_discipline_query_and_keeps_both_codes():
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = [
        {"id": 7, "title_p": "Математика", "number_p": "01", "usercode_p": "МАТ", "guid_p": None}
    ]
    result = await TandemDictionaryReader(client).disciplines_page(after_id=2, limit=10)
    assert result == [RegistryElement("7", "Математика", "01", "МАТ", None)]
    client.fetch.assert_awaited_once_with(queries.DISCIPLINES_PAGE, 2, 10)


async def test_disciplines_page_rejects_invalid_cursor():
    client = AsyncMock(spec=TandemClient)
    with pytest.raises(ValueError):
        await TandemDictionaryReader(client).disciplines_page(after_id=0)
    client.fetch.assert_not_awaited()


async def test_disciplines_by_title_passes_literal_search_and_cursor():
    client = AsyncMock(spec=TandemClient)
    client.fetch.return_value = [
        {"id": 7, "title_p": "Математика", "number_p": "01", "usercode_p": "МАТ", "guid_p": None}
    ]
    result = await TandemDictionaryReader(client).disciplines_by_title(" мат ", after_id=2, limit=10)
    assert result == [RegistryElement("7", "Математика", "01", "МАТ", None)]
    client.fetch.assert_awaited_once_with(queries.DISCIPLINES_BY_TITLE, "мат", 2, 10)


async def test_disciplines_by_title_rejects_empty_query():
    client = AsyncMock(spec=TandemClient)
    with pytest.raises(ValueError):
        await TandemDictionaryReader(client).disciplines_by_title("   ")
    client.fetch.assert_not_awaited()
