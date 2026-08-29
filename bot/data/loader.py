"""
data/loader.py
==============
Load historical OHLCV data for NSE instruments.

Sources:
1. Synthetic (GBM) - for offline testing
2. CSV files
3. yfinance with .NS suffix
4. Zerodha Kite API
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

REQUIRED_COLS = {"Open", "High", "Low", "Close", "Volume"}


def load_data(symbols, start, end, source="synthetic", kite=None, interval="day"):
    """Load OHLCV data for symbols."""
    result = {}
    
    if source == "synthetic":
        for sym in symbols:
            df = _generate_synthetic(sym, start, end)
            if df is not None:
                result[sym] = df
    elif source == "yfinance":
        for sym in symbols:
            try:
                import yfinance as yf
                ticker = f"{sym}.NS"
                df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
                if not df.empty:
                    df = _normalise(df, sym)
                    if df is not None:
                        result[sym] = df
            except Exception as e:
                log.warning(f"Failed to load {sym} from yfinance: {e}")
    elif source == "csv":
        for sym in symbols:
            try:
                path = Path(__file__).parent / "raw" / f"{sym}.csv"
                if path.exists():
                    df = pd.read_csv(path)
                    df.columns = [c.strip().title() for c in df.columns]
                    if "Date" in df.columns:
                        df["Date"] = pd.to_datetime(df["Date"])
                        df = df.set_index("Date")
                    df = _normalise(df, sym)
                    if df is not None:
                        result[sym] = df
            except Exception as e:
                log.warning(f"Failed to load {sym} from CSV: {e}")
    
    log.info(f"Loaded data for {len(result)}/{len(symbols)} symbols from {source}")
    return result


def load_universe(filepath=None):
    """Load symbol universe from CSV."""
    if filepath is None:
        filepath = Path(__file__).parent / "universe" / "nse_tracker.csv"
    
    df = pd.read_csv(filepath)
    df.columns = [c.strip() for c in df.columns]
    return df


def load_portfolio_universe(filepath=None):
    """Load portfolio symbol universe from portfolio.csv."""
    if filepath is None:
        filepath = Path(__file__).parent / "universe" / "portfolio.csv"
    if not Path(filepath).exists():
        log.warning(f"Portfolio file {filepath} not found. Falling back to nse_tracker.csv")
        filepath = Path(__file__).parent / "universe" / "nse_tracker.csv"
    
    df = pd.read_csv(filepath)
    df.columns = [c.strip() for c in df.columns]
    return df


def validate_ohlcv(df, symbol=""):
    """Check OHLCV data quality."""
    warnings = []
    tag = f"[{symbol}] " if symbol else ""
    
    if (df["High"] < df["Low"]).any():
        warnings.append(f"{tag}High < Low")
    if ((df["Close"] < df["Low"]) | (df["Close"] > df["High"])).any():
        warnings.append(f"{tag}Close outside [Low,High]")
    if df.index.duplicated().any():
        warnings.append(f"{tag}Duplicate dates")
    
    return warnings


def _normalise(df, symbol):
    """Standardise columns and types."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df = df.rename(columns={"Adj Close": "Close"})
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        log.warning(f"{symbol} missing {missing}")
        return None
    
    df = df[list(REQUIRED_COLS)].copy()
    df.index = pd.to_datetime(df.index)
    df.index.name = "Date"
    df.sort_index(inplace=True)
    df.dropna(inplace=True)
    df = df[df["Close"] > 0]
    
    return df


def _generate_synthetic(symbol, start, end):
    """Generate synthetic GBM data for testing."""
    seed = sum(ord(c) for c in symbol) % 2**32
    rng = np.random.default_rng(seed)
    
    dates = pd.bdate_range(start=start, end=end)
    n = len(dates)
    dt = 1/252
    mu = 0.12
    sigma = 0.25
    
    log_rets = (mu - 0.5*sigma**2)*dt + sigma*np.sqrt(dt)*rng.standard_normal(n)
    closes = 500.0 * np.exp(np.cumsum(log_rets))
    opens = np.roll(closes, 1)
    opens[0] = 500.0
    
    range_ = closes * sigma * np.sqrt(dt) * np.abs(rng.standard_normal(n)) * 1.5
    highs = np.maximum(opens, closes) + range_ * rng.uniform(0.1, 0.8, n)
    lows = np.minimum(opens, closes) - range_ * rng.uniform(0.1, 0.8, n)
    lows = np.maximum(lows, 1.0)
    
    volumes = (rng.integers(500_000, 5_000_000, n) * np.exp(rng.standard_normal(n)*0.4)).astype(int)
    
    df = pd.DataFrame({
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    }, index=pd.DatetimeIndex(dates, name="Date"))
    
    return df.round(2)
