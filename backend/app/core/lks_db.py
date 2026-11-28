from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

lks_engine = create_async_engine(settings.lks_db_dsn)
_session_factory = async_sessionmaker(lks_engine)


async def get_lks_session() -> AsyncIterator[AsyncSession]:
    async with _session_factory() as session:
        yield session


LksSessionDep = Annotated[AsyncSession, Depends(get_lks_session)]
