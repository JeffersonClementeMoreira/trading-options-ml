#!/usr/bin/env python3
"""
Enhanced Features for XGBoost - SMC + Technical Indicators

Combines:
1. TOP 5 SMC Features (27% of decision power)
2. 5 Technical Indicators (SMA, RSI, MACD, ATR%)
3. Derived Features (Ratios, Interactions, Momentum)

Target: Improve accuracy from 54.4% → 60-65%
"""

import numpy as np
import pandas as pd
from typing import Tuple
from core.advanced_indicators import (
    generate_all_advanced_indicators,
    calculate_entry_quality_advanced
)


def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate core technical indicators.
    
    Returns DataFrame with:
    - sma_20, sma_50: Simple Moving Averages (primary trend)
    - atr_percent: ATR as % of close price
    - ema_12, ema_26: Exponential Moving Averages (faster trend detection)
    
    Note: Removed RSI & MACD as they showed low importance in XGBoost feature ranking.
    """
    tech = pd.DataFrame(index=df.index)
    
    # SMAs (trend following) - Primary
    tech["sma_20"] = df["close"].rolling(20).mean()
    tech["sma_50"] = df["close"].rolling(50).mean()
    
    # EMAs (faster response to changes)
    tech["ema_12"] = df["close"].ewm(span=12).mean()
    tech["ema_26"] = df["close"].ewm(span=26).mean()
    
    # ATR as % of price
    if "atr" in df.columns:
        tech["atr_percent"] = (df["atr"] / df["close"].clip(lower=1e-6)) * 100
    else:
        # Estimate ATR if not available
        tr1 = df["high"] - df["low"]
        tr2 = abs(df["high"] - df["close"].shift(1))
        tr3 = abs(df["low"] - df["close"].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        tech["atr_percent"] = (atr / df["close"].clip(lower=1e-6)) * 100
    
    return tech.fillna(0)


def calculate_trend_features(df: pd.DataFrame, tech: pd.DataFrame) -> pd.DataFrame:
    """
    Trend-related features using SMA interactions.
    
    Returns:
    - price_above_sma20: 1 if price > SMA20
    - price_above_sma50: 1 if price > SMA50
    - sma_alignment: Trend strength (1=strong up, -1=strong down, 0=confusion)
    - momentum_score: Combined RSI + MACD signal (0-1 scale)
    """
    features = pd.DataFrame(index=df.index)
    
    # Price vs SMAs
    features["price_above_sma20"] = (df["close"] > tech["sma_20"]).astype(int)
    features["price_above_sma50"] = (df["close"] > tech["sma_50"]).astype(int)
    
    # SMA alignment (trend clarity)
    sma20_above_50 = (tech["sma_20"] > tech["sma_50"]).astype(int)
    features["sma_alignment"] = sma20_above_50 * 2 - 1  # 1 if bullish, -1 if bearish
    
    # Momentum score: Combine RSI + MACD
    rsi_normalized = tech["rsi_14"] / 100  # 0-1
    macd_direction = np.sign(tech["macd_histogram"]).clip(-1, 1)  # -1, 0, or 1
    
    # When RSI > 50 AND MACD histogram > 0: strong momentum
    # When RSI < 50 AND MACD histogram < 0: strong negative momentum
    momentum = (rsi_normalized - 0.5) + (macd_direction * 0.3)
    momentum = np.tanh(momentum) * 0.5 + 0.5  # Normalize to 0-1
    
    features["momentum_score"] = momentum
    
    # Trend strength: How many technical indicators agree
    bullish_signals = 0
    bearish_signals = 0
    
    bullish_signals += (df["close"] > tech["sma_20"]).astype(int)
    bullish_signals += (tech["sma_20"] > tech["sma_50"]).astype(int)
    bullish_signals += (tech["rsi_14"] > 50).astype(int)
    bullish_signals += (tech["macd_histogram"] > 0).astype(int)
    
    bearish_signals = 4 - bullish_signals
    
    features["trend_confirmation"] = (bullish_signals - bearish_signals) / 4  # -1 to 1
    
    return features


def calculate_volatility_features(df: pd.DataFrame, tech: pd.DataFrame) -> pd.DataFrame:
    """
    Volatility-related features.
    
    Returns:
    - vol_normalized: ATR% normalized to 0-1 scale
    - vol_spike: 1 if current volatility > 150% of 20-period average
    - vol_trend: Is volatility expanding or contracting
    """
    features = pd.DataFrame(index=df.index)
    
    # Normalized volatility (0 = low, 1 = high)
    atr_pct = tech["atr_percent"]
    atr_min = atr_pct.rolling(100).min()
    atr_max = atr_pct.rolling(100).max()
    
    vol_range = atr_max - atr_min
    vol_range = vol_range.clip(lower=0.01)
    
    features["vol_normalized"] = (atr_pct - atr_min) / vol_range
    features["vol_normalized"] = features["vol_normalized"].clip(0, 1)
    
    # Volatility spike
    atr_20_avg = atr_pct.rolling(20).mean()
    features["vol_spike"] = (atr_pct > atr_20_avg * 1.5).astype(int)
    
    # Volatility trend (expanding = 1, contracting = -1)
    atr_change = atr_pct.diff()
    features["vol_trend"] = np.sign(atr_change.rolling(5).mean())
    
    return features.fillna(0)


def calculate_price_action_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pure price action features (no indicators needed).
    
    Returns:
    - candle_body_percent: (close-open) / (high-low)
    - close_position: (close-low) / (high-low) normalized
    - range_expansion: Current range vs 20-period average
    """
    features = pd.DataFrame(index=df.index)
    
    # Candle body strength
    range_size = df["high"] - df["low"]
    body_size = abs(df["close"] - df["open"])
    
    range_size = range_size.clip(lower=1e-6)
    features["candle_body_percent"] = body_size / range_size
    
    # Close position in candle (0=bottom, 1=top)
    features["close_position"] = (df["close"] - df["low"]) / range_size
    features["close_position"] = features["close_position"].clip(0, 1)
    
    # Range expansion vs average
    range_avg = range_size.rolling(20).mean()
    range_avg = range_avg.clip(lower=1e-6)
    features["range_expansion"] = range_size / range_avg
    
    return features.fillna(0)


def combine_top5_smc_features(
    df: pd.DataFrame,
    smc_features: pd.DataFrame
) -> pd.DataFrame:
    """
    Extract and combine TOP 5 most important SMC features.
    
    These 5 features represent 27% of the model's decision:
    1. dist_top_liquidity (6.23%)
    2. dist_bottom_liquidity (5.80%)
    3. vol_regime (5.51%)
    4. premium_discount_score (4.73%)
    5. range_duration (4.66%)
    """
    top5 = pd.DataFrame(index=df.index)
    
    # Extract if they exist, otherwise provide fallbacks
    if "dist_top_liquidity" in smc_features.columns:
        top5["dist_top_liquidity"] = smc_features["dist_top_liquidity"]
    else:
        top5["dist_top_liquidity"] = 0.0
    
    if "dist_bottom_liquidity" in smc_features.columns:
        top5["dist_bottom_liquidity"] = smc_features["dist_bottom_liquidity"]
    else:
        top5["dist_bottom_liquidity"] = 0.0
    
    if "vol_regime" in smc_features.columns:
        top5["vol_regime"] = smc_features["vol_regime"]
    else:
        top5["vol_regime"] = 0.0
    
    if "premium_discount_score" in smc_features.columns:
        top5["premium_discount_score"] = smc_features["premium_discount_score"]
    else:
        top5["premium_discount_score"] = 0.0
    
    if "range_duration" in smc_features.columns:
        top5["range_duration"] = smc_features["range_duration"]
    else:
        top5["range_duration"] = 0.0
    
    return top5


def combine_smc_context_features(
    df: pd.DataFrame,
    smc_features: pd.DataFrame
) -> pd.DataFrame:
    """
    Add explicit SMC context features that are often strong only in specific regimes.

    These features help capture conditional behavior (e.g. FVG near SD zones)
    that may be obvious visually but diluted in global importance.
    """
    ctx = pd.DataFrame(index=df.index)

    ctx["bull_fvg_count"] = smc_features.get("bull_fvg_count", pd.Series(0.0, index=df.index))
    ctx["bear_fvg_count"] = smc_features.get("bear_fvg_count", pd.Series(0.0, index=df.index))
    ctx["fvg_pressure"] = smc_features.get("fvg_pressure", pd.Series(0.0, index=df.index))

    ctx["bos_bull_count"] = smc_features.get("bos_bull_count", pd.Series(0.0, index=df.index))
    ctx["bos_bear_count"] = smc_features.get("bos_bear_count", pd.Series(0.0, index=df.index))

    # Clip long-tail recency to reduce noise while preserving ordering.
    candles_since_choch = smc_features.get("candles_since_choch", pd.Series(999.0, index=df.index))
    ctx["candles_since_choch"] = candles_since_choch.clip(lower=0, upper=250)
    ctx["choch_type"] = smc_features.get("choch_type", pd.Series(0.0, index=df.index))

    return ctx.fillna(0)


def create_composite_features(
    df: pd.DataFrame,
    advanced: pd.DataFrame,
    tech: pd.DataFrame,
    smc_features: pd.DataFrame
) -> pd.DataFrame:
    """
    Create advanced composite features that combine multiple signals.
    
    These capture entry quality when multiple conditions align:
    - sweep_displacement: Strong sweep with good body size
    - break_momentum: Breaking structure with positive flow
    - reversal_quality: Reversal signal in good position
    - entry_setup: Composite entry readiness score
    """
    composite = pd.DataFrame(index=df.index)
    
    # 1. Sweep + Displacement: Quality reversal wick
    sweep = advanced["is_strong_sweep"].fillna(0)
    displacement = advanced["displacement"].fillna(0.5)
    composite["sweep_displacement"] = (sweep * displacement).clip(0, 10)
    
    # 2. Break + Momentum: Directional breakout
    break_strength = advanced["break_strength"].fillna(0)
    flow_acc = advanced["flow_acceleration"].fillna(0)
    composite["break_momentum"] = break_strength * np.sign(flow_acc)  # -10 to +10
    
    # 3. Position Quality: Being in good zone (not at extremes)
    pos_range = advanced["pos_range"].fillna(0.5)
    # Best at 0.3-0.7 range (not too high, not too low)
    pos_quality = 1 - np.abs(pos_range - 0.5) * 2  # Peaks at 0.5
    composite["position_quality"] = pos_quality.clip(0, 1)
    
    # 4. Volatility Context: Entry in volatile vs calm
    vol_expansion = advanced["vol_expansion"].fillna(0)
    vol_regime = advanced["vol_regime"].fillna(1).clip(0.5, 2)
    composite["vol_context"] = vol_expansion * vol_regime
    
    # 5. Structure Alignment: Price near moving averages
    ema_diff = np.abs(df["close"] - tech["ema_12"]) / df["close"].clip(lower=1e-6)
    composite["ema_alignment"] = (1 - ema_diff.clip(0, 0.1) / 0.1).clip(0, 1)
    
    # 6. Entry Score: Composite quality (0-100)
    # Weighted combination of all signals
    entry_score = (
        (sweep * 20) +                          # 20: Strong sweep detected
        (displacement.clip(0, 2) * 15) +       # 15: Good displacement
        (composite["position_quality"] * 20) + # 20: Good position in range
        (composite["vol_context"] * 15) +       # 15: Vol expansion context
        (composite["ema_alignment"] * 15) +     # 15: EMA alignment
        (advanced["reversal_score"].fillna(0) * 15)  # 15: Reversal strength
    ).clip(0, 100)
    
    composite["entry_score"] = entry_score
    
    # 7. Setup Readiness: Should we be looking for entry?
    # High when: sweep occurred recently, displacement good, not exhausted
    recent_sweep = advanced["recent_sweep"].fillna(0)
    not_exhausted = (advanced["exhaustion"] < 3).astype(float)
    
    composite["setup_readiness"] = (recent_sweep * 40 + not_exhausted * 60).clip(0, 100)
    
    return composite.fillna(0)


def create_derivative_features(
    df: pd.DataFrame,
    smc_features: pd.DataFrame,
    tech: pd.DataFrame
) -> pd.DataFrame:
    """
    Create derivative/interaction features.
    
    Removed: dist_ratio, displacement_volatility (low importance)
    Added: More targeted interactions based on entry logic
    """
    derived = pd.DataFrame(index=df.index)
    
    # 1. Liquidity Pressure: How close to liquidity + flow
    dist_top = smc_features.get("dist_top_liquidity", pd.Series(1.0, index=df.index))
    dist_bottom = smc_features.get("dist_bottom_liquidity", pd.Series(1.0, index=df.index))
    
    min_dist = np.minimum(dist_top, dist_bottom).clip(lower=0.1)
    
    # Calculate flow from returns if not in smc_features
    returns = df["close"].pct_change().rolling(10).sum()
    flow_value = returns.fillna(0)
    
    derived["liquidity_pressure"] = (1 / min_dist * np.tanh(flow_value / 10)).clip(-5, 5)
    
    # 2. Confluence Score: Multiple SMC signals at once
    bos_bull = smc_features.get("bos_bull_count", pd.Series(0, index=df.index))
    bos_bear = smc_features.get("bos_bear_count", pd.Series(0, index=df.index))
    fvg_bull = smc_features.get("bull_fvg_count", pd.Series(0, index=df.index))
    fvg_bear = smc_features.get("bear_fvg_count", pd.Series(0, index=df.index))
    
    confluence = ((bos_bull > 0) + (bos_bear > 0) + (np.abs(fvg_bull - fvg_bear) > 0)) / 3.0
    derived["smc_confluence"] = confluence.fillna(0)
    
    # 3. Directional Clarity: Is trend clear?
    sma_above = (tech["sma_20"] > tech["sma_50"]).astype(float)
    ema_above = (tech["ema_12"] > tech["ema_26"]).astype(float)
    price_above_sma = (df["close"] > tech["sma_20"]).astype(float)
    
    derived["trend_clarity"] = (sma_above + ema_above + price_above_sma) / 3.0
    
    return derived.fillna(0)


def generate_enhanced_features(
    df: pd.DataFrame,
    smc_features: pd.DataFrame,
    include_smc_top5: bool = True,
    include_technical: bool = True,
    include_derived: bool = True,
    include_smc_context: bool = True,
) -> pd.DataFrame:
    """
    Generate complete enhanced feature set for XGBoost training.
    
    Args:
        df: OHLCV dataframe
        smc_features: SMC features from smc_features.generate_all_smc_features()
        include_smc_top5: Include top 5 SMC features
        include_technical: Include technical indicators
        include_derived: Include interaction features
    
    Returns:
        DataFrame with all enhanced features
    """
    enhanced = pd.DataFrame(index=df.index)
    
    # 1. Technical Indicators (5 base indicators)
    if include_technical:
        tech = calculate_technical_indicators(df)
        enhanced = enhanced.join(tech)
        
        # 2. Trend Features (4 derived from technicals)
        trend_feat = calculate_trend_features(df, tech)
        enhanced = enhanced.join(trend_feat)
        
        # 3. Volatility Features (3 features)
        vol_feat = calculate_volatility_features(df, tech)
        enhanced = enhanced.join(vol_feat)
    
    # 4. Price Action (3 features)
    price_feat = calculate_price_action_features(df)
    enhanced = enhanced.join(price_feat)
    
    # 5. TOP 5 SMC Features (most important ones)
    if include_smc_top5:
        smc_top5 = combine_top5_smc_features(df, smc_features)
        enhanced = enhanced.join(smc_top5)

    # 5b. Explicit SMC context features (FVG/BOS/CHOCH)
    if include_smc_context:
        smc_context = combine_smc_context_features(df, smc_features)
        enhanced = enhanced.join(smc_context)
    
    # 6. Derived Features (4 interaction features)
    if include_derived and include_technical:
        tech = calculate_technical_indicators(df)
        derived_feat = create_derivative_features(df, smc_features, tech)
        enhanced = enhanced.join(derived_feat)
    
    # 7. ADVANCED INDICATORS (sweep, displacement, flow, volatility, position)
    advanced = generate_all_advanced_indicators(df)
    enhanced = enhanced.join(advanced)
    
    # 8. COMPOSITE FEATURES (entry readiness, setup quality)
    if include_technical:
        tech = calculate_technical_indicators(df)
        composite = create_composite_features(df, advanced, tech, smc_features)
        enhanced = enhanced.join(composite)
    
    # Fill any remaining NaNs
    enhanced = enhanced.fillna(0)
    
    # Remove any infinite values
    enhanced = enhanced.replace([np.inf, -np.inf], 0)
    
    return enhanced


def get_feature_list() -> dict:
    """
    Return categorized list of all features.
    
    Useful for understanding what each feature group represents.
    """
    return {
        "technical_indicators": [
            "sma_20", "sma_50",     # Primary trends
            "ema_12", "ema_26",     # Fast response
            "atr_percent"           # Volatility
        ],
        "trend_features": [
            "price_above_sma20",     # Price vs trend
            "price_above_sma50",
            "sma_alignment",         # Trend clarity
            "momentum_score",        # Combined momentum
            "trend_confirmation"     # How many indicators agree
        ],
        "volatility_features": [
            "vol_normalized",        # Volatility level
            "vol_spike",             # Sudden expansion
            "vol_trend"              # Contraction vs expansion
        ],
        "price_action": [
            "candle_body_percent",   # Candle strength
            "close_position",        # Close position
            "range_expansion"        # Range size change
        ],
        "smc_top5": [
            "dist_top_liquidity",    # Distance to top liquidity
            "dist_bottom_liquidity", # Distance to bottom liquidity
            "vol_regime",            # Vol regime score
            "premium_discount_score",# Premium/discount
            "range_duration"         # How long range persists
        ],
        "smc_context": [
            "bull_fvg_count",        # Bullish FVG accumulation
            "bear_fvg_count",        # Bearish FVG accumulation
            "fvg_pressure",          # Bull-Bear imbalance
            "bos_bull_count",        # Bullish BOS count
            "bos_bear_count",        # Bearish BOS count
            "candles_since_choch",   # CHOCH recency
            "choch_type"             # Last CHOCH direction
        ],
        "advanced_indicators": [
            # Sweep metrics
            "sweep_top",             # Top sweep detected
            "sweep_bottom",          # Bottom sweep detected
            "sweep_strength",        # Wick size / ATR
            "is_strong_sweep",       # Strong sweep (>1.5 ATR)
            "recent_sweep",          # Recent sweep in lookback
            # Displacement metrics
            "displacement",          # Real body / ATR
            "directional_displacement",  # Net move / ATR
            "momentum_burst",        # 3-candle momentum
            "exhaustion",            # 10-candle exhaustion
            # Structure breaks
            "break_high",            # Break above high
            "break_low",             # Break below low
            "break_strength",        # Distance from break level
            # Flow metrics
            "flow",                  # Sum of returns
            "flow_acceleration",     # Change in flow
            "flow_volatility",       # Std of returns
            # Position metrics
            "pos_range",             # Position in 20-bar range
            "dist_mean",             # Distance from MA20 %
            "zscore",                # Z-score of price
            # Volatility metrics
            "atr_pct",               # ATR as % (duplicate)
            "vol_regime",            # ATR / MA(ATR) ratio
            "vol_expansion",         # Vol expanding (1/0)
            # Reversal
            "reversal_score"         # Composite reversal score
        ],
        "derivative_features": [
            "liquidity_pressure",    # Proximity + flow
            "smc_confluence",        # Multiple SMC signals
            "trend_clarity"          # Trend alignment strength
        ],
        "composite_features": [
            "sweep_displacement",    # Sweep * body size
            "break_momentum",        # Break strength * flow direction
            "position_quality",      # Position in good zone
            "vol_context",           # Vol expansion * regime
            "ema_alignment",         # Price near EMA12
            "entry_score",           # MAIN: Composite entry quality (0-100)
            "setup_readiness"        # Should we look for entry? (0-100)
        ]
    }


if __name__ == "__main__":
    print("✅ Enhanced Features Module Loaded")
    print("\nFeature Categories:")
    features = get_feature_list()
    for category, feat_list in features.items():
        print(f"  {category}: {len(feat_list)} features")
        for f in feat_list[:3]:
            print(f"    - {f}")
        if len(feat_list) > 3:
            print(f"    ... and {len(feat_list) - 3} more")
