"""Technical indicators helpers."""

import numpy as np
import pandas as pd


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def kaufman_efficiency_ratio(df: pd.DataFrame, period: int = 20) -> pd.Series:
    direction = (df["close"] - df["close"].shift(period)).abs()
    volatility = (df["close"] - df["close"].shift(1)).abs().rolling(period).sum()
    er = direction / volatility
    return er.fillna(0.0)


def kama(df: pd.DataFrame, period_er: int = 10, fast: int = 2, slow: int = 30) -> pd.Series:
    close = df["close"]
    er = kaufman_efficiency_ratio(df, period=period_er)

    fast_sc = 2 / (fast + 1)
    slow_sc = 2 / (slow + 1)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

    kama_values = np.zeros(len(close))
    kama_values[0] = close.iloc[0]

    for i in range(1, len(close)):
        kama_values[i] = kama_values[i - 1] + sc.iloc[i] * (close.iloc[i] - kama_values[i - 1])

    return pd.Series(kama_values, index=df.index)


def build_indicators(df: pd.DataFrame, bars_per_day: int = 96, days_per_year: int = 252) -> pd.DataFrame:
    """Return dataframe enriched with core indicators used by v3 modules."""
    enriched = df.copy()

    enriched["atr"] = calculate_atr(enriched)
    enriched["kama"] = kama(enriched)
    enriched["er"] = kaufman_efficiency_ratio(enriched)

    realized_vol = (
        enriched["return"].rolling(bars_per_day).std() * np.sqrt(bars_per_day * days_per_year)
    )

    atr_pct = enriched["atr"] / enriched["close"]
    atr_vol = atr_pct.rolling(bars_per_day).mean() * np.sqrt(days_per_year)
    enriched["realized_vol"] = np.maximum(realized_vol, atr_vol)

    return enriched
