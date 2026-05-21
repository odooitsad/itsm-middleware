from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from src.bmc_helix.api.router import router as bmc_helix_router
from src.bmc_helix.infrastructure.adapters import BmcHelixAdapter
from src.constans import DESCRIPTION, PROJECT_NAME
from src.core.config import get_settings
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    str_path = str(settings.model_config.get("env_file"))
    logger.info(f"Loading settings from: {Path(str_path).name}")

    bmc_helix = None
    try:
        logger.info("Database connection pool established")

        bmc_helix = await init_bmc_helix_adapter()
        app.state.bmc_helix = bmc_helix
        logger.info("BMC Helix adapter started")

        yield
    except Exception as e:
        logger.exception(f"Error during application startup: {e}")
        raise
    finally:
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
