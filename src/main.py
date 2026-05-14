import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routers import health
from src.constans import DESCRIPTION, PROJECT_NAME
from src.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__).setLevel(logging.DEBUG)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from logging import getLogger
    from pathlib import Path

    logger = getLogger(__name__)

    logger.debug("Debug mode")
    str_path = str(settings.model_config.get("env_file"))
    env_file_path = Path(str_path)
    logger.info(f"Loading settings from: {env_file_path.name}")
    yield


app = FastAPI(
    title=PROJECT_NAME,
    description=DESCRIPTION,
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(health.router)
