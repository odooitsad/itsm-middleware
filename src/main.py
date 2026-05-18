from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from src.api.routers import health
from src.constans import DESCRIPTION, PROJECT_NAME
from src.core.config import get_settings
from src.core.logger import get_logger
from src.infrastructure.http.client import AuthType, HttpxClient, JwtProviderConfig

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    str_path = str(settings.model_config.get("env_file"))
    logger.info(f"Loading settings from: {Path(str_path).name}")

    # --- BMC Helix HTTP client ---
    bmc_helix_http = HttpxClient(
        base_url=settings.BMC_HELIX_BASE_URL,
        auth_type=AuthType.JWT_FROM_API,
        jwt_config=JwtProviderConfig(
            login_path=settings.BMC_HELIX_LOGIN_PATH,
            username=settings.BMC_HELIX_USERNAME,
            password=settings.BMC_HELIX_PASSWORD,
            token_field=settings.BMC_HELIX_TOKEN_FIELD,
            ttl_seconds=settings.BMC_HELIX_TOKEN_TTL_SECONDS,
        ),
        timeout=settings.BMC_HELIX_TIMEOUT,
    )
    await bmc_helix_http.start()
    app.state.bmc_helix_http = bmc_helix_http
    logger.info("BMC Helix HTTP client started")

    yield

    await bmc_helix_http.stop()
    logger.info("BMC Helix HTTP client stopped")


app = FastAPI(
    title=PROJECT_NAME,
    description=DESCRIPTION,
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(health.router)
