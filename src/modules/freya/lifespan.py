from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.config import get_settings
from src.core.database.base import Base
from src.core.logger import get_logger
from src.modules.freya.infrastructure.adapters import FreyaAdapter
from src.modules.freya.infrastructure.models import TransactionModel

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def freya_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if settings.freya is None:
        logger.info("Freya integration is disabled — skipping initialization")
        yield
        return

    async with app.state.db.engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[TransactionModel.__table__],  # type: ignore[arg-type]
            )
        )
    logger.info("Freya table ensured in database")

    adapter = FreyaAdapter.build(
        settings.freya.base_url,
        settings.freya.username,
        settings.freya.password,
        settings.freya.timeout,
    )
    app.state.freya = adapter
    logger.info("Freya adapter started")
    try:
        yield
    finally:
        await adapter.stop()
        logger.info("Freya adapter stopped")
