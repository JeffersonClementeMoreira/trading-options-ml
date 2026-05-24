"""
SMC Features Generator - Transform SMC events into continuous numeric features for XGBoost.

Converts event-driven SMC (BOS, CHOCH, FVG, Sweep) into measurable patterns:
- Distance to liquidity zones
- Intensity/momentum of moves
- Compression/volatility regimes
- Support/resistance confluence
- Institutional move patterns
"""

import numpy as np
import pandas as pd
from typing import Tuple


def calculate_distance_to_liquidity(df: pd.DataFrame, window: int = 50) -> pd.DataFrame:
    """
    Calculate distance to next potential liquidity zones (extremes).
    
    Returns:
    - dist_top_liquidity: Points to nearest top extreme, normalized by ATR
    - dist_bottom_liquidity: Points to nearest bottom extreme, normalized by ATR
    """
    features = pd.DataFrame(index=df.index)
    features["dist_top_liquidity"] = np.nan
    features["dist_bottom_liquidity"] = np.nan
    
    for i in range(len(df)):
        current_price = df["close"].iloc[i]
        current_atr = df["atr"].iloc[i] if "atr" in df.columns else 1.0
        atr = max(current_atr, 0.0001)
        
        # Look ahead for next tops and bottoms
        future_window = df.iloc[max(0, i-window):i+window]
        tops = future_window["high"].values
        bottoms = future_window["low"].values
        
        # Nearest top above current price
        tops_above = tops[tops > current_price]
        if len(tops_above) > 0:
            dist_top = (tops_above.min() - current_price) / atr
        else:
            dist_top = np.nan
        
        # Nearest bottom below current price
        bottoms_below = bottoms[bottoms < current_price]
        if len(bottoms_below) > 0:
            dist_bottom = (current_price - bottoms_below.max()) / atr
        else:
            dist_bottom = np.nan
        
        features.loc[features.index[i], "dist_top_liquidity"] = dist_top
        features.loc[features.index[i], "dist_bottom_liquidity"] = dist_bottom
    
    return features.fillna(0)


def calculate_sweep_pressure(df: pd.DataFrame, extremos: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Count recent sweeps of top and bottom liquidity.
    
    Returns:
    - sweep_top_count: Number of sweeps of previous tops in window
    - sweep_bottom_count: Number of sweeps of previous bottoms in window
    - sweep_imbalance: (top_count - bottom_count) / total
    """
    features = pd.DataFrame(index=df.index)
    features["sweep_top_count"] = 0
    features["sweep_bottom_count"] = 0
    features["sweep_imbalance"] = 0.0
    
    if extremos.empty:
        return features
    
    for i in range(len(df)):
        # Count sweeps in the window
        window_start = max(0, i - window)
        window_extremos = extremos.iloc[window_start:i]
        
        if not window_extremos.empty:
            tops = len(window_extremos[window_extremos["type"] == "top"])
            bottoms = len(window_extremos[window_extremos["type"] == "bottom"])
            total = tops + bottoms
            
            features.loc[features.index[i], "sweep_top_count"] = tops
            features.loc[features.index[i], "sweep_bottom_count"] = bottoms
            
            if total > 0:
                features.loc[features.index[i], "sweep_imbalance"] = (tops - bottoms) / total
    
    return features


def calculate_bos_pressure(df: pd.DataFrame, extremos: pd.DataFrame, window: int = 50) -> pd.DataFrame:
    """
    Count Break of Structure events in recent history.
    
    Returns:
    - bos_bull_count: BOS breaks to upside in window
    - bos_bear_count: BOS breaks to downside in window
    - bos_ratio: Bull BOS vs Bear BOS ratio
    """
    features = pd.DataFrame(index=df.index)
    features["bos_bull_count"] = 0
    features["bos_bear_count"] = 0
    features["bos_ratio"] = 0.0
    
    if len(extremos) < 2:
        return features
    
    for i in range(len(df)):
        window_start = max(0, i - window)
        current_price = df["close"].iloc[i]
        
        # Look at extremes in the window
        window_extremos = extremos.iloc[window_start:i]
        
        if len(window_extremos) >= 2:
            # BOS Bull: price breaks above previous top
            tops_in_window = window_extremos[window_extremos["type"] == "top"]["price"].values
            bottoms_in_window = window_extremos[window_extremos["type"] == "bottom"]["price"].values
            
            bos_bull = 0
            bos_bear = 0
            
            if len(tops_in_window) > 0:
                # Count how many tops were broken above
                prev_tops = tops_in_window[:-1] if len(tops_in_window) > 1 else []
                if len(prev_tops) > 0:
                    bos_bull = sum(1 for top in prev_tops if current_price > top)
            
            if len(bottoms_in_window) > 0:
                # Count how many bottoms were broken below
                prev_bottoms = bottoms_in_window[:-1] if len(bottoms_in_window) > 1 else []
                if len(prev_bottoms) > 0:
                    bos_bear = sum(1 for bottom in prev_bottoms if current_price < bottom)
            
            features.loc[features.index[i], "bos_bull_count"] = bos_bull
            features.loc[features.index[i], "bos_bear_count"] = bos_bear
            
            total_bos = bos_bull + bos_bear
            if total_bos > 0:
                features.loc[features.index[i], "bos_ratio"] = (bos_bull - bos_bear) / total_bos
    
    return features


def calculate_choch_recency(df: pd.DataFrame, extremos: pd.DataFrame) -> pd.DataFrame:
    """
    Detect CHOCH (Change of Character) and measure recency.
    
    Returns:
    - candles_since_choch: Candles since last structural change
    - choch_type: Last CHOCH was BULL (1) or BEAR (-1)
    """
    features = pd.DataFrame(index=df.index)
    features["candles_since_choch"] = np.inf
    features["choch_type"] = 0
    
    if len(extremos) < 2:
        return features
    
    # Simple CHOCH detection: when swing structure changes
    extremo_types = extremos["type"].values
    extremo_prices = extremos["price"].values
    
    for i in range(len(df)):
        # Find last CHOCH
        min_candles_since = np.inf
        last_choch_type = 0
        
        for j in range(len(extremo_types) - 1, -1):
            if extremo_types[j] == "top":
                # Check if followed by bottom (potential CHOCH)
                if j < len(extremo_types) - 1 and extremo_types[j+1] == "bottom":
                    # Lower bottom after top = CHOCH_BEAR
                    if extremo_prices[j+1] < extremo_prices[j-1] if j > 0 else True:
                        candles = i - j
                        if candles >= 0 and candles < min_candles_since:
                            min_candles_since = candles
                            last_choch_type = -1
        
        features.loc[features.index[i], "candles_since_choch"] = min_candles_since if min_candles_since != np.inf else 999
        features.loc[features.index[i], "choch_type"] = last_choch_type
    
    return features.fillna(999)


def calculate_fvg_features(df: pd.DataFrame, fvg_lookback: int = 50) -> pd.DataFrame:
    """
    Count FVG (Fair Value Gap) imbalances.
    
    Returns:
    - bull_fvg_count: FVGs with low > previous high (gaps up)
    - bear_fvg_count: FVGs with high < previous low (gaps down)
    - fvg_pressure: Bull count - Bear count (directional bias)
    """
    features = pd.DataFrame(index=df.index)
    features["bull_fvg_count"] = 0
    features["bear_fvg_count"] = 0
    features["fvg_pressure"] = 0.0
    
    for i in range(2, len(df)):
        window_start = max(0, i - fvg_lookback)
        
        bull_fvg = 0
        bear_fvg = 0
        
        # Check for FVGs in window
        for j in range(window_start, i - 1):
            candle_0 = df.iloc[j]
            candle_2 = df.iloc[j + 2]
            
            if candle_2["low"] > candle_0["high"]:
                bull_fvg += 1
            elif candle_2["high"] < candle_0["low"]:
                bear_fvg += 1
        
        features.loc[features.index[i], "bull_fvg_count"] = bull_fvg
        features.loc[features.index[i], "bear_fvg_count"] = bear_fvg
        features.loc[features.index[i], "fvg_pressure"] = (bull_fvg - bear_fvg) / max(1, bull_fvg + bear_fvg)
    
    return features


def calculate_displacement_score(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Measure institutional aggressiveness through candle displacement.
    
    Returns:
    - mean_displacement: Average (close - open) / (high - low) in window
    - max_displacement: Maximum displacement in window
    - displacement_efficiency: How efficiently moves are made
    """
    features = pd.DataFrame(index=df.index)
    features["mean_displacement"] = 0.0
    features["max_displacement"] = 0.0
    features["displacement_efficiency"] = 0.0
    
    for i in range(len(df)):
        window_start = max(0, i - window)
        window_df = df.iloc[window_start:i+1]
        
        # Displacement = how much candle moved vs range
        ranges = window_df["high"] - window_df["low"]
        displacements = window_df["close"] - window_df["open"]
        
        # Avoid division by zero
        ranges = ranges.clip(lower=1e-6)
        efficiency = np.abs(displacements) / ranges
        
        features.loc[features.index[i], "mean_displacement"] = efficiency.mean()
        features.loc[features.index[i], "max_displacement"] = efficiency.max()
        features.loc[features.index[i], "displacement_efficiency"] = efficiency.iloc[-1] if len(efficiency) > 0 else 0
    
    return features


def calculate_premium_discount(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Position within range (institutional love point).
    
    Returns:
    - premium_position: Current price position in 20-period range (0=bottom, 1=top)
    - premium_discount_score: Bias towards premium (>0.5) or discount (<0.5)
    """
    features = pd.DataFrame(index=df.index)
    features["premium_position"] = 0.0
    features["premium_discount_score"] = 0.0
    
    for i in range(window, len(df)):
        window_df = df.iloc[i-window:i+1]
        
        range_high = window_df["high"].max()
        range_low = window_df["low"].min()
        range_size = range_high - range_low
        
        if range_size > 0:
            current_price = df["close"].iloc[i]
            position = (current_price - range_low) / range_size
            position = np.clip(position, 0, 1)
            
            # Premium when price > equilibrium (0.5)
            premium_score = position - 0.5  # -0.5 to +0.5
            
            features.loc[features.index[i], "premium_position"] = position
            features.loc[features.index[i], "premium_discount_score"] = premium_score
    
    return features.fillna(0)


def calculate_atr_compression(df: pd.DataFrame, fast: int = 5, slow: int = 50) -> pd.DataFrame:
    """
    Detect volatility compression (precedes breakouts).
    
    Returns:
    - atr_compression_ratio: Fast ATR / Slow ATR (low = compression)
    - vol_regime: Compressed (0) or Normal/Expanded (1)
    """
    features = pd.DataFrame(index=df.index)
    features["atr_compression_ratio"] = 1.0
    features["vol_regime"] = 1
    
    if "atr" not in df.columns:
        return features
    
    # Calculate fast and slow ATR
    fast_atr = df["atr"].rolling(fast).mean()
    slow_atr = df["atr"].rolling(slow).mean()
    
    # Ratio
    ratio = (fast_atr / slow_atr.clip(lower=1e-6)).fillna(1.0)
    features["atr_compression_ratio"] = ratio
    
    # Regime: compressed when ratio < 0.7
    features["vol_regime"] = (ratio > 0.7).astype(int)
    
    return features


def calculate_liquidity_void(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Detect liquidity voids (strong moves with minimal pullback).
    
    Returns:
    - liquidity_void_score: Likelihood of continued move (high when no pullback)
    """
    features = pd.DataFrame(index=df.index)
    features["liquidity_void_score"] = 0.0
    
    for i in range(window, len(df)):
        window_df = df.iloc[i-window:i+1]
        
        # Measure: total displacement vs pullback
        prices = window_df["close"].values
        displacement = abs(prices[-1] - prices[0])
        
        # Pullback: largest reversal within window
        running_max = np.maximum.accumulate(prices)
        running_min = np.minimum.accumulate(prices)
        pullback = np.max(running_max - prices)
        
        if displacement > 0:
            # High score when displacement >> pullback
            void_score = 1 - (pullback / displacement) if displacement > pullback else 0
            void_score = np.clip(void_score, 0, 1)
        else:
            void_score = 0
        
        features.loc[features.index[i], "liquidity_void_score"] = void_score
    
    return features


def calculate_stop_hunt_probability(
    df: pd.DataFrame,
    extremos: pd.DataFrame,
    window: int = 20
) -> pd.DataFrame:
    """
    Detect stop hunt patterns (sweep + reversal).
    
    Returns:
    - stop_hunt_prob: Probability of stop hunt occurring (0-1)
    """
    features = pd.DataFrame(index=df.index)
    features["stop_hunt_prob"] = 0.0
    
    if extremos.empty:
        return features
    
    for i in range(window, len(df)):
        window_start = max(0, i - window)
        current_price = df["close"].iloc[i]
        atr = df["atr"].iloc[i] if "atr" in df.columns else 1.0
        atr = max(atr, 0.0001)
        
        window_extremos = extremos.iloc[window_start:i]
        
        if len(window_extremos) >= 2:
            # Check for recent sweep followed by reversal
            tops = window_extremos[window_extremos["type"] == "top"]["price"].values
            bottoms = window_extremos[window_extremos["type"] == "bottom"]["price"].values
            
            hunt_score = 0.0
            
            # Top sweep + downside reversal
            if len(tops) > 0:
                top_distance = (tops[-1] - current_price) / atr
                if top_distance < 5 and current_price < tops[-1]:  # Recently swept
                    hunt_score += 0.5
            
            # Bottom sweep + upside reversal
            if len(bottoms) > 0:
                bottom_distance = (current_price - bottoms[-1]) / atr
                if bottom_distance < 5 and current_price > bottoms[-1]:  # Recently swept
                    hunt_score += 0.5
            
            features.loc[features.index[i], "stop_hunt_prob"] = np.clip(hunt_score, 0, 1)
    
    return features


def calculate_regime_persistence(df: pd.DataFrame, window: int = 50) -> pd.DataFrame:
    """
    Measure how long current regime (trend/range) has persisted.
    
    Returns:
    - trend_duration: Candles in current trend
    - range_duration: Candles in current range
    - regime_strength: How clearly defined the regime is
    """
    features = pd.DataFrame(index=df.index)
    features["trend_duration"] = 0
    features["range_duration"] = 0
    features["regime_strength"] = 0.0
    
    for i in range(window, len(df)):
        window_df = df.iloc[i-window:i+1]
        
        # Simple trend detection: compare recent highs/lows
        first_half = window_df.iloc[:window//2]
        second_half = window_df.iloc[window//2:]
        
        first_high = first_half["high"].max()
        first_low = first_half["low"].min()
        second_high = second_half["high"].max()
        second_low = second_half["low"].min()
        
        # Uptrend: higher highs and higher lows
        if second_high > first_high and second_low > first_low:
            features.loc[features.index[i], "trend_duration"] = window // 2
            features.loc[features.index[i], "regime_strength"] = 0.7
        # Downtrend: lower highs and lower lows
        elif second_high < first_high and second_low < first_low:
            features.loc[features.index[i], "trend_duration"] = window // 2
            features.loc[features.index[i], "regime_strength"] = -0.7
        # Range: overlapping highs and lows
        else:
            features.loc[features.index[i], "range_duration"] = window // 2
            features.loc[features.index[i], "regime_strength"] = 0.0
    
    return features


def generate_all_smc_features(df: pd.DataFrame, extremos: pd.DataFrame) -> pd.DataFrame:
    """
    Generate all SMC continuous features for XGBoost.
    
    Returns DataFrame with all features joined to original index.
    """
    smc_features = pd.DataFrame(index=df.index)
    
    # Feature 1-2: Distance to liquidity
    dist_features = calculate_distance_to_liquidity(df)
    smc_features = smc_features.join(dist_features)
    
    # Feature 3-5: Sweep pressure
    sweep_features = calculate_sweep_pressure(df, extremos)
    smc_features = smc_features.join(sweep_features)
    
    # Feature 6-8: BOS pressure
    bos_features = calculate_bos_pressure(df, extremos)
    smc_features = smc_features.join(bos_features)
    
    # Feature 9-10: CHOCH recency
    choch_features = calculate_choch_recency(df, extremos)
    smc_features = smc_features.join(choch_features)
    
    # Feature 11-13: FVG
    fvg_features = calculate_fvg_features(df)
    smc_features = smc_features.join(fvg_features)
    
    # Feature 14-16: Displacement
    displacement_features = calculate_displacement_score(df)
    smc_features = smc_features.join(displacement_features)
    
    # Feature 17-18: Premium/Discount
    premium_features = calculate_premium_discount(df)
    smc_features = smc_features.join(premium_features)
    
    # Feature 19-20: ATR Compression
    compression_features = calculate_atr_compression(df)
    smc_features = smc_features.join(compression_features)
    
    # Feature 21: Liquidity void
    void_features = calculate_liquidity_void(df)
    smc_features = smc_features.join(void_features)
    
    # Feature 22: Stop hunt probability
    hunt_features = calculate_stop_hunt_probability(df, extremos)
    smc_features = smc_features.join(hunt_features)
    
    # Feature 23-25: Regime persistence
    regime_features = calculate_regime_persistence(df)
    smc_features = smc_features.join(regime_features)
    
    return smc_features.fillna(0)
