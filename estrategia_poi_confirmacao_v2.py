#!/usr/bin/env python3
"""
ESTRATÉGIA POI+CONFIRMAÇÃO v2 - Usando Dataset Completo

Objetivo: Implementar a estratégia de 3 camadas em 84k candles
Para alcançar: 50%+ WR com Profit Factor > 1.3x
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 140)
print("🚀 ESTRATÉGIA POI+CONFIRMAÇÃO v2 - Dataset Completo")
print("=" * 140)
print()

# =====================================================================
# 1. CARREGAR E PREPARAR DADOS
# =====================================================================
print("1️⃣ CARREGANDO DADOS (84k candles)")
print("-" * 140)

df = pd.read_csv('/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015_processed.csv')
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.sort_values('datetime').reset_index(drop=True)

print(f"✅ {len(df)} candles carregados")
print(f"   Período: {df['datetime'].min()} → {df['datetime'].max()}")
print()

# =====================================================================
# 2. CALCULAR INDICADORES
# =====================================================================
print("2️⃣ CALCULANDO INDICADORES MT5")
print("-" * 140)

# SMA
df['sma_20'] = df['close'].rolling(window=20, min_periods=1).mean()
df['sma_50'] = df['close'].rolling(window=50, min_periods=1).mean()
df['sma_200'] = df['close'].rolling(window=200, min_periods=1).mean()

# RSI
def calcular_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))

df['rsi_14'] = calcular_rsi(df['close'], 14)

# Bollinger Bands (20,2)
bb_middle = df['close'].rolling(20).mean()
bb_std = df['close'].rolling(20).std()
df['bb_upper'] = bb_middle + (bb_std * 2)
df['bb_lower'] = bb_middle - (bb_std * 2)
df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

# CCI (20 período)
def calcular_cci(high, low, close, period=20):
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
    cci = (tp - sma_tp) / (0.015 * mad)
    return cci

df['cci_20'] = calcular_cci(df['high'], df['low'], df['close'], 20)

print("✅ Indicadores calculados:")
print(f"   - SMA (20, 50, 200)")
print(f"   - RSI (14)")
print(f"   - Bollinger Bands (20,2)")
print(f"   - CCI (20)")
print()

# =====================================================================
# 3. CALCULAR POI FEATURES DIÁRIAS
# =====================================================================
print("3️⃣ CALCULANDO POI FEATURES")
print("-" * 140)

df['date'] = df['datetime'].dt.date
df['hora'] = df['datetime'].dt.hour
df['next_close'] = df['close'].shift(-1)
df['change_pct'] = ((df['next_close'] - df['close']) / df['close'] * 100)
df['ganho'] = (df['change_pct'] > 0).astype(int)

# Calcular POI
for col in ['daily_high', 'daily_low', 'dist_sup_pct', 'dist_res_pct', 'pos_in_range', 'range_pct']:
    df[col] = np.nan

dias = df['date'].unique()
for date in dias:
    mask_day = df['date'] == date
    if mask_day.sum() > 0:
        high_dia = df.loc[mask_day, 'high'].max()
        low_dia = df.loc[mask_day, 'low'].min()
        range_dia = high_dia - low_dia
        
        df.loc[mask_day, 'daily_high'] = high_dia
        df.loc[mask_day, 'daily_low'] = low_dia
        df.loc[mask_day, 'range_pct'] = (range_dia / df.loc[mask_day, 'close'].iloc[0]) * 100
        
        # Distância ao suporte (fundo)
        df.loc[mask_day, 'dist_sup_pct'] = ((df.loc[mask_day, 'close'] - low_dia) / df.loc[mask_day, 'close'] * 100)
        
        # Distância à resistência (topo)
        df.loc[mask_day, 'dist_res_pct'] = ((high_dia - df.loc[mask_day, 'close']) / df.loc[mask_day, 'close'] * 100)
        
        # Posição na range [0, 1]
        if range_dia > 0:
            df.loc[mask_day, 'pos_in_range'] = (df.loc[mask_day, 'close'] - low_dia) / range_dia
        else:
            df.loc[mask_day, 'pos_in_range'] = 0.5

df_clean = df.dropna(subset=['sma_200', 'rsi_14', 'cci_20']).reset_index(drop=True)

print(f"✅ POI features calculadas")
print(f"   Dataset final: {len(df_clean)} candles")
print()

# =====================================================================
# 4. DEFINIR ESTRATÉGIA POI+CONFIRMAÇÃO (MULTI-TIER)
# =====================================================================
print("=" * 140)
print("4️⃣ TESTANDO ESTRATÉGIA POI+CONFIRMAÇÃO")
print("=" * 140)
print()

estrategias = {}

# ===== ESTRATÉGIA 1: BASELINE (FAR BELOW) =====
print("📊 ESTRATÉGIA 1: BASELINE (FAR BELOW)")
print("-" * 140)

s1 = df_clean[
    df_clean['dist_sup_pct'] > 0.1
]

s1_ganhos = s1['ganho'].sum()
s1_trades = len(s1)
s1_wr = s1['ganho'].mean() * 100 if s1_trades > 0 else 0
s1_avg_ganho = s1[s1['ganho'] == 1]['change_pct'].mean() if s1_ganhos > 0 else 0
s1_avg_perda = s1[s1['ganho'] == 0]['change_pct'].mean() if (s1_trades - s1_ganhos) > 0 else 0
s1_pf = (s1_ganhos * s1_avg_ganho) / (abs((s1_trades - s1_ganhos) * s1_avg_perda) + 0.0001)
s1_expectancy = (s1_wr/100) * s1_avg_ganho + (1 - s1_wr/100) * s1_avg_perda

print(f"Critério: dist_sup_pct > 0.1%")
print(f"✅ Trades: {s1_trades} | WR: {s1_wr:.1f}% | PF: {s1_pf:.2f}x | Expectancy: {s1_expectancy:+.4f}%")
print()

estrategias['S1_BASELINE'] = {
    'trades': s1_trades,
    'wr': s1_wr,
    'pf': s1_pf,
    'expectancy': s1_expectancy,
    'criteria': 'FAR BELOW',
    'avg_ganho': s1_avg_ganho,
    'avg_perda': s1_avg_perda
}

# ===== ESTRATÉGIA 2: FAR BELOW + CONFIRMAÇÃO SMA =====
print("📊 ESTRATÉGIA 2: FAR BELOW + SMA200 + SMA TREND")
print("-" * 140)

s2 = df_clean[
    (df_clean['dist_sup_pct'] > 0.1) &
    (df_clean['close'] > df_clean['sma_200']) &
    (df_clean['sma_50'] > df_clean['sma_200'])
]

s2_ganhos = s2['ganho'].sum()
s2_trades = len(s2)
s2_wr = s2['ganho'].mean() * 100 if s2_trades > 0 else 0
s2_avg_ganho = s2[s2['ganho'] == 1]['change_pct'].mean() if s2_ganhos > 0 else 0
s2_avg_perda = s2[s2['ganho'] == 0]['change_pct'].mean() if (s2_trades - s2_ganhos) > 0 else 0
s2_pf = (s2_ganhos * s2_avg_ganho) / (abs((s2_trades - s2_ganhos) * s2_avg_perda) + 0.0001)
s2_expectancy = (s2_wr/100) * s2_avg_ganho + (1 - s2_wr/100) * s2_avg_perda

print(f"Critério: FAR BELOW + Close > SMA200 + SMA50 > SMA200")
print(f"✅ Trades: {s2_trades} | WR: {s2_wr:.1f}% | PF: {s2_pf:.2f}x | Expectancy: {s2_expectancy:+.4f}%")
print()

estrategias['S2_SMA'] = {
    'trades': s2_trades,
    'wr': s2_wr,
    'pf': s2_pf,
    'expectancy': s2_expectancy,
    'criteria': 'FAR BELOW + SMA',
    'avg_ganho': s2_avg_ganho,
    'avg_perda': s2_avg_perda
}

# ===== ESTRATÉGIA 3: FAR BELOW + SMA + RANGE MID =====
print("📊 ESTRATÉGIA 3: FAR BELOW + SMA + MID RANGE")
print("-" * 140)

s3 = df_clean[
    (df_clean['dist_sup_pct'] > 0.1) &
    (df_clean['close'] > df_clean['sma_200']) &
    (df_clean['sma_50'] > df_clean['sma_200']) &
    (df_clean['pos_in_range'] > 0.3) &
    (df_clean['pos_in_range'] < 0.7)
]

s3_ganhos = s3['ganho'].sum()
s3_trades = len(s3)
s3_wr = s3['ganho'].mean() * 100 if s3_trades > 0 else 0
s3_avg_ganho = s3[s3['ganho'] == 1]['change_pct'].mean() if s3_ganhos > 0 else 0
s3_avg_perda = s3[s3['ganho'] == 0]['change_pct'].mean() if (s3_trades - s3_ganhos) > 0 else 0
s3_pf = (s3_ganhos * s3_avg_ganho) / (abs((s3_trades - s3_ganhos) * s3_avg_perda) + 0.0001)
s3_expectancy = (s3_wr/100) * s3_avg_ganho + (1 - s3_wr/100) * s3_avg_perda

print(f"Critério: FAR BELOW + SMA + Posição (0.3-0.7)")
print(f"✅ Trades: {s3_trades} | WR: {s3_wr:.1f}% | PF: {s3_pf:.2f}x | Expectancy: {s3_expectancy:+.4f}%")
print()

estrategias['S3_RANGE'] = {
    'trades': s3_trades,
    'wr': s3_wr,
    'pf': s3_pf,
    'expectancy': s3_expectancy,
    'criteria': 'FAR BELOW + SMA + RANGE',
    'avg_ganho': s3_avg_ganho,
    'avg_perda': s3_avg_perda
}

# ===== ESTRATÉGIA 4: FAR BELOW + SMA + HORÁRIO OTIMIZADO =====
print("📊 ESTRATÉGIA 4: FAR BELOW + SMA + HORÁRIO ÓTIMO (16-18h UTC)")
print("-" * 140)

melhores_horas = [16, 17, 18]

s4 = df_clean[
    (df_clean['dist_sup_pct'] > 0.1) &
    (df_clean['close'] > df_clean['sma_200']) &
    (df_clean['sma_50'] > df_clean['sma_200']) &
    (df_clean['pos_in_range'] > 0.3) &
    (df_clean['pos_in_range'] < 0.7) &
    (df_clean['hora'].isin(melhores_horas))
]

s4_ganhos = s4['ganho'].sum()
s4_trades = len(s4)
s4_wr = s4['ganho'].mean() * 100 if s4_trades > 0 else 0
s4_avg_ganho = s4[s4['ganho'] == 1]['change_pct'].mean() if s4_ganhos > 0 else 0
s4_avg_perda = s4[s4['ganho'] == 0]['change_pct'].mean() if (s4_trades - s4_ganhos) > 0 else 0
s4_pf = (s4_ganhos * s4_avg_ganho) / (abs((s4_trades - s4_ganhos) * s4_avg_perda) + 0.0001)
s4_expectancy = (s4_wr/100) * s4_avg_ganho + (1 - s4_wr/100) * s4_avg_perda

print(f"Critério: FAR BELOW + SMA + RANGE + Horário (16-18 UTC)")
print(f"✅ Trades: {s4_trades} | WR: {s4_wr:.1f}% | PF: {s4_pf:.2f}x | Expectancy: {s4_expectancy:+.4f}%")
print()

estrategias['S4_HORARIO'] = {
    'trades': s4_trades,
    'wr': s4_wr,
    'pf': s4_pf,
    'expectancy': s4_expectancy,
    'criteria': 'FAR BELOW + SMA + RANGE + HORÁRIO',
    'avg_ganho': s4_avg_ganho,
    'avg_perda': s4_avg_perda
}

# ===== ESTRATÉGIA 5: ULTRA - Tudo + CCI Filtro =====
print("📊 ESTRATÉGIA 5: ULTRA (+ CCI Confirmação)")
print("-" * 140)

s5 = df_clean[
    (df_clean['dist_sup_pct'] > 0.1) &
    (df_clean['close'] > df_clean['sma_200']) &
    (df_clean['sma_50'] > df_clean['sma_200']) &
    (df_clean['pos_in_range'] > 0.3) &
    (df_clean['pos_in_range'] < 0.7) &
    (df_clean['hora'].isin(melhores_horas)) &
    (df_clean['rsi_14'] > 30) &
    (df_clean['rsi_14'] < 70)
]

s5_ganhos = s5['ganho'].sum()
s5_trades = len(s5)
s5_wr = s5['ganho'].mean() * 100 if s5_trades > 0 else 0
s5_avg_ganho = s5[s5['ganho'] == 1]['change_pct'].mean() if s5_ganhos > 0 else 0
s5_avg_perda = s5[s5['ganho'] == 0]['change_pct'].mean() if (s5_trades - s5_ganhos) > 0 else 0
s5_pf = (s5_ganhos * s5_avg_ganho) / (abs((s5_trades - s5_ganhos) * s5_avg_perda) + 0.0001)
s5_expectancy = (s5_wr/100) * s5_avg_ganho + (1 - s5_wr/100) * s5_avg_perda

print(f"Critério: TUDO + RSI (30-70)")
print(f"✅ Trades: {s5_trades} | WR: {s5_wr:.1f}% | PF: {s5_pf:.2f}x | Expectancy: {s5_expectancy:+.4f}%")
print()

estrategias['S5_ULTRA'] = {
    'trades': s5_trades,
    'wr': s5_wr,
    'pf': s5_pf,
    'expectancy': s5_expectancy,
    'criteria': 'POI + SMA + RANGE + HORÁRIO + RSI',
    'avg_ganho': s5_avg_ganho,
    'avg_perda': s5_avg_perda
}

# =====================================================================
# 5. RESUMO E RECOMENDAÇÃO
# =====================================================================
print("=" * 140)
print("5️⃣ RESUMO DE ESTRATÉGIAS")
print("=" * 140)
print()

df_summary = pd.DataFrame(estrategias).T.reset_index()
df_summary = df_summary.rename(columns={'index': 'estrategia'})
df_summary = df_summary.sort_values('expectancy', ascending=False)

print(f"{'Estratégia':<25} {'Trades':>10} {'WR%':>10} {'PF':>10} {'Expectancy':>15} {'Recomendação':<30}")
print("-" * 100)

for idx, row in df_summary.iterrows():
    rec = ""
    if row['wr'] >= 55:
        rec = "🚀 EXCELENTE"
    elif row['wr'] >= 52:
        rec = "✅ BOM"
    elif row['wr'] >= 50:
        rec = "✅ ACEITÁVEL"
    elif row['wr'] >= 48:
        rec = "⚠️ MARGINAL"
    else:
        rec = "❌ RUIM"
    
    print(f"{row['estrategia']:<25} {row['trades']:>10.0f} {row['wr']:>9.1f}% {row['pf']:>9.2f}x {row['expectancy']:>14.4f}% {rec:<30}")

print()

# =====================================================================
# 6. SALVAR RESULTADOS
# =====================================================================
print("=" * 140)
print("6️⃣ SALVANDO RESULTADOS")
print("=" * 140)
print()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f'/home/ubuntu/pessoal/options/backtest_results/estrategias_completas_{timestamp}.csv'

df_summary.to_csv(output_file, index=False)

print(f"✅ Arquivo salvo: {output_file}")
print()
print(df_summary.to_string(index=False))
print()

print("=" * 140)
print("✨ ANÁLISE CONCLUÍDA")
print("=" * 140)
