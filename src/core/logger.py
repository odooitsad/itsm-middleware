import copy
import json
import logging
import sys
from typing import ClassVar

from concurrent_log_handler import ConcurrentRotatingFileHandler

from src.core.config import get_settings

LOGGER_NAME = "itsm_middleware_logger"
settings = get_settings()


class ColorFormatter(logging.Formatter):
    COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: "\033[36m",  # Cyan
        logging.INFO: "\033[32m",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    @staticmethod
    def _prettify(arg):
        if isinstance(arg, (list, tuple, dict)):
            return json.dumps(arg, indent=2, ensure_ascii=False)
        return arg

    def format(self, record):
        # Copia el record para no afectar a otros handlers (p. ej. el de archivo)
        record = copy.copy(record)
        if isinstance(record.args, tuple):
            record.args = tuple(self._prettify(arg) for arg in record.args)
        elif isinstance(record.args, dict) and "%(" not in str(record.msg):
            record.args = (self._prettify(record.args),)

        color = self.COLORS.get(record.levelno, "")
        levelname = f"{color}{record.levelname}{self.RESET}"

        # Usa la función estándar para formatear el mensaje, incluye args correctamente
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        fmt = self._fmt or "%(message)s"
        formatted = fmt % record.__dict__

        # Colorea solo levelname y message, si están en el string
        formatted = formatted.replace(record.levelname, levelname, 1)
        formatted = formatted.replace(
            record.message, f"{color}{record.message}{self.RESET}", 1
        )
        return formatted


def get_logger(name: str = LOGGER_NAME) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # evita duplicados

    logger.setLevel(
        logging.DEBUG if settings.DEBUG else logging.INFO
    )  # DEBUG en modo debug, INFO en producción

    # Formato para ambos handlers
    fmt = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # Handler para consola (con colores)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColorFormatter(fmt, datefmt)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Handler concurrente para archivo (sin colores, con rotación)
    file_handler = ConcurrentRotatingFileHandler(
        settings.LOG_FILE_PATH,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_formatter = logging.Formatter(fmt, datefmt)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger


app_logger = get_logger()
