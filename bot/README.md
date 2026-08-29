# 📈 Stock Alert Bot - Quick User Guide

An automated trading alert system for Indian Stock Market (NSE) equity trading. It runs two dedicated bots:
1. ⚡ **Intraday Portfolio Bot** (Mon–Fri, 9:15 AM to 3:30 PM IST)
2. 📊 **Swing Trading Scanner** (Mon–Fri, 4:05 PM IST after market close)

All alerts are delivered directly to your Telegram phone app.

---

## ⚡ Quick Setup (Do This First)

### 1. Configure Telegram Alerts
1. Open Telegram and search for **`@BotFather`**.
2. Send `/newbot` and follow instructions to get your **Bot Token** (e.g. `123456789:ABC...`).
3. Search for **`@userinfobot`** on Telegram to get your numeric **Chat ID** (e.g. `987654321`).
4. Open the file `bot/.env` (or copy `.env.template` to `.env`) and add your keys:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyZ
   TELEGRAM_CHAT_ID=987654321
   ```

### 2. Test Your Telegram Connection
Open PowerShell/Command Prompt in `d:\Stock Bot\bot` and run:
```powershell
python -m alerts.scanner --test
```
You should receive a test notification on Telegram: `OK ✓`.

---

## ⚡ 1. Intraday Portfolio Bot (9:15 AM - 3:30 PM IST)

Monitors your personal portfolio stocks continuously during live market hours.

### Target Stock List
Edit `bot/data/universe/portfolio.csv` to add your portfolio stock symbols (e.g. `RELIANCE`, `TCS`, `INFY`):
```csv
symbol,name,sector,index
RELIANCE,Reliance Industries Ltd,Energy,PORTFOLIO
TCS,Tata Consultancy Services Ltd,IT,PORTFOLIO
INFY,Infosys Ltd,IT,PORTFOLIO
```

### How to Run

* **Run Manually Anytime:**
  Double-click `bot/tasks/run_intraday_scanner.bat` or run:
  ```powershell
  python -m alerts.intraday_scanner --force
  ```

* **Automate via Windows Task Scheduler (Recommended):**
  Runs automatically every 15 minutes during market hours (9:15 AM – 3:30 PM IST).
  Open PowerShell in `bot/` directory and run:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\tasks\setup_intraday_task.ps1
  ```

* **Run in Background Daemon Mode:**
  ```powershell
  python intraday_scheduler.py --interval 15
  ```

---

## 📊 2. Swing Trading Bot (Market Close 4:05 PM IST)

Scans the Nifty equity universe daily after market close to catch multi-day swing breakout & reversal setups.

### Target Stock List
Uses `bot/data/universe/nse_tracker.csv`.

### How to Run

* **Run Manually Anytime:**
  Double-click `bot/tasks/run_scanner.bat` or run:
  ```powershell
  python -m alerts.scanner
  ```

* **Automate via Windows Task Scheduler (Recommended):**
  Runs automatically every weekday at 4:05 PM IST.
  Open PowerShell in `bot/` directory and run:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\tasks\setup_task.ps1
  ```

---

## 📱 Viewing Generated Alerts

Besides Telegram, you can browse alerts in your command line:

* **View Latest Intraday Alerts:**
  ```powershell
  python -m analytics.view_alerts --intraday
  ```

* **View Latest Swing Alerts:**
  ```powershell
  python -m analytics.view_alerts
  ```

* **Filter High-Confidence Signals (Score ≥ 80):**
  ```powershell
  python -m analytics.view_alerts --min-score 80
  ```

---

## 📖 Full Documentation
For complete technical details, indicator algorithms, and troubleshooting, see [DOCUMENTATION.md](../DOCUMENTATION.md).
