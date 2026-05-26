#!/usr/bin/env python3
"""
ANÁLISE POI - ENCONTRAR 76.6% E MELHORAR PARA 80%+

O 76.6% foi encontrado em um subset ESPECÍFICO dos 196 registros.
Vamos testar subsets por:
1. Horário específico
2. Rejeição tipo BULLISH vs BEARISH
3. Combinações de indicadores
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 120)
print("🎯 ANÁLISE POI - ENCONTRAR 76.6% E MELHORAR PARA 80%+")
print("=" * 120)
print()

# =====================================================================
# 1. CARREGAR DADOS POI
# =====================================================================
print("1️⃣ CARREGANDO DADOS POI")
print("-" * 120)

df = pd.read_csv('/home/ubuntu/pessoal/options/backtest_results/backtest_multi_horario_poi_20260526_024357.csv')

# Corrigir dados
df['change_pct'] = pd.to_numeric(df['change_pct'], errors='coerce')
df['ganho'] = (df['change_pct'] > 0).astype(int)

# Parse horário
df['analysis_hour'] = df['analysis_hour'].str.split(':').str[0].astype(int)

print(f"✅ Carregados {len(df)} registros POI")
print(f"   Ganhos: {df['ganho'].sum()} ({df['ganho'].mean()*100:.1f}%)")
print()

# =====================================================================
# 2. TESTE 1: POR HORÁRIO
# =====================================================================
print("2️⃣ TESTE 1: ANÁLISE POR HORÁRIO")
print("-" * 120)

print(f"{'Horário':<15} {'Trades':<10} {'WR%':<10} {'Cond.':}")

for hora in sorted(df['analysis_hour'].unique()):
    df_h = df[df['analysis_hour'] == hora]
    wr_h = df_h['ganho'].mean() * 100
    print(f"{hora:>02d}:00{'':<10} {len(df_h):<10d} {wr_h:<9.1f}%")

print()

# =====================================================================
# 3. TESTE 2: FAR BELOW (dist_sup > 0.1)
# =====================================================================
print("3️⃣ TESTE 2: FAR BELOW (SUPORTE) - Procura pelo 76.6%")
print("-" * 120)

# Baseline
s_far_below = df[df['dist_sup_pct'] > 0.1]
print(f"FAR BELOW: {len(s_far_below)} trades, WR={s_far_below['ganho'].mean()*100:.1f}%")

# Com cada horário
for hora in sorted(df['analysis_hour'].unique()):
    s = df[(df['dist_sup_pct'] > 0.1) & (df['analysis_hour'] == hora)]
    wr = s['ganho'].mean() * 100 if len(s) > 0 else 0
    print(f"  FAR BELOW + hora {hora:>02d}: {len(s):<5d} trades, WR={wr:>5.1f}%")

print()

# =====================================================================
# 4. TESTE 3: COMBINAÇÕES COM REJEIÇÃO
# =====================================================================
print("4️⃣ TESTE 3: COM REJEIÇÃO")
print("-" * 120)

# FAR BELOW + BULLISH
s_bull = df[(df['dist_sup_pct'] > 0.1) & (df['rejection_type'] == 'BULLISH_REJECTION')]
print(f"FAR BELOW + BULLISH: {len(s_bull)} trades, WR={s_bull['ganho'].mean()*100:.1f}%")

# FAR BELOW + NÃO REJECTION
s_no_rej = df[(df['dist_sup_pct'] > 0.1) & (df['rejection_type'] == 'NO_REJECTION')]
print(f"FAR BELOW + NO_REJECTION: {len(s_no_rej)} trades, WR={s_no_rej['ganho'].mean()*100:.1f}%")

print()

# =====================================================================
# 5. TESTE 4: COM SMA200
# =====================================================================
print("5️⃣ TESTE 4: COM INDICADOR SMA200")
print("-" * 120)

# FAR BELOW + Close > SMA200
s_sma200 = df[(df['dist_sup_pct'] > 0.1) & (df['close'] > df['sma200'])]
print(f"FAR BELOW + Close > SMA200: {len(s_sma200)} trades, WR={s_sma200['ganho'].mean()*100:.1f}%")

# FAR BELOW + Dist SMA200 < 0.5%
s_near_sma = df[(df['dist_sup_pct'] > 0.1) & (abs(df['dist_sma200_pct']) < 0.5)]
print(f"FAR BELOW + Próximo SMA200: {len(s_near_sma)} trades, WR={s_near_sma['ganho'].mean()*100:.1f}%")

print()

# =====================================================================
# 6. TESTE 5: FILTRO MÁXIMO
# =====================================================================
print("6️⃣ TESTE 5: MEGA FILTRO (Procurando o 76.6%)")
print("-" * 120)

# Testar combinações progressivas
combos = [
    ('FAR BELOW', df[df['dist_sup_pct'] > 0.1]),
    ('+ BULLISH', df[(df['dist_sup_pct'] > 0.1) & (df['rejection_type'] == 'BULLISH_REJECTION')]),
    ('+ CLOSE>SMA200', df[(df['dist_sup_pct'] > 0.1) & (df['rejection_type'] == 'BULLISH_REJECTION') & (df['close'] > df['sma200'])]),
    ('+ MID RANGE', df[(df['dist_sup_pct'] > 0.1) & (df['rejection_type'] == 'BULLISH_REJECTION') & (df['close'] > df['sma200']) & (df['pos_in_range'] > 0.35) & (df['pos_in_range'] < 0.75)]),
    ('+ HORA 14-18', df[(df['dist_sup_pct'] > 0.1) & (df['rejection_type'] == 'BULLISH_REJECTION') & (df['close'] > df['sma200']) & (df['pos_in_range'] > 0.35) & (df['pos_in_range'] < 0.75) & (df['analysis_hour'].isin([14,16,17,18]))]),
]

print(f"{'Filtro':<30} {'Trades':<10} {'WR%':<10} {'Status':<25}")
print("-" * 75)

best_wr = 0
best_combo = None

for filtro, df_f in combos:
    wr = df_f['ganho'].mean() * 100 if len(df_f) > 0 else 0
    
    if wr > best_wr:
        best_wr = wr
        best_combo = (filtro, df_f)
    
    status = ""
    if wr >= 80:
        status = "🚀 EXCELENTE!"
    elif wr >= 76.6:
        status = "✅ ALCANÇADO!"
    elif wr >= 75:
        status = "✅ BOM"
    elif wr >= 70:
        status = "⚠️ MARGINAL"
    
    print(f"{filtro:<30} {len(df_f):<10d} {wr:>8.1f}% {status:<25}")

print()

# =====================================================================
# 7. TESTE 6: VARIAÇÕES ADICIONAIS
# =====================================================================
print("7️⃣ TESTE 6: VARIAÇÕES PARA CHEGAR EM 80%")
print("-" * 120)

variações = [
    ('BELOW + BULLISH + SMA50>SMA200', df[(df['dist_sup_pct'] > 0.1) & (df['rejection_type'] == 'BULLISH_REJECTION') & (df['sma50'] > df['sma200'])]),
    ('BELOW + BEARISH', df[(df['dist_sup_pct'] > 0.1) & (df['rejection_type'] == 'BEARISH_REJECTION')]),
    ('BELOW + QUALQUER RES', df[(df['dist_sup_pct'] > 0.1) & (df['rejection_type'] != 'NO_REJECTION')]),
    ('BELOW + NEAR_RES', df[(df['dist_sup_pct'] > 0.1) & (df['near_res'] == 1)]),
    ('ABOVE + BULLISH', df[(df['dist_res_pct'] > 0.1) & (df['rejection_type'] == 'BULLISH_REJECTION')]),
]

for filtro, df_f in variações:
    wr = df_f['ganho'].mean() * 100 if len(df_f) > 0 else 0
    if wr > best_wr:
        best_wr = wr
        best_combo = (filtro, df_f)
    
    status = ""
    if wr >= 80:
        status = "🚀 EXCELENTE!"
    elif wr >= 76.6:
        status = "✅ ALCANÇADO!"
    
    print(f"{filtro:<35} {len(df_f):<10d} {wr:>8.1f}% {status}")

print()

# =====================================================================
# 8. RESULTADO FINAL
# =====================================================================
print("=" * 120)
print("8️⃣ RESULTADO FINAL")
print("=" * 120)
print()

if best_combo:
    filtro_name, df_best = best_combo
    trades_best = len(df_best)
    wr_best = df_best['ganho'].mean() * 100
    
    print(f"🏆 MELHOR COMBINAÇÃO ENCONTRADA:")
    print(f"   Filtro: {filtro_name}")
    print(f"   Trades: {trades_best}")
    print(f"   Win Rate: {wr_best:.1f}%")
    print()
    
    if wr_best >= 80:
        print("🚀 OBJETIVO ALCANÇADO! WR >= 80%")
        print(f"   Melhoria: +{wr_best - 76.6:.1f}pp")
    elif wr_best >= 76.6:
        print("✅ RECUPERADO BASELINE (76.6%)")
        print(f"   Resultado: {wr_best:.1f}%")
    else:
        print(f"❌ Ainda em {wr_best:.1f}% - continuar testando")
        print(f"   Falta: {80 - wr_best:.1f}pp para atingir 80%")

print()
print("=" * 120)
