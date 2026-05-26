#!/usr/bin/env python3
"""
POI/SMC + Indicadores como CONFIRMAÇÃO (não extremos)
Objetivo: Recuperar 76.6% e melhorar para 80%+

Estratégia: Use POI como filtro PRINCIPAL + indicadores como CONFIRMAÇÃO
Não use indicadores extremos - use deles para confirmar direção
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 100)
print("🎯 POI/SMC COM CONFIRMAÇÃO DE INDICADORES (Estratégia Melhorada)")
print("=" * 100)
print()

# =====================================================================
# 1. CARREGAR E PROCESSAR DADOS
# =====================================================================
print("1️⃣ CARREGANDO E PROCESSANDO DADOS")
print("-" * 100)

df = pd.read_csv('/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015_processed.csv')
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.sort_values('datetime').reset_index(drop=True)

print(f"✅ Carregados {len(df)} candles")
print()

# =====================================================================
# 2. CALCULAR INDICADORES
# =====================================================================
print("2️⃣ CALCULANDO INDICADORES DE CONFIRMAÇÃO")
print("-" * 100)

def calcular_sma(df, col, window):
    return df[col].rolling(window=window, min_periods=1).mean()

def calcular_rsi(df, col, period=14):
    delta = df[col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
    rs = gain / loss.replace(0, 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calcular_cci(df, period=20):
    tp = (df['high'] + df['low'] + df['close']) / 3
    sma_tp = tp.rolling(window=period, min_periods=1).mean()
    mad = (tp - sma_tp).abs().rolling(window=period, min_periods=1).mean()
    cci = (tp - sma_tp) / (0.015 * mad + 1e-9)
    return cci

def calcular_momentum(df, col, period=10):
    return df[col] - df[col].shift(period)

# Calcular
df['sma_50'] = calcular_sma(df, 'close', 50)
df['sma_200'] = calcular_sma(df, 'close', 200)
df['rsi_14'] = calcular_rsi(df, 'close', 14)
df['cci_20'] = calcular_cci(df, 20)
df['momentum_10'] = calcular_momentum(df, 'close', 10)

# Próximo close
df['next_close'] = df['close'].shift(-1)
df['change_pct'] = ((df['next_close'] - df['close']) / df['close'] * 100)
df['ganho'] = (df['change_pct'] > 0).astype(int)

# Hora
df['hora'] = df['datetime'].dt.hour
df['date'] = df['datetime'].dt.date

print("✅ Indicadores calculados")
print()

# =====================================================================
# 3. CALCULAR POI FEATURES (Simplificado)
# =====================================================================
print("3️⃣ CALCULANDO POI FEATURES")
print("-" * 100)

# Por dia
def calcular_poi_simples(df_day):
    """Calcula POI de forma simples e direta"""
    
    close_atual = df_day['close'].iloc[-1]
    high_dia = df_day['high'].max()
    low_dia = df_day['low'].min()
    
    # Distância ao topo/fundo
    dist_high = (high_dia - close_atual) / close_atual * 100
    dist_low = (close_atual - low_dia) / close_atual * 100
    
    # Posição na range
    range_dia = high_dia - low_dia
    pos_range = (close_atual - low_dia) / range_dia if range_dia > 0 else 0.5
    
    # Rejeição (confirmação)
    candle_alto = df_day['high'].iloc[-1] - df_day['low'].iloc[-1]
    had_rejeicao = (df_day['high'].iloc[-1] > high_dia) and (df_day['close'].iloc[-1] < (high_dia + low_dia) / 2)
    
    return {
        'dist_high': dist_high,
        'dist_low': dist_low,
        'pos_range': pos_range,
        'rejeicao': 1 if had_rejeicao else 0
    }

# Aplicar para cada dia
dias = df['date'].unique()
poi_dict = {'dist_high': [], 'dist_low': [], 'pos_range': [], 'rejeicao': []}

for date in dias:
    df_day = df[df['date'] == date]
    if len(df_day) > 0:
        poi = calcular_poi_simples(df_day)
        # Replicar para todos os candles do dia
        for _ in range(len(df_day)):
            poi_dict['dist_high'].append(poi['dist_high'])
            poi_dict['dist_low'].append(poi['dist_low'])
            poi_dict['pos_range'].append(poi['pos_range'])
            poi_dict['rejeicao'].append(poi['rejeicao'])

# Adicionar ao dataframe
for key in poi_dict.keys():
    df[key] = pd.NA
    df.loc[:len(poi_dict[key])-1, key] = poi_dict[key]

# Remover NaN
df_clean = df.dropna().reset_index(drop=True)

print(f"✅ POI features calculadas para {len(dias)} dias")
print()

# =====================================================================
# 4. DEFINIR ESTRATÉGIAS MELHORADAS
# =====================================================================
print("4️⃣ DEFININDO ESTRATÉGIAS COM CONFIRMAÇÃO")
print("-" * 100)
print()

# =====================================================================
# ESTRATÉGIA 1: ORIGINAL (Apenas POI - baseline)
# =====================================================================
print("📊 ESTRATÉGIA 1: ORIGINAL (POI Far from extremes)")
print("-" * 100)

# Entrada: FAR DO EXTREMO (>0.15%)
s1 = df_clean[
    (df_clean['dist_high'] > 0.15) | (df_clean['dist_low'] > 0.15)
]

s1_wr = s1['ganho'].mean() * 100 if len(s1) > 0 else 0
s1_trades = len(s1)

print(f"Critério: Entrada FAR DO EXTREMO (dist > 0.15%)")
print(f"✅ Win Rate: {s1_wr:.1f}%")
print(f"   Trades: {s1_trades}")
print()

# =====================================================================
# ESTRATÉGIA 2: POI + MOMENTUM (Confirmação suave)
# =====================================================================
print("📊 ESTRATÉGIA 2: POI + MOMENTUM")
print("-" * 100)

# Entrada: FAR DO EXTREMO + Momentum em direção certa
# Se perto do topo (dist_high > 0.15) -> espera momentum positivo
# Se perto do fundo (dist_low > 0.15) -> espera momentum positivo também (recovery)

s2 = df_clean[
    ((df_clean['dist_high'] > 0.15) & (df_clean['momentum_10'] > 0)) |
    ((df_clean['dist_low'] > 0.15) & (df_clean['momentum_10'] > 0))
]

s2_wr = s2['ganho'].mean() * 100 if len(s2) > 0 else 0
s2_trades = len(s2)

print(f"Critério: FAR DO EXTREMO + Momentum positivo")
print(f"✅ Win Rate: {s2_wr:.1f}%")
print(f"   Trades: {s2_trades}")
print()

# =====================================================================
# ESTRATÉGIA 3: POI + RSI CONFIRMAÇÃO (Suave)
# =====================================================================
print("📊 ESTRATÉGIA 3: POI + RSI (Suave 40-60)")
print("-" * 100)

# RSI 40-60 = neutro/confirmação, não extremo
# Entrada: FAR + RSI em zona saudável
s3 = df_clean[
    ((df_clean['dist_high'] > 0.15) | (df_clean['dist_low'] > 0.15)) &
    (df_clean['rsi_14'] > 40) & (df_clean['rsi_14'] < 60)
]

s3_wr = s3['ganho'].mean() * 100 if len(s3) > 0 else 0
s3_trades = len(s3)

print(f"Critério: FAR DO EXTREMO + RSI confirmação (40-60)")
print(f"✅ Win Rate: {s3_wr:.1f}%")
print(f"   Trades: {s3_trades}")
print()

# =====================================================================
# ESTRATÉGIA 4: POI + MULTI-CONFIRMAÇÃO (Moderado)
# =====================================================================
print("📊 ESTRATÉGIA 4: POI + MULTI-CONFIRMAÇÃO")
print("-" * 100)

# Entrada: FAR + CCI OK + RSI OK + Momentum OK
s4 = df_clean[
    ((df_clean['dist_high'] > 0.15) | (df_clean['dist_low'] > 0.15)) &
    (df_clean['cci_20'] > -50) & (df_clean['cci_20'] < 50) &  # CCI neutro (não extremo)
    (df_clean['rsi_14'] > 40) & (df_clean['rsi_14'] < 60) &   # RSI neutro
    (df_clean['momentum_10'] > df_clean['momentum_10'].quantile(0.3)) &  # Momentum acima do 30º percentil
    (df_clean['hora'].isin([16, 17, 18, 23]))  # Melhores horários
]

s4_wr = s4['ganho'].mean() * 100 if len(s4) > 0 else 0
s4_trades = len(s4)

print(f"Critério: FAR + Indicadores suaves + Horário bom")
print(f"✅ Win Rate: {s4_wr:.1f}%")
print(f"   Trades: {s4_trades}")
print()

# =====================================================================
# ESTRATÉGIA 5: POI + REJEIÇÃO + INDICADORES (Ultra-Confirmado)
# =====================================================================
print("📊 ESTRATÉGIA 5: POI + REJEIÇÃO + INDICADORES")
print("-" * 100)

# Entrada: FAR + Rejeição confirmada + Todos indicadores OK
s5 = df_clean[
    ((df_clean['dist_high'] > 0.15) | (df_clean['dist_low'] > 0.15)) &
    (df_clean['rejeicao'] == 1) &  # Rejeição detectada
    (df_clean['cci_20'] > -50) & (df_clean['cci_20'] < 50) &
    (df_clean['rsi_14'] > 40) & (df_clean['rsi_14'] < 60) &
    (df_clean['momentum_10'] > 0) &
    (df_clean['hora'].isin([16, 17, 18]))  # Melhores horários (sem 23:00)
]

s5_wr = s5['ganho'].mean() * 100 if len(s5) > 0 else 0
s5_trades = len(s5)

print(f"Critério: FAR + REJEIÇÃO + Indicadores suaves + Horário ótimo")
print(f"✅ Win Rate: {s5_wr:.1f}%")
print(f"   Trades: {s5_trades}")
print()

# =====================================================================
# 5. COMPARAR COM BASELINE
# =====================================================================
print("=" * 100)
print("5️⃣ COMPARAÇÃO COM BASELINE")
print("=" * 100)
print()

def calcular_metricas(est_df, name):
    if len(est_df) < 2:
        return None
    
    wr = est_df['ganho'].mean() * 100
    avg_ganho = est_df[est_df['ganho'] == 1]['change_pct'].mean()
    avg_perda = est_df[est_df['ganho'] == 0]['change_pct'].mean()
    
    total_ganho = est_df[est_df['ganho'] == 1]['change_pct'].sum()
    total_perda = abs(est_df[est_df['ganho'] == 0]['change_pct'].sum())
    pf = total_ganho / (total_perda + 1e-9)
    
    ganhos_cum = est_df['change_pct'].cumsum()
    runup = ganhos_cum.expanding().max()
    dd = (ganhos_cum - runup) / runup.replace(0, 1e-9) * 100
    max_dd = dd.min()
    
    ret_medio = est_df['change_pct'].mean()
    desvio = est_df['change_pct'].std()
    sharpe = (ret_medio / desvio) * np.sqrt(252) if desvio > 0 else 0
    
    expectativa = (wr/100) * avg_ganho + ((1-wr/100) * avg_perda)
    
    return {
        'nome': name,
        'trades': len(est_df),
        'wr': wr,
        'avg_ganho': avg_ganho,
        'avg_perda': avg_perda,
        'pf': pf,
        'max_dd': max_dd,
        'sharpe': sharpe,
        'expectativa': expectativa
    }

estrategias = [
    (s1, "1. ORIGINAL (POI only)"),
    (s2, "2. POI + MOMENTUM"),
    (s3, "3. POI + RSI SUAVE"),
    (s4, "4. MULTI-CONFIRMAÇÃO"),
    (s5, "5. POI+REJEIÇÃO+IND")
]

resultados = []
for est_df, name in estrategias:
    met = calcular_metricas(est_df, name)
    if met:
        resultados.append(met)

print("RANKING DE ESTRATÉGIAS:")
print("=" * 130)
print(f"{'Estratégia':<25} {'Trades':>10} {'WR%':>8} {'Avg Win':>10} {'Avg Loss':>10} {'PF':>8} {'MaxDD%':>10} {'Sharpe':>10} {'Expect%':>10}")
print("-" * 130)

for met in sorted(resultados, key=lambda x: x['wr'], reverse=True):
    print(f"{met['nome']:<25} {met['trades']:>10d} {met['wr']:>7.1f}% {met['avg_ganho']:>9.4f}% {met['avg_perda']:>9.4f}% {met['pf']:>7.2f} {met['max_dd']:>9.1f}% {met['sharpe']:>9.2f} {met['expectativa']:>9.4f}%")

print("=" * 130)
print()

# =====================================================================
# 6. RECOMENDAÇÃO FINAL
# =====================================================================
print("=" * 100)
print("6️⃣ RECOMENDAÇÃO E PRÓXIMOS PASSOS")
print("=" * 100)
print()

melhor = sorted(resultados, key=lambda x: x['sharpe'], reverse=True)[0]

print(f"🏆 MELHOR ESTRATÉGIA: {melhor['nome']}")
print()
print("Performance:")
print(f"  ✅ Win Rate: {melhor['wr']:.1f}%")
print(f"  ✅ Profit Factor: {melhor['pf']:.2f}x")
print(f"  ✅ Trades: {melhor['trades']}")
print(f"  ✅ Expectativa: {melhor['expectativa']:.4f}% por trade")
print()

if melhor['wr'] >= 76.6:
    ganho = melhor['wr'] - 76.6
    print(f"✅ OBJETIVO ATINGIDO! +{ganho:.1f}pp em relação ao baseline de 76.6%")
elif melhor['wr'] >= 75:
    print(f"⚠️ Próximo ao objetivo (atual {melhor['wr']:.1f}% vs meta 76.6%)")
else:
    print(f"❌ Abaixo do esperado (atual {melhor['wr']:.1f}% vs meta 76.6%)")

print()
print("Análise de Risco:")
if melhor['max_dd'] > -5:
    print(f"  🟢 DRAWDOWN BAIXO ({melhor['max_dd']:.1f}%) = SEGURO ✅")
elif melhor['max_dd'] > -20:
    print(f"  🟡 DRAWDOWN MÉDIO ({melhor['max_dd']:.1f}%) = ACEITÁVEL")
else:
    print(f"  🔴 DRAWDOWN ALTO ({melhor['max_dd']:.1f}%) = ARRISCADO")

if melhor['pf'] > 1.5:
    print(f"  🟢 PROFIT FACTOR BOAS ({melhor['pf']:.2f}x) = MARGEM SAUDÁVEL ✅")
elif melhor['pf'] > 1.0:
    print(f"  🟡 PROFIT FACTOR OK ({melhor['pf']:.2f}x)")
else:
    print(f"  🔴 PROFIT FACTOR RUIM ({melhor['pf']:.2f}x)")

print()
print("Recomendação:")
if melhor['wr'] >= 76:
    print("✅ PRONTO PARA PRODUÇÃO")
    print("   1. Fazer backtesting rigoroso (fora da amostra)")
    print("   2. Testar em dados de 2020-2022 (validação histórica)")
    print("   3. Implementar com stop loss em -0.05%")
    print("   4. Iniciar com 1 lote, depois aumentar")
elif melhor['wr'] >= 70:
    print("⚠️ BOM, MAS PRECISA REFINAMENTO")
    print("   1. Ajustar thresholds dos indicadores")
    print("   2. Testar períodos diferentes")
    print("   3. Adicionar análise multiframe (H4)")
else:
    print("❌ PRECISA DE MAIS PESQUISA")
    print("   1. Testar combinações diferentes")
    print("   2. Revisar cálculo de POI")
    print("   3. Considerar mudança de timeframe")

print()

# =====================================================================
# 7. SALVAR RESULTADOS
# =====================================================================
print("=" * 100)
print("7️⃣ SALVANDO RESULTADOS")
print("=" * 100)
print()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f'/home/ubuntu/pessoal/options/backtest_results/estrategias_poi_confirmacao_{timestamp}.csv'

df_resultado = pd.DataFrame(resultados).sort_values('wr', ascending=False)
df_resultado.to_csv(output_file, index=False)

print(f"✅ Arquivo salvo: {output_file}")
print()
print(df_resultado.to_string(index=False))
print()

print("=" * 100)
print("✨ ANÁLISE CONCLUÍDA")
print("=" * 100)
