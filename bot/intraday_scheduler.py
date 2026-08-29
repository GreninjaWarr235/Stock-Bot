"""
intraday_scheduler.py
=====================
Continuous Intraday Market Hours Daemon Scheduler (9:15 AM - 3:30 PM IST).

Monitors portfolio.csv by periodically running the intraday scanner during
active market hours.

Usage:
    python intraday_scheduler.py                  # Polls every 15 mins during 9:15 AM - 3:30 PM IST
    python intraday_scheduler.py --interval 10    # Polls every 10 mins
    python intraday_scheduler.py --force          # Force run continuously outside market hours (testing)
"""

from __future__ import annotations

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config.settings import TZ_IST

# Ensure 'bot' directory is in sys.path
BOT_DIR = Path(__file__).resolve().parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from config.logger import get_logger
from alerts.intraday_scanner import scan_portfolio, is_market_hours

log = get_logger("intraday_scheduler")


def run_intraday_daemon(interval_minutes: int = 15, force: bool = False):
    """
    Runs intraday portfolio scanner periodically during market hours (9:15 AM - 3:30 PM IST).
    """
    log.info(f"🚀 Starting Intraday Portfolio Scheduler (Polling Interval: {interval_minutes} mins)")
    print(f"Active Market Window: 09:15 AM to 03:30 PM IST (Mon-Fri)")
    print("Press Ctrl+C to stop.\n")

    while True:
        now = datetime.now(ZoneInfo(TZ_IST))
        in_market = is_market_hours()

        if in_market or force:
            log.info(f"⏰ [Market Hours] Triggering Intraday Portfolio Scan ({now.strftime('%H:%M:%S')} IST)...")
            try:
                result = scan_portfolio(force_scan=force)
                alerts_count = result.get("alerts_generated", 0)
                log.info(f"✓ Scan completed: {alerts_count} intraday alerts sent.")
            except Exception as exc:
                log.error(f"Error during intraday scan: {exc}", exc_info=True)

            log.info(f"Sleeping for {interval_minutes} minutes until next intraday check...")
            time.sleep(interval_minutes * 60)

        else:
            # Outside market hours
            current_minutes = now.hour * 60 + now.minute
            market_open_minutes = 9 * 60 + 15  # 09:15 AM

            if now.weekday() in (5, 6):  # Weekend
                log.info("Weekend detected. Market closed. Daemon waiting for Monday 09:15 AM IST...")
                time.sleep(1800)  # Sleep 30 mins between checks on weekend
            elif current_minutes < market_open_minutes:
                # Before 9:15 AM today
                target_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
                wait_seconds = (target_open - now).total_seconds()
                log.info(f"Before market open. Sleeping {wait_seconds / 60:.1f} mins until 09:15 AM IST...")
                time.sleep(min(wait_seconds, 600))  # Sleep max 10 mins at a time
            else:
                # After 3:30 PM today -> sleep until 09:15 AM tomorrow
                next_day = now + timedelta(days=1)
                target_open = next_day.replace(hour=9, minute=15, second=0, microsecond=0)
                wait_seconds = (target_open - now).total_seconds()
                log.info(f"Market closed for today. Next session: {target_open.strftime('%Y-%m-%d 09:15:00')} (sleeping {wait_seconds / 3600:.2f} hrs)...")
                time.sleep(min(wait_seconds, 1800))  # Sleep max 30 mins at a time


def main():
    parser = argparse.ArgumentParser(description="Intraday Market Hours Portfolio Scanner Daemon")
    parser.add_argument("--interval", type=int, default=15, help="Scan interval in minutes during market hours (default: 15)")
    parser.add_argument("--force", action="store_true", help="Force scanner execution even outside 9:15-3:30 window")

    args = parser.parse_args()

    try:
        run_intraday_daemon(interval_minutes=args.interval, force=args.force)
    except KeyboardInterrupt:
        log.info("Intraday scheduler stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
