"""Зависимости FastAPI: текущий пользователь и проверка ролей."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header

from app.core.config import settings
from app.core.errors import ApiError


@dataclass(frozen=True)
class User:
    id: str
    login: str
    roles: tuple[str, ...]


async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> User:
    """TODO(T10.1): проверка JWT через identity (JWKS) и кэш ролей.

    Пока — заглушка для локальной разработки: при наличии заголовка Authorization
    возвращается тестовый пользователь. В stage и prod заглушка запрещена.
    """
    if settings.app_env in {"stage", "prod"}:
        raise ApiError(503, "authentication_unavailable", "Аутентификация не настроена")
    if not authorization:
        raise ApiError(401, "unauthorized", "Требуется аутентификация")
    # TODO: разбор и валидация токена
    return User(id="dev", login="dev", roles=("methodist",))


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed: str):  # type: ignore[no-untyped-def]
    async def _dep(user: CurrentUser) -> User:
        if not set(allowed) & set(user.roles):
            raise ApiError(
                403,
                "insufficient_scope",
                "Недостаточно прав",
                detail=f"required: {', '.join(allowed)}",
            )
        return user

    return _dep
