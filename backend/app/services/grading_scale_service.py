from app.repositories.grading_scale_repository import GradingScaleRepository
from app.schemas.dictionaries import GradingScale


class GradingScaleService:
    def __init__(self, repository: GradingScaleRepository) -> None:
        self._repository = repository

    async def list_scales(self) -> list[GradingScale]:
        return await self._repository.list_all()