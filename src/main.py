from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from src.constans import DESCRIPTION, PROJECT_NAME
from src.core.base_exception_handlers import register_base_exception_handlers
from src.core.config import get_settings
from src.core.database.base import Base
from src.core.database.session import DatabaseAdapter
from src.core.logger import get_logger
from src.health_router import router as health_router
from src.modules.bmc_helix.api.exception_handlers import (
    register_bmc_helix_exception_handlers,
)
from src.modules.bmc_helix.api.routers.main import bmc_helix_router
from src.modules.bmc_helix.lifespan import bmc_helix_lifespan

logger = get_logger(__name__)
settings = get_settings()


async def build_db_adapter() -> DatabaseAdapter:
    return DatabaseAdapter(
        db_url=settings.database_url,
        echo=settings.DEBUG,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    str_path = str(settings.model_config.get("env_file"))
    logger.info(f"Loading settings from: {Path(str_path).name}")

    db = await build_db_adapter()
    try:
        await db.connect()
        app.state.db = db
        logger.info("Database connection pool established")

        async with db.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured (bmc_helix)")

        # async with bmc_helix_lifespan(app), its_helpdesk_lifespan(app):
        async with bmc_helix_lifespan(app):
            yield
    except Exception as e:
        logger.exception(f"Error during application startup: {e}")
        raise
    finally:
        await db.disconnect()
        logger.info("Database connection pool closed")


app = FastAPI(
    title=PROJECT_NAME,
    description=DESCRIPTION,
    version="0.1.0",
    lifespan=lifespan,
    prefix="/api",
)


app.include_router(health_router)
app.include_router(bmc_helix_router)
# app.include_router(its_helpdesk_router)


register_base_exception_handlers(app)
register_bmc_helix_exception_handlers(app)
# app.add_exception_handler(TicketCreationError, ticket_creation_error_handler)
# app.add_exception_handler(ItsHelpdeskClientError, its_helpdesk_client_error_handler)
