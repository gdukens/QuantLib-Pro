"""
Structured logging factory for QuantLib Pro.
All modules should obtain loggers via this function
to ensure consistent formatting across the platform.
"""

import logging
import logging.config
import os
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Return a consistently configured logger."""
    return logging.getLogger(name)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
        "plain": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "plain",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/quantlib_pro.log",
            "maxBytes": 10_485_760,   # 10 MB
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "root": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "handlers": ["console", "file"],
    },
    "loggers": {
        "quantlib_pro": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": True,
        },
        "uvicorn": {"level": "INFO", "propagate": True},
        "streamlit": {"level": "WARNING", "propagate": True},
    },
}


def setup_logging() -> None:
    """Call once at application startup."""
    os.makedirs("logs", exist_ok=True)
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
    except Exception:
        # Fallback to basic config if json formatter not installed yet
        logging.basicConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            stream=sys.stdout,
        )
