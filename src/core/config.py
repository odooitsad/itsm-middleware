from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.env_utils import ROOT_DIR, get_env_file_path


class DBDriver(StrEnum):
    AIOMYSQL = "aiomysql"
    ASYNCPG = "asyncpg"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=get_env_file_path(), env_ignore_empty=True, extra="ignore"
    )

    LOG_FILE_PATH: Path = ROOT_DIR / "logs" / "itsm_middleware.log"
    API_KEY: str
    DEBUG: bool = False
    TZ: str = "UTC"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
