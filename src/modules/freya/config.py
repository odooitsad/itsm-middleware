from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.env_utils import get_env_file_path


class FreyaSettings(BaseSettings):
    base_url: str
    username: str
    password: str
    timeout: float = 30.0

    model_config = SettingsConfigDict(
        env_prefix="FREYA_",
        env_file=get_env_file_path(),
        env_ignore_empty=True,
        extra="ignore",
    )
