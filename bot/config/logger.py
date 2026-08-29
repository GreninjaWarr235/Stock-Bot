"""
config/logger.py
================
Structured logging module for India Swing Trading Alert System.

Provides console and file logging with customizable log levels,
formatting, and structured event helper function `log_event`.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

from config.settings import LOGS_DIR

_loggers = {}

class CleanFormatter(logging.Formatter):
    """Custom formatter with clean timestamp and level colors/icons."""
    
    LEVEL_PREFIXES = {
        logging.DEBUG: "[DEBUG]",
        logging.INFO: "[INFO]",
        logging.WARNING: "[WARNING]",
        logging.ERROR: "[ERROR]",
        logging.CRITICAL: "[CRITICAL]",
    }

    def format(self, record):
        prefix = self.LEVEL_PREFIXES.get(record.levelno, "[LOG]")
        asctime = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        return f"{asctime} {prefix} [{record.name}] {record.getMessage()}"


def get_logger(name: str = "india_swing", level: int = logging.INFO) -> logging.Logger:
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
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass

    # Stream Handler (Console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (logs/india_swing.log)
    try:
        log_file = LOGS_DIR / f"india_swing_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Failed to setup log file handler: {e}")

    _loggers[name] = logger
    return logger


def log_event(logger: logging.Logger, event_type: str, level: str = "INFO", **kwargs):
    """
    Helper function for logging structured key-value events.
    
    Example:
        log_event(log, "ALERT_SENT", symbol="RELIANCE", signal="BREAKOUT_UP", confidence=85)
    """
    kv_pairs = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    msg = f"EVENT={event_type} {kv_pairs}".strip()
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.log(log_level, msg)
