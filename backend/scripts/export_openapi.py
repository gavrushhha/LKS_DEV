"""Экспорт сгенерированной OpenAPI-схемы для сверки с эталонной (CI)."""

import json
from pathlib import Path

from app.main import app

if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "openapi" / "generated.json"
    out.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written: {out}")
