"""
alerts/scanner.py
=================
Main watchlist scanner. Runs once per day after market close.

Workflow:
1. Load symbol universe from CSV
2. Fetch historical OHLCV data for each symbol
3. Run pattern detection
4. Generate and score alerts
5. Send Telegram notifications
6. Log results and close-of-business report

Usage:
    python -m alerts.scanner              # Scan full universe
    python -m alerts.scanner --symbols RELIANCE TCS  # Scan specific symbols
    python -m alerts.scanner --test       # Telegram connectivity test
    python -m alerts.scanner --backfill   # Refresh all data
"""

from __future__ import annotations

import sys
import argparse
import logging
from pathlib import Path

# Ensure 'bot' directory is in sys.path for absolute package imports
BOT_DIR = Path(__file__).resolve().parent.parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json

import pandas as pd

from config.settings import (
    ROOT_DIR,
    REPORTS_DIR,
    MIN_AVG_DAILY_VOLUME,
    MIN_PRICE,
    TZ_IST,
    DATA_SOURCE,
    ALERT_MIN_SCORE,
    ALERT_DEDUP_HOURS
)
from config.logger import get_logger, log_event

from data.loader import load_data, load_universe, validate_ohlcv

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

log = get_logger(__name__)

ALERT_HISTORY_FILE = REPORTS_DIR / "alert_history.json"
REPORT_FILE = REPORTS_DIR / f"alerts_{datetime.now(ZoneInfo(TZ_IST)).strftime('%Y%m%d')}.json"


def scan_universe(symbols: list[str] | None = None,
                  test_mode: bool = False,
                  force_scan: bool = False) -> dict:
    """
    Scan a list of symbols for trading alerts.
    """
    # Check for weekend (Saturday = 5, Sunday = 6)
    if datetime.now(ZoneInfo(TZ_IST)).weekday() in (5, 6) and not test_mode and not force_scan and symbols is None:
        log.info("Weekend detected (Saturday/Sunday). Stock market is closed. Skipping scan.")
        return {
            "scan_time": datetime.now(ZoneInfo(TZ_IST)).isoformat(),
            "scan_duration_seconds": 0,
            "symbols_scanned": 0,
            "alerts_generated": 0,
            "errors": [],
            "alerts": [],
            "skipped": "Weekend",
        }

    start_time = datetime.now(ZoneInfo(TZ_IST))
    
    if symbols is None:
        # Load universe
        universe_df = load_universe()
        symbols = universe_df["symbol"].tolist()[:20]  # Start with top 20
        log.info(f"Scanning {len(symbols)} symbols from universe")
    else:
        log.info(f"Scanning {len(symbols)} specified symbols")
    
    # Load 1 year of data
    end_date = datetime.now(ZoneInfo(TZ_IST)).strftime("%Y-%m-%d")
    start_date = (datetime.now(ZoneInfo(TZ_IST)) - timedelta(days=365)).strftime("%Y-%m-%d")
    
    data_map = load_data(
        symbols=symbols,
        start=start_date,
        end=end_date,
        source=DATA_SOURCE
    )
    
    log.info(f"Data loaded for {len(data_map)} symbols")
    
    # Initialize alert generator
    alert_gen = AlertGenerator(
        min_score=ALERT_MIN_SCORE,
        min_price=MIN_PRICE,
        min_avg_volume=MIN_AVG_DAILY_VOLUME,
        alert_dedup_hours=ALERT_DEDUP_HOURS,
    )
    alert_gen.load_alert_history(str(ALERT_HISTORY_FILE))
    
    # Initialize notifier
    notifier = NotificationHub()
    
    # Scan each symbol
    alerts: list[Alert] = []
    errors: list[tuple[str, str]] = []
    
    for symbol in symbols:
        try:
            if symbol not in data_map:
                errors.append((symbol, "No data available"))
                continue
            
            df = data_map[symbol]
            
            # Validate
            warnings = validate_ohlcv(df, symbol)
            if warnings:
                log.warning(f"{symbol}: {'; '.join(warnings)}")
            
            # Generate alert
            alert = alert_gen.generate(df, symbol)
            if alert:
                alerts.append(alert)
                log.info(f"✓ {symbol}: {alert.signal_type} (score: {alert.confidence})")
                
                # Send immediately if not in test mode
                if not test_mode:
                    results = notifier.send_alert(alert)
                    log.debug(f"  Notification results: {results}")
            
        except Exception as exc:
            log.error(f"{symbol}: Exception during scan: {exc}")
            errors.append((symbol, str(exc)))
    
    # Save alert history
    alert_gen.save_alert_history(str(ALERT_HISTORY_FILE))
    
    # Generate report
    duration = (datetime.now(ZoneInfo(TZ_IST)) - start_time).total_seconds()
    
    result = {
        "scan_time": start_time.isoformat(),
        "scan_duration_seconds": duration,
        "symbols_scanned": len(symbols),
        "alerts_generated": len(alerts),
        "errors": errors,
        "alerts": [alert.to_dict() for alert in alerts],
    }
    
    # Send summary notification
    if alerts and not test_mode:
        notifier.telegram.send_summary(alerts, duration_minutes=int(duration / 60))
    
    # Save report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    log.info(
        f"Scan complete: {len(alerts)} alerts, {len(errors)} errors in {duration:.0f}s"
    )
    
    return result


def main():
    parser = argparse.ArgumentParser(description="NSE Swing Trading Alert Scanner")
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Specific symbols to scan (default: full universe)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test Telegram connectivity without scanning",
    )
    parser.add_argument(
        "--full-universe",
        action="store_true",
        help="Scan entire universe (slower, ~5-10 min)",
    )
    
    args = parser.parse_args()
    
    # Test mode
    if args.test:
        log.info("Testing Telegram connectivity...")
        notifier = NotificationHub()
        results = notifier.test_connectivity()
        for channel, success in results.items():
            status = "OK ✓" if success else "FAILED ✗"
            log.info(f"  {channel}: {status}")
        return
    
    # Determine symbols
    symbols = args.symbols
    if args.full_universe:
        universe_df = load_universe()
        symbols = universe_df["symbol"].tolist()
        log.info(f"Scanning full universe: {len(symbols)} symbols")
    
    # Run scan
    try:
        result = scan_universe(symbols=symbols)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Scan Report: {result['scan_time']}")
        print(f"{'='*60}")
        print(f"Symbols scanned: {result['symbols_scanned']}")
        print(f"Alerts generated: {result['alerts_generated']}")
        print(f"Errors: {len(result['errors'])}")
        print(f"Duration: {result['scan_duration_seconds']:.1f}s")
        
        if result['alerts']:
            print(f"\nAlerts ({result['alerts_generated']}):")
            for alert_dict in result['alerts']:
                a = Alert(**alert_dict)
                print(f"  {a.symbol}: {a.signal_type} ({a.confidence}/100)")
        
        if result['errors']:
            print(f"\nErrors ({len(result['errors'])}):")
            for symbol, error in result['errors']:
                print(f"  {symbol}: {error}")
        
        print(f"\nFull report: {REPORT_FILE}")
        print("="*60)
    
    except KeyboardInterrupt:
        log.info("Scan interrupted by user")
        sys.exit(0)
    except Exception as exc:
        log.error(f"Fatal error during scan: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
