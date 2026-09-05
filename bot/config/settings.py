"""
config/settings.py
==================
Central configuration module for Stock Bot.

Loads environment variables from .env file and provides default parameters
for indicator calculations, pattern detection, risk management, and notifications.
"""

import os
from pathlib import Path

# Load .env file
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file, override=True)
    except ImportError:
        # Fallback parser if python-dotenv is not installed
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")


# System Paths
CONFIG_DIR = Path(__file__).parent
ROOT_DIR = CONFIG_DIR.parent
LOGS_DIR = ROOT_DIR / "logs"
REPORTS_DIR = ROOT_DIR / "reports"
DATA_DIR = ROOT_DIR / "data"

# Ensure essential directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Timezone & Regional
TZ_IST = "Asia/Kolkata"

# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# System Execution Parameters
DATA_SOURCE = os.getenv("DATA_SOURCE", "synthetic").strip()

# Alert & Signal Thresholds
ALERT_MIN_SCORE = int(os.getenv("ALERT_MIN_SCORE", "70"))
MIN_PRICE = float(os.getenv("MIN_PRICE", "50.0"))               # Ignore penny stocks < ₹50
MIN_AVG_DAILY_VOLUME = int(os.getenv("MIN_AVG_DAILY_VOLUME", "200000"))  # Liquidity filter
ALERT_DEDUP_HOURS = int(os.getenv("ALERT_DEDUP_HOURS", "4"))    # Don't repeat signal within 4h

# Risk Management Defaults
MAX_RISK_PCT_PER_TRADE = float(os.getenv("MAX_RISK_PCT_PER_TRADE", "0.01"))  # Risk 1% per trade
DEFAULT_STOP_LOSS_PCT = float(os.getenv("DEFAULT_STOP_LOSS_PCT", "0.05"))    # 5% stop loss default
DEFAULT_TRAILING_STOP_PCT = None

# Technical Indicator Settings
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

BOLLINGER_PERIOD = 20
BOLLINGER_STD_DEV = 2.0

ATR_PERIOD = 14
BREAKOUT_LOOKBACK = 20
VOLUME_SURGE_MULTIPLIER = 2.0
