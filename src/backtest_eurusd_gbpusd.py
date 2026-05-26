#!/usr/bin/env python3
"""
Backtest Comparativo EURUSD vs GBPUSD
Usa SMC Edge Framework para detectar eventos críticos e calcular performance
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

# ═══════════════════════════════════════════════════════════════════════════
# CARREGAR DADOS
# ═══════════════════════════════════════════════════════════════════════════

def load_mt5_csv(file_path: Path) -> pd.DataFrame:
    """Carrega CSV - detecta formato automaticamente (MT5 ou padrão)"""
    
    # Tentar com tab primeiro (formato MT5)
    try:
        df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
        
        # Rename columns
        df.columns = df.columns.str.strip().str.lower().str.replace('<', '').str.replace('>', '')
        
        # Parse datetime (MT5 format: 2023.01.01 22:00:00)
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%Y.%m.%d %H:%M:%S')
        df = df.set_index('datetime').sort_index()
    except (KeyError, ValueError):
        # Tentar formato padrão CSV
        df = pd.read_csv(file_path, encoding='utf-8')
        df.columns = df.columns.str.strip().str.lower()
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime').sort_index()
    
    # Ensure numeric
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove rows with NaN prices
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    
    # Remove duplicate indices
    df = df[~df.index.duplicated(keep='first')]
    
    return df


def calculate_smc_features(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """
    Calcula features SMC:
    - Extremos (high/low de N candles)
    - Sweeps (penetração + reversão)
    - Distância aos extremos
    - Confluência de sinais
    """
    
    df = df.copy()
    
    # 1. Extremos
    df['high_lookback'] = df['high'].rolling(window=lookback, min_periods=1).max()
    df['low_lookback'] = df['low'].rolling(window=lookback, min_periods=1).min()
    
    # 2. Distância ao extremo (%)
    df['dist_to_high'] = ((df['high_lookback'] - df['close']) / df['close'] * 100).round(4)
    df['dist_to_low'] = ((df['close'] - df['low_lookback']) / df['close'] * 100).round(4)
    
    # 3. Detectar toques em extremos
    df['touched_high'] = ((df['high'] >= df['high_lookback'].shift(1)) & 
                          (df['close'] < df['high_lookback'].shift(1))).astype(int)
    df['touched_low'] = ((df['low'] <= df['low_lookback'].shift(1)) & 
                         (df['close'] > df['low_lookback'].shift(1))).astype(int)
    
    # 4. Volatilidade (ATR normalizado)
    df['atr_14'] = calculate_atr(df, period=14)
    df['atr_pct'] = (df['atr_14'] / df['close'] * 100).round(4)
    
    # 5. Tamanho do candle (body %)
    df['candle_body'] = abs(df['close'] - df['open']) / df['close'] * 100
    df['candle_body'] = df['candle_body'].round(4)
    
    # 6. Wick ratio (wick/total candle)
    df['high_wick'] = (df['high'] - df[['open', 'close']].max(axis=1)) / (df['high'] - df['low'] + 1e-8)
    df['low_wick'] = (df[['open', 'close']].min(axis=1) - df['low']) / (df['high'] - df['low'] + 1e-8)
    df['high_wick'] = df['high_wick'].round(3)
    df['low_wick'] = df['low_wick'].round(3)
    
    # 7. Regime (range vs trend)
    sma_20 = df['close'].rolling(window=20, min_periods=1).mean()
    sma_50 = df['close'].rolling(window=50, min_periods=1).mean()
    
    df['regime'] = 'RANGE'
    df.loc[sma_20 > sma_50 + (df['atr_14'] * 0.5), 'regime'] = 'UPTREND'
    df.loc[sma_20 < sma_50 - (df['atr_14'] * 0.5), 'regime'] = 'DOWNTREND'
    
    return df


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calcula Average True Range"""
    tr = pd.concat([
        df['high'] - df['low'],
        abs(df['high'] - df['close'].shift(1)),
        abs(df['low'] - df['close'].shift(1))
    ], axis=1).max(axis=1)
    
    return tr.rolling(window=period, min_periods=1).mean()


def detect_critical_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta eventos críticos SMC:
    - Confluência >= 3 sinais
    - ATR > 0.04%
    - Small body < 0.03%
    """
    
    df = df.copy()
    df['is_critical'] = 0
    
    # Critérios de críticidade
    touch_signal = (df['touched_high'] | df['touched_low']).astype(int)
    vol_signal = (df['atr_pct'] > 0.04).astype(int)
    small_body_signal = (df['candle_body'] < 0.03).astype(int)
    
    # Confluência: quantos sinais confirmam
    df['confluence'] = touch_signal + vol_signal + small_body_signal
    
    # Evento crítico: at least 2 signals
    df['is_critical'] = (df['confluence'] >= 2).astype(int)
    
    return df


def calculate_reversal_accuracy(df: pd.DataFrame, forward_candles: int = 5) -> dict:
    """
    Calcula acerto de reversão nos próximos N candles
    Bullish: se low foi tocado e preço sobe nos próximos N
    Bearish: se high foi tocado e preço cai nos próximos N
    """
    
    results = {
        'total_events': 0,
        'bullish_events': 0,
        'bearish_events': 0,
        'bullish_wins': 0,
        'bearish_wins': 0,
        'bullish_wr': 0.0,
        'bearish_wr': 0.0,
        'overall_wr': 0.0,
    }
    
    for i in range(len(df) - forward_candles):
        if df['is_critical'].iloc[i] == 0:
            continue
        
        results['total_events'] += 1
        
        # Next N candles close (em % de movimento)
        current_close = df['close'].iloc[i]
        max_close = df['close'].iloc[i+1:i+1+forward_candles].max()
        min_close = df['close'].iloc[i+1:i+1+forward_candles].min()
        
        move_up = (max_close - current_close) / current_close * 100
        move_down = (current_close - min_close) / current_close * 100
        
        # Bullish event (low touched)
        if df['touched_low'].iloc[i]:
            results['bullish_events'] += 1
            if move_up > 0.01:  # Move up > 0.01%
                results['bullish_wins'] += 1
        
        # Bearish event (high touched)
        if df['touched_high'].iloc[i]:
            results['bearish_events'] += 1
            if move_down > 0.01:  # Move down > 0.01%
                results['bearish_wins'] += 1
    
    # Calculate win rates
    if results['bullish_events'] > 0:
        results['bullish_wr'] = round(results['bullish_wins'] / results['bullish_events'] * 100, 2)
    
    if results['bearish_events'] > 0:
        results['bearish_wr'] = round(results['bearish_wins'] / results['bearish_events'] * 100, 2)
    
    if results['total_events'] > 0:
        total_wins = results['bullish_wins'] + results['bearish_wins']
        results['overall_wr'] = round(total_wins / results['total_events'] * 100, 2)
    
    # Convert to int to avoid JSON serialization issues
    for key in results:
        if isinstance(results[key], (np.int64, np.int32)):
            results[key] = int(results[key])
    
    return results


def analyze_pair(file_path: Path, symbol: str) -> dict:
    """Analisa um par de moedas completo"""
    
    print(f"\n{'='*80}")
    print(f"📊 BACKTEST: {symbol}")
    print(f"{'='*80}")
    
    # Load
    print(f"⏳ Carregando dados de {file_path.name}...")
    df = load_mt5_csv(file_path)
    print(f"✅ {len(df):,} candles carregados")
    print(f"   Período: {df.index.min()} até {df.index.max()}")
    
    # Features
    print(f"🔧 Calculando features SMC...")
    df = calculate_smc_features(df)
    
    # Critical events
    print(f"🎯 Detectando eventos críticos...")
    df = detect_critical_events(df)
    
    critical_count = df['is_critical'].sum()
    critical_pct = (critical_count / len(df) * 100)
    print(f"   Eventos críticos encontrados: {critical_count:,} ({critical_pct:.2f}%)")
    
    # Accuracy
    print(f"📈 Calculando acurácia de reversão...")
    accuracy = calculate_reversal_accuracy(df)
    
    # Convert all numpy types to python types
    accuracy_clean = {}
    for k, v in accuracy.items():
        if isinstance(v, (np.int64, np.int32)):
            accuracy_clean[k] = int(v)
        elif isinstance(v, (np.float64, np.float32)):
            accuracy_clean[k] = float(v)
        else:
            accuracy_clean[k] = v
    
    # Price stats
    current_price = df['close'].iloc[-1]
    min_price = df['low'].min()
    max_price = df['high'].max()
    price_range = max_price - min_price
    
    return {
        'symbol': symbol,
        'total_candles': int(len(df)),
        'critical_events': int(critical_count),
        'critical_pct': round(critical_pct, 2),
        'min_price': round(float(min_price), 5),
        'max_price': round(float(max_price), 5),
        'current_price': round(float(current_price), 5),
        'price_range': round(float(price_range), 5),
        'accuracy': accuracy_clean,
    }


def print_comparison(results: list[dict]) -> None:
    """Imprime comparação entre pares"""
    
    print(f"\n{'='*80}")
    print("📊 COMPARAÇÃO EURUSD vs GBPUSD")
    print(f"{'='*80}\n")
    
    for r in results:
        symbol = r['symbol']
        acc = r['accuracy']
        
        print(f"📌 {symbol}")
        print(f"   Candles: {r['total_candles']:,}")
        print(f"   Eventos críticos: {r['critical_events']:,} ({r['critical_pct']:.2f}%)")
        print(f"   Range de preço: {r['min_price']} - {r['max_price']}")
        print(f"   Preço atual: {r['current_price']}")
        print()
        print(f"   📈 PERFORMANCE:")
        print(f"      Total de eventos: {acc['total_events']:,}")
        print(f"      Overall WR: {acc['overall_wr']:.2f}%")
        print(f"      ├─ Bullish: {acc['bullish_wr']:.2f}% ({acc['bullish_wins']}/{acc['bullish_events']} eventos)")
        print(f"      └─ Bearish: {acc['bearish_wr']:.2f}% ({acc['bearish_wins']}/{acc['bearish_events']} eventos)")
        print()


def main():
    """Main entrypoint"""
    
    data_dir = Path('/home/ubuntu/pessoal/options/dados')
    
    # Process both pairs
    results = []
    
    # EURUSD
    eurusd_file = data_dir / 'EURUSD_M15_202301012200_202605222015.csv'
    if eurusd_file.exists():
        eurusd_result = analyze_pair(eurusd_file, 'EURUSD')
        results.append(eurusd_result)
    
    # GBPUSD
    gbpusd_file = data_dir / 'GBPUSD_M15_202601012000_202603012345_processed.csv'
    if gbpusd_file.exists():
        gbpusd_result = analyze_pair(gbpusd_file, 'GBPUSD')
        results.append(gbpusd_result)
    
    # Print comparison
    print_comparison(results)
    
    # Save results
    output_file = Path('/home/ubuntu/pessoal/options/backtest_results/backtest_eurusd_gbpusd.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Resultados salvos em: {output_file}")


if __name__ == '__main__':
    main()
