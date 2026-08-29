"""
alerts/indicators.py
====================
Compute technical indicators for trend and pattern detection.

All functions work on OHLCV DataFrames and are lookback-aware
(no lookahead bias).

Indicators computed:
- Moving averages (SMA, EMA)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- ATR (Average True Range)
- Support/Resistance levels
- Trend direction and strength
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(period).mean()


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index (Wilder's smoothing).
    Values: 0-100. <30 oversold, >70 overbought.
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD (Moving Average Convergence Divergence).
    Returns: (macd_line, signal_line, histogram)
    """
    ema_fast = compute_ema(close, fast)
    ema_slow = compute_ema(close, slow)
    
    macd_line   = ema_fast - ema_slow
    signal_line = compute_ema(macd_line, signal)
    histogram   = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def compute_bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands: (upper, middle, lower).
    """
    sma = compute_sma(close, period)
    std = close.rolling(period).std()
    
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    
    return upper, sma, lower


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average True Range. Measures volatility.
    """
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    
    return tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()


def compute_support_resistance(df: pd.DataFrame, lookback: int = 20) -> tuple[float, float]:
    """
    Identify recent support and resistance levels from rolling highs/lows.
    """
    recent_high = df["High"].tail(lookback).max()
    recent_low  = df["Low"].tail(lookback).min()
    
    return recent_low, recent_high


def compute_trend(sma_fast: pd.Series, sma_slow: pd.Series) -> pd.Series:
    """
    Determine trend direction: 1 (up), -1 (down), 0 (unclear).
    """
    return pd.Series(
        np.where(sma_fast > sma_slow, 1, np.where(sma_fast < sma_slow, -1, 0)),
        index=sma_fast.index
    )


def compute_trend_strength(rsi: pd.Series, atr: pd.Series, close: pd.Series) -> pd.Series:
    """
    Measure trend strength on 0-100 scale.
    Combines RSI distance from 50 and ATR relative to price.
    """
    # RSI component: distance from 50 (neutral)
    rsi_strength = (abs(rsi - 50) / 50) * 100
    
    # Volatility component: higher ATR% = stronger moves
    atr_pct = (atr / close) * 100
    vol_strength = np.clip(atr_pct * 10, 0, 100)
    
    # Combined strength
    return (rsi_strength * 0.6 + vol_strength * 0.4).fillna(0)


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all technical indicators. Returns updated DataFrame.
    """
    result = df.copy()
    
    # Moving averages
    result["SMA_20"] = compute_sma(result["Close"], 20)
    result["SMA_50"] = compute_sma(result["Close"], 50)
    result["SMA_200"] = compute_sma(result["Close"], 200)
    result["EMA_12"] = compute_ema(result["Close"], 12)
    result["EMA_26"] = compute_ema(result["Close"], 26)
    
    # Momentum
    result["RSI_14"] = compute_rsi(result["Close"], 14)
    macd, signal, hist = compute_macd(result["Close"])
    result["MACD"] = macd
    result["MACD_SIGNAL"] = signal
    result["MACD_HIST"] = hist
    
    # Volatility
    upper, middle, lower = compute_bollinger_bands(result["Close"], 20, 2.0)
    result["BB_UPPER"] = upper
    result["BB_MIDDLE"] = middle
    result["BB_LOWER"] = lower
    result["ATR_14"] = compute_atr(result["High"], result["Low"], result["Close"], 14)
    
    # Trend
    result["TREND"] = compute_trend(result["SMA_20"], result["SMA_50"])
    result["TREND_STRENGTH"] = compute_trend_strength(result["RSI_14"], result["ATR_14"], result["Close"])
    
    # Previous day reference (for signal detection)
    result["PREV_CLOSE"] = result["Close"].shift(1)
    result["PREV_RSI"] = result["RSI_14"].shift(1)
    result["PREV_MACD"] = result["MACD"].shift(1)
    
    return result


def get_latest_indicators(df: pd.DataFrame) -> dict:
    """
    Extract latest indicator values from a DataFrame.
    Safe for NaN handling.
    """
    row = df.iloc[-1]
    return {
        "close": float(row["Close"]),
        "prev_close": float(row["PREV_CLOSE"]) if pd.notna(row["PREV_CLOSE"]) else None,
        "high": float(row["High"]),
        "low": float(row["Low"]),
        "volume": int(row["Volume"]),
        "sma_20": float(row["SMA_20"]) if pd.notna(row["SMA_20"]) else None,
        "sma_50": float(row["SMA_50"]) if pd.notna(row["SMA_50"]) else None,
        "sma_200": float(row["SMA_200"]) if pd.notna(row["SMA_200"]) else None,
        "rsi_14": float(row["RSI_14"]) if pd.notna(row["RSI_14"]) else None,
        "macd": float(row["MACD"]) if pd.notna(row["MACD"]) else None,
        "macd_signal": float(row["MACD_SIGNAL"]) if pd.notna(row["MACD_SIGNAL"]) else None,
        "macd_hist": float(row["MACD_HIST"]) if pd.notna(row["MACD_HIST"]) else None,
        "bb_upper": float(row["BB_UPPER"]) if pd.notna(row["BB_UPPER"]) else None,
        "bb_lower": float(row["BB_LOWER"]) if pd.notna(row["BB_LOWER"]) else None,
        "atr_14": float(row["ATR_14"]) if pd.notna(row["ATR_14"]) else None,
        "trend": int(row["TREND"]),
        "trend_strength": float(row["TREND_STRENGTH"]),
    }
