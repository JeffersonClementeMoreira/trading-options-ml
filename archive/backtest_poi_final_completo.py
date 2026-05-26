#!/usr/bin/env python3
"""
POI/SMC + Indicadores MT5 - VERSÃO DATASET COMPLETO
Objetivo: Usar dados completos (84k candles) para recuperar 76.6% WR e melhorar para 80%+

Estratégia:
1. Carregar 84k candles EURUSD
2. Calcular POI para cada dia
3. Calcular indicadores MT5 (SMA, etc)
4. Testar 5 estratégias com confirmação
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 120)
print("🎯 POI/SMC + INDICADORES MT5 - DATASET COMPLETO (84k candles)")
print("=" * 120)
print()

# =====================================================================
# 1. CARREGAR DADOS COMPLETOS
# =====================================================================
print("1️⃣ CARREGANDO DATASET COMPLETO")
print("-" * 120)

df = pd.read_csv('/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015_processed.csv')
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.sort_values('datetime').reset_index(drop=True)

print(f"✅ Carregados {len(df)} candles")
print(f"   Período: {df['datetime'].min()} → {df['datetime'].max()}")
print()

# =====================================================================
# 2. CALCULAR INDICADORES
# =====================================================================
print("2️⃣ CALCULANDO INDICADORES MT5")
print("-" * 120)

def calcular_sma(df, col, window):
    return df[col].rolling(window=window, min_periods=1).mean()

# SMA
df['sma_20'] = calcular_sma(df, 'close', 20)
df['sma_50'] = calcular_sma(df, 'close', 50)
df['sma_200'] = calcular_sma(df, 'close', 200)

print("✅ Indicadores MT5 calculados (SMA20, SMA50, SMA200)")
print()

# =====================================================================
# 3. CALCULAR POI PARA CADA DIA
# =====================================================================
print("3️⃣ CALCULANDO POI FEATURES")
print("-" * 120)

df['date'] = df['datetime'].dt.date
df['hora'] = df['datetime'].dt.hour
df['next_close'] = df['close'].shift(-1)
df['change_pct'] = ((df['next_close'] - df['close']) / df['close'] * 100)
df['ganho'] = (df['change_pct'] > 0).astype(int)

dias = df['date'].unique()

print(f"Processando {len(dias)} dias...")

# Adicionar POI features
for col in ['dist_res_pct', 'dist_sup_pct', 'near_res', 'near_sup', 'pos_in_range', 'poi_strength']:
    df[col] = np.nan

for date in dias:
    df_day = df[df['date'] == date]
    if len(df_day) > 1:
        high_dia = df_day['high'].max()
        low_dia = df_day['low'].min()
        
        # Calcular para cada candle do dia
        dist_res = (high_dia - df_day['close']) / df_day['close'] * 100
        dist_sup = (df_day['close'] - low_dia) / df_day['close'] * 100
        
        range_dia = high_dia - low_dia
        pos_range = (df_day['close'] - low_dia) / range_dia if range_dia > 0 else 0.5
        
        poi_force = min(range_dia / (df_day['close'].max() * 0.005), 1.0)
        
        # Preencher no dataframe
        df.loc[df_day.index, 'dist_res_pct'] = dist_res.values
        df.loc[df_day.index, 'dist_sup_pct'] = dist_sup.values
        df.loc[df_day.index, 'near_res'] = (abs(dist_res) < 0.05).astype(int).values
        df.loc[df_day.index, 'near_sup'] = (abs(dist_sup) < 0.05).astype(int).values
        df.loc[df_day.index, 'pos_in_range'] = pos_range.values
        df.loc[df_day.index, 'poi_strength'] = poi_force

df_clean = df.dropna().reset_index(drop=True)

print(f"✅ POI features calculadas para {len(dias)} dias")
print(f"   Dataset final: {len(df_clean)} candles com dados completos")
print()

# =====================================================================
# 4. DEFINIR ESTRATÉGIAS
# =====================================================================
print("=" * 120)
print("4️⃣ TESTANDO 5 ESTRATÉGIAS")
print("=" * 120)
print()

# ESTRATÉGIA 1: BASELINE (FAR BELOW - recuperar 76.6%)
print("📊 ESTRATÉGIA 1: BASELINE (FAR BELOW POI)")
print("-" * 120)

s1 = df_clean[df_clean['dist_sup_pct'] > 0.1]
s1_wr = s1['ganho'].mean() * 100 if len(s1) > 0 else 0

print(f"Critério: dist_sup_pct > 0.1%")
print(f"✅ Win Rate: {s1_wr:.1f}%")
print(f"   Trades: {len(s1)}")
print()

# ESTRATÉGIA 2: FAR BELOW + Acima da SMA200
print("📊 ESTRATÉGIA 2: FAR BELOW + Acima SMA200")
print("-" * 120)

s2 = df_clean[
    (df_clean['dist_sup_pct'] > 0.1) &
    (df_clean['close'] > df_clean['sma_200'])
]
s2_wr = s2['ganho'].mean() * 100 if len(s2) > 0 else 0

print(f"Critério: FAR BELOW + Close > SMA200")
print(f"✅ Win Rate: {s2_wr:.1f}%")
print(f"   Trades: {len(s2)}")
print()

# ESTRATÉGIA 3: FAR BELOW + SMA50 > SMA200 (tendência de alta)
print("📊 ESTRATÉGIA 3: FAR BELOW + Tendência (SMA50 > SMA200)")
print("-" * 120)

s3 = df_clean[
    (df_clean['dist_sup_pct'] > 0.1) &
    (df_clean['sma_50'] > df_clean['sma_200'])
]
s3_wr = s3['ganho'].mean() * 100 if len(s3) > 0 else 0

print(f"Critério: FAR BELOW + SMA50 > SMA200")
print(f"✅ Win Rate: {s3_wr:.1f}%")
print(f"   Trades: {len(s3)}")
print()

# ESTRATÉGIA 4: FAR BELOW + Posição na range (0.2-0.8)
print("📊 ESTRATÉGIA 4: FAR BELOW + Posição Range (0.2-0.8)")
print("-" * 120)

s4 = df_clean[
    (df_clean['dist_sup_pct'] > 0.1) &
    (df_clean['pos_in_range'] > 0.2) &
    (df_clean['pos_in_range'] < 0.8)
]
s4_wr = s4['ganho'].mean() * 100 if len(s4) > 0 else 0

print(f"Critério: FAR BELOW + Posição (0.2-0.8)")
print(f"✅ Win Rate: {s4_wr:.1f}%")
print(f"   Trades: {len(s4)}")
print()

# ESTRATÉGIA 5: ULTRA (Tudo + Melhores horários)
print("📊 ESTRATÉGIA 5: ULTRA (Máxima Confirmação)")
print("-" * 120)

melhores_horas = [14, 16, 17, 18]

s5 = df_clean[
    (df_clean['dist_sup_pct'] > 0.1) &
    (df_clean['sma_50'] > df_clean['sma_200']) &
    (df_clean['pos_in_range'] > 0.2) &
    (df_clean['pos_in_range'] < 0.8) &
    (df_clean['hora'].isin(melhores_horas))
]
s5_wr = s5['ganho'].mean() * 100 if len(s5) > 0 else 0

print(f"Critério: FAR BELOW + Tendência + Range + Horário")
print(f"✅ Win Rate: {s5_wr:.1f}%")
print(f"   Trades: {len(s5)}")
print()

# =====================================================================
# 5. COMPARAR E RECOMENDAR
# =====================================================================
print("=" * 120)
print("5️⃣ RESUMO E RECOMENDAÇÃO")
print("=" * 120)
print()

estrategias_result = [
    {'name': 'BASELINE (FAR BELOW)', 'trades': len(s1), 'wr': s1_wr},
    {'name': 'FAR BELOW + SMA200', 'trades': len(s2), 'wr': s2_wr},
    {'name': 'FAR BELOW + TEND', 'trades': len(s3), 'wr': s3_wr},
    {'name': 'FAR BELOW + RANGE', 'trades': len(s4), 'wr': s4_wr},
    {'name': 'ULTRA', 'trades': len(s5), 'wr': s5_wr},
]

df_resultado = pd.DataFrame(estrategias_result).sort_values('wr', ascending=False)

print(f"{'Estratégia':<30} {'Trades':>10} {'WR%':>10} {'Status':>20}")
print("-" * 70)

for idx, row in df_resultado.iterrows():
    status = ""
    if row['wr'] >= 80:
        status = "🚀 EXCELENTE"
    elif row['wr'] >= 76.6:
        status = "✅ ALCANÇADO"
    elif row['wr'] >= 75:
        status = "✅ BOM"
    elif row['wr'] >= 70:
        status = "⚠️ MARGINAL"
    else:
        status = "❌ RUIM"
    
    print(f"{row['name']:<30} {row['trades']:>10d} {row['wr']:>9.1f}% {status:>20}")

print()

# Análise
melhor = df_resultado.iloc[0]
print(f"🏆 MELHOR ESTRATÉGIA: {melhor['name']}")
print(f"   Win Rate: {melhor['wr']:.1f}%")
print(f"   Trades: {melhor['trades']}")
print()

if melhor['wr'] >= 80:
    print("🚀 OBJETIVO ALCANÇADO!")
    melhoria = melhor['wr'] - 76.6
    print(f"   Melhoria: +{melhoria:.1f}pp em relação aos 76.6% anteriores")
elif melhor['wr'] >= 76.6:
    print("✅ BASELINE RECUPERADO")
elif melhor['wr'] >= 75:
    print("⚠️ Próximo ao baseline")
else:
    print("❌ Abaixo do esperado - continuar testando variações")

print()

# =====================================================================
# 6. SALVAR RESULTADOS
# =====================================================================
print("=" * 120)
print("6️⃣ SALVANDO RESULTADOS")
print("=" * 120)
print()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f'/home/ubuntu/pessoal/options/backtest_results/ESTRATEGIAS_FINAL_{timestamp}.csv'

df_resultado.to_csv(output_file, index=False)

print(f"✅ Arquivo salvo: {output_file}")
print()
print(df_resultado.to_string(index=False))
print()

print("=" * 120)
print("✨ ANÁLISE CONCLUÍDA")
print("=" * 120)
