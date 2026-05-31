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
    
    # Normalizar indicadores em percentual (para cada ativo, melhor pattern learning)
    df = normalize_indicators_to_percentage(df)
    
    return df

def normalize_indicators_to_percentage(df):
    """Normaliza indicadores para percentual do preço (melhora pattern learning por ativo)"""
    df = df.copy()
    close = df['close'].clip(lower=1e-6)
    
    if 'sma20' in df.columns:
        df['sma20_pct'] = ((df['close'] - df['sma20']) / df['sma20'].clip(lower=1e-6)) * 100
    if 'sma50' in df.columns:
        df['sma50_pct'] = ((df['close'] - df['sma50']) / df['sma50'].clip(lower=1e-6)) * 100
    if 'ema12' in df.columns:
        df['ema12_pct'] = ((df['close'] - df['ema12']) / df['ema12'].clip(lower=1e-6)) * 100
    if 'ema26' in df.columns:
        df['ema26_pct'] = ((df['close'] - df['ema26']) / df['ema26'].clip(lower=1e-6)) * 100
    if 'macd' in df.columns:
        df['macd_pct'] = (df['macd'] / close) * 100
    if 'atr' in df.columns:
        df['atr_pct'] = (df['atr'] / close) * 100
    if 'momentum' in df.columns:
        df['momentum_pct'] = (df['momentum'] / close) * 100
    if 'sd' in df.columns:
        df['sd_pct'] = (df['sd'] / close) * 100
    if 'bb_width' in df.columns:
        df['bb_width_pct'] = (df['bb_width'] / close) * 100
    if 'kama' in df.columns:
        df['kama_pct'] = ((df['close'] - df['kama']) / df['kama'].clip(lower=1e-6)) * 100
    if 'smc_support' in df.columns:
        df['smc_support_pct'] = ((df['close'] - df['smc_support']) / df['smc_support'].clip(lower=1e-6)) * 100
    if 'smc_resistance' in df.columns:
        df['smc_resistance_pct'] = ((df['smc_resistance'] - df['close']) / df['close'].clip(lower=1e-6)) * 100
    
    pct_cols = [col for col in df.columns if col.endswith('_pct')]
    df[pct_cols] = df[pct_cols].fillna(0)
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

def calculate_sd_zones(df, vol_period=20):
    """
    Supply and Demand Zones - OTIMIZADA (operações vetorizadas)
    Calcula níveis de suporte/resistência baseado em volatilidade
    """
    # Calcular volatilidade (operação vetorizada)
    returns = df['close'].pct_change()
    rolling_vol = returns.rolling(vol_period).std() * np.sqrt(96)  # M15: 96 barras/dia
    
    # Deslocar para obter vol do período anterior
    vol_prev = rolling_vol.shift(1)
    close_prev = df['close'].shift(1)
    
    # Calcular suporte e resistência (vetorizado)
    offset = vol_prev * close_prev
    support = close_prev - offset
    resistance = close_prev + offset
    
    # Detectar proximidade (vetorizado)
    current_price = df['close']
    price_range = df['high'] - df['low']
    
    # Criar série de resultado
    sd_zone = pd.Series(0, index=df.index)
    
    # Próximo a support
    sd_zone[((current_price - support).abs() < price_range * 1.5) & (price_range > 0)] = -1
    
    # Próximo a resistance  
    sd_zone[((current_price - resistance).abs() < price_range * 1.5) & (price_range > 0) & (sd_zone == 0)] = 1
    
    return sd_zone.fillna(0)

def calculate_liquidity_sweep(df, lookback=8, atr_filter=0.5):
    """
    Liquidity Sweep Detection - OTIMIZADA (operações vetorizadas)
    Detecta varreduras de liquidez (highs/lows tocados e revertidos)
    """
    # Rolling max/min dos últimos lookback candles
    rolling_high = df['high'].rolling(lookback).max().shift(1)  # Shift 1 para não usar futuro
    rolling_low = df['low'].rolling(lookback).min().shift(1)
    
    # ATR ou fallback
    atr = df.get('atr', df['high'] - df['low']) if 'atr' in df.columns else (df['high'] - df['low'])
    
    sweep = pd.Series(0, index=df.index)
    
    # Bearish sweep: high > rolling_high E close < (rolling_high - atr*0.15)
    bearish_condition = (df['high'] > rolling_high) & (df['close'] < (rolling_high - atr * 0.15))
    sweep[bearish_condition] = -1
    
    # Bullish sweep: low < rolling_low E close > (rolling_low + atr*0.15)
    bullish_condition = (df['low'] < rolling_low) & (df['close'] > (rolling_low + atr * 0.15))
    sweep[bullish_condition] = 1
    
    return sweep.fillna(0)

def calculate_market_regime(df, window=10):
    """
    Market Regime Detection - OTIMIZADA (operações vetorizadas)
    Detecta regime: TREND_BULL, TREND_BEAR, RANGE, MANIPULATION
    """
    if 'er' not in df.columns or 'kama' not in df.columns:
        return pd.Series(0, index=df.index).fillna(0)
    
    # Calcular ER médio (rolling window)
    er_rolling = df['er'].rolling(window).mean()
    
    # Calcular slope do KAMA
    kama_slope = df['kama'].diff(window)
    
    # Criar série de regime
    regime = pd.Series(0, index=df.index)
    
    # TREND_BULL: ER > 0.45 E slope > 0
    regime[(er_rolling > 0.45) & (kama_slope > 0)] = 1
    
    # TREND_BEAR: ER > 0.45 E slope < 0
    regime[(er_rolling > 0.45) & (kama_slope < 0)] = -1
    
    # RANGE: ER < 0.25
    regime[(er_rolling < 0.25)] = 0
    
    # MANIPULATION: else (ER entre 0.25-0.45)
    regime[(regime == 0) & (er_rolling >= 0.25) & (er_rolling <= 0.45)] = 2
    
    return regime.fillna(0)

def get_model_features():
    """Retorna lista de features para o modelo (sem target)"""
    # Features recomendadas para o modelo
    # Evita multicolinearidade e mantém features significativas
    return [
        'rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum',
        'er', 'kama', 'realized_vol',
        'sd', 'bb_width',
        'smc_support', 'smc_resistance',
        'price_above_sma20', 'price_above_sma50',
        'price_above_bb_upper', 'price_below_bb_lower',
        'rsi_oversold', 'rsi_overbought',
        'macd_positive', 'momentum_positive',
        'smc_order_block', 'smc_fvg'
    ]
