# 📈 Stock Bot - Complete User Guide & Operational Manual

The Stock Bot is an automated, end-to-end technical analysis scanner built specifically for National Stock Exchange (NSE) equity swing trading. It identifies high-probability breakout, reversal, and momentum patterns after market close, computes exact entry, stop-loss, and multi-target price levels, and dispatches formatted alerts directly to Telegram.

---

## 📋 Table of Contents

1. [Architecture & Directory Structure](#-architecture--directory-structure)
2. [Quick Start & Setup](#-quick-start--setup)
3. [Telegram Notification Setup](#-telegram-notification-setup)
4. [Manual Scanner Execution](#-manual-scanner-execution)
5. [Market Hours Intraday Portfolio Detection System](#-market-hours-intraday-portfolio-detection-system-915-am---330-pm-ist)
6. [Production Scheduling on Oracle Cloud](#️-production-scheduling-on-oracle-cloud)
7. [Analytics & Performance Engine](#-analytics--performance-engine)
8. [Trading Signal & Pattern Logic](#-trading-signal--pattern-logic)
9. [Troubleshooting & Maintenance](#-troubleshooting--maintenance)

---

## 🏗️ Architecture & Directory Structure

**Local development (Windows)**

```text
D:\Stock Bot\
├── DOCUMENTATION.md
├── pyrightconfig.json
└── bot/
    ├── .env.template
    ├── intraday_scheduler.py
    ├── alerts/
    │   ├── alerts.py
    │   ├── indicators.py
    │   ├── intraday_scanner.py
    │   ├── notifier.py
    │   ├── patterns.py
    │   └── scanner.py
    ├── analytics/
    ├── config/
    ├── data/
    ├── reports/
    └── logs/
```

**Production (Oracle Cloud)**

```text
Oracle Cloud VM (Ubuntu 24.04)
└── /home/ubuntu/Stock-Bot/
    ├── .env                    # git-ignored production configuration
    ├── venv/                   # Python virtual environment
    └── bot/
        ├── intraday_scheduler.py
        ├── alerts/
        │   ├── intraday_scanner.py
        │   └── scanner.py
        ├── config/
        ├── data/
        ├── reports/
        └── logs/

systemd
├── stock-bot.service           # long-running intraday Python scheduler
├── stock-bot-daily.timer       # 4:05 PM IST weekday scheduler
└── stock-bot-daily.service     # one-shot daily scanner execution
```

The production source of truth for automated scanning is Oracle Cloud. GitHub is used for source-code version control and deployment, not as the production scheduler.

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

---

## ☁️ Production Scheduling on Oracle Cloud

The production bot runs on an Oracle Cloud Always Free VM. The two scanners intentionally use different scheduling mechanisms because their execution patterns are different.

### Intraday scanner: long-running Python scheduler

`bot/intraday_scheduler.py` is a persistent process managed by `stock-bot.service`. It stays alive and handles market-session logic itself:

- Monday-Friday only.
- NSE market hours: 09:15-15:30 IST.
- Runs `alerts.intraday_scanner` every 15 minutes.
- Uses `Asia/Kolkata` explicitly for market-hour calculations.
- Waits outside market hours and over weekends.
- Restarts automatically if the process fails.

The systemd service is:

```ini
[Unit]
Description=Stock Bot Intraday Scanner
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Stock-Bot
Environment="PYTHONPATH=/home/ubuntu/Stock-Bot/bot"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/ubuntu/Stock-Bot/venv/bin/python /home/ubuntu/Stock-Bot/bot/intraday_scheduler.py
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Useful commands:

```bash
sudo systemctl status stock-bot --no-pager
sudo journalctl -u stock-bot -f
sudo systemctl restart stock-bot
```

### Daily scanner: systemd timer + one-shot service

The daily scanner only needs to execute once per weekday at 4:05 PM IST, so it does not need a continuously running Python scheduler. A systemd timer handles the schedule and starts a short-lived `Type=oneshot` service.

```text
stock-bot-daily.timer
        │
        │ Mon-Fri 16:05 IST
        ▼
stock-bot-daily.service
        │
        ▼
python -m alerts.scanner
        │
        ▼
      exits
```

Timer configuration:

```ini
[Unit]
Description=Run Stock Bot Daily Scanner at 4:05 PM IST

[Timer]
OnCalendar=Mon..Fri 16:05:00 Asia/Kolkata
Persistent=true
Unit=stock-bot-daily.service

[Install]
WantedBy=timers.target
```

Daily service configuration:

```ini
[Unit]
Description=Stock Bot Daily Scanner
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/Stock-Bot
Environment="PYTHONPATH=/home/ubuntu/Stock-Bot/bot"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/ubuntu/Stock-Bot/venv/bin/python -m alerts.scanner
```

Useful commands:

```bash
systemctl list-timers --all | grep stock-bot
sudo systemctl status stock-bot-daily.timer --no-pager
sudo systemctl start stock-bot-daily.service
sudo journalctl -u stock-bot-daily.service -n 100 --no-pager
```

Validate the timer calendar with:

```bash
systemd-analyze calendar 'Mon..Fri 16:05:00 Asia/Kolkata'
```

The application logger also formats timestamps in IST. systemd/journald may display its own service timestamps in UTC depending on the VM's system timezone; this does not change the timer's configured IST schedule.

### Oracle VM configuration

```text
Provider       : Oracle Cloud Infrastructure
OS             : Ubuntu 24.04
Shape          : VM.Standard.A1.Flex
CPU            : 1 OCPU
RAM            : 6 GB
Public IPv4    : Enabled
Repository     : /home/ubuntu/Stock-Bot
Python         : /home/ubuntu/Stock-Bot/venv
Data source    : yfinance
```

The VM is intended to remain within Oracle's Always Free allocation. Keep OCI resource usage within the applicable limits.

### Production environment

The production `.env` is stored at the repository root:

```text
/home/ubuntu/Stock-Bot/.env
```

It is git-ignored and must never be committed. Example configuration:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
ALERT_MIN_SCORE=70
MIN_PRICE=50.0
MIN_AVG_DAILY_VOLUME=200000
ALERT_DEDUP_HOURS=4
DATA_SOURCE=yfinance
```

The code explicitly resolves this root-level `.env` file.

### Production verification

Intraday scheduler syntax check:

```bash
python -m py_compile bot/intraday_scheduler.py
```

Manual intraday test:

```bash
python -m alerts.intraday_scanner --force
```

Manual daily test:

```bash
python -m alerts.scanner
```

A daily test on a weekend will correctly report that the market is closed and scan zero symbols.

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
   - **Stop-Loss**: Placed dynamically at 1.5 × ATR(14) below entry price.
   - **Target-1**: Placed at 2.0 × ATR(14) (Risk:Reward minimum 1:1.5).
   - **Target-2**: Placed at 3.0 × ATR(14) for runner targets.

4. **Deduplication Engine**:
   - Stores sent alerts in `bot/alerts/alert_history.json`.
   - Suppresses duplicate alerts for the same symbol/signal within 4 hours.

---

## 🔍 Troubleshooting & Maintenance

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| `Cannot find module alerts.alerts` | Python search path mismatch in IDE | Open root folder `d:\Stock Bot` in VS Code. `pyrightconfig.json` and `.vscode/settings.json` resolve paths automatically. |
| `Telegram credentials not configured` | Missing or blank `.env` values | Ensure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set in `/home/ubuntu/Stock-Bot/.env` on Oracle, or in the appropriate local root `.env`. |
| `Weekend detected. Skipping scan.` | Scanner run on Saturday/Sunday | Market is closed. Pass `--force` or specify `--symbols` if testing on weekends. |
| View logs | Check daily logs | Open log files in `bot/logs/stock_bot_YYYYMMDD.log`. Log timestamps are formatted in IST. |
| yfinance returns no data | Incorrect data source or ticker format | Use `DATA_SOURCE=yfinance`, ensure `yfinance` is in `requirements.txt`, and keep CSV symbols as plain NSE symbols such as `RELIANCE`, not `RELIANCE.NS`. |
| Oracle service not running | systemd service stopped or failed | Run `sudo systemctl status stock-bot --no-pager`, then inspect `sudo journalctl -u stock-bot -n 100 --no-pager`. |
| Oracle intraday scanner not running at market open | systemd service or scheduler issue | Run `sudo systemctl status stock-bot --no-pager` and `sudo journalctl -u stock-bot -n 100 --no-pager`. The scheduler uses IST explicitly. |
| Oracle `.env` not loaded | Incorrect `.env` path | Production `.env` must be `/home/ubuntu/Stock-Bot/.env`; verify `config/settings.py` resolves the repository root correctly. |
| Oracle daily timer not firing | Timer disabled or calendar configuration issue | Run `systemctl list-timers --all \| grep stock-bot`, `sudo systemctl status stock-bot-daily.timer --no-pager`, and `systemd-analyze calendar 'Mon..Fri 16:05:00 Asia/Kolkata'`. |

---

*Happy Trading! Always practice strict risk management.* 🚀