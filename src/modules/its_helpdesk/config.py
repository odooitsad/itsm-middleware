from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.env_utils import get_env_file_path


class ItsHelpdeskSettings(BaseSettings):
    base_url: str
    db_name: str
    username: str
    password: str
    jsonrpc_id: int
    timeout: float = 30.0

    model_config = SettingsConfigDict(
        env_prefix="ITS_HELPDESK_",
        env_file=get_env_file_path(),
        env_ignore_empty=True,
        extra="ignore",
    )
