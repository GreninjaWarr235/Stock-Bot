"""
alerts/notifier.py
==================
Sends alerts via Telegram, email, and other channels.

Handles:
- Telegram bot messaging
- Rich formatting with emojis and indicators
- Rate limiting to avoid spam
- Retry logic for failed sends
- Alert logging for audit trail

For Telegram setup:
1. Create bot via @BotFather
2. Get TOKEN and CHAT_ID
3. Store in .env as TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
"""

from __future__ import annotations

import logging
import time
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from config.settings import TZ_IST

import requests

from config.settings import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from config.logger import log_event, get_logger
try:
    from alerts.alerts import Alert
except (ImportError, ModuleNotFoundError):
    try:
        from .alerts import Alert
    except (ImportError, ModuleNotFoundError):
        from alerts import Alert

log = get_logger(__name__)


class TelegramNotifier:
    """
    Sends alerts to Telegram with formatting and error handling.
    """
    
    def __init__(self,
                 bot_token: str = TELEGRAM_BOT_TOKEN,
                 chat_id: str = TELEGRAM_CHAT_ID,
                 retry_count: int = 3,
                 retry_delay: float = 2.0):
        """
        Parameters:
        - bot_token: Telegram bot API token
        - chat_id: Destination chat ID
        - retry_count: Number of retry attempts on failure
        - retry_delay: Seconds between retries
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Validate credentials
        if not self.bot_token or not self.chat_id:
            log.warning("Telegram credentials not configured. Alerts will not be sent.")
            self.enabled = False
        else:
            self.enabled = True
    
    def send_alert(self, alert: Alert) -> bool:
        """
        Send a trading alert via Telegram.
        Returns True if successful, False otherwise.
        """
        if not self.enabled:
            log.debug(f"Telegram disabled. Alert not sent: {alert.symbol}")
            return False
        
        message = alert.format_telegram()
        
        for attempt in range(1, self.retry_count + 1):
            try:
                result = self._send_message(message)
                if result:
                    log_event(
                        log,
                        "ALERT_SENT",
                        level="INFO",
                        symbol=alert.symbol,
                        signal=alert.signal_type,
                        confidence=alert.confidence,
                        rr_ratio=f"{alert.risk_reward_ratio:.1f}",
                    )
                    return True
                else:
                    log.warning(f"Attempt {attempt}: Failed to send alert for {alert.symbol}")
            except Exception as exc:
                log.error(f"Attempt {attempt}: Exception sending alert: {exc}")
            
            if attempt < self.retry_count:
                log.info(f"Retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)
        
        log.error(f"Failed to send alert for {alert.symbol} after {self.retry_count} attempts")
        return False
    
    def _send_message(self, text: str) -> bool:
        """
        Send a message to Telegram chat. Returns True if successful.
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",  # For potential formatting later
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result.get("ok", False)
        except requests.exceptions.RequestException as exc:
            log.error(f"Telegram API error: {exc}")
            return False
    
    def send_summary(self, alerts: list[Alert], duration_minutes: int = 60) -> bool:
        """
        Send a summary of all alerts generated in a scan run.
        """
        if not alerts or not self.enabled:
            return False
        
        total_alerts = len(alerts)
        buy_signals = sum(1 for a in alerts if "UP" in a.signal_type or "UP" in a.description)
        sell_signals = total_alerts - buy_signals
        
        avg_confidence = sum(a.confidence for a in alerts) / total_alerts if alerts else 0
        
        # Group by symbol
        by_symbol = {}
        for alert in alerts:
            if alert.symbol not in by_symbol:
                by_symbol[alert.symbol] = []
            by_symbol[alert.symbol].append(alert)
        
        summary = f"""📊 SCAN SUMMARY ({duration_minutes}min run)

🎯 Alerts Generated: {total_alerts}
  ↗️ Buy Signals: {buy_signals}
  ↘️ Sell Signals: {sell_signals}
📈 Avg Confidence: {avg_confidence:.0f}/100

📋 Breakdown:"""
        
        for symbol in sorted(by_symbol.keys())[:20]:  # Show top 20
            symbol_alerts = by_symbol[symbol]
            signals_str = ", ".join([a.signal_type for a in symbol_alerts])
            summary += f"\n  {symbol}: {signals_str}"
        
        summary += f"""

⏰ Time: {datetime.now(ZoneInfo(TZ_IST)).strftime('%Y-%m-%d %H:%M IST')}
✅ Check individual alerts above for details."""
        
        return self._send_message(summary)
    
    def send_test_message(self) -> bool:
        """Send a test message to verify Telegram connectivity."""
        message = """✅ Telegram Notifier Test
        
If you see this message, your Telegram bot is configured correctly!

You will receive trading alerts here."""
        
        result = self._send_message(message)
        if result:
            log.info("Test message sent successfully")
        else:
            log.error("Test message failed")
        return result


class EmailNotifier:
    """
    Sends alerts via email. (Stub for now; implement if needed)
    """
    
    def __init__(self, smtp_server: str = None, sender: str = None, password: str = None):
        self.smtp_server = smtp_server
        self.sender = sender
        self.password = password
        self.enabled = all([smtp_server, sender, password])
    
    def send_alert(self, alert: Alert) -> bool:
        if not self.enabled:
            return False
        # Implementation deferred
        log.debug("Email notifications not yet implemented")
        return False


class NotificationHub:
    """
    Unified notification interface. Supports multiple channels.
    """
    
    def __init__(self):
        self.telegram = TelegramNotifier()
        self.email = EmailNotifier()
        self.channels = [self.telegram, self.email]
    
    def send_alert(self, alert: Alert) -> dict[str, bool]:
        """
        Send alert to all configured channels.
        Returns dict of {channel_name: success}.
        """
        results = {}
        
        if self.telegram.enabled:
            results["telegram"] = self.telegram.send_alert(alert)
        
        if self.email.enabled:
            results["email"] = self.email.send_alert(alert)
        
        return results
    
    def test_connectivity(self) -> dict[str, bool]:
        """Test all configured notification channels."""
        results = {}
        
        if self.telegram.enabled:
            results["telegram"] = self.telegram.send_test_message()
        
        if self.email.enabled:
            log.info("Email test not implemented")
            results["email"] = False
        
        return results
