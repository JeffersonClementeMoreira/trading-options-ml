#!/usr/bin/env python3
"""
Módulo de Cálculo de Indicadores Técnicos
Reutilizável para: Backtest, Treinamento, Produção
"""

import numpy as np
import pandas as pd

def calculate_rsi(df, period=14):
    """Calcula RSI (Relative Strength Index)"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def calculate_sma(df, window):
    """Calcula SMA (Simple Moving Average)"""
    sma = df['close'].rolling(window=window).mean()
    return sma.fillna(df['close'])

def calculate_ema(df, window):
    """Calcula EMA (Exponential Moving Average)"""
    ema = df['close'].ewm(span=window).mean()
    return ema.fillna(df['close'])

def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calcula MACD (Moving Average Convergence Divergence)"""
    ema_fast = df['close'].ewm(span=fast).mean()
    ema_slow = df['close'].ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    return macd_line.fillna(0)

def calculate_atr(df, period=14):
    """Calcula ATR (Average True Range)"""
    tr = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            np.abs(df['high'] - df['close'].shift()),
            np.abs(df['low'] - df['close'].shift())
        )
    )
    atr = tr.rolling(window=period).mean()
    return atr.fillna(df['high'] - df['low'])

def calculate_momentum(df, period=14):
    """Calcula Momentum"""
    momentum = df['close'].diff(periods=period)
    return momentum.fillna(0)

def calculate_sd(df, window=20):
    """Calcula SD (Standard Deviation)"""
    sd = df['close'].rolling(window=window).std()
    return sd.fillna(0)

def calculate_bollinger_bands(df, window=20, num_std=2):
    """Calcula Bandas de Bollinger"""
    sma = df['close'].rolling(window=window).mean()
    sd = df['close'].rolling(window=window).std()
    
    upper_band = sma + (sd * num_std)
    lower_band = sma - (sd * num_std)
    
    upper_band = upper_band.fillna(df['close'])
    lower_band = lower_band.fillna(df['close'])
    
    return upper_band, lower_band

def calculate_smc_support_resistance(df, window=20):
    """
    Calcula níveis de Suporte/Resistência (SMC - Smart Money Concepts)
    Baseado em highs/lows recentes
    """
    # Resistência: máxima dos últimos N candles
    resistance = df['high'].rolling(window=window).max()
    
    # Suporte: mínima dos últimos N candles
    support = df['low'].rolling(window=window).min()
    
    return support.fillna(df['low']), resistance.fillna(df['high'])

def calculate_smc_order_blocks(df, window=5):
    """
    Detecta Order Blocks (SMC)
    Blocos onde institucionais acumulam/distribuem
    """
    # Order Block Bullish: mínima local seguida por candles altos
    local_min = df['low'].rolling(window=window, center=True).min()
    
    # Order Block Bearish: máxima local seguida por candles baixos
    local_max = df['high'].rolling(window=window, center=True).max()
    
    # Flag: 1 se é possível order block bullish, -1 se bearish, 0 se neutro
    order_block_type = pd.Series(0, index=df.index)
    
    for i in range(window, len(df)):
        if df['low'].iloc[i] == local_min.iloc[i]:
            order_block_type.iloc[i] = 1  # Possível OB Bullish
        elif df['high'].iloc[i] == local_max.iloc[i]:
            order_block_type.iloc[i] = -1  # Possível OB Bearish
    
    return order_block_type

def calculate_fvg(df, threshold=0.0001):
    """
    Calcula FVG (Fair Value Gap) - SMC
    Gap entre candles onde ninguém fez transação
    """
    # FVG Bullish: low(n) > high(n-2)
    # FVG Bearish: high(n) < low(n-2)
    
    fvg_type = pd.Series(0, index=df.index)
    
    for i in range(2, len(df)):
        bullish_fvg = df['low'].iloc[i] > df['high'].iloc[i-2]
        bearish_fvg = df['high'].iloc[i] < df['low'].iloc[i-2]
        
        if bullish_fvg:
            fvg_type.iloc[i] = 1  # FVG Bullish
        elif bearish_fvg:
            fvg_type.iloc[i] = -1  # FVG Bearish
    
    return fvg_type

def calculate_kaufman_efficiency_ratio(df, period=20):
    """
    Calcula Kaufman Efficiency Ratio (ER)
    Mede o quanto uma sequência de preços é eficiente em relação à sua volatilidade
    ER alta = trend forte | ER baixa = range
    """
    direction = (df['close'] - df['close'].shift(period)).abs()
    volatility = (df['close'] - df['close'].shift(1)).abs().rolling(period).sum()
    er = direction / volatility.clip(lower=1e-6)
    return er.fillna(0.0)

def calculate_kama(df, period_er=10, fast=2, slow=30):
    """
    Calcula KAMA (Kaufman's Adaptive Moving Average)
    MA adaptativa que se ajusta à eficiência do trend
    """
    close = df['close']
    er = calculate_kaufman_efficiency_ratio(df, period=period_er)
    
    fast_sc = 2 / (fast + 1)
    slow_sc = 2 / (slow + 1)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
    
    kama_values = np.zeros(len(close))
    kama_values[0] = close.iloc[0]
    
    for i in range(1, len(close)):
        kama_values[i] = kama_values[i - 1] + sc.iloc[i] * (close.iloc[i] - kama_values[i - 1])
    
    return pd.Series(kama_values, index=df.index)

def calculate_realized_volatility(df, bars_per_day=96, days_per_year=252):
    """
    Calcula Realized Volatility (volatilidade realizada)
    Volatilidade observada dos retornos recentes
    """
    returns = df['close'].pct_change()
    realized_vol = (returns.rolling(bars_per_day).std() * np.sqrt(bars_per_day * days_per_year))
    
    # Também considera ATR como componente
    if 'atr' in df.columns:
        atr_pct = df['atr'] / df['close'].clip(lower=1e-6)
        atr_vol = atr_pct.rolling(bars_per_day).mean() * np.sqrt(days_per_year)
        realized_vol = np.maximum(realized_vol, atr_vol)
    
    return realized_vol.fillna(0.0)

def calculate_all_indicators(df):
    """
    Calcula TODOS os indicadores de uma vez
    Entrada: DataFrame com colunas [timestamp, open, high, low, close, ...]
    Saída: DataFrame com todos os indicadores adicionados
    """
    
    # Indicadores básicos
    df['rsi'] = calculate_rsi(df, period=14)
    df['sma20'] = calculate_sma(df, window=20)
    df['sma50'] = calculate_sma(df, window=50)
    df['ema12'] = calculate_ema(df, window=12)
    df['ema26'] = calculate_ema(df, window=26)
    df['macd'] = calculate_macd(df)
    df['atr'] = calculate_atr(df, period=14)
    df['momentum'] = calculate_momentum(df, period=14)
    
    # Indicadores avançados (do backup)
    df['er'] = calculate_kaufman_efficiency_ratio(df, period=20)
    df['kama'] = calculate_kama(df, period_er=10, fast=2, slow=30)
    df['realized_vol'] = calculate_realized_volatility(df, bars_per_day=96, days_per_year=252)
    
    # Novo: Standard Deviation
    df['sd'] = calculate_sd(df, window=20)
    
    # Novo: Bollinger Bands
    df['bb_upper'], df['bb_lower'] = calculate_bollinger_bands(df, window=20, num_std=2)
    df['bb_width'] = df['bb_upper'] - df['bb_lower']
    
    # Novo: SMC Support/Resistance
    df['smc_support'], df['smc_resistance'] = calculate_smc_support_resistance(df, window=20)
    
    # Novo: SMC Order Blocks
    df['smc_order_block'] = calculate_smc_order_blocks(df, window=5)
    
    # Novo: SMC Fair Value Gaps
    df['smc_fvg'] = calculate_fvg(df)
    
    # Indicadores binários (baseados nos contínuos)
    df['price_above_sma20'] = (df['close'] > df['sma20']).astype(int)
    df['price_above_sma50'] = (df['close'] > df['sma50']).astype(int)
    df['price_above_bb_upper'] = (df['close'] > df['bb_upper']).astype(int)
    df['price_below_bb_lower'] = (df['close'] < df['bb_lower']).astype(int)
    df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
    df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
    df['macd_positive'] = (df['macd'] > 0).astype(int)
    df['momentum_positive'] = (df['momentum'] > 0).astype(int)
    
    return df

def get_indicator_names():
    """Retorna lista de todos os indicadores calculados"""
    continuous = [
        'rsi', 'sma20', 'sma50', 'ema12', 'ema26', 'macd', 'atr', 'momentum',
        'er', 'kama', 'realized_vol',  # Novos do backup
        'sd', 'bb_upper', 'bb_lower', 'bb_width',
        'smc_support', 'smc_resistance'
    ]
    
    binary = [
        'price_above_sma20', 'price_above_sma50',
        'price_above_bb_upper', 'price_below_bb_lower',
        'rsi_oversold', 'rsi_overbought', 'macd_positive', 'momentum_positive',
        'smc_order_block', 'smc_fvg'
    ]
    
    return {
        'continuous': continuous,
        'binary': binary,
        'all': continuous + binary
    }

def get_model_features():
    """Retorna lista de features para o modelo (sem target)"""
    # Features recomendadas para o modelo
    # Evita multicolinearidade e mantém features significativas
    return [
        'rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum',
        'er', 'kama', 'realized_vol',  # Novos do backup
        'sd', 'bb_width',
        'smc_support', 'smc_resistance',
        'price_above_sma20', 'price_above_sma50',
        'price_above_bb_upper', 'price_below_bb_lower',
        'rsi_oversold', 'rsi_overbought',
        'macd_positive', 'momentum_positive',
        'smc_order_block', 'smc_fvg'
    ]
