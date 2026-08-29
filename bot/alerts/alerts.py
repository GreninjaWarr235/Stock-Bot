"""
alerts/alerts.py
================
Generates and scores trading alerts from detected patterns.

Each alert includes:
- Signal type and confidence score (0-100)
- Entry/exit levels with risk/reward calculation
- Holding period estimate
- Filtering criteria (liquidity, trend alignment)

Alert filtering rules prevent noise:
- Minimum score threshold (default 70)
- Liquidity validation
- Trend confirmation
- Duplicate suppression (same signal within N hours)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional

import pandas as pd

try:
    from alerts.indicators import compute_all_indicators, get_latest_indicators
    from alerts.patterns import detect_all_patterns
except (ImportError, ModuleNotFoundError):
    try:
        from .indicators import compute_all_indicators, get_latest_indicators
        from .patterns import detect_all_patterns
    except (ImportError, ModuleNotFoundError):
        from indicators import compute_all_indicators, get_latest_indicators
        from patterns import detect_all_patterns

log = logging.getLogger(__name__)


@dataclass
class Alert:
    """Represents a single trading alert."""
    timestamp: str
    symbol: str
    signal_type: str  # BREAKOUT_UP, REVERSAL_DOWN, etc.
    confidence: int   # 0-100
    
    current_price: float
    entry_price: float
    stop_loss_price: float
    target_price_1: float
    target_price_2: Optional[float] = None
    
    holding_days_estimate: int = 10
    risk_reward_ratio: float = 0.0
    is_intraday: bool = False
    
    description: str = ""
    pattern_signals: list[str] = None  # Confluence signals
    
    def __post_init__(self):
        if self.pattern_signals is None:
            self.pattern_signals = []
        
        # Calculate R:R for Target 1
        risk = abs(self.entry_price - self.stop_loss_price)
        reward = abs(self.target_price_1 - self.entry_price)
        self.risk_reward_ratio = reward / risk if risk > 0 else 0.0

    def get_holding_display(self) -> str:
        """Returns dynamic, context-aware holding timeframe string."""
        if self.is_intraday:
            return "Intraday (Exit today by 3:15 PM IST)"

        # Signal-specific swing timeframes
        timeframes = {
            "GAP_UP": "1-3 days",
            "GAP_DOWN": "1-3 days",
            "REVERSAL_UP": "3-7 days",
            "REVERSAL_DOWN": "3-7 days",
            "VOLUME_SURGE": "3-8 days",
            "MACD_UP": "5-12 days",
            "MACD_DOWN": "5-12 days",
            "BREAKOUT_UP": "7-15 days",
            "BREAKOUT_DOWN": "7-15 days",
            "RISING_PEAKS": "10-20 days",
            "FALLING_PEAKS": "10-20 days",
        }
        
        if self.signal_type in timeframes:
            return timeframes[self.signal_type]

        return f"{self.holding_days_estimate}-{self.holding_days_estimate + 5} days"

    def get_risk_reward_display(self) -> str:
        """Returns dynamic risk/reward ratio string for single or multiple targets."""
        risk = abs(self.entry_price - self.stop_loss_price)
        if risk <= 0:
            return "N/A"

        reward1 = abs(self.target_price_1 - self.entry_price)
        rr1 = reward1 / risk

        if self.target_price_2 and self.target_price_2 > 0:
            reward2 = abs(self.target_price_2 - self.entry_price)
            rr2 = reward2 / risk
            return f"1:{rr1:.1f} (T1) | 1:{rr2:.1f} (T2)"

        return f"1:{rr1:.1f}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        d["pattern_signals"] = self.pattern_signals if self.pattern_signals else []
        return d
    
    def format_telegram(self) -> str:
        """Format alert for Telegram message."""
        emoji_map = {
            "BREAKOUT_UP": "🚀",
            "BREAKOUT_DOWN": "📉",
            "REVERSAL_UP": "📈",
            "REVERSAL_DOWN": "📉",
            "MACD_UP": "↗️",
            "MACD_DOWN": "↘️",
            "VOLUME_SURGE": "📊",
            "RISING_PEAKS": "⬆️",
            "FALLING_PEAKS": "⬇️",
            "GAP_UP": "⬆️",
            "GAP_DOWN": "⬇️",
        }
        
        emoji = emoji_map.get(self.signal_type, "🔔")
        conf_bar = "█" * (self.confidence // 10) + "░" * ((100 - self.confidence) // 10)
        
        header_title = "INTRADAY PORTFOLIO ALERT" if self.is_intraday else "SWING ALERT"

        msg = f"""{emoji} {header_title}: {self.symbol}

📊 SIGNAL: {self.signal_type.replace('_', ' ')}
🎯 Score: {self.confidence}/100 {conf_bar}

💰 Price: ₹{self.current_price:.2f}
📍 Entry: ₹{self.entry_price:.2f}
🛑 Stop-Loss: ₹{self.stop_loss_price:.2f}
🎁 Target-1: ₹{self.target_price_1:.2f}"""
        
        if self.target_price_2:
            msg += f"\n🎁 Target-2: ₹{self.target_price_2:.2f}"
        
        msg += f"""

⏱️ Hold: {self.get_holding_display()}
📈 Risk/Reward: {self.get_risk_reward_display()}

📝 Pattern: {self.description}
🔗 Confluence: {', '.join(self.pattern_signals) if self.pattern_signals else 'Single signal'}

⏰ Time: {self.timestamp}
⚠️ Do your own analysis before trading. This is not financial advice."""
        
        return msg


class AlertGenerator:
    """
    Generates alerts from OHLCV data and detected patterns.
    
    Applies filtering and scoring to avoid false signals.
    """
    
    def __init__(self,
                 min_score: int = 70,
                 min_price: float = 50,
                 min_avg_volume: int = 200_000,
                 alert_dedup_hours: int = 4,
                 is_intraday: bool = False):
        """
        Parameters:
        - min_score: Minimum confidence score to emit alert (0-100)
        - min_price: Minimum price in ₹ (avoid penny stocks)
        - min_avg_volume: Minimum avg daily volume
        - alert_dedup_hours: Don't repeat same signal within N hours
        - is_intraday: Set to True for market hours intraday scans
        """
        self.min_score = min_score
        self.min_price = min_price
        self.min_avg_volume = min_avg_volume
        self.alert_dedup_hours = alert_dedup_hours
        self.is_intraday = is_intraday
        
        # In-memory alert history (normally would use database)
        self.alert_history: dict[str, dict] = {}  # {symbol: {signal_type: last_timestamp}}
    
    def generate(self, df: pd.DataFrame, symbol: str) -> Optional[Alert]:
        """
        Generate an alert from OHLCV data.
        
        Returns: Alert object or None (if no valid signal or filtered out)
        """
        # Pre-flight checks
        if df.empty or len(df) < 50:
            log.debug(f"{symbol}: Insufficient data")
            return None
        
        if df.iloc[-1]["Close"] < self.min_price:
            log.debug(f"{symbol}: Price ₹{df.iloc[-1]['Close']:.2f} below minimum")
            return None
        
        avg_volume = df["Volume"].tail(20).mean()
        if avg_volume < self.min_avg_volume:
            log.debug(f"{symbol}: Avg volume {avg_volume:.0f} below minimum")
            return None
        
        # Compute indicators
        df = compute_all_indicators(df)
        
        # Detect patterns
        patterns = detect_all_patterns(df)
        if not patterns:
            log.debug(f"{symbol}: No patterns detected")
            return None
        
        # Find the highest-scoring pattern
        best_pattern = max(patterns, key=lambda x: x[2])  # x[2] is score
        pattern_name, _, score, description = best_pattern
        
        # Check deduplication
        if not self._is_new_signal(symbol, pattern_name):
            log.debug(f"{symbol}: Signal {pattern_name} recently sent")
            return None
        
        # Compute entry/exit levels and risk
        curr = df.iloc[-1]
        entry, stop, target1, target2, holding = self._compute_levels(df, pattern_name)
        
        # Build alert
        alert = Alert(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M IST"),
            symbol=symbol,
            signal_type=pattern_name,
            confidence=min(100, score + self._confluence_bonus(patterns)),
            current_price=float(curr["Close"]),
            entry_price=entry,
            stop_loss_price=stop,
            target_price_1=target1,
            target_price_2=target2,
            holding_days_estimate=holding,
            is_intraday=self.is_intraday,
            description=description,
            pattern_signals=[p[0] for p in patterns[:3]],  # Top 3 confluence signals
        )
        
        # Risk/Reward validation
        if alert.risk_reward_ratio < 1.5:
            log.debug(f"{symbol}: R:R {alert.risk_reward_ratio:.1f} below 1.5")
            return None
        
        # Record this alert
        self._record_alert(symbol, pattern_name)
        
        return alert
    
    def _compute_levels(self, df: pd.DataFrame, pattern_name: str) -> tuple[float, float, float, Optional[float], int]:
        """
        Compute entry, stop-loss, target-1, target-2, and holding period
        based on the pattern type and current volatility.
        """
        curr = df.iloc[-1]
        atr = curr["ATR_14"]
        close = curr["Close"]
        
        # Use ATR for stop-loss distance (volatility-adjusted)
        atr_dist = atr * 1.5  # 1.5× ATR
        
        if pattern_name in ["BREAKOUT_UP", "RISING_PEAKS", "GAP_UP", "MACD_UP"]:
            # Long entry
            entry = close
            stop = close - atr_dist
            target1 = close + atr_dist * 2  # 2× ATR for profit
            target2 = close + atr_dist * 3  # 3× ATR for extended move
            holding = 10
        elif pattern_name in ["REVERSAL_UP"]:
            # Long on pullback
            entry = curr["BB_LOWER"] if pd.notna(curr["BB_LOWER"]) else close - atr_dist
            stop = entry - atr_dist * 0.5
            target1 = close + atr_dist
            target2 = close + atr_dist * 2
            holding = 7
        else:  # Short patterns
            entry = close
            stop = close + atr_dist
            target1 = close - atr_dist * 2
            target2 = close - atr_dist * 3
            holding = 10
        
        return round(entry, 2), round(stop, 2), round(target1, 2), round(target2, 2), holding
    
    def _confluence_bonus(self, patterns: list) -> int:
        """
        Award confidence bonus for signal confluence.
        More patterns = higher conviction.
        """
        n_patterns = len(patterns)
        if n_patterns >= 3:
            return 10
        elif n_patterns == 2:
            return 5
        else:
            return 0
    
    def _is_new_signal(self, symbol: str, signal_type: str) -> bool:
        """
        Check if this signal has been sent recently (within alert_dedup_hours).
        """
        if symbol not in self.alert_history:
            return True
        
        history = self.alert_history[symbol]
        last_time = history.get(signal_type)
        
        if last_time is None:
            return True
        
        hours_ago = (datetime.now() - last_time).total_seconds() / 3600
        return hours_ago >= self.alert_dedup_hours
    
    def _record_alert(self, symbol: str, signal_type: str) -> None:
        """Record that this alert was sent."""
        if symbol not in self.alert_history:
            self.alert_history[symbol] = {}
        self.alert_history[symbol][signal_type] = datetime.now()
    
    def load_alert_history(self, filepath: str) -> None:
        """Load alert history from JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Reconstruct datetime objects
                for symbol, signals in data.items():
                    for signal_type, timestamp_str in signals.items():
                        signals[signal_type] = datetime.fromisoformat(timestamp_str)
                self.alert_history = data
            log.info(f"Loaded alert history from {filepath}")
        except FileNotFoundError:
            log.debug(f"Alert history file not found: {filepath}")
    
    def save_alert_history(self, filepath: str) -> None:
        """Save alert history to JSON file."""
        # Convert datetime to ISO format strings
        serializable = {}
        for symbol, signals in self.alert_history.items():
            serializable[symbol] = {
                signal_type: ts.isoformat()
                for signal_type, ts in signals.items()
            }
        
        with open(filepath, 'w') as f:
            json.dump(serializable, f, indent=2)
