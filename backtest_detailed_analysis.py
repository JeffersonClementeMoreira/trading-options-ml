#!/usr/bin/env python3
"""
Backtest Detalhado com Análise SMC
- Eventos críticos por tipo
- Win rate em diferentes configurações
- Estatísticas de trades
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

# ═══════════════════════════════════════════════════════════════════════════

def load_csv(file_path: Path) -> pd.DataFrame:
    """Carrega CSV - detecta formato automaticamente"""
    try:
        # MT5 format
        df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
        df.columns = df.columns.str.strip().str.lower().str.replace('<', '').str.replace('>', '')
        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%Y.%m.%d %H:%M:%S')
        df = df.set_index('datetime').sort_index()
    except (KeyError, ValueError):
        # Standard CSV
        df = pd.read_csv(file_path, encoding='utf-8')
        df.columns = df.columns.str.strip().str.lower()
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime').sort_index()
    
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    df = df[~df.index.duplicated(keep='first')]
    
    return df


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """ATR"""
    tr = pd.concat([
        df['high'] - df['low'],
        abs(df['high'] - df['close'].shift(1)),
        abs(df['low'] - df['close'].shift(1))
    ], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=1).mean()


def analyze_detailed(file_path: Path, symbol: str) -> dict:
    """Análise detalhada de um par"""
    
    print(f"\n{'='*80}")
    print(f"📊 ANÁLISE DETALHADA: {symbol}")
    print(f"{'='*80}\n")
    
    # Load
    print(f"⏳ Carregando dados...")
    df = load_csv(file_path)
    print(f"✅ {len(df):,} candles ({df.index.min().date()} até {df.index.max().date()})")
    
    # Calculate features
    lookback = 20
    df['high_20'] = df['high'].rolling(window=lookback, min_periods=1).max()
    df['low_20'] = df['low'].rolling(window=lookback, min_periods=1).min()
    df['atr_14'] = calculate_atr(df)
    df['atr_pct'] = (df['atr_14'] / df['close'] * 100).round(4)
    
    # SMC signals
    df['touched_high'] = ((df['high'] >= df['high_20'].shift(1)) & 
                          (df['close'] < df['high_20'].shift(1))).astype(int)
    df['touched_low'] = ((df['low'] <= df['low_20'].shift(1)) & 
                         (df['close'] > df['low_20'].shift(1))).astype(int)
    
    # Candle structure
    df['body_pct'] = abs(df['close'] - df['open']) / df['close'] * 100
    df['high_wick'] = (df['high'] - df[['open', 'close']].max(axis=1)) / (df['high'] - df['low'] + 1e-8)
    df['low_wick'] = (df[['open', 'close']].min(axis=1) - df['low']) / (df['high'] - df['low'] + 1e-8)
    
    # Regime
    sma_20 = df['close'].rolling(20, min_periods=1).mean()
    sma_50 = df['close'].rolling(50, min_periods=1).mean()
    df['regime'] = 'RANGE'
    df.loc[sma_20 > sma_50, 'regime'] = 'UP'
    df.loc[sma_20 < sma_50, 'regime'] = 'DOWN'
    
    # ───────────────────────────────────────────────────────────────────
    print("📊 STATISTICS\n")
    print(f"Preço Min: {df['low'].min():.5f}")
    print(f"Preço Max: {df['high'].max():.5f}")
    print(f"Preço Atual: {df['close'].iloc[-1]:.5f}")
    print(f"ATR Médio: {df['atr_pct'].mean():.4f}%")
    print()
    
    # ───────────────────────────────────────────────────────────────────
    print("🎯 EVENTOS SMC\n")
    
    bullish_touches = df['touched_low'].sum()
    bearish_touches = df['touched_high'].sum()
    total_touches = bullish_touches + bearish_touches
    
    print(f"Toques em extremos baixos (BULLISH): {bullish_touches:,}")
    print(f"Toques em extremos altos (BEARISH): {bearish_touches:,}")
    print(f"Total de eventos: {total_touches:,}")
    print(f"Taxa de eventos: {(total_touches/len(df)*100):.2f}% dos candles")
    print()
    
    # ───────────────────────────────────────────────────────────────────
    print("📈 ANÁLISE DE WIN RATE (diferentes thresholds)\n")
    
    # Test different reversal thresholds
    thresholds = [0.005, 0.01, 0.02, 0.03, 0.05]
    forward_candles = 5
    
    for threshold in thresholds:
        bullish_wins = 0
        bearish_wins = 0
        bullish_total = 0
        bearish_total = 0
        
        for i in range(len(df) - forward_candles):
            current_close = df['close'].iloc[i]
            max_close = df['close'].iloc[i+1:i+1+forward_candles].max()
            min_close = df['close'].iloc[i+1:i+1+forward_candles].min()
            
            move_up_pct = (max_close - current_close) / current_close * 100
            move_down_pct = (current_close - min_close) / current_close * 100
            
            # Bullish
            if df['touched_low'].iloc[i]:
                bullish_total += 1
                if move_up_pct > threshold:
                    bullish_wins += 1
            
            # Bearish
            if df['touched_high'].iloc[i]:
                bearish_total += 1
                if move_down_pct > threshold:
                    bearish_wins += 1
        
        total_wins = bullish_wins + bearish_wins
        total_trades = bullish_total + bearish_total
        overall_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0
        bullish_wr = (bullish_wins / bullish_total * 100) if bullish_total > 0 else 0
        bearish_wr = (bearish_wins / bearish_total * 100) if bearish_total > 0 else 0
        
        print(f"Threshold: {threshold:.3f}%")
        print(f"  Overall WR: {overall_wr:.2f}% ({total_wins}/{total_trades} trades)")
        print(f"  ├─ Bullish: {bullish_wr:.2f}% ({bullish_wins}/{bullish_total})")
        print(f"  └─ Bearish: {bearish_wr:.2f}% ({bearish_wins}/{bearish_total})")
        print()
    
    # ───────────────────────────────────────────────────────────────────
    print("🔥 EVENTOS COM ALTA CONFLUÊNCIA\n")
    
    # High confluence: touched + high ATR + small body
    df['high_confluence'] = (
        ((df['touched_high'] | df['touched_low']).astype(int)) +
        (df['atr_pct'] > df['atr_pct'].quantile(0.75)).astype(int) +
        (df['body_pct'] < df['body_pct'].quantile(0.25)).astype(int)
    )
    
    high_conf_events = df[df['high_confluence'] >= 2]
    print(f"Eventos com 2+ sinais: {len(high_conf_events):,} ({len(high_conf_events)/len(df)*100:.2f}%)")
    
    if len(high_conf_events) > 0:
        # Win rate for high confluence
        bullish_high = 0
        bearish_high = 0
        bullish_high_wins = 0
        bearish_high_wins = 0
        
        for i in high_conf_events.index:
            idx = df.index.get_loc(i)
            if idx >= len(df) - forward_candles:
                continue
            
            current_close = df['close'].iloc[idx]
            max_close = df['close'].iloc[idx+1:idx+1+forward_candles].max()
            min_close = df['close'].iloc[idx+1:idx+1+forward_candles].min()
            
            move_up = (max_close - current_close) / current_close * 100
            move_down = (current_close - min_close) / current_close * 100
            
            if df['touched_low'].iloc[idx]:
                bullish_high += 1
                if move_up > 0.02:
                    bullish_high_wins += 1
            
            if df['touched_high'].iloc[idx]:
                bearish_high += 1
                if move_down > 0.02:
                    bearish_high_wins += 1
        
        bullish_wr_hc = (bullish_high_wins / bullish_high * 100) if bullish_high > 0 else 0
        bearish_wr_hc = (bearish_high_wins / bearish_high * 100) if bearish_high > 0 else 0
        
        print(f"Bullish (2+ sinais): {bullish_wr_hc:.2f}% ({bullish_high_wins}/{bullish_high})")
        print(f"Bearish (2+ sinais): {bearish_wr_hc:.2f}% ({bearish_high_wins}/{bearish_high})")
        print()
    
    # ───────────────────────────────────────────────────────────────────
    print("📊 REGIME ANALYSIS\n")
    
    for regime in ['RANGE', 'UP', 'DOWN']:
        regime_df = df[df['regime'] == regime]
        regime_pct = len(regime_df) / len(df) * 100
        regime_events = ((regime_df['touched_high'] | regime_df['touched_low']).sum())
        print(f"{regime}: {len(regime_df):,} candles ({regime_pct:.1f}%) | {regime_events} eventos")
    
    print()
    return {
        'symbol': symbol,
        'data_points': len(df),
        'period': f"{df.index.min().date()} to {df.index.max().date()}",
        'price_stats': {
            'min': float(df['low'].min()),
            'max': float(df['high'].max()),
            'current': float(df['close'].iloc[-1]),
            'atr_mean': float(df['atr_pct'].mean()),
        },
        'smc_events': {
            'bullish_touches': int(bullish_touches),
            'bearish_touches': int(bearish_touches),
            'total_events': int(total_touches),
            'events_pct': float((total_touches/len(df)*100)),
        },
        'high_confluence': int(len(high_conf_events)),
    }


def main():
    """Main"""
    data_dir = Path('/home/ubuntu/pessoal/options/dados')
    
    results = []
    
    # EURUSD
    eurusd_file = data_dir / 'EURUSD_M15_202301012200_202605222015.csv'
    if eurusd_file.exists():
        eurusd_result = analyze_detailed(eurusd_file, 'EURUSD')
        results.append(eurusd_result)
    
    # GBPUSD
    gbpusd_file = data_dir / 'GBPUSD_M15_202601012000_202603012345_processed.csv'
    if gbpusd_file.exists():
        gbpusd_result = analyze_detailed(gbpusd_file, 'GBPUSD')
        results.append(gbpusd_result)
    
    # Save
    output_file = Path('/home/ubuntu/pessoal/options/backtest_results/backtest_detailed_analysis.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Análise detalhada salva: {output_file}")


if __name__ == '__main__':
    main()
