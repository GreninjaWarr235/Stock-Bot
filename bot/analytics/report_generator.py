"""
analytics/report_generator.py
==============================
Generates Markdown summary reports of trading alerts and scan history.

Usage:
    python -m analytics.report_generator
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

# Ensure 'bot' directory is in sys.path
BOT_DIR = Path(__file__).resolve().parent.parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from datetime import datetime

from config.settings import REPORTS_DIR
from config.logger import get_logger

log = get_logger(__name__)


def generate_markdown_summary(output_file: Path | None = None) -> Path:
    """Generate a clean markdown summary report from recent alert scan files."""
    if output_file is None:
        output_file = REPORTS_DIR / "summary_report.md"

    report_files = sorted(REPORTS_DIR.glob("alerts_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    md_lines = [
        "# 📊 Swing Trading Alert System - Digest Report",
        f"**Generated At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}  ",
        f"**Total Scan Runs Found:** {len(report_files)}",
        "",
        "---",
        "",
        "## 🚀 Recent Scans & Alerts",
        "",
    ]

    if not report_files:
        md_lines.append("No scan reports found in `reports/` directory.")
    else:
        for rf in report_files[:5]:  # Summarize last 5 runs
            try:
                with open(rf, "r", encoding="utf-8") as f:
                    data = json.load(f)

                scan_time = data.get("scan_time", "Unknown")
                alerts = data.get("alerts", [])
                symbols_scanned = data.get("symbols_scanned", 0)

                md_lines.append(f"### 📅 Scan: {rf.name}")
                md_lines.append(f"- **Scan Time:** {scan_time}")
                md_lines.append(f"- **Symbols Scanned:** {symbols_scanned}")
                md_lines.append(f"- **Alerts Generated:** {len(alerts)}")
                md_lines.append("")

                if alerts:
                    md_lines.append("| Symbol | Signal | Score | Price | Entry | Stop-Loss | Target-1 | R:R |")
                    md_lines.append("|---|---|---|---|---|---|---|---|")
                    for a in alerts:
                        md_lines.append(
                            f"| **{a.get('symbol')}** | {a.get('signal_type')} | {a.get('confidence')}/100 | "
                            f"₹{a.get('current_price', 0):.2f} | ₹{a.get('entry_price', 0):.2f} | "
                            f"₹{a.get('stop_loss_price', 0):.2f} | ₹{a.get('target_price_1', 0):.2f} | "
                            f"1:{a.get('risk_reward_ratio', 0):.1f} |"
                        )
                    md_lines.append("")

            except Exception as e:
                log.warning(f"Could not parse {rf}: {e}")

    md_content = "\n".join(md_lines)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    log.info(f"Markdown summary report generated at {output_file}")
    return output_file


def main():
    path = generate_markdown_summary()
    print(f"Report generated successfully: {path}")


if __name__ == "__main__":
    main()
