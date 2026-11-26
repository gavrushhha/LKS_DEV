from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.dictionaries import GradingScale

_LIST_GRADING_SCALES = text("""
    SELECT id, name, "values", pass_value, brs_thresholds
    FROM education.grading_scale
    ORDER BY name, id
""")


class GradingScaleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[GradingScale]:
        result = await self._session.execute(_LIST_GRADING_SCALES)

        scales: list[GradingScale] = []
        for row in result.mappings():
            scale = GradingScale.model_validate(dict(row))
            scales.append(scale)

        return scales
