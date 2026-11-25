"""Клиент identity: проверка JWT по JWKS (T10.1)."""

from app.core.config import settings


class IdentityClient:
    def __init__(self) -> None:
        self._jwks: dict[str, object] | None = None

    async def verify_token(self, token: str) -> dict[str, object]:
        """TODO(T10.1): получить JWKS, проверить подпись и срок, вернуть claims."""
        if not settings.identity_jwks_url:
            raise RuntimeError("IDENTITY_JWKS_URL не задан")
        raise NotImplementedError("T10.1")
