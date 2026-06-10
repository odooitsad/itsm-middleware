from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.bmc_helix.api.exception_handlers import (
    bmc_helix_client_error_handler,
    incident_creation_error_handler,
    validation_exception_handler,
)
from src.bmc_helix.api.routers.main import bmc_helix_router
from src.bmc_helix.domain.exceptions import BmcHelixClientError, IncidentCreationError
from src.bmc_helix.infrastructure.adapters import BmcHelixAdapter
from src.constans import DESCRIPTION, PROJECT_NAME
from src.core.config import get_settings
from src.core.database.base import Base
from src.core.database.session import DatabaseAdapter
from src.core.logger import get_logger
from src.health_router import router as health_router

logger = get_logger(__name__)
settings = get_settings()


async def init_bmc_helix_adapter() -> BmcHelixAdapter:
    return BmcHelixAdapter.build(
        settings.bmc_helix.base_url,
        settings.bmc_helix.username,
        settings.bmc_helix.password,
        settings.bmc_helix.timeout,
    )


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
    bmc_helix = None
    try:
        await db.connect()
        app.state.db = db
        logger.info("Database connection pool established")

        async with db.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables ensured (bmc_helix)")

        bmc_helix = await init_bmc_helix_adapter()
        app.state.bmc_helix = bmc_helix
        logger.info("BMC Helix adapter started")

        yield
    except Exception as e:
        logger.exception(f"Error during application startup: {e}")
        raise
    finally:
        await db.disconnect()
        logger.info("Database connection pool closed")

        if bmc_helix:
            await bmc_helix.stop()
            logger.info("BMC Helix adapter stopped")


app = FastAPI(
    title=PROJECT_NAME,
    description=DESCRIPTION,
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(health_router)
app.include_router(bmc_helix_router)


app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IncidentCreationError, incident_creation_error_handler)
app.add_exception_handler(BmcHelixClientError, bmc_helix_client_error_handler)
