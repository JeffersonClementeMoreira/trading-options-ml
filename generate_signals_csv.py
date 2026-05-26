#!/usr/bin/env python3
"""
Análise Detalhada com CSV Completo
Mostra cada candle, a decisão do modelo, e o resultado da operação
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

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


def analyze_with_signals(file_path: Path, symbol: str, output_csv: Path) -> pd.DataFrame:
    """
    Análise completa com sinais de entrada/saída
    """
    
    print(f"\n{'='*100}")
    print(f"📊 ANÁLISE DETALHADA COM SINAIS: {symbol}")
    print(f"{'='*100}\n")
    
    # Load
    print(f"⏳ Carregando dados...")
    df = load_csv(file_path)
    print(f"✅ {len(df):,} candles carregados")
    
    # Copy for processing
    df = df.copy()
    df.reset_index(inplace=True)
    
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
    # Detectar sinal: confluência >= 2
    df['confluence'] = (
        ((df['touched_high'] | df['touched_low']).astype(int)) +
        (df['atr_pct'] > df['atr_pct'].quantile(0.75)).astype(int) +
        (df['body_pct'] < df['body_pct'].quantile(0.25)).astype(int)
    )
    
    df['signal'] = 'HOLD'
    df.loc[(df['touched_low'] == 1) & (df['confluence'] >= 2), 'signal'] = 'BUY (BULLISH)'
    df.loc[(df['touched_high'] == 1) & (df['confluence'] >= 2), 'signal'] = 'SELL (BEARISH)'
    
    # ───────────────────────────────────────────────────────────────────
    # Calcular entrada e saída
    df['entry_price'] = np.nan
    df['exit_price'] = np.nan
    df['exit_time'] = ''
    df['exit_idx'] = np.nan
    df['movement_pct'] = np.nan
    df['result'] = ''
    
    forward_candles = 5
    threshold = 0.01  # 1.0% movement
    
    for idx in range(len(df) - forward_candles):
        if df['signal'].iloc[idx] == 'HOLD':
            continue
        
        signal = df['signal'].iloc[idx]
        entry_price = df['close'].iloc[idx]
        
        # Find exit in next 5 candles
        future_slice = df.iloc[idx+1:idx+1+forward_candles]
        
        if signal == 'BUY (BULLISH)':
            # Look for 1% up movement
            max_high = future_slice['high'].max()
            move_pct = (max_high - entry_price) / entry_price * 100
            
            if move_pct >= threshold:
                # Find first candle that reaches 1% up
                for future_idx, row in future_slice.iterrows():
                    if row['high'] >= entry_price * (1 + threshold/100):
                        df.at[idx, 'exit_price'] = entry_price * (1 + threshold/100)
                        df.at[idx, 'exit_time'] = str(row['datetime'])
                        df.at[idx, 'exit_idx'] = future_idx
                        df.at[idx, 'movement_pct'] = round(move_pct, 2)
                        df.at[idx, 'result'] = f'WIN ✅ (+{threshold}%)'
                        break
            else:
                # No exit reached
                df.at[idx, 'exit_price'] = future_slice['close'].iloc[-1]
                df.at[idx, 'exit_time'] = str(future_slice.iloc[-1]['datetime'])
                df.at[idx, 'exit_idx'] = future_slice.index[-1]
                df.at[idx, 'movement_pct'] = round(move_pct, 2)
                df.at[idx, 'result'] = f'LOSS ❌ ({move_pct:.2f}%)'
        
        elif signal == 'SELL (BEARISH)':
            # Look for 1% down movement
            min_low = future_slice['low'].min()
            move_pct = (entry_price - min_low) / entry_price * 100
            
            if move_pct >= threshold:
                # Find first candle that reaches 1% down
                for future_idx, row in future_slice.iterrows():
                    if row['low'] <= entry_price * (1 - threshold/100):
                        df.at[idx, 'exit_price'] = entry_price * (1 - threshold/100)
                        df.at[idx, 'exit_time'] = str(row['datetime'])
                        df.at[idx, 'exit_idx'] = future_idx
                        df.at[idx, 'movement_pct'] = round(move_pct, 2)
                        df.at[idx, 'result'] = f'WIN ✅ (+{threshold}%)'
                        break
            else:
                # No exit reached
                df.at[idx, 'exit_price'] = future_slice['close'].iloc[-1]
                df.at[idx, 'exit_time'] = str(future_slice.iloc[-1]['datetime'])
                df.at[idx, 'exit_idx'] = future_slice.index[-1]
                df.at[idx, 'movement_pct'] = round(move_pct, 2)
                df.at[idx, 'result'] = f'LOSS ❌ ({move_pct:.2f}%)'
        
        df.at[idx, 'entry_price'] = entry_price
    
    # ───────────────────────────────────────────────────────────────────
    # Selecionar apenas colunas relevantes
    output_cols = [
        'datetime',
        'open',
        'high',
        'low',
        'close',
        'atr_pct',
        'confluence',
        'regime',
        'signal',
        'entry_price',
        'exit_price',
        'exit_time',
        'movement_pct',
        'result',
    ]
    
    result_df = df[output_cols].copy()
    
    # ───────────────────────────────────────────────────────────────────
    # Salvar
    result_df.to_csv(output_csv, index=False)
    print(f"✅ CSV salvo: {output_csv}")
    
    # ───────────────────────────────────────────────────────────────────
    # Mostrar estatísticas
    print(f"\n📊 ESTATÍSTICAS\n")
    
    signals = result_df[result_df['signal'] != 'HOLD']
    print(f"Total de sinais: {len(signals)}")
    
    buys = signals[signals['signal'] == 'BUY (BULLISH)']
    sells = signals[signals['signal'] == 'SELL (BEARISH)']
    print(f"├─ BUY: {len(buys)}")
    print(f"└─ SELL: {len(sells)}")
    
    print(f"\n📈 RESULTADOS\n")
    
    wins = result_df[result_df['result'].str.contains('WIN', na=False)]
    losses = result_df[result_df['result'].str.contains('LOSS', na=False)]
    
    if len(wins) + len(losses) > 0:
        wr = len(wins) / (len(wins) + len(losses)) * 100
        print(f"Win Rate: {wr:.2f}% ({len(wins)}/{len(wins) + len(losses)})")
        print(f"├─ Wins: {len(wins)} ✅")
        print(f"└─ Losses: {len(losses)} ❌")
    
    # ───────────────────────────────────────────────────────────────────
    # Mostrar últimas operações
    print(f"\n🎯 ÚLTIMAS OPERAÇÕES COM SINAL\n")
    
    recent_signals = result_df[result_df['signal'] != 'HOLD'].tail(10)
    for idx, row in recent_signals.iterrows():
        print(f"Data: {row['datetime']} | {row['signal']}")
        print(f"   Entrada: {row['entry_price']:.5f} | Saída: {row['exit_price']:.5f}")
        print(f"   Movimento: {row['movement_pct']:.2f}% | {row['result']}")
        print()
    
    return result_df


def main():
    """Main"""
    data_dir = Path('/home/ubuntu/pessoal/options/dados')
    output_dir = Path('/home/ubuntu/pessoal/options/backtest_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # GBPUSD (mais interessante por ter melhor WR)
    gbpusd_file = data_dir / 'GBPUSD_M15_202601012000_202603012345_processed.csv'
    gbpusd_output = output_dir / 'gbpusd_signals_completo.csv'
    
    if gbpusd_file.exists():
        gbpusd_df = analyze_with_signals(gbpusd_file, 'GBPUSD', gbpusd_output)
        print(f"\n✅ Arquivo salvo para análise visual em Excel/Google Sheets")
    
    # EURUSD também
    eurusd_file = data_dir / 'EURUSD_M15_202301012200_202605222015.csv'
    eurusd_output = output_dir / 'eurusd_signals_completo.csv'
    
    if eurusd_file.exists():
        print("\n" + "="*100)
        eurusd_df = analyze_with_signals(eurusd_file, 'EURUSD', eurusd_output)


if __name__ == '__main__':
    main()
