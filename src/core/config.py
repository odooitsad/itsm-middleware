from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent.parent


class DBDriver(StrEnum):
    AIOMYSQL = "aiomysql"
    ASYNCPG = "asyncpg"


def get_env_file_path():
    """
    Determina qué archivo .env cargar según la variable ENV_FILE.

    - En desarrollo: export ENV_FILE=.bbvaclient.env
    - En producción: usa .env por defecto
    """
    import os

    env_file = os.getenv("ENV_FILE", ".env")
    env_file_path = ROOT_DIR / env_file
    if not env_file_path.exists():
        # In Docker, the variables are already loaded by docker-compose
        # If the file does not exist but we have API_KEY, it means it has already been loaded
        if os.getenv("API_KEY"):
            return env_file
        raise FileNotFoundError(f"Configuration file not found at {env_file_path}")
    return env_file_path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=get_env_file_path(), env_ignore_empty=True, extra="ignore"
    )

    LOG_FILE_PATH: Path = ROOT_DIR / "logs" / "itsm_middleware.log"
    DEBUG: bool = False
    TZ: str = "UTC"

    # BMC Helix
    BMC_HELIX_BASE_URL: str = ""
    BMC_HELIX_USERNAME: str = ""
    BMC_HELIX_PASSWORD: str = ""
    BMC_HELIX_LOGIN_PATH: str = "/api/jwt/login"
    BMC_HELIX_TOKEN_FIELD: str = "token"
    BMC_HELIX_TOKEN_TTL_SECONDS: float = 3600.0
    BMC_HELIX_TIMEOUT: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
