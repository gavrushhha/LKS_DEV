"""Страж: в слое источника нет операций записи (ТЗ, 2.2 и 5.6).

Тест ломается, если в app/source/ появится INSERT/UPDATE/DELETE.
Это блокирующее требование: ЛКС не пишет в БД Тандема.
"""

import ast
import re
from pathlib import Path

FORBIDDEN = re.compile(r"\b(insert|update|delete|truncate|merge|alter)\b", re.IGNORECASE)
SOURCE_DIR = Path(__file__).resolve().parents[2] / "app" / "source"


def _docstring_lines(tree: ast.AST) -> set[int]:
    """Строки, занятые докстрингами: их не проверяем (там текст, а не SQL)."""
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        body = getattr(node, "body", [])
        value = body[0].value if body else None
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            start = body[0].lineno
            end = body[0].end_lineno or start
            lines.update(range(start, end + 1))
    return lines


def test_source_layer_has_no_write_statements() -> None:
    offenders: list[str] = []
    for path in SOURCE_DIR.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        skip = _docstring_lines(ast.parse(source))
        for lineno, line in enumerate(source.splitlines(), 1):
            if lineno in skip or line.strip().startswith("#"):
                continue
            if FORBIDDEN.search(line):
                offenders.append(f"{path.name}:{lineno}: {line.strip()[:80]}")
    assert not offenders, "В слое source найдены операции записи:\n" + "\n".join(offenders)


def test_guard_catches_real_write() -> None:
    """Самопроверка стража: строка записи действительно детектируется."""
    assert FORBIDDEN.search("INSERT INTO schedule_entry VALUES (1)")
