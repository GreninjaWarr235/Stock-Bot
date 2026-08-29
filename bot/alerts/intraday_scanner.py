"""
alerts/intraday_scanner.py
==========================
Market Hours Intraday Portfolio Scanner (9:15 AM - 3:30 PM IST).

Monitors stocks specified in `data/universe/portfolio.csv` during market hours,
detects live intraday breakout, reversal, and volume surge signals, and sends
instant notifications via Telegram.

Usage:
    python -m alerts.intraday_scanner              # Run intraday scan during market hours
    python -m alerts.intraday_scanner --force      # Force run scan regardless of market hours
    python -m alerts.intraday_scanner --test       # Test Telegram notifier
"""

from __future__ import annotations

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
import json

# Ensure 'bot' directory is in sys.path
BOT_DIR = Path(__file__).resolve().parent.parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

import pandas as pd

from config.settings import (
    ROOT_DIR,
    REPORTS_DIR,
    MIN_AVG_DAILY_VOLUME,
    MIN_PRICE,
    TZ_IST,
)
from config.logger import get_logger, log_event
from data.loader import load_data, load_portfolio_universe, validate_ohlcv

try:
    from alerts.alerts import AlertGenerator, Alert
    from alerts.notifier import NotificationHub
except (ImportError, ModuleNotFoundError):
    try:
        from .alerts import AlertGenerator, Alert
        from .notifier import NotificationHub
    except (ImportError, ModuleNotFoundError):
        from alerts import AlertGenerator, Alert
        from notifier import NotificationHub

log = get_logger("intraday_scanner")

INTRADAY_ALERT_HISTORY_FILE = REPORTS_DIR / "intraday_alert_history.json"
INTRADAY_REPORT_FILE = REPORTS_DIR / f"intraday_alerts_{datetime.now().strftime('%Y%m%d')}.json"


def is_market_hours() -> bool:
    """
    Check if current local time is within Indian Stock Market hours:
    Monday to Friday, 09:15 AM to 03:30 PM (15:30 IST).
    """
    now = datetime.now()
    # Check weekday (0 = Monday, 4 = Friday, 5 = Sat, 6 = Sun)
    if now.weekday() in (5, 6):
        return False

    current_minutes = now.hour * 60 + now.minute
    market_open = 9 * 60 + 15    # 09:15 AM = 555 mins
    market_close = 15 * 60 + 30  # 03:30 PM = 930 mins

    return market_open <= current_minutes <= market_close


def scan_portfolio(symbols: list[str] | None = None,
                   test_mode: bool = False,
                   force_scan: bool = False) -> dict:
    """
    Scan portfolio stocks for intraday trading signals during market hours.
    """
    now = datetime.now()

    # Verify Market Hours unless force_scan or test_mode is True
    if not is_market_hours() and not test_mode and not force_scan and symbols is None:
        log.info("Outside market hours (9:15 AM - 3:30 PM IST Mon-Fri). Intraday scan skipped.")
        return {
            "scan_time": now.isoformat(),
            "symbols_scanned": 0,
            "alerts_generated": 0,
            "skipped": "Outside market hours",
            "alerts": [],
            "errors": [],
        }

    start_time = datetime.now()

    if symbols is None:
        # Load portfolio universe from portfolio.csv
        portfolio_df = load_portfolio_universe()
        symbols = portfolio_df["symbol"].tolist()
        log.info(f"⚡ Intraday Scan started for {len(symbols)} portfolio symbols from portfolio.csv")
    else:
        log.info(f"⚡ Intraday Scan started for {len(symbols)} specified symbols")

    # Load OHLCV data for portfolio symbols
    end_date = now.strftime("%Y-%m-%d")
    start_date = (now - timedelta(days=180)).strftime("%Y-%m-%d")

    data_map = load_data(
        symbols=symbols,
        start=start_date,
        end=end_date,
        source="synthetic",  # Uses synthetic/historical feed
    )

    log.info(f"Loaded market data for {len(data_map)} portfolio symbols")

    # Initialize alert generator with 2-hour deduplication for intraday agility
    alert_gen = AlertGenerator(
        min_score=65,  # Slightly lower threshold for intraday alerts
        min_price=MIN_PRICE,
        min_avg_volume=MIN_AVG_DAILY_VOLUME,
        alert_dedup_hours=2,
        is_intraday=True,
    )
    alert_gen.load_alert_history(str(INTRADAY_ALERT_HISTORY_FILE))

    notifier = NotificationHub()

    alerts: list[Alert] = []
    errors: list[tuple[str, str]] = []

    for symbol in symbols:
        try:
            if symbol not in data_map:
                errors.append((symbol, "No data available"))
                continue

            df = data_map[symbol]
            warnings = validate_ohlcv(df, symbol)
            if warnings:
                log.warning(f"{symbol}: {'; '.join(warnings)}")

            # Generate signal
            alert = alert_gen.generate(df, symbol)
            if alert:
                # Customize alert description for intraday context
                alert.description = f"[INTRADAY PORTFOLIO] {alert.description}"
                alert.is_intraday = True
                alerts.append(alert)
                log.info(f"⚡ Live Alert {symbol}: {alert.signal_type} (score: {alert.confidence})")

                if not test_mode:
                    # Format message specifically for intraday alerts
                    msg = alert.format_telegram()
                    results = notifier.telegram._send_message(msg)
                    log.debug(f"  Telegram notification result: {results}")

        except Exception as exc:
            log.error(f"{symbol}: Exception during intraday scan: {exc}")
            errors.append((symbol, str(exc)))

    # Save alert history
    alert_gen.save_alert_history(str(INTRADAY_ALERT_HISTORY_FILE))

    duration = (datetime.now() - start_time).total_seconds()

    result = {
        "scan_time": start_time.isoformat(),
        "scan_duration_seconds": duration,
        "symbols_scanned": len(symbols),
        "alerts_generated": len(alerts),
        "errors": errors,
        "alerts": [alert.to_dict() for alert in alerts],
    }

    # Save intraday report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(INTRADAY_REPORT_FILE, "w") as f:
        json.dump(result, f, indent=2, default=str)

    log.info(f"Intraday portfolio scan complete: {len(alerts)} alerts generated in {duration:.1f}s")
    return result


def main():
    parser = argparse.ArgumentParser(description="Market Hours Intraday Portfolio Scanner (9:15 AM - 3:30 PM IST)")
    parser.add_argument("--symbols", nargs="+", help="Specific portfolio symbols to scan")
    parser.add_argument("--force", action="store_true", help="Force scan execution regardless of market hours")
    parser.add_argument("--test", action="store_true", help="Test Telegram connectivity")

    args = parser.parse_args()

    if args.test:
        log.info("Testing Telegram connectivity for Intraday Notifier...")
        notifier = NotificationHub()
        results = notifier.test_connectivity()
        for channel, success in results.items():
            status = "OK ✓" if success else "FAILED ✗"
            log.info(f"  {channel}: {status}")
        return

    try:
        result = scan_portfolio(symbols=args.symbols, force_scan=args.force)

        print(f"\n{'='*65}")
        print(f"⚡ Intraday Portfolio Scan Report: {result['scan_time']}")
        print(f"{'='*65}")
        if result.get("skipped"):
            print(f"Status: Skipped ({result['skipped']})")
            print("Note: Use --force flag to run scan outside 9:15 AM - 3:30 PM IST market hours.")
        else:
            print(f"Portfolio symbols scanned: {result['symbols_scanned']}")
            print(f"Intraday alerts generated: {result['alerts_generated']}")
            print(f"Errors: {len(result['errors'])}")
            print(f"Duration: {result['scan_duration_seconds']:.1f}s")

            if result['alerts']:
                print(f"\n⚡ Generated Alerts ({result['alerts_generated']}):")
                for alert_dict in result['alerts']:
                    a = Alert(**alert_dict)
                    print(f"  {a.symbol}: {a.signal_type} (Score: {a.confidence}/100 | Entry: ₹{a.entry_price:.2f})")

        print(f"\nFull report: {INTRADAY_REPORT_FILE}")
        print("="*65)

    except KeyboardInterrupt:
        log.info("Intraday scan interrupted by user")
        sys.exit(0)
    except Exception as exc:
        log.error(f"Fatal error during intraday scan: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
