"""
scheduler.py
============
Built-in daemon scheduler for daily automated scanning without external cron/Task Scheduler.

Usage:
    python scheduler.py                 # Runs daily at 16:05 (4:05 PM IST)
    python scheduler.py --time 16:05    # Custom time (HH:MM 24h format)
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config.settings import TZ_IST

BOT_DIR = Path(__file__).resolve().parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from config.logger import get_logger
from alerts.scanner import scan_universe

log = get_logger("scheduler")


def run_daily_scheduler(target_time_str: str = "16:05"):
    """
    Schedules and executes scanner daily at target_time_str (HH:MM format).
    """
    try:
        target_hour, target_minute = map(int, target_time_str.split(":"))
    except ValueError:
        log.error(f"Invalid time format '{target_time_str}'. Use HH:MM in 24h format (e.g. 16:05).")
        sys.exit(1)

    log.info(f"🚀 Swing Bot Scheduler started. Daily target time: {target_hour:02d}:{target_minute:02d} IST.")
    print(f"Press Ctrl+C to stop.\n")

    while True:
        now = datetime.now(ZoneInfo(TZ_IST))
        target_today = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

        # If today's run time has passed, schedule for tomorrow
        if now >= target_today:
            next_run = target_today + timedelta(days=1)
        else:
            next_run = target_today

        wait_seconds = (next_run - now).total_seconds()
        log.info(f"Next scan scheduled for {next_run.strftime('%Y-%m-%d %H:%M:%S')} (waiting {wait_seconds / 3600:.2f} hours)")

        # Sleep until scheduled time
        try:
            time.sleep(wait_seconds)
        except KeyboardInterrupt:
            log.info("Scheduler stopped by user.")
            sys.exit(0)

        # Run scanner (Skip weekends if desired, e.g. Saturday=5, Sunday=6)
        run_day = datetime.now(ZoneInfo(TZ_IST)).weekday()
        if run_day in (5, 6):
            log.info("Weekend detected (Saturday/Sunday). Skipping market scan.")
        else:
            log.info("⏰ Triggering daily market scanner run...")
            try:
                scan_universe()
            except Exception as exc:
                log.error(f"Error during scheduled scan: {exc}")

        # Sleep 60 seconds to prevent re-triggering immediately
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="Swing Alert Bot Daily Scheduler Daemon")
    parser.add_argument("--time", type=str, default="16:05", help="Target daily run time in HH:MM (24h format, default 16:05)")
    args = parser.parse_args()

    run_daily_scheduler(args.time)


if __name__ == "__main__":
    main()
