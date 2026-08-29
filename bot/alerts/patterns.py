"""
alerts/patterns.py
==================
Identifies specific chart patterns and trading setups.

Each pattern detection function returns:
  (is_pattern_present: bool, confidence_score: 0-100, description: str)

Patterns detected:
- Breakouts (above/below levels)
- Reversals (oversold/overbought bounces)
- Momentum shifts (MACD crossovers)
- Volume surges
- Gaps
- Trend confirmations (rising/falling peaks)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from alerts.indicators import get_latest_indicators


def detect_breakout_up(df: pd.DataFrame, lookback: int = 20) -> tuple[bool, int, str]:
    """
    Breakout above recent high.
    Signal: Close > SMA_20 close above 20-day high with volume surge.
    """
    if len(df) < lookback + 2:
        return False, 0, "Insufficient data"
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    recent_high = df["High"].tail(lookback).max()
    avg_volume = df["Volume"].tail(20).mean()
    
    close = curr["Close"]
    prev_close = prev["Close"]
    volume = curr["Volume"]
    
    # Breakout: close crosses above recent high (not touched before)
    breakout = (prev_close <= recent_high) and (close > recent_high)
    volume_confirmed = volume > avg_volume * 1.5
    
    if not breakout:
        return False, 0, "No breakout detected"
    
    if not volume_confirmed:
        return breakout, 60, "Breakout without volume confirmation"
    
    # Check RSI and trend for strength
    rsi = curr["RSI_14"]
    trend = curr["TREND"]
    
    score = 75
    if 50 < rsi < 70:  # Not overbought yet
        score += 10
    if trend == 1:  # Uptrend
        score += 5
    if volume > avg_volume * 2:  # Strong volume
        score += 5
    
    return True, min(100, score), f"Breakout above ₹{recent_high:.2f} on volume"


def detect_breakout_down(df: pd.DataFrame, lookback: int = 20) -> tuple[bool, int, str]:
    """Breakout below recent low (potential short or exit long)."""
    if len(df) < lookback + 2:
        return False, 0, "Insufficient data"
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    recent_low = df["Low"].tail(lookback).min()
    avg_volume = df["Volume"].tail(20).mean()
    
    close = curr["Close"]
    prev_close = prev["Close"]
    volume = curr["Volume"]
    
    breakout = (prev_close >= recent_low) and (close < recent_low)
    volume_confirmed = volume > avg_volume * 1.5
    
    if not breakout:
        return False, 0, "No breakout detected"
    
    if not volume_confirmed:
        return breakout, 60, "Breakout without volume confirmation"
    
    rsi = curr["RSI_14"]
    trend = curr["TREND"]
    
    score = 75
    if 30 < rsi < 50:  # Not oversold yet
        score += 10
    if trend == -1:  # Downtrend
        score += 5
    if volume > avg_volume * 2:  # Strong volume
        score += 5
    
    return True, min(100, score), f"Breakout below ₹{recent_low:.2f} on volume"


def detect_reversal_up(df: pd.DataFrame) -> tuple[bool, int, str]:
    """
    Oversold bounce: RSI < 30 + recent low + price rising.
    Classic mean-reversion setup.
    """
    if len(df) < 5:
        return False, 0, "Insufficient data"
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    rsi = curr["RSI_14"]
    close = curr["Close"]
    low = curr["Low"]
    
    # Oversold + rising from low
    oversold = rsi < 30
    rising = close > prev["Close"]
    near_low = low == df["Low"].tail(5).min()
    
    if not (oversold and rising and near_low):
        return False, 0, "No reversal setup"
    
    # Check for rejection candle (lower wick, higher close)
    candle_range = curr["High"] - curr["Low"]
    lower_wick = curr["Low"] - prev["Low"] if curr["Low"] < prev["Low"] else 0
    
    score = 70
    if lower_wick > candle_range * 0.3:  # Deep wick = rejection
        score += 10
    if rsi < 20:  # Extremely oversold
        score += 5
    if curr["TREND"] == 1:  # Trending up
        score += 5
    
    return True, min(100, score), f"Oversold bounce (RSI: {rsi:.0f})"


def detect_reversal_down(df: pd.DataFrame) -> tuple[bool, int, str]:
    """
    Overbought reversal: RSI > 70 + recent high + price falling.
    """
    if len(df) < 5:
        return False, 0, "Insufficient data"
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    rsi = curr["RSI_14"]
    close = curr["Close"]
    high = curr["High"]
    
    overbought = rsi > 70
    falling = close < prev["Close"]
    near_high = high == df["High"].tail(5).max()
    
    if not (overbought and falling and near_high):
        return False, 0, "No reversal setup"
    
    candle_range = curr["High"] - curr["Low"]
    upper_wick = prev["High"] - curr["High"] if curr["High"] < prev["High"] else 0
    
    score = 70
    if upper_wick > candle_range * 0.3:
        score += 10
    if rsi > 80:
        score += 5
    if curr["TREND"] == -1:
        score += 5
    
    return True, min(100, score), f"Overbought reversal (RSI: {rsi:.0f})"


def detect_macd_crossover_up(df: pd.DataFrame) -> tuple[bool, int, str]:
    """
    Bullish MACD crossover: MACD crosses above signal line.
    Momentum shift indicator.
    """
    if len(df) < 3:
        return False, 0, "Insufficient data"
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    macd = curr["MACD"]
    signal = curr["MACD_SIGNAL"]
    prev_macd = prev["MACD"]
    prev_signal = prev["MACD_SIGNAL"]
    
    if pd.isna(macd) or pd.isna(signal):
        return False, 0, "MACD not computed"
    
    crossover = (prev_macd <= prev_signal) and (macd > signal)
    if not crossover:
        return False, 0, "No MACD crossover"
    
    # Check histogram for strength
    hist = curr["MACD_HIST"]
    trend = curr["TREND"]
    
    score = 65
    if hist > 0 and hist > prev.get("MACD_HIST", 0):  # Histogram rising
        score += 10
    if trend == 1:  # Already in uptrend
        score += 10
    
    return True, min(100, score), "Bullish MACD crossover"


def detect_macd_crossover_down(df: pd.DataFrame) -> tuple[bool, int, str]:
    """Bearish MACD crossover: MACD crosses below signal line."""
    if len(df) < 3:
        return False, 0, "Insufficient data"
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    macd = curr["MACD"]
    signal = curr["MACD_SIGNAL"]
    prev_macd = prev["MACD"]
    prev_signal = prev["MACD_SIGNAL"]
    
    if pd.isna(macd) or pd.isna(signal):
        return False, 0, "MACD not computed"
    
    crossover = (prev_macd >= prev_signal) and (macd < signal)
    if not crossover:
        return False, 0, "No MACD crossover"
    
    hist = curr["MACD_HIST"]
    trend = curr["TREND"]
    
    score = 65
    if hist < 0 and hist < prev.get("MACD_HIST", 0):
        score += 10
    if trend == -1:
        score += 10
    
    return True, min(100, score), "Bearish MACD crossover"


def detect_volume_surge(df: pd.DataFrame, multiplier: float = 3.0) -> tuple[bool, int, str]:
    """Unusual volume spike (3× average). Could precede breakout or reversal."""
    if len(df) < 20:
        return False, 0, "Insufficient data"
    
    curr = df.iloc[-1]
    volume = curr["Volume"]
    avg_volume = df["Volume"].tail(20).mean()
    
    surge = volume > avg_volume * multiplier
    if not surge:
        return False, 0, "No volume surge"
    
    # Assess context
    trend = curr["TREND"]
    rsi = curr["RSI_14"]
    
    score = 60
    if trend != 0:  # Clear trend direction
        score += 10
    if 30 < rsi < 70:  # RSI in middle range (room to move)
        score += 10
    
    return True, min(100, score), f"Volume surge: {volume/avg_volume:.1f}× average"


def detect_gap_up(df: pd.DataFrame, threshold: float = 0.02) -> tuple[bool, int, str]:
    """
    Gap up: Open > Previous Close * (1 + threshold).
    Typical gap threshold: 2% for swing trading.
    """
    if len(df) < 2:
        return False, 0, "Insufficient data"
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    gap_pct = (curr["Open"] - prev["Close"]) / prev["Close"]
    gap = gap_pct > threshold
    
    if not gap:
        return False, 0, "No gap"
    
    # Context: continuation or reversal?
    volume = curr["Volume"]
    avg_volume = df["Volume"].tail(5).mean()
    trend = curr["TREND"]
    
    score = 65
    if volume > avg_volume * 1.5:  # Volume confirms
        score += 10
    if trend == 1:  # Up gap in uptrend
        score += 10
    
    return True, min(100, score), f"Gap up {gap_pct*100:.1f}%"


def detect_gap_down(df: pd.DataFrame, threshold: float = 0.02) -> tuple[bool, int, str]:
    """Gap down: Open < Previous Close * (1 - threshold)."""
    if len(df) < 2:
        return False, 0, "Insufficient data"
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    gap_pct = (prev["Close"] - curr["Open"]) / prev["Close"]
    gap = gap_pct > threshold
    
    if not gap:
        return False, 0, "No gap"
    
    volume = curr["Volume"]
    avg_volume = df["Volume"].tail(5).mean()
    trend = curr["TREND"]
    
    score = 65
    if volume > avg_volume * 1.5:
        score += 10
    if trend == -1:
        score += 10
    
    return True, min(100, score), f"Gap down {gap_pct*100:.1f}%"


def detect_rising_peaks(df: pd.DataFrame, periods: int = 3) -> tuple[bool, int, str]:
    """
    Higher highs + higher lows over N periods.
    Uptrend confirmation / continuation.
    """
    if len(df) < periods + 1:
        return False, 0, "Insufficient data"
    
    recent = df.tail(periods + 1)
    highs = recent["High"].values
    lows = recent["Low"].values
    
    # Check for monotonic increase in both
    higher_highs = all(highs[i] < highs[i+1] for i in range(len(highs)-1))
    higher_lows = all(lows[i] < lows[i+1] for i in range(len(lows)-1))
    
    if not (higher_highs and higher_lows):
        return False, 0, "Not rising"
    
    # Strength: trend, RSI, volume
    curr = df.iloc[-1]
    trend = curr["TREND"]
    rsi = curr["RSI_14"]
    volume = curr["Volume"]
    avg_volume = df["Volume"].tail(10).mean()
    
    score = 75
    if trend == 1:
        score += 10
    if 50 < rsi < 70:  # Strong but not overbought
        score += 5
    if volume > avg_volume:
        score += 5
    
    return True, min(100, score), f"Rising peaks ({periods} bars)"


def detect_falling_peaks(df: pd.DataFrame, periods: int = 3) -> tuple[bool, int, str]:
    """Lower highs + lower lows. Downtrend confirmation."""
    if len(df) < periods + 1:
        return False, 0, "Insufficient data"
    
    recent = df.tail(periods + 1)
    highs = recent["High"].values
    lows = recent["Low"].values
    
    lower_highs = all(highs[i] > highs[i+1] for i in range(len(highs)-1))
    lower_lows = all(lows[i] > lows[i+1] for i in range(len(lows)-1))
    
    if not (lower_highs and lower_lows):
        return False, 0, "Not falling"
    
    curr = df.iloc[-1]
    trend = curr["TREND"]
    rsi = curr["RSI_14"]
    volume = curr["Volume"]
    avg_volume = df["Volume"].tail(10).mean()
    
    score = 75
    if trend == -1:
        score += 10
    if 30 < rsi < 50:
        score += 5
    if volume > avg_volume:
        score += 5
    
    return True, min(100, score), f"Falling peaks ({periods} bars)"


def detect_all_patterns(df: pd.DataFrame) -> list[tuple[str, bool, int, str]]:
    """
    Run all pattern detections. Returns list of (pattern_name, detected, score, description).
    """
    patterns = [
        ("BREAKOUT_UP", detect_breakout_up(df)),
        ("BREAKOUT_DOWN", detect_breakout_down(df)),
        ("REVERSAL_UP", detect_reversal_up(df)),
        ("REVERSAL_DOWN", detect_reversal_down(df)),
        ("MACD_UP", detect_macd_crossover_up(df)),
        ("MACD_DOWN", detect_macd_crossover_down(df)),
        ("VOLUME_SURGE", detect_volume_surge(df)),
        ("GAP_UP", detect_gap_up(df)),
        ("GAP_DOWN", detect_gap_down(df)),
        ("RISING_PEAKS", detect_rising_peaks(df)),
        ("FALLING_PEAKS", detect_falling_peaks(df)),
    ]
    
    return [
        (name, detected, score, desc)
        for name, (detected, score, desc) in patterns
        if detected
    ]
