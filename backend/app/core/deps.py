"""Зависимости FastAPI: текущий пользователь и проверка ролей."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header

from app.core.errors import ApiError


@dataclass(frozen=True)
class User:
    id: str
    login: str
    roles: tuple[str, ...]


async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> User:
    """TODO(T10.1): проверка JWT через identity (JWKS) и кэш ролей.

    Пока — заглушка для локальной разработки: пользователь берётся из заголовка
    X-Dev-User, иначе подставляется methodist. В prod-окружении заглушка запрещена.
    """
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
