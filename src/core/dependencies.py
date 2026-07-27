from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.session import DatabaseAdapter


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    db: DatabaseAdapter = request.app.state.db
    async for session in db.session():
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
