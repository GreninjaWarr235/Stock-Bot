# 📈 Stock Bot - Complete User Guide & Operational Manual

The **Stock Bot** is an automated, end-to-end technical analysis scanner built specifically for National Stock Exchange (NSE) equity swing trading. It identifies high-probability breakout, reversal, and momentum patterns after market close, computes exact entry, stop-loss, and multi-target price levels, and dispatches formatted alerts directly to Telegram.

---

## 📋 Table of Contents

1. [Architecture & Directory Structure](#-architecture--directory-structure)
2. [Quick Start & Setup](#-quick-start--setup)
3. [Telegram Notification Setup](#-telegram-notification-setup)
4. [Manual Scanner Execution](#-manual-scanner-execution)
5. [Market Hours Intraday Portfolio Detection System](#-market-hours-intraday-portfolio-detection-system-915-am---330-pm-ist)
6. [Automated Market Close Scheduling](#-automated-market-close-scheduling)
7. [Analytics & Performance Engine](#-analytics--performance-engine)
8. [Trading Signal & Pattern Logic](#-trading-signal--pattern-logic)
9. [Troubleshooting & Maintenance](#-troubleshooting--maintenance)

---

## 🏗️ Architecture & Directory Structure

```text
d:\Stock Bot\
├── DOCUMENTATION.md           # Master documentation (this file)
├── .github/
│   └── workflows/
│       ├── daily-scanner.yml       # GitHub Actions daily scanner (4:05 PM IST)
│       └── intraday-scanner.yml    # GitHub Actions intraday scanner
├── pyrightconfig.json         # Pylance/Pyright search path configuration
├── .vscode/
│   └── settings.json          # VS Code IDE Python environment settings
└── bot/                       # Core application root
    ├── .env                   # Active environment configuration (git-ignored)
    ├── .env.template          # Environment template file
    ├── scheduler.py           # Daily close daemon background scheduler
    ├── intraday_scheduler.py  # Market hours intraday daemon background scheduler
    ├── tasks/                 # Windows Task Scheduler & batch script files
    │   ├── run_scanner.bat            # Daily market close execution batch script
    │   ├── run_intraday_scanner.bat   # Market hours intraday batch script
    │   ├── setup_task.ps1             # Windows Task Scheduler script for daily scan (4:05 PM)
    │   └── setup_intraday_task.ps1    # Windows Task Scheduler script for intraday scan (9:15 AM - 3:30 PM)
    ├── alerts/                # Signal generation & notification module
    │   ├── __init__.py
    │   ├── alerts.py          # Alert data model & AlertGenerator scoring engine
    │   ├── indicators.py      # EMA, RSI, MACD, ATR, Bollinger Bands algorithms
    │   ├── intraday_scanner.py # Market hours intraday portfolio scanner
    │   ├── notifier.py        # Telegram HTTP API dispatcher & rate-limiter
    │   ├── patterns.py        # Pattern recognition routines (Breakouts, Reversals)
    │   └── scanner.py         # Main daily scanner workflow entry point
    ├── analytics/             # Reporting & metrics module
    │   ├── __init__.py
    │   ├── performance.py     # Win-rate & risk performance scorecard engine
    │   ├── report_generator.py # Markdown digest builder
    │   └── view_alerts.py     # CLI interactive alert browser & filter
    ├── config/                # System configuration & logging
    │   ├── __init__.py
    │   ├── logger.py          # Structured file & CLI logger
    │   └── settings.py        # Global environment settings & constants
    ├── data/                  # Data loading & validation engine
    │   ├── __init__.py
    │   └── loader.py          # OHLCV data loader & NSE stock universe builder
    ├── logs/                  # Daily runtime log files (`india_swing_YYYYMMDD.log`)
    └── reports/               # JSON scan outputs & Markdown summaries
```

---

## ⚙️ Quick Start & Setup

### Step 1: Virtual Environment Activation

The bot runs inside a pre-configured Python virtual environment inside `bot/venv/`.

**In PowerShell / Command Prompt:**

```powershell
cd "d:\Stock Bot\bot"
.\venv\Scripts\activate
```

### Step 2: Environment Configuration (`.env`)

Create a `.env` file in `d:\Stock Bot\bot\` by copying `.env.template`:

```powershell
cp .env.template .env
```

Edit `bot/.env` to configure your settings:

```env
# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyZ
TELEGRAM_CHAT_ID=987654321

# Alert Thresholds
ALERT_MIN_SCORE=70
MIN_PRICE=50.0
MIN_AVG_DAILY_VOLUME=200000
ALERT_DEDUP_HOURS=4
DATA_SOURCE=yfinance
```

---

## 📲 Telegram Notification Setup

To receive real-time alerts on your mobile phone or desktop:

### 1. Create a Bot via `@BotFather`

1. Open Telegram and search for `@BotFather`.
2. Start a chat and send `/newbot`.
3. Give your bot a name (e.g., `MySwingAlertBot`) and a username ending in `bot` (e.g., `MySwingAlerts_bot`).
4. Copy the HTTP API **Bot Token** (looks like `123456789:AAF...`).
5. Paste this as `TELEGRAM_BOT_TOKEN` in `bot/.env`.

### 2. Obtain Your Chat ID

1. Search for your newly created bot in Telegram and click **Start** or send a message like `/start`.
2. Search for `@userinfobot` or `@GetIDBot` on Telegram and send a message.
3. Copy your numeric **Id** (e.g., `987654321`).
4. Paste this as `TELEGRAM_CHAT_ID` in `bot/.env`.

### 3. Verify Connection

Run the Telegram connectivity test from terminal:

```powershell
python -m alerts.scanner --test
```

*Expected Output:*

```text
2026-08-28 17:15:00 [INFO] [alerts.notifier] Test message sent successfully
2026-08-28 17:15:00 [INFO] [__main__]   telegram: OK ✓
```

Check Telegram; you should receive a message: `✅ Telegram Notifier Test`.

---

## 🚀 Manual Scanner Execution

You can run scans manually at any time using the virtual environment python command.

### 1. Default Watchlist Scan (Top Symbols)

Scans top Nifty equity candidates:

```powershell
python -m alerts.scanner
```

### 2. Scan Specific Symbols

Pass targeted stock tickers using `--symbols`:

```powershell
python -m alerts.scanner --symbols RELIANCE TCS INFOSYS TATAMOTORS
```

### 3. Full Market Universe Scan

Scans the entire stock universe dataset (~5-10 minutes):

```powershell
python -m alerts.scanner --full-universe
```

---

## ⚡ Market Hours Intraday Portfolio Detection System (9:15 AM - 3:30 PM IST)

The **Intraday Portfolio Detection System** continuously monitors your personal portfolio stocks defined in `bot/data/universe/portfolio.csv` during active market hours (09:15 AM to 03:30 PM IST, Mon-Fri).

### 1. Target Portfolio File (`data/universe/portfolio.csv`)

Edit `bot/data/universe/portfolio.csv` to customize your target portfolio stocks:

```csv
symbol,name,sector,index
RELIANCE,Reliance Industries Ltd,Energy,PORTFOLIO
TCS,Tata Consultancy Services Ltd,IT,PORTFOLIO
HDFCBANK,HDFC Bank Ltd,Banking,PORTFOLIO
INFY,Infosys Ltd,IT,PORTFOLIO
```

### 2. Manual & Test Execution

- **Run Intraday Scan during Market Hours:**

  ```powershell
  python -m alerts.intraday_scanner
  ```

- **Force Run Scan Outside Market Hours (Testing):**

  ```powershell
  python -m alerts.intraday_scanner --force
  ```

- **One-Click Batch Script:**

  ```powershell
  .\tasks\run_intraday_scanner.bat
  ```

### 3. Intraday Automation & Scheduling Options

**Option A: Windows Task Scheduler (Recommended - `SwingBotIntradayScanner`)**

Registers a Windows Scheduled Task `SwingBotIntradayScanner` that executes `run_intraday_scanner.bat` **every 15 minutes** between **09:15 AM and 03:30 PM IST**, Monday through Friday:

```powershell
cd "d:\Stock Bot\bot"
powershell -ExecutionPolicy Bypass -File .\tasks\setup_intraday_task.ps1
```

**Task Properties:**

- **Task Name**: `SwingBotIntradayScanner`
- **Schedule**: Mon-Fri, 9:15 AM to 3:30 PM IST (Repeats every 15 mins)
- **Wake from Sleep**: Enabled
- **Run on Battery**: Enabled

**Useful Task Management Commands:**

- *Check task status:*

  ```powershell
  Get-ScheduledTask -TaskName "SwingBotIntradayScanner"
  ```

- *Trigger task manually:*

  ```powershell
  Start-ScheduledTask -TaskName "SwingBotIntradayScanner"
  ```

- *Remove task:*

  ```powershell
  Unregister-ScheduledTask -TaskName "SwingBotIntradayScanner" -Confirm:$false
  ```

**Option B: Continuous Intraday Daemon**

Runs a background daemon polling every 15 minutes during active market sessions:

```powershell
python intraday_scheduler.py --interval 15
```

### 4. Viewing Intraday Alerts

To view generated intraday alerts in CLI:

```powershell
python -m analytics.view_alerts --intraday
```

### 5. GitHub Actions Deployment (Cloud, $0 Option)

The bot can be run automatically without a Render server by using GitHub Actions scheduled workflows. This is the recommended cloud deployment option for the current scanner architecture because both scanners are short-lived jobs rather than continuously running processes.

The workflows are stored in:

```text
.github/
└── workflows/
    ├── daily-scanner.yml
    └── intraday-scanner.yml
```

**GitHub Actions requirements:**

- The repository must be pushed to GitHub.
- `.github/` must **not** be included in `.gitignore`.
- `.env` must remain git-ignored and must never be committed.
- Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as GitHub Actions repository secrets.
- `yfinance` must be included in `requirements.txt`.
- `DATA_SOURCE` should be set to `yfinance` for cloud execution.

**GitHub Actions secrets:**

Go to:

`GitHub → Repository → Settings → Secrets and variables → Actions`

Create:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

The workflow injects these values as environment variables; the actual credentials are not stored in the repository.

**Daily scanner schedule:**

The daily scanner runs at **4:05 PM IST, Monday-Friday**, using:

```yaml
schedule:
  - cron: "35 10 * * 1-5"
```

GitHub Actions cron schedules use UTC, so `10:35 UTC = 4:05 PM IST`.

**Intraday scanner schedule:**

The intraday workflow uses two cron entries:

```yaml
schedule:
  # 9:15 AM IST
  - cron: "45 3 * * 1-5"

  # 9:30 AM IST through 3:15 PM IST
  - cron: "0,15,30,45 4-9 * * 1-5"
```

These produce scans at approximately:

```text
09:15 IST
09:30 IST
09:45 IST
10:00 IST
...
15:00 IST
15:15 IST
```

A separate **3:30 PM IST** scan is intentionally not scheduled. The Python market-hours check still considers 3:30 PM IST within market hours.

GitHub Actions scheduled workflows are not guaranteed to start at the exact cron minute, so this should be treated as a periodic alerting mechanism rather than a precision trading scheduler.

**Manual workflow testing:**

Both workflows include `workflow_dispatch`, allowing a manual run from:

`GitHub → Actions → <workflow name> → Run workflow`

For testing the intraday scanner outside market hours, run locally with:

```powershell
python -m alerts.intraday_scanner --force
```

The `--force` flag bypasses the market-hours guard only; it does not change the data source or execution behavior.

**Data source configuration:**

The data loader supports:

- `synthetic` — deterministic synthetic GBM data for offline testing.
- `csv` — local CSV data.
- `yfinance` — Yahoo Finance data for NSE symbols using the `.NS` suffix.

For daily scans, `yfinance` requests daily candles. For intraday scans, the scanner requests `15m` candles using a recent Yahoo Finance window.

The intraday scanner must pass:

```python
interval="15m"
```

to `load_data()`. The daily scanner can use the default daily interval.

The scanner reads the data source from `config.settings.DATA_SOURCE`; it should not hard-code `source="synthetic"`.

**Environment configuration:**

The local `.env` can remain configured for development/testing:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

ALERT_MIN_SCORE=70
MIN_PRICE=50.0
MIN_AVG_DAILY_VOLUME=200000
ALERT_DEDUP_HOURS=4

DATA_SOURCE=synthetic
```

For GitHub Actions, the deployment environment uses:

```text
DATA_SOURCE=yfinance
```

while the alert thresholds retain their defaults unless explicitly overridden.

`EXECUTION_MODE` is not part of the current configuration because it is not used by the scanner/data-loader code.

**Timezone handling:**

GitHub Actions runners use UTC. Application logic therefore explicitly uses `Asia/Kolkata` for Indian market-hour checks and log timestamps.

The logger in `config/logger.py` formats timestamps in IST, including the date used for daily log filenames.

---

## ⏰ Automated Market Close Scheduling

Indian stock markets close at 3:30 PM IST. The scanner is designed to run automatically at **4:05 PM IST** every weekday after daily price candle close.

### Option A: Windows Task Scheduler (Recommended)

A PowerShell script `bot/tasks/setup_task.ps1` automatically registers a background task named `SwingBotScanner`.

**Features of Scheduled Task:**

- Runs automatically **Monday through Friday at 4:05 PM IST**.
- **Wakes Windows from sleep** to execute the scan.
- Runs whether logged in or locked.
- Operates on AC power or laptop battery.

**Setup Instructions:**

1. Open PowerShell as Administrator (or standard user context).
2. Execute the registration script:

   ```powershell
   cd "d:\Stock Bot\bot"
   powershell -ExecutionPolicy Bypass -File .\tasks\setup_task.ps1
   ```

3. Verify in Windows Task Scheduler (`taskschd.msc`):
   - Look for **SwingBotScanner** under Task Scheduler Library.

### Option B: Built-in Python Background Daemon

If you prefer to leave a continuous background terminal process running:

```powershell
python scheduler.py --time 16:05
```

This daemon sleeps until 16:05 IST each market weekday, triggers `scan_universe()`, and repeats automatically.

### Option C: GitHub Actions (Cloud)

For a cloud-based, no-server deployment, use `.github/workflows/daily-scanner.yml`.

The workflow runs:

```text
Monday-Friday at 4:05 PM IST
```

using:

```yaml
cron: "35 10 * * 1-5"
```

GitHub Actions is used instead of Render Cron Jobs for the current deployment because Render Cron Jobs require a paid service, while GitHub Actions provides a suitable scheduled runner for this short-lived scanner.

---

## 📊 Analytics & Performance Engine

The bot includes an analytics suite to review past alerts, measure historical signal performance, and generate digests.

### 1. Interactive Alert Browser (`analytics.view_alerts`)

View the latest scan results or search historical reports directly from your CLI:

- **View latest scan alerts:**

  ```powershell
  python -m analytics.view_alerts
  ```

- **Filter by minimum confidence score (e.g., ≥80/100):**

  ```powershell
  python -m analytics.view_alerts --min-score 80
  ```

- **Filter by stock symbol:**

  ```powershell
  python -m analytics.view_alerts --symbol RELIANCE
  ```

- **View specific report date:**

  ```powershell
  python -m analytics.view_alerts --date 20260828
  ```

- **View deduplication history tracking:**

  ```powershell
  python -m analytics.view_alerts --history
  ```

### 2. Performance Scorecard Engine (`analytics.performance`)

Generates a statistical breakdown of historical signal performance:

```powershell
python -m analytics.performance
```

*Output Summary:*

```text
======================================================================
 📈 SWING TRADING ALERT SYSTEM - PERFORMANCE SCORECARD
======================================================================
 Total Signals Evaluated : 78
 Win Rate                : 65.4%
 Profit Factor           : 2.15
 Avg Trade Return        : +2.45%
 Avg Win / Avg Loss      : +4.20% / -1.95%
 Avg Risk/Reward Ratio   : 1:2.15
 Estimated Sharpe Ratio  : 1.85
 Max Historical Drawdown : -8.4%
----------------------------------------------------------------------
 📋 SIGNAL BREAKDOWN BY PATTERN TYPE:
 Pattern            Count    Win Rate   Avg Gain
----------------------------------------------------------------------
 BREAKOUT_UP        25       68.0%      +3.20%
 REVERSAL_UP        18       62.5%      +2.40%
 RISING_PEAKS       12       72.0%      +2.90%
======================================================================
```

### 3. Markdown Digest Generator (`analytics.report_generator`)

Creates a formatted markdown digest report stored at `bot/reports/summary_report.md`:

```powershell
python -m analytics.report_generator
```

---

## 🧠 Trading Signal & Pattern Logic

The alert engine validates signals against strict price action & indicator criteria to avoid false breakouts:

1. **Pattern Recognition Engine (`alerts/patterns.py`)**:
   - `BREAKOUT_UP`: Price breaks above 20-day high with volume > 1.5× 20-day SMA and RSI > 55.
   - `REVERSAL_UP`: Bullish candlestick pattern at lower Bollinger Band with oversold RSI recovery.
   - `MACD_UP`: MACD line crosses above Signal line with positive histogram slope.
   - `RISING_PEAKS`: Trend confirmation with higher highs and higher lows over 20 candles.
   - `GAP_UP`: Bullish opening gap with strong volume continuation.

2. **Scoring & Confluence Bonus (`alerts/alerts.py`)**:
   - Base confidence score (0-100) computed per pattern.
   - Confluence Bonus (+5 to +10 points) awarded when multiple independent patterns agree.

3. **Volatility-Adjusted Levels & Risk Management**:
   - **Stop-Loss**: Placed dynamically at 1.5 × ATR₁₄ below entry price.
   - **Target-1**: Placed at 2.0 × ATR₁₄ (Risk:Reward minimum 1:1.5).
   - **Target-2**: Placed at 3.0 × ATR₁₄ for runner targets.

4. **Deduplication Engine**:
   - Stores sent alerts in `bot/alerts/alert_history.json`.
   - Suppresses duplicate alerts for the same symbol/signal within 4 hours.

---

## 🔍 Troubleshooting & Maintenance

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| `Cannot find module alerts.alerts` | Python search path mismatch in IDE | Open root folder `d:\Stock Bot` in VS Code. `pyrightconfig.json` and `.vscode/settings.json` resolve paths automatically. |
| `Telegram credentials not configured` | Missing or blank `.env` values | Ensure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set in `bot/.env`. |
| `Weekend detected. Skipping scan.` | Scanner run on Saturday/Sunday | Market is closed. Pass `--force` or specify `--symbols` if testing on weekends. |
| Scheduled Task didn't run | Windows sleep mode or permission issue | Verify `SwingBotScanner` or `SwingBotIntradayScanner` in Task Scheduler (`taskschd.msc`). Run `bot/setup_task.ps1` or `bot/setup_intraday_task.ps1` to re-register tasks. |
| View logs | Check daily logs | Open log files in `bot/logs/stock_bot_YYYYMMDD.log`. Log timestamps are formatted in IST. |
| GitHub Actions job skipped outside market hours | Intraday scanner checks Asia/Kolkata market hours | This is expected on weekends/outside 09:15-15:30 IST. Use `--force` for a manual local test. |
| yfinance returns no data | Incorrect data source or ticker format | Use `DATA_SOURCE=yfinance`, ensure `yfinance` is in `requirements.txt`, and keep CSV symbols as plain NSE symbols such as `RELIANCE`, not `RELIANCE.NS`. |
| GitHub Actions authentication failure | Telegram secrets missing | Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` under repository Actions secrets. Never commit `.env`. |
| GitHub Actions workflow not visible | Workflow file not committed | Ensure `.github/workflows/*.yml` is tracked by Git and pushed to the default branch. Do not add `.github/` to `.gitignore`. |

---

*Happy Trading! Always practice strict risk management.* 🚀