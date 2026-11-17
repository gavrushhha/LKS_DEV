"""Клиент сервиса access: проверка прав на ресурс (T10.1)."""

from app.core.config import settings
from app.core.errors import ApiError


class AccessClient:
    async def has_access(self, user_id: str, resource: str, resource_id: str, action: str) -> bool:
        """TODO(T10.1): HTTP-вызов access с кэшем в Redis (TTL 60 с)."""
        if not settings.access_base_url:
            raise ApiError(503, "access_unavailable", "Сервис прав недоступен")
        raise NotImplementedError("T10.1")
