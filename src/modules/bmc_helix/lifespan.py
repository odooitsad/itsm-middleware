from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.config import get_settings
from src.core.database.base import Base
from src.core.logger import get_logger
from src.modules.bmc_helix.infrastructure.adapters import BmcHelixAdapter
from src.modules.bmc_helix.infrastructure.models import TransactionModel

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def bmc_helix_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if settings.bmc_helix is None:
        logger.info("BMC Helix integration is disabled — skipping initialization")
        yield
        return

    async with app.state.db.engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn,
                tables=[TransactionModel.__table__],  # type: ignore[arg-type]
            )
        )
    logger.info("BMC Helix table ensured")

    adapter = BmcHelixAdapter.build(
        settings.bmc_helix.base_url,
        settings.bmc_helix.username,
        settings.bmc_helix.password,
        settings.bmc_helix.timeout,
    )
    app.state.bmc_helix = adapter
    logger.info("BMC Helix adapter started")
    try:
        yield
    finally:
        await adapter.stop()
        logger.info("BMC Helix adapter stopped")
