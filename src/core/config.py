from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.bmc_helix.config import BMCHelixSettings
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

    db_driver: DBDriver
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str

    db_pool_size: int = 5
    db_max_overflow: int = 5  # additional connections beyond pool_size
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    @property
    def database_url(self) -> str:
        """
        Builds the database connection URL based on the configured driver and credentials.
        """
        uri = f"{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        drivers = {
            DBDriver.AIOMYSQL: "mysql+aiomysql",
            DBDriver.ASYNCPG: "postgresql+asyncpg",
        }
        return drivers[self.db_driver] + "://" + uri

    bmc_helix: BMCHelixSettings = Field(default_factory=BMCHelixSettings)  # type: ignore[call-arg]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
