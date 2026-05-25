#!/usr/bin/env python3
"""
Advanced Indicators for Entry Quality Assessment

Calculates sweep detection, displacement, flow, and other advanced metrics
for evaluating entry quality.

These indicators should ideally be calculated in MT5 EA (options.mq5) and passed
to Python, but can also be calculated here if not available from MT5.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict


def calculate_sweep_strength(df: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    """
    Detect sweep (liquidity run) and measure strength.
    
    sweep_top: high > previous_high && close < previous_high (wick above)
    sweep_bottom: low < previous_low && close > previous_low (wick below)
    sweep_strength: (wick_size / ATR)
    
    Args:
        df: OHLCV dataframe with 'atr' column
        lookback: Candles to lookback for sweep detection
    
    Returns:
        DataFrame with:
        - sweep_top: 1 if top sweep, 0 otherwise
        - sweep_bottom: 1 if bottom sweep, 0 otherwise
        - sweep_strength: Normalized wick size / ATR
        - is_strong_sweep: 1 if sweep_strength > threshold (>1.5)
    """
    result = pd.DataFrame(index=df.index)
    
    # Previous highs/lows
    prev_high = df["high"].shift(1)
    prev_low = df["low"].shift(1)
    
    # Sweep detection
    result["sweep_top"] = ((df["high"] > prev_high) & (df["close"] < prev_high)).astype(int)
    result["sweep_bottom"] = ((df["low"] < prev_low) & (df["close"] > prev_low)).astype(int)
    
    # Sweep strength: (wick_size / ATR)
    atr = df.get("atr", pd.Series(1.0, index=df.index)).clip(lower=0.0001)
    
    wick_top = df["high"] - prev_high.clip(lower=df["close"])
    wick_bottom = prev_low.clip(upper=df["close"]) - df["low"]
    
    result["sweep_strength_top"] = wick_top / atr
    result["sweep_strength_bottom"] = wick_bottom / atr
    result["sweep_strength"] = np.maximum(result["sweep_strength_top"], result["sweep_strength_bottom"])
    
    # Strong sweep: strength > 1.5 ATR
    result["is_strong_sweep"] = (result["sweep_strength"] > 1.5).astype(int)
    
    # Lookback: Any strong sweep in last N candles?
    result["recent_sweep"] = result["is_strong_sweep"].rolling(lookback).max().fillna(0).astype(int)
    
    return result.fillna(0)


def calculate_displacement(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate various displacement/strength metrics.
    
    displacement: Real body size = abs(close - open) / ATR
    directional_move: Net move = (close - open) / ATR
    momentum_burst: 3-candle momentum = (close - close_3) / ATR
    
    Returns:
        DataFrame with displacement metrics
    """
    result = pd.DataFrame(index=df.index)
    
    atr = df.get("atr", pd.Series(1.0, index=df.index)).clip(lower=0.0001)
    
    # Real body displacement
    result["displacement"] = np.abs(df["close"] - df["open"]) / atr
    
    # Directional displacement
    result["directional_displacement"] = (df["close"] - df["open"]) / atr
    
    # 3-candle momentum
    close_3_ago = df["close"].shift(3)
    result["momentum_burst"] = (df["close"] - close_3_ago) / atr
    
    # Exhaustion: Large move without progress
    close_10_ago = df["close"].shift(10)
    result["exhaustion"] = np.abs(df["close"] - close_10_ago) / atr
    
    return result.fillna(0)


def calculate_structure_breaks(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """
    Detect break above/below structure.
    
    break_high: close > highest(lookback)
    break_low: close < lowest(lookback)
    break_strength: How many previous highs/lows were broken
    
    Returns:
        DataFrame with structure break metrics
    """
    result = pd.DataFrame(index=df.index)
    
    highest = df["high"].rolling(lookback).max()
    lowest = df["low"].rolling(lookback).min()
    
    result["break_high"] = (df["close"] > highest.shift(1)).astype(int)
    result["break_low"] = (df["close"] < lowest.shift(1)).astype(int)
    
    # Break strength: distance from breaking level / ATR
    atr = df.get("atr", pd.Series(1.0, index=df.index)).clip(lower=0.0001)
    
    break_distance_high = df["close"] - highest.shift(1)
    break_distance_low = lowest.shift(1) - df["close"]
    
    result["break_strength"] = np.maximum(
        break_distance_high / atr,
        break_distance_low / atr
    )
    
    return result.fillna(0)


def calculate_flow_metrics(df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """
    Calculate flow and flow acceleration.
    
    flow: Sum of returns over window
    flow_acceleration: Change in flow
    flow_volatility: Std of returns
    
    Returns:
        DataFrame with flow metrics
    """
    result = pd.DataFrame(index=df.index)
    
    # Returns
    returns = df["close"].pct_change() * 100  # In %
    
    # Flow (sum of returns)
    result["flow"] = returns.rolling(window).sum().fillna(0)
    
    # Flow acceleration
    result["flow_acceleration"] = result["flow"].diff().fillna(0)
    
    # Flow volatility (std of returns)
    result["flow_volatility"] = returns.rolling(window).std().fillna(0)
    
    return result


def calculate_position_metrics(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Calculate price position within range.
    
    pos_range: (close - low_20) / (high_20 - low_20) [0-1]
    dist_mean: (close - MA20) / MA20 [%]
    zscore: (close - mean) / std
    
    Returns:
        DataFrame with position metrics
    """
    result = pd.DataFrame(index=df.index)
    
    # Position within 20-bar range
    high_20 = df["high"].rolling(window).max()
    low_20 = df["low"].rolling(window).min()
    range_20 = high_20 - low_20
    range_20 = range_20.clip(lower=0.0001)
    
    result["pos_range"] = ((df["close"] - low_20) / range_20).fillna(0.5)
    
    # Distance from MA20
    ma20 = df["close"].rolling(window).mean()
    result["dist_mean"] = ((df["close"] - ma20) / ma20 * 100).fillna(0)
    
    # Z-score
    mean = df["close"].rolling(window).mean()
    std = df["close"].rolling(window).std().clip(lower=0.0001)
    result["zscore"] = ((df["close"] - mean) / std).fillna(0)
    
    return result


def calculate_volatility_metrics(df: pd.DataFrame, atr_window: int = 14) -> pd.DataFrame:
    """
    Calculate volatility and regime metrics.
    
    atr_pct: ATR as % of close
    vol_regime: Current ATR / Average ATR
    vol_expansion: ATR > avg(ATR_20)
    
    Returns:
        DataFrame with volatility metrics
    """
    result = pd.DataFrame(index=df.index)
    
    # ATR % of close
    atr = df.get("atr", pd.Series(1.0, index=df.index))
    result["atr_pct"] = (atr / df["close"].clip(lower=0.0001) * 100).fillna(0)
    
    # Volatility regime (current ATR / MA(ATR, 20))
    atr_ma = atr.rolling(20).mean().clip(lower=0.0001)
    result["vol_regime"] = (atr / atr_ma).fillna(1.0)
    
    # Volatility expansion: ATR in expansion or contraction?
    result["vol_expansion"] = (atr > atr_ma).astype(int)
    
    return result


def calculate_reversal_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Composite reversal signal.
    
    reversal_score = sweep + displacement + (1 if direction_change else 0)
    
    Returns:
        DataFrame with reversal metrics
    """
    result = pd.DataFrame(index=df.index)
    
    # Direction change (close crosses MA20)
    ma20 = df["close"].rolling(20).mean()
    close_above_ma = (df["close"] > ma20).astype(int)
    close_above_ma_prev = close_above_ma.shift(1)
    direction_change = (close_above_ma != close_above_ma_prev).astype(int)
    
    # Sweep + Displacement
    sweep_strength = calculate_sweep_strength(df)["sweep_strength"].fillna(0)
    displacement = calculate_displacement(df)["displacement"].fillna(0)
    
    # Composite reversal score
    result["reversal_score"] = (
        sweep_strength * 0.4 +  # 40% sweep strength
        displacement * 0.4 +    # 40% displacement
        direction_change * 0.2  # 20% direction change
    ).fillna(0)
    
    # Normalized to 0-1
    result["reversal_score"] = result["reversal_score"].clip(0, 1)
    
    return result


def calculate_entry_quality_advanced(
    df: pd.DataFrame,
    has_choch: pd.Series = None,
    has_bos: pd.Series = None,
    in_sd_zone: pd.Series = None,
    fvg_proximity: pd.Series = None
) -> pd.DataFrame:
    """
    Composite entry quality score combining all metrics.
    
    Entry Logic:
    1. Price reached SD3 (or SD2/S1) ✓
    2. Has CHOCH or BOS formed ✓
    3. Strong sweep detected ✓
    4. Displacement showing real move ✓
    5. Not exhausted (not at extremes)
    
    Args:
        df: OHLCV dataframe
        has_choch: Boolean series indicating CHOCH
        has_bos: Boolean series indicating BOS
        in_sd_zone: Boolean series indicating SD zone
        fvg_proximity: Score 0-100 for FVG proximity
    
    Returns:
        DataFrame with entry_quality_score (0-100)
    """
    result = pd.DataFrame(index=df.index)
    
    # Base score = 0
    score = pd.Series(0.0, index=df.index)
    
    # 1. SD Zone: +25 points
    if in_sd_zone is not None:
        score += in_sd_zone.astype(float) * 25
    
    # 2. CHOCH/BOS: +20 points
    if has_choch is not None:
        score += has_choch.astype(float) * 10
    if has_bos is not None:
        score += has_bos.astype(float) * 10
    
    # 3. Strong Sweep: +15 points
    sweep = calculate_sweep_strength(df)
    score += sweep["is_strong_sweep"] * 15
    
    # 4. Good Displacement: +20 points
    displacement = calculate_displacement(df)
    displacement_good = (displacement["displacement"] > 1.5).astype(float)  # > 1.5 ATR
    score += displacement_good * 20
    
    # 5. FVG proximity: +10 points (if provided)
    if fvg_proximity is not None:
        fvg_score = fvg_proximity.clip(0, 100) / 10  # Normalize 100→10
        score += fvg_score
    
    # 6. Not Exhausted: +10 points (position not at extremes)
    position = calculate_position_metrics(df)
    pos_ok = ((position["pos_range"] > 0.2) & (position["pos_range"] < 0.8)).astype(float)
    score += pos_ok * 10
    
    result["entry_quality_score"] = score.clip(0, 100)
    
    return result


def generate_all_advanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate all advanced indicators at once.
    
    Returns:
        DataFrame with all advanced indicator columns
    """
    advanced = pd.DataFrame(index=df.index)
    
    # Sweep metrics
    sweep = calculate_sweep_strength(df)
    advanced = advanced.join(sweep)
    
    # Displacement metrics
    displacement = calculate_displacement(df)
    advanced = advanced.join(displacement)
    
    # Structure breaks
    breaks = calculate_structure_breaks(df)
    advanced = advanced.join(breaks)
    
    # Flow metrics
    flow = calculate_flow_metrics(df)
    advanced = advanced.join(flow)
    
    # Position metrics
    position = calculate_position_metrics(df)
    advanced = advanced.join(position)
    
    # Volatility metrics
    volatility = calculate_volatility_metrics(df)
    advanced = advanced.join(volatility)
    
    # Reversal signals
    reversal = calculate_reversal_signals(df)
    advanced = advanced.join(reversal)
    
    return advanced.fillna(0)


if __name__ == "__main__":
    print("✅ Advanced Indicators Module Loaded")
    print("\nMetrics available:")
    print("  - Sweep detection & strength")
    print("  - Displacement (real body, directional, momentum)")
    print("  - Structure breaks (high/low)")
    print("  - Flow metrics (sum, acceleration, volatility)")
    print("  - Position metrics (range, distance from mean, zscore)")
    print("  - Volatility metrics (ATR%, regime, expansion)")
    print("  - Reversal signals (composite)")
