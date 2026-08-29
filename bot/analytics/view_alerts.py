"""
analytics/view_alerts.py
========================
Viewer for generated trading alerts and alert history.

Usage:
    python -m analytics.view_alerts                     # View latest report alerts
    python -m analytics.view_alerts --date 20260828     # View specific date report
    python -m analytics.view_alerts --min-score 80      # Filter by minimum score
    python -m analytics.view_alerts --symbol RELIANCE   # Filter by symbol
    python -m analytics.view_alerts --history           # View stored alert history
"""

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

# Ensure 'bot' directory is in sys.path
BOT_DIR = Path(__file__).resolve().parent.parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from datetime import datetime

from config.settings import REPORTS_DIR, ROOT_DIR
from config.logger import get_logger

log = get_logger(__name__)


def load_latest_report(date_str: str | None = None, intraday: bool = False) -> tuple[Path | None, dict]:
    """Load alert report JSON from reports directory."""
    if not REPORTS_DIR.exists():
        return None, {}

    prefix = "intraday_alerts_" if intraday else "alerts_"

    if date_str:
        file_path = REPORTS_DIR / f"{prefix}{date_str}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return file_path, json.load(f)
        else:
            log.warning(f"No report found for date {date_str} at {file_path}")
            return None, {}

    # Find the most recent alerts_*.json or intraday_alerts_*.json file
    report_files = sorted(REPORTS_DIR.glob(f"{prefix}*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not report_files:
        return None, {}
        return None, {}

    latest_file = report_files[0]
    with open(latest_file, "r", encoding="utf-8") as f:
        return latest_file, json.load(f)


def load_alert_history(intraday: bool = False) -> dict:
    """Load alert history JSON file."""
    filename = "intraday_alert_history.json" if intraday else "alert_history.json"
    history_file = REPORTS_DIR / filename
    if not history_file.exists():
        log.warning(f"Alert history file not found: {history_file}")
        return {}

    with open(history_file, "r", encoding="utf-8") as f:
        return json.load(f)


def display_alerts_table(alerts: list[dict], title: str = "ALERTS SUMMARY"):
    """Format and print alerts in clean CLI table."""
    print("\n" + "=" * 90)
    print(f" 📊 {title}")
    print("=" * 90)
    
    if not alerts:
        print(" No alerts found matching criteria.")
        print("=" * 90 + "\n")
        return

    header = f"{'Symbol':<12} {'Signal':<16} {'Score':<8} {'Price':<10} {'Entry':<10} {'Stop-Loss':<10} {'Target-1':<10} {'R:R':<6}"
    print(header)
    print("-" * 90)

    for a in alerts:
        symbol = a.get("symbol", "N/A")
        signal = a.get("signal_type", "N/A")
        score = f"{a.get('confidence', 0)}/100"
        price = f"₹{a.get('current_price', 0):.2f}"
        entry = f"₹{a.get('entry_price', 0):.2f}"
        stop = f"₹{a.get('stop_loss_price', 0):.2f}"
        target = f"₹{a.get('target_price_1', 0):.2f}"
        rr = f"1:{a.get('risk_reward_ratio', 0):.1f}"

        print(f"{symbol:<12} {signal:<16} {score:<8} {price:<10} {entry:<10} {stop:<10} {target:<10} {rr:<6}")

    print("-" * 90)
    print(f" Total Alerts: {len(alerts)}")
    print("=" * 90 + "\n")


def view_recent_alerts(date_str: str | None = None,
                       min_score: int = 0,
                       symbol_filter: str | None = None,
                       intraday: bool = False) -> list[dict]:
    """Retrieve and filter recent alerts."""
    report_file, report_data = load_latest_report(date_str, intraday=intraday)
    if not report_file or not report_data:
        log.info("No report data available.")
        return []

    alerts = report_data.get("alerts", [])
    
    if min_score > 0:
        alerts = [a for a in alerts if a.get("confidence", 0) >= min_score]

    if symbol_filter:
        symbol_filter = symbol_filter.upper()
        alerts = [a for a in alerts if a.get("symbol", "").upper() == symbol_filter]

    display_alerts_table(alerts, title=f"Scan Alerts ({report_file.name})")
    return alerts


def view_history(intraday: bool = False):
    """View stored alert history."""
    history = load_alert_history(intraday=intraday)
    label = "INTRADAY PORTFOLIO" if intraday else "DAILY SWING"
    print("\n" + "=" * 70)
    print(f" 📜 {label} ALERT DEDUPLICATION HISTORY")
    print("=" * 70)
    if not history:
        print(" No alert history recorded yet.")
        print("=" * 70 + "\n")
        return

    for symbol, signals in history.items():
        print(f"\n🔹 {symbol}")
        for sig_type, timestamp in signals.items():
            print(f"   - {sig_type:<18} Last trigger: {timestamp}")

    print("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="View Stock Bot Alerts")
    parser.add_argument("--date", type=str, help="Report date YYYYMMDD (default: latest)")
    parser.add_argument("--min-score", type=int, default=0, help="Filter alerts by minimum confidence score")
    parser.add_argument("--symbol", type=str, help="Filter alerts by symbol (e.g. RELIANCE)")
    parser.add_argument("--intraday", action="store_true", help="View intraday market hours portfolio alerts")
    parser.add_argument("--history", action="store_true", help="View alert history tracking")

    args = parser.parse_args()

    if args.history:
        view_history(intraday=args.intraday)
    else:
        view_recent_alerts(
            date_str=args.date,
            min_score=args.min_score,
            symbol_filter=args.symbol,
            intraday=args.intraday,
        )


if __name__ == "__main__":
    main()
