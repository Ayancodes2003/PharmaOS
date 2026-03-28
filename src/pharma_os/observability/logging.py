"""Structured logging setup for PHARMA-OS."""

import logging
from logging.config import dictConfig

from pharma_os.core.settings import Settings


def configure_logging(settings: Settings) -> None:
    """Configure global structured logging based on environment settings."""
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "level": settings.log_level.upper(),
                }
            },
            "root": {
                "handlers": ["default"],
                "level": settings.log_level.upper(),
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get a module-level logger."""
    return logging.getLogger(name)
