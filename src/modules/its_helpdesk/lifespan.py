from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.config import get_settings
from src.core.database.base import Base
from src.core.logger import get_logger
from src.modules.its_helpdesk.infrastructure.adapters import ItsHelpdeskAdapter
from src.modules.its_helpdesk.infrastructure.models import TicketTransactionModel

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def its_helpdesk_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if settings.its_helpdesk is None:
        logger.info("ITS Helpdesk integration is disabled — skipping initialization")
        yield
        return

    async with app.state.db.engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: Base.metadata.create_all(
                sync_conn, tables=[TicketTransactionModel.__table__]
            )
        )
    logger.info("ITS Helpdesk table ensured")

    # TODO: Verify SSL depends on DEBUG?
    verify_ssl = False
    adapter = ItsHelpdeskAdapter.build(
        settings.its_helpdesk.base_url,
        verify_ssl,
        settings.its_helpdesk.db_name,
        settings.its_helpdesk.username,
        settings.its_helpdesk.password,
        settings.its_helpdesk.jsonrpc_id,
        settings.its_helpdesk.timeout,
    )
    app.state.its_helpdesk = adapter
    logger.info("ITS Helpdesk adapter started")
    try:
        yield
    finally:
        await adapter.stop()
        logger.info("ITS Helpdesk adapter stopped")
