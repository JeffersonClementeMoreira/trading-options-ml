#!/usr/bin/env python3
"""
POI/SMC + Indicadores MT5 (Do arquivo existente)
Objetivo: Melhorar de 76.6% para 80%+ WR com análise de risco

Usa os indicadores que já estão no backtest_multi_horario_poi:
- SMA20, SMA50, SMA200
- Distâncias (dist_res_pct, dist_sup_pct)
- Rejeições (rejection_res, rejection_sup, rejection_type)
- Posição na range (pos_in_range)
- Força do POI (poi_strength)
- Posição vs tendência (pos_vs_trend)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 120)
print("🎯 POI/SMC + INDICADORES MT5 - ESTRATÉGIAS MULTI-NÍVEL")
print("=" * 120)
print()

# =====================================================================
# 1. CARREGAR DADOS POI COM INDICADORES
# =====================================================================
print("1️⃣ CARREGANDO DADOS POI COM INDICADORES MT5")
print("-" * 120)

df = pd.read_csv('/home/ubuntu/pessoal/options/backtest_results/backtest_multi_horario_poi_20260526_024357.csv')

print(f"✅ Carregados {len(df)} análises")
print(f"   Colunas disponíveis: {len(df.columns)}")
print(f"   Indicadores: SMA20, SMA50, SMA200, Rejeição, Posição")
print()

print("Colunas disponíveis:")
for col in df.columns:
    print(f"   - {col}")
print()

# =====================================================================
# 2. CONVERTER RESULT PARA GANHO/PERDA
# =====================================================================
print("2️⃣ PREPARANDO DADOS")
print("-" * 120)

# Usar change_pct para determinar ganho/perda (não o campo result que pode estar truncado)
df['change_pct'] = pd.to_numeric(df['change_pct'], errors='coerce')
df['ganho'] = (df['change_pct'] > 0).astype(int)

# Contabilizar
ganhos = df['ganho'].sum()
perdas = len(df) - ganhos

print(f"✅ {ganhos} ganhos de {len(df)} total ({ganhos/len(df)*100:.1f}%)")
print(f"   Média de ganho: {df[df['ganho']==1]['change_pct'].mean():.5f}%")
print(f"   Média de perda: {df[df['ganho']==0]['change_pct'].mean():.5f}%")
print()

# =====================================================================
# 3. EXPLORAR OS INDICADORES
# =====================================================================
print("3️⃣ ANÁLISE EXPLORATÓRIA DOS INDICADORES")
print("-" * 120)

print("\nDistância do Resistência (dist_res_pct):")
print(f"  Min: {df['dist_res_pct'].min():.4f}%")
print(f"  Max: {df['dist_res_pct'].max():.4f}%")
print(f"  Mean: {df['dist_res_pct'].mean():.4f}%")

print("\nDistância do Suporte (dist_sup_pct):")
print(f"  Min: {df['dist_sup_pct'].min():.4f}%")
print(f"  Max: {df['dist_sup_pct'].max():.4f}%")
print(f"  Mean: {df['dist_sup_pct'].mean():.4f}%")

print("\nPosição na Range (pos_in_range):")
print(f"  Min: {df['pos_in_range'].min():.4f}")
print(f"  Max: {df['pos_in_range'].max():.4f}")

print("\nTipo de Rejeição:")
print(df['rejection_type'].value_counts())

print("\nHorário de Análise:")
print(df['analysis_hour'].value_counts().sort_index())

print()

# =====================================================================
# 4. DEFINIR ESTRATÉGIAS COM MÚLTIPLOS NÍVEIS
# =====================================================================
print("=" * 120)
print("4️⃣ DEFININDO 5 ESTRATÉGIAS COM CONFIRMAÇÃO")
print("=" * 120)
print()

estrategias = {}

# =====================================================================
# ESTRATÉGIA 1: BASELINE (Apenas POI - Original)
# =====================================================================
print("📊 ESTRATÉGIA 1: BASELINE POI FAR BELOW (Original - 76.6%)")
print("-" * 120)

# Critério ESPECÍFICO: FAR BELOW DO POI (perto do fundo = positivo)
# dist_sup_pct > 0.1% = preço está longe do suporte (fundo)
s1 = df[
    df['dist_sup_pct'] > 0.1
]

s1_wr = s1['ganho'].mean() * 100 if len(s1) > 0 else 0
s1_trades = len(s1)

estrategias['BASELINE'] = {
    'df': s1,
    'name': 'BASELINE: FAR BELOW POI',
    'criterios': 'dist_sup > 0.1 (longe do fundo)',
    'wr': s1_wr,
    'trades': s1_trades
}

print(f"Critério: FAR BELOW POI (dist_sup > 0.1%)")
print(f"✅ Win Rate: {s1_wr:.1f}%")
print(f"   Trades: {s1_trades}")
print()

# =====================================================================
# ESTRATÉGIA 2: POI + REJEIÇÃO
# =====================================================================
print("📊 ESTRATÉGIA 2: FAR BELOW + REJEIÇÃO BULLISH")
print("-" * 120)

# Critério: FAR BELOW + Rejeição BULLISH (confirmação)
s2 = df[
    (df['dist_sup_pct'] > 0.1) &
    (df['rejection_type'] == 'BULLISH_REJECTION')
]

s2_wr = s2['ganho'].mean() * 100 if len(s2) > 0 else 0
s2_trades = len(s2)

estrategias['POI+REJEICAO'] = {
    'df': s2,
    'name': 'FAR BELOW + BULLISH_REJECTION',
    'criterios': 'dist_sup > 0.1 + Rejeição bullish',
    'wr': s2_wr,
    'trades': s2_trades
}

print(f"Critério: FAR BELOW + Rejeição Bullish")
print(f"✅ Win Rate: {s2_wr:.1f}%")
print(f"   Trades: {s2_trades}")
print()

# =====================================================================
# ESTRATÉGIA 3: POI + REJEIÇÃO + MELHOR HORÁRIO
# =====================================================================
print("📊 ESTRATÉGIA 3: POI + REJEIÇÃO + MELHOR HORÁRIO")
print("-" * 120)

# Melhores horários (17:00, 16:00, 14:00 em UTC)
melhores_horas = [14, 16, 17]

s3 = df[
    ((abs(df['dist_res_pct']) > 0.1) | (abs(df['dist_sup_pct']) > 0.1)) &
    (df['rejection_type'] != 'NO_REJECTION') &
    (df['analysis_hour'].isin(melhores_horas))
]

s3_wr = s3['ganho'].mean() * 100 if len(s3) > 0 else 0
s3_trades = len(s3)

estrategias['POI+REJEICAO+HORA'] = {
    'df': s3,
    'name': 'POI + REJEIÇÃO + HORA',
    'criterios': 'FAR + Rejeição + Horário ótimo',
    'wr': s3_wr,
    'trades': s3_trades
}

print(f"Critério: FAR + Rejeição + Horário (14:00, 16:00, 17:00 UTC)")
print(f"✅ Win Rate: {s3_wr:.1f}%")
print(f"   Trades: {s3_trades}")
print()

# =====================================================================
# ESTRATÉGIA 4: POI + REJEIÇÃO + POSIÇÃO NA RANGE
# =====================================================================
print("📊 ESTRATÉGIA 4: POI + REJEIÇÃO + POSIÇÃO NA RANGE")
print("-" * 120)

# Entrada em zonas específicas da range (evitar extremos muito radicais)
# pos_in_range 0.3-0.7 = zona média (menos risco de reversão extrema)

s4 = df[
    ((abs(df['dist_res_pct']) > 0.1) | (abs(df['dist_sup_pct']) > 0.1)) &
    (df['rejection_type'] != 'NO_REJECTION') &
    (df['pos_in_range'] > 0.2) & (df['pos_in_range'] < 0.8)  # Evitar extremos
]

s4_wr = s4['ganho'].mean() * 100 if len(s4) > 0 else 0
s4_trades = len(s4)

estrategias['POI+REJEICAO+RANGE'] = {
    'df': s4,
    'name': 'POI + REJEIÇÃO + RANGE',
    'criterios': 'FAR + Rejeição + Posição (0.2-0.8)',
    'wr': s4_wr,
    'trades': s4_trades
}

print(f"Critério: FAR + Rejeição + Posição na range (0.2-0.8)")
print(f"✅ Win Rate: {s4_wr:.1f}%")
print(f"   Trades: {s4_trades}")
print()

# =====================================================================
# ESTRATÉGIA 5: ULTRA (Tudo combinado - Máximo filtro)
# =====================================================================
print("📊 ESTRATÉGIA 5: ULTRA (Máxima Confirmação)")
print("-" * 120)

# FAR + Rejeição + Horário + Posição range + Força POI
s5 = df[
    ((abs(df['dist_res_pct']) > 0.1) | (abs(df['dist_sup_pct']) > 0.1)) &
    (df['rejection_type'] != 'NO_REJECTION') &
    (df['analysis_hour'].isin(melhores_horas)) &
    (df['pos_in_range'] > 0.2) & (df['pos_in_range'] < 0.8) &
    (df['poi_strength'] > df['poi_strength'].quantile(0.5))  # Force do POI acima da mediana
]

s5_wr = s5['ganho'].mean() * 100 if len(s5) > 0 else 0
s5_trades = len(s5)

estrategias['ULTRA'] = {
    'df': s5,
    'name': 'ULTRA: Máxima Confirmação',
    'criterios': 'FAR + Rejeição + Hora + Range + Força',
    'wr': s5_wr,
    'trades': s5_trades
}

print(f"Critério: FAR + Rejeição + Hora ótima + Range + Força POI")
print(f"✅ Win Rate: {s5_wr:.1f}%")
print(f"   Trades: {s5_trades}")
print()

# =====================================================================
# 5. CALCULAR MÉTRICAS DE RISCO
# =====================================================================
print("=" * 120)
print("5️⃣ ANÁLISE DE RISCO PARA CADA ESTRATÉGIA")
print("=" * 120)
print()

def calcular_metricas_completas(est_df, name):
    """Calcula métricas de risco/retorno"""
    
    if len(est_df) < 2:
        return None
    
    # Win rate
    wr = est_df['ganho'].mean() * 100
    ganhos = est_df['ganho'].sum()
    perdas = len(est_df) - ganhos
    
    # Lucro/perda média
    avg_ganho = est_df[est_df['ganho'] == 1]['change_pct'].mean()
    avg_perda = est_df[est_df['ganho'] == 0]['change_pct'].mean()
    
    # Profit factor
    total_ganho = est_df[est_df['ganho'] == 1]['change_pct'].sum()
    total_perda = abs(est_df[est_df['ganho'] == 0]['change_pct'].sum())
    pf = total_ganho / (total_perda + 1e-9)
    
    # Drawdown
    cum_pnl = est_df['change_pct'].cumsum()
    running_max = cum_pnl.expanding().max()
    dd = (cum_pnl - running_max) / abs(running_max).replace(0, 1e-9) * 100
    max_dd = dd.min()
    
    # Sharpe
    ret_medio = est_df['change_pct'].mean()
    desvio = est_df['change_pct'].std()
    sharpe = (ret_medio / desvio) * np.sqrt(252) if desvio > 0 else 0
    
    # Expectativa
    expectativa = (wr/100) * avg_ganho + ((1-wr/100) * avg_perda)
    
    # Índice de confiança (WR vs trades)
    confianca = wr / 100 if len(est_df) > 100 else wr / 100 * 0.5  # Reduz confiança com poucos trades
    
    return {
        'name': name,
        'trades': len(est_df),
        'ganhos': ganhos,
        'perdas': perdas,
        'wr': wr,
        'avg_ganho': avg_ganho,
        'avg_perda': avg_perda,
        'pf': pf,
        'max_dd': max_dd,
        'sharpe': sharpe,
        'expectativa': expectativa,
        'confianca': confianca
    }

resultados = []
for key, est in estrategias.items():
    met = calcular_metricas_completas(est['df'], est['name'])
    if met:
        resultados.append(met)

# Mostrar tabela
print("COMPARAÇÃO DE ESTRATÉGIAS:")
print("=" * 160)
print(f"{'Estratégia':<25} {'Trades':>10} {'Ganhos':>8} {'Perdas':>8} {'WR%':>8} {'Avg Win':>10} {'Avg Loss':>10} {'PF':>8} {'MaxDD%':>10} {'Sharpe':>10} {'Expect':>10}")
print("-" * 160)

for met in sorted(resultados, key=lambda x: x['wr'], reverse=True):
    print(f"{met['name']:<25} {met['trades']:>10d} {met['ganhos']:>8d} {met['perdas']:>8d} {met['wr']:>7.1f}% {met['avg_ganho']:>9.5f}% {met['avg_perda']:>9.5f}% {met['pf']:>7.2f} {met['max_dd']:>9.1f}% {met['sharpe']:>9.2f} {met['expectativa']:>9.5f}%")

print("=" * 160)
print()

# =====================================================================
# 6. RECOMENDAÇÃO
# =====================================================================
print("=" * 120)
print("6️⃣ RECOMENDAÇÃO ESTRATÉGICA E ANÁLISE DE RISCO")
print("=" * 120)
print()

# Melhor por Sharpe ratio (risco/retorno)
melhor_sharpe = sorted(resultados, key=lambda x: x['sharpe'], reverse=True)[0]
melhor_wr = sorted(resultados, key=lambda x: x['wr'], reverse=True)[0]

print(f"🏆 MELHOR ESTRATÉGIA (por Sharpe Ratio): {melhor_sharpe['name']}")
print(f"   Win Rate: {melhor_sharpe['wr']:.1f}%")
print(f"   Sharpe: {melhor_sharpe['sharpe']:.3f}")
print()

print(f"📈 MAIOR WIN RATE: {melhor_wr['name']}")
print(f"   Win Rate: {melhor_wr['wr']:.1f}%")
print(f"   Trades: {melhor_wr['trades']}")
print()

print("ANÁLISE:")
print("-" * 120)

for met in sorted(resultados, key=lambda x: x['wr'], reverse=True):
    print()
    print(f"📊 {met['name']}")
    print(f"   Trades: {met['trades']} | WR: {met['wr']:.1f}% | PF: {met['pf']:.2f}x | MaxDD: {met['max_dd']:.1f}%")
    
    # Análise de WR
    if met['wr'] >= 80:
        print(f"   ✅ WR EXCELENTE (80%+) - PRONTO PARA PRODUÇÃO")
    elif met['wr'] >= 76.6:
        melhoria = met['wr'] - 76.6
        print(f"   ✅ WR BOM (+{melhoria:.1f}pp vs baseline 76.6%)")
    elif met['wr'] >= 70:
        print(f"   ⚠️ WR ACEITÁVEL (70%+) - Precisa validação")
    else:
        print(f"   ❌ WR BAIXO (<70%) - Não recomendado")
    
    # Análise de risco
    if met['max_dd'] > -5:
        print(f"   🟢 DRAWDOWN BAIXO ({met['max_dd']:.1f}%) = SEGURO")
    elif met['max_dd'] > -20:
        print(f"   🟡 DRAWDOWN MÉDIO ({met['max_dd']:.1f}%) = ACEITÁVEL")
    else:
        print(f"   🔴 DRAWDOWN ALTO ({met['max_dd']:.1f}%) = ARRISCADO")
    
    # Análise de profit factor
    if met['pf'] > 1.5:
        print(f"   🟢 PROFIT FACTOR ALTO ({met['pf']:.2f}x)")
    elif met['pf'] > 1.0:
        print(f"   🟡 PROFIT FACTOR OK ({met['pf']:.2f}x)")
    else:
        print(f"   🔴 PROFIT FACTOR BAIXO ({met['pf']:.2f}x)")
    
    # Recomendação
    if met['wr'] >= 80 and met['pf'] > 1.3 and met['max_dd'] > -10:
        print(f"   🚀 RECOMENDAÇÃO: IMPLEMENTAR EM PRODUÇÃO")
    elif met['wr'] >= 76.6 and met['pf'] > 1.0:
        print(f"   ✅ RECOMENDAÇÃO: Validar e depois produção")
    else:
        print(f"   ⚠️ RECOMENDAÇÃO: Continuar testando")

print()

# =====================================================================
# 7. SALVAR RESULTADOS
# =====================================================================
print("=" * 120)
print("7️⃣ SALVANDO RESULTADOS")
print("=" * 120)
print()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Salvar resumo de estratégias
output_file = f'/home/ubuntu/pessoal/options/backtest_results/estrategias_poi_mt5_{timestamp}.csv'
df_resultado = pd.DataFrame(resultados).sort_values('wr', ascending=False)
df_resultado.to_csv(output_file, index=False)

print(f"✅ Arquivo de estratégias: {output_file}")
print()

# Salvar trades da melhor estratégia
melhor = estrategias[list(estrategias.keys())[0]]
for key, est in estrategias.items():
    met = calcular_metricas_completas(est['df'], est['name'])
    if met and met['wr'] >= 76.6:  # Usar primeira que atinge baseline
        melhor = est
        break

output_trades = f'/home/ubuntu/pessoal/options/backtest_results/trades_melhor_estrategia_{timestamp}.csv'
melhor_df = melhor['df'][[
    'analysis_time', 'close', 'high_day', 'low_day',
    'dist_res_pct', 'dist_sup_pct', 'near_res', 'near_sup',
    'pos_in_range', 'poi_strength', 'rejection_type',
    'change_pct', 'result', 'analysis_hour'
]].copy()
melhor_df['estrategia'] = melhor['name']
melhor_df.to_csv(output_trades, index=False)

print(f"✅ Arquivo de trades: {output_trades}")
print()

# Mostrar resumo final
print("=" * 120)
print("📊 RESUMO FINAL")
print("=" * 120)
print()
print(df_resultado.to_string(index=False))
print()

print("=" * 120)
print("✨ ANÁLISE CONCLUÍDA")
print("=" * 120)
