"""
Continuous intraday scheduler for the Oracle Cloud VM.

Runs the intraday portfolio scanner every 15 minutes during
Indian market hours (09:15 - 15:30 IST), Monday-Friday.

The process is intended to run continuously under systemd.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


# Project paths
BOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BOT_DIR.parent

# Timezone
IST = ZoneInfo("Asia/Kolkata")

# Market hours
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MINUTE = 30

# Scan interval
SCAN_INTERVAL_MINUTES = 15

# Scanner module
SCANNER_MODULE = "alerts.intraday_scanner"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [intraday_scheduler] %(message)s",
)

log = logging.getLogger("intraday_scheduler")


def is_weekday(now: datetime) -> bool:
    return now.weekday() < 5


def market_open(now: datetime) -> datetime:
    return now.replace(
        hour=MARKET_OPEN_HOUR,
        minute=MARKET_OPEN_MINUTE,
        second=0,
        microsecond=0,
    )


def market_close(now: datetime) -> datetime:
    return now.replace(
        hour=MARKET_CLOSE_HOUR,
        minute=MARKET_CLOSE_MINUTE,
        second=0,
        microsecond=0,
    )


def is_market_hours(now: datetime) -> bool:
    if not is_weekday(now):
        return False

    return market_open(now) <= now <= market_close(now)


def seconds_until_next_scan(now: datetime) -> float:
    """
    Return seconds until the next 15-minute scan boundary.

    Scan times:
        09:15
        09:30
        09:45
        ...
        15:15
        15:30
    """

    today_open = market_open(now)
    today_close = market_close(now)

    if now < today_open:
        return (today_open - now).total_seconds()

    if now >= today_close:
        return 0

    # Minutes elapsed since market open.
    elapsed_minutes = int((now - today_open).total_seconds() // 60)

    # Find the next 15-minute boundary.
    next_boundary_minutes = (
        (elapsed_minutes // SCAN_INTERVAL_MINUTES) + 1
    ) * SCAN_INTERVAL_MINUTES

    next_scan = today_open + timedelta(minutes=next_boundary_minutes)

    # Never schedule beyond market close.
    if next_scan > today_close:
        return 0

    return max(0, (next_scan - now).total_seconds())


def run_scan() -> bool:
    """Run one intraday scanner process."""

    log.info("Starting intraday scan")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                SCANNER_MODULE,
            ],
            cwd=PROJECT_ROOT,
            check=False,
        )

        if result.returncode == 0:
            log.info("Intraday scan completed successfully")
            return True

        log.error(
            "Intraday scanner exited with return code %s",
            result.returncode,
        )
        return False

    except Exception:
        log.exception("Failed to start intraday scanner")
        return False


def main() -> None:
    log.info("==============================================")
    log.info("Intraday Scheduler started")
    log.info("Market hours: 09:15-15:30 IST, Monday-Friday")
    log.info("Scan interval: every 15 minutes")
    log.info("==============================================")

    while True:
        now = datetime.now(IST)

        # Weekend
        if not is_weekday(now):
            next_monday = now + timedelta(days=(7 - now.weekday()))
            next_start = next_monday.replace(
                hour=MARKET_OPEN_HOUR,
                minute=MARKET_OPEN_MINUTE,
                second=0,
                microsecond=0,
            )

            sleep_seconds = (next_start - now).total_seconds()

            log.info(
                "Weekend. Next market open: %s",
                next_start.strftime("%Y-%m-%d %H:%M:%S IST"),
            )

            time.sleep(min(sleep_seconds, 3600))
            continue

        # Before market open
        if now < market_open(now):
            sleep_seconds = (market_open(now) - now).total_seconds()

            log.info(
                "Waiting for market open at 09:15 IST (%.0f seconds)",
                sleep_seconds,
            )

            time.sleep(min(sleep_seconds, 300))
            continue

        # After market close
        if now > market_close(now):
            tomorrow = now + timedelta(days=1)

            while tomorrow.weekday() >= 5:
                tomorrow += timedelta(days=1)

            next_open = tomorrow.replace(
                hour=MARKET_OPEN_HOUR,
                minute=MARKET_OPEN_MINUTE,
                second=0,
                microsecond=0,
            )

            sleep_seconds = (next_open - now).total_seconds()

            log.info(
                "Market closed. Next market open: %s",
                next_open.strftime("%Y-%m-%d %H:%M:%S IST"),
            )

            time.sleep(min(sleep_seconds, 3600))
            continue

        # We are inside market hours.
        # Calculate next scan boundary.
        wait_seconds = seconds_until_next_scan(now)

        if wait_seconds > 0:
            log.info(
                "Next scan in %.0f seconds at approximately %s",
                wait_seconds,
                (
                    now + timedelta(seconds=wait_seconds)
                ).strftime("%H:%M:%S IST"),
            )

            time.sleep(wait_seconds)

        # Re-check time after sleeping.
        now = datetime.now(IST)

        if is_market_hours(now):
            run_scan()

        # Prevent accidental rapid re-execution.
        time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("Intraday scheduler stopped by user")
        sys.exit(0)
