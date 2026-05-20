from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from src.constans import DESCRIPTION, PROJECT_NAME
from src.core.config import get_settings
from src.core.logger import get_logger
from src.health_router import router as health_router

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    str_path = str(settings.model_config.get("env_file"))
    logger.info(f"Loading settings from: {Path(str_path).name}")

    yield


app = FastAPI(
    title=PROJECT_NAME,
    description=DESCRIPTION,
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(health_router)
