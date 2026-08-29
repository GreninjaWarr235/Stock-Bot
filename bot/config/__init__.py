"""
config package
==============
Configuration settings and logging utilities for Stock Bot.
"""

from config.settings import (
    ROOT_DIR,
    CONFIG_DIR,
    LOGS_DIR,
    REPORTS_DIR,
    DATA_DIR,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    ALERT_MIN_SCORE,
    MIN_PRICE,
    MIN_AVG_DAILY_VOLUME,
    ALERT_DEDUP_HOURS,
    MAX_RISK_PCT_PER_TRADE,
    DEFAULT_STOP_LOSS_PCT,
    DEFAULT_TRAILING_STOP_PCT,
    TZ_IST,
    DATA_SOURCE,
)
from config.logger import get_logger, log_event

__all__ = [
    "ROOT_DIR",
    "CONFIG_DIR",
    "LOGS_DIR",
    "REPORTS_DIR",
    "DATA_DIR",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "ALERT_MIN_SCORE",
    "MIN_PRICE",
    "MIN_AVG_DAILY_VOLUME",
    "ALERT_DEDUP_HOURS",
    "MAX_RISK_PCT_PER_TRADE",
    "DEFAULT_STOP_LOSS_PCT",
    "DEFAULT_TRAILING_STOP_PCT",
    "TZ_IST",
    "DATA_SOURCE",
    "get_logger",
    "log_event",
]
