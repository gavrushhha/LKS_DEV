"""Проверка подключения клиента к тестовому источнику Тандема только чтением."""

import os

import pytest
from pydantic import SecretStr

from app.core.config import settings
from app.source.tandem.client import TandemClient

pytestmark = pytest.mark.integration

_DSN = os.environ.get("TANDEM_INTEGRATION_TEST_DSN", "")


@pytest.mark.skipif(not _DSN, reason="Не задан TANDEM_INTEGRATION_TEST_DSN для интеграционной проверки")
async def test_real_connection_is_read_only(monkeypatch):
    """Проверить настройки реальной транзакции и доступ к таблицам без записи."""
    monkeypatch.setattr(settings, "tandem_db_dsn", SecretStr(_DSN))
    client = TandemClient()
    try:
        await client.connect()
        rows = await client.fetch(
            """
            SELECT current_setting('transaction_read_only') = 'on' AS read_only,
                   current_setting('transaction_isolation') = 'read committed' AS read_committed,
                   current_setting('statement_timeout')::interval > interval '0 seconds'
                     AND current_setting('statement_timeout')::interval <= interval '5 seconds' AS timeout_ok,
                   pg_is_in_recovery() AS is_replica
            """
        )
        assert len(rows) == 1
        assert rows[0]["read_only"] is True
        assert rows[0]["read_committed"] is True
        assert rows[0]["timeout_ok"] is True

        tables = [
            "ttevent_t",
            "timetableversion_t",
            "sc_bell_entry",
            "ttevent2pps_t",
            "ttevent2place_t",
            "ttevent2realedugroup_t",
            "epp_rgrp_row_t",
            "student_t",
            "group_t",
            "places_place",
            "places_building",
            "pps_entry_base_t",
            "personrole_t",
            "person_t",
            "identitycard_t",
            "epp_reg_base_t",
            "epp_reg_discipline_t",
            "epp_real_edu_group_t",
            "epp_reg_element_part_t",
        ]
        grants = await client.fetch(
            """
            SELECT name,
                   has_table_privilege(to_regclass(format('public.%I', name)), 'SELECT') AS can_read,
                   has_table_privilege(to_regclass(format('public.%I', name)),
                       'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER,REFERENCES') AS can_write,
                   has_any_column_privilege(to_regclass(format('public.%I', name)),
                       'INSERT,UPDATE,REFERENCES') AS can_write_columns
            FROM unnest($1::text[]) AS names(name)
            """,
            tables,
        )
        assert len(grants) == len(tables)
        for row in grants:
            assert row["can_read"] is True, f"Нет SELECT или отсутствует таблица: {row['name']}"
            assert row["can_write"] is False, f"Есть права изменения таблицы: {row['name']}"
            assert row["can_write_columns"] is False, f"Есть права изменения столбцов: {row['name']}"

        schema = await client.fetch(
            """
            SELECT has_schema_privilege('public', 'CREATE') AS schema_create,
                   (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'public' AND CASE
                      WHEN c.relkind IN ('r','p','v','m','f') THEN
                        has_table_privilege(c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,TRIGGER,REFERENCES')
                        OR has_any_column_privilege(c.oid, 'INSERT,UPDATE,REFERENCES')
                      ELSE false END) AS writable_relations,
                   (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'public' AND CASE
                      WHEN c.relkind = 'S' THEN has_sequence_privilege(c.oid, 'USAGE,UPDATE')
                      ELSE false END) AS writable_sequences
            """
        )
        assert len(schema) == 1
        assert schema[0]["schema_create"] is False
        assert schema[0]["writable_relations"] == 0
        assert schema[0]["writable_sequences"] == 0
    finally:
        await client.close()
