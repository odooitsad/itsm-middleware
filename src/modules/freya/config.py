from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.env_utils import get_env_file_path


class FreyaSettings(BaseSettings):
    base_url: str
    username: str
    password: str
    timeout: float = 30.0

    troubleshooting_enabled: bool = False
    troubleshooting_base_url: str
    troubleshooting_timeout: float = 15.0
    troubleshooting_token: str

    notifications_enabled: bool = False
    notifications_base_url: str | None = None
    notifications_timeout: float = 15.0

    model_config = SettingsConfigDict(
        env_prefix="FREYA_",
        env_file=get_env_file_path(),
        env_ignore_empty=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_notifications(self) -> "FreyaSettings":
        if self.notifications_enabled and not self.notifications_base_url:
            raise ValueError(
                "FREYA_NOTIFICATIONS_BASE_URL is required when "
                "FREYA_NOTIFICATIONS_ENABLED is set"
            )
        return self
