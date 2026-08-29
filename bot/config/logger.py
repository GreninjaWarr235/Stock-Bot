"""
config/logger.py
================
Structured logging module for Stock Bot.

Provides console and file logging with customizable log levels,
formatting, and structured event helper function `log_event`.

All timestamps are explicitly formatted in India Standard Time (IST),
regardless of the server/runner's system timezone.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from config.settings import TZ_IST

from config.settings import LOGS_DIR

_loggers = {}


class CleanFormatter(logging.Formatter):
    """Custom formatter with clean IST timestamp and level prefixes."""

    LEVEL_PREFIXES = {
        logging.DEBUG: "[DEBUG]",
        logging.INFO: "[INFO]",
        logging.WARNING: "[WARNING]",
        logging.ERROR: "[ERROR]",
        logging.CRITICAL: "[CRITICAL]",
    }

    def format(self, record):
        prefix = self.LEVEL_PREFIXES.get(record.levelno, "[LOG]")

        # record.created is a Unix timestamp (UTC-independent).
        # Explicitly convert it to IST instead of relying on the
        # system/server timezone.
        asctime = datetime.fromtimestamp(
            record.created,
            tz=ZoneInfo(TZ_IST)
        ).strftime("%Y-%m-%d %H:%M:%S")

        return f"{asctime} {prefix} [{record.name}] {record.getMessage()}"


def get_logger(name: str = "stock_bot", level: int = logging.INFO) -> logging.Logger:
    """
    Get or create a configured logger instance.

    Parameters:
        name: Module or component logger name
        level: Minimum log level (e.g. logging.INFO)

    Returns:
        logging.Logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Clear pre-existing handlers if re-initializing
    if logger.handlers:
        logger.handlers.clear()

    formatter = CleanFormatter()

    # Ensure stdout handles UTF-8 cleanly on Windows
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(
                encoding="utf-8",
                errors="backslashreplace"
            )
        except Exception:
            pass

    # Stream Handler (Console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (logs/stock_bot_YYYYMMDD.log)
    # Use IST for the filename date as well.
    try:
        ist_now = datetime.now(ZoneInfo(TZ_IST))
        log_file = LOGS_DIR / f"stock_bot_{ist_now.strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(
            log_file,
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    except Exception as e:
        print(f"Warning: Failed to setup log file handler: {e}")

    _loggers[name] = logger
    return logger


def log_event(
    logger: logging.Logger,
    event_type: str,
    level: str = "INFO",
    **kwargs
):
    """
    Helper function for logging structured key-value events.

    Example:
        log_event(
            log,
            "ALERT_SENT",
            symbol="RELIANCE",
            signal="BREAKOUT_UP",
            confidence=85
        )
    """
    kv_pairs = " ".join(
        [f"{k}={v}" for k, v in kwargs.items()]
    )

    msg = f"EVENT={event_type} {kv_pairs}".strip()

    log_level = getattr(
        logging,
        level.upper(),
        logging.INFO
    )

    logger.log(log_level, msg)