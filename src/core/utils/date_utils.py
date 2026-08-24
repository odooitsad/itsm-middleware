from datetime import datetime
from zoneinfo import ZoneInfo

from src.core.config import get_settings
from src.core.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


def add_settings_timezone(date_value: str) -> str:
    """Attach the configured timezone to a naive ISO datetime string.

    Example:
        # Time Zone: America/Bogota (UTC-5)
        add_settings_timezone("2026-04-01T08:31:24")
        # "2026-04-01T08:31:24-05:00"
    """
    naive_datetime = datetime.fromisoformat(date_value)
    if naive_datetime.tzinfo is not None:
        return naive_datetime.astimezone(settings.tz).isoformat()

    return naive_datetime.replace(tzinfo=settings.tz).isoformat()


def now_with_settings_timezone() -> str:
    """Return the current datetime as an ISO string in the configured timezone.

    Example:
        now_with_settings_timezone()
        # "2026-04-01T08:31:24-05:00"
    """
    return datetime.now(settings.tz).isoformat(timespec="seconds")


def parse_date_format(date_str: str) -> str:
    """
    Converts a date string in the format "YYYY.MM.DDTHH:MM:SS" UTC
    to "YYYY-MM-DD HH:MM:SS" with the Colombia timezone.
    """
    try:
        date = datetime.fromisoformat(date_str)
        if date.tzinfo is None:
            date = date.replace(tzinfo=ZoneInfo("UTC"))

        return date.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.warning(f"Error parsing date: {date_str}")
        return date_str
