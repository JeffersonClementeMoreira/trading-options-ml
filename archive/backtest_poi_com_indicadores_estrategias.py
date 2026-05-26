#!/usr/bin/env python3
"""
POI/SMC + Indicadores + Estratégias de Risco
Objetivo: Melhorar de 76.6% para 80%+ com análise de risco

Estratégias:
1. CONSERVADORA: Apenas POI (original) → 76.6% WR, baixo risco
2. MODERADA: POI + CCI20 confirmação → ~78-80% WR, médio risco
3. AGRESSIVA: POI + CCI20 + RSI + BBPosition → ~82-85% WR, alto risco
4. ULTRA: Tudo + filtro de horário → ~85-90% WR, muito alto risco
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 100)
print("🎯 POI/SMC + INDICADORES + ESTRATÉGIAS DE RISCO")
print("=" * 100)
print()

# =====================================================================
# 1. CARREGAR DADOS
# =====================================================================
print("1️⃣ CARREGANDO DADOS POI/SMC")
print("-" * 100)

df = pd.read_csv('/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015_processed.csv')
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.sort_values('datetime').reset_index(drop=True)

print(f"✅ Carregados {len(df)} candles")
print(f"   Período: {df['datetime'].min()} → {df['datetime'].max()}")
print()

# =====================================================================
# 2. CALCULAR INDICADORES
# =====================================================================
print("2️⃣ CALCULANDO INDICADORES")
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

def calcular_bollinger_bands(df, col, period=20, std_dev=2):
    sma = df[col].rolling(window=period, min_periods=1).mean()
    std = df[col].rolling(window=period, min_periods=1).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    bb_position = (df[col] - lower) / (upper - lower)
    return bb_position

def calcular_stochastic(df, period=14):
    low_min = df['low'].rolling(window=period, min_periods=1).min()
    high_max = df['high'].rolling(window=period, min_periods=1).max()
    k_percent = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-9)
    return k_percent

# Calcular indicadores
df['sma_200'] = calcular_sma(df, 'close', 200)
df['rsi_14'] = calcular_rsi(df, 'close', 14)
df['cci_20'] = calcular_cci(df, 20)
df['bb_position'] = calcular_bollinger_bands(df, 'close', 20, 2)
df['stoch_k'] = calcular_stochastic(df, 14)

print("✅ Indicadores calculados: SMA200, RSI14, CCI20, BBPosition, StochK")
print()

# =====================================================================
# 3. CALCULAR POI FEATURES (como antes)
# =====================================================================
print("3️⃣ CALCULANDO POI FEATURES")
print("-" * 100)

def calcular_poi_features(df_day, df_hist):
    """Calcula features de POI para cada dia"""
    
    features = {
        'dist_res_pct': [],
        'dist_sup_pct': [],
        'near_res': [],
        'near_sup': [],
        'pos_in_range': [],
        'poi_strength': [],
        'rejection_type': []
    }
    
    for idx, row in df_day.iterrows():
        close = row['close']
        high = row['high']
        low = row['low']
        
        # Resistência = máximo do dia
        resistance = df_day['high'].max()
        support = df_day['low'].min()
        
        # Distâncias
        dist_res = (close - resistance) / close * 100
        dist_sup = (close - support) / close * 100
        
        # Proximidade
        near_res = abs(dist_res) < 0.05
        near_sup = abs(dist_sup) < 0.05
        
        # Posição na range
        range_alta = high - low
        if range_alta > 0:
            pos_range = (close - low) / range_alta
        else:
            pos_range = 0.5
        
        # Força do POI
        poi_str = min(range_alta / (df_day['close'].max() * 0.005), 1.0)
        
        # Tipo de rejeição
        high_greater_res = high > resistance
        close_lower_mid = close < (resistance + support) / 2
        if high_greater_res and close_lower_mid:
            rejection = 'BULLISH_REJECTION'
        elif not high_greater_res:
            rejection = 'BEARISH_REJECTION'
        else:
            rejection = 'NO_REJECTION'
        
        features['dist_res_pct'].append(dist_res)
        features['dist_sup_pct'].append(dist_sup)
        features['near_res'].append(1 if near_res else 0)
        features['near_sup'].append(1 if near_sup else 0)
        features['pos_in_range'].append(pos_range)
        features['poi_strength'].append(poi_str)
        features['rejection_type'].append(rejection)
    
    return features

# Aplicar POI por dia
df['date'] = df['datetime'].dt.date
dias = df['date'].unique()

print(f"Processando {len(dias)} dias...")

poi_data = {
    'dist_res_pct': [],
    'dist_sup_pct': [],
    'near_res': [],
    'near_sup': [],
    'pos_in_range': [],
    'poi_strength': [],
    'rejection_type': []
}

for date in dias:
    df_day = df[df['date'] == date]
    if len(df_day) > 0:
        features = calcular_poi_features(df_day, df)
        
        for key in poi_data.keys():
            poi_data[key].extend(features[key])

# Adicionar ao dataframe
for key, values in poi_data.items():
    df[key] = pd.NA
    df.loc[df.index[:len(values)], key] = values

print("✅ POI features calculadas")
print()

# =====================================================================
# 4. DEFINIR ESTRATÉGIAS
# =====================================================================
print("4️⃣ DEFININDO 4 ESTRATÉGIAS DE RISCO/RETORNO")
print("-" * 100)

df['next_close'] = df['close'].shift(-1)
df['change_pct'] = ((df['next_close'] - df['close']) / df['close'] * 100)

# Remover NaN
df_clean = df.dropna().reset_index(drop=True)

# Criar resultado binário (ganho ou perda)
df_clean['ganho'] = (df_clean['change_pct'] > 0).astype(int)

# =====================================================================
# ESTRATÉGIA 1: CONSERVADORA (Apenas POI original)
# =====================================================================
print("\n📊 ESTRATÉGIA 1: CONSERVADORA (POI apenas)")
print("-" * 100)

# Filtro: Entrada FAR DO POI (>0.1%)
s1 = df_clean[
    (abs(df_clean['dist_res_pct']) > 0.1) | 
    (abs(df_clean['dist_sup_pct']) > 0.1)
]

s1_wr = s1['ganho'].mean() * 100 if len(s1) > 0 else 0
s1_trades = len(s1)

print(f"Critério: Entrada FAR DO POI (|dist| > 0.1%)")
print(f"✅ Win Rate: {s1_wr:.1f}%")
print(f"   Trades: {s1_trades}")
print(f"   Risco: BAIXO (menos filtros = mais trades)")
print()

# =====================================================================
# ESTRATÉGIA 2: MODERADA (POI + CCI20)
# =====================================================================
print("📊 ESTRATÉGIA 2: MODERADA (POI + CCI20)")
print("-" * 100)

# Filtro: FAR DO POI + CCI20 confirmação (extremo)
s2 = df_clean[
    ((abs(df_clean['dist_res_pct']) > 0.1) | (abs(df_clean['dist_sup_pct']) > 0.1)) &
    ((df_clean['cci_20'] > 100) | (df_clean['cci_20'] < -100))
]

s2_wr = s2['ganho'].mean() * 100 if len(s2) > 0 else 0
s2_trades = len(s2)

print(f"Critério: FAR DO POI + CCI20 extremo (>100 ou <-100)")
print(f"✅ Win Rate: {s2_wr:.1f}%")
print(f"   Trades: {s2_trades}")
print(f"   Risco: MÉDIO (1 filtro adicional)")
print()

# =====================================================================
# ESTRATÉGIA 3: AGRESSIVA (POI + CCI20 + RSI + BBPosition)
# =====================================================================
print("📊 ESTRATÉGIA 3: AGRESSIVA (POI + 3 indicadores)")
print("-" * 100)

# Filtro: FAR DO POI + CCI20 + RSI extremo + BB extremo
s3 = df_clean[
    ((abs(df_clean['dist_res_pct']) > 0.1) | (abs(df_clean['dist_sup_pct']) > 0.1)) &
    ((df_clean['cci_20'] > 100) | (df_clean['cci_20'] < -100)) &
    ((df_clean['rsi_14'] > 65) | (df_clean['rsi_14'] < 35)) &
    ((df_clean['bb_position'] > 0.75) | (df_clean['bb_position'] < 0.25))
]

s3_wr = s3['ganho'].mean() * 100 if len(s3) > 0 else 0
s3_trades = len(s3)

print(f"Critério: FAR DO POI + CCI20 extremo + RSI extremo + BB extremo")
print(f"✅ Win Rate: {s3_wr:.1f}%")
print(f"   Trades: {s3_trades}")
print(f"   Risco: ALTO (múltiplos filtros)")
print()

# =====================================================================
# ESTRATÉGIA 4: ULTRA (POI + Indicadores + Horário)
# =====================================================================
print("📊 ESTRATÉGIA 4: ULTRA (POI + Indicadores + Hora)")
print("-" * 100)

# Adicionar hora
df_clean['hora'] = df_clean['datetime'].dt.hour

# Filtro: FAR DO POI + CCI20 + RSI + BB + HORA (melhor horário = 17:00)
s4 = df_clean[
    ((abs(df_clean['dist_res_pct']) > 0.1) | (abs(df_clean['dist_sup_pct']) > 0.1)) &
    ((df_clean['cci_20'] > 100) | (df_clean['cci_20'] < -100)) &
    ((df_clean['rsi_14'] > 65) | (df_clean['rsi_14'] < 35)) &
    ((df_clean['bb_position'] > 0.75) | (df_clean['bb_position'] < 0.25)) &
    (df_clean['hora'].isin([16, 17, 18]))  # Melhores horários
]

s4_wr = s4['ganho'].mean() * 100 if len(s4) > 0 else 0
s4_trades = len(s4)

print(f"Critério: FAR DO POI + Indicadores extremos + Horário (16:00-18:00)")
print(f"✅ Win Rate: {s4_wr:.1f}%")
print(f"   Trades: {s4_trades}")
print(f"   Risco: MUITO ALTO (extremamente seletivo)")
print()

# =====================================================================
# 5. CALCULAR RISCO PARA CADA ESTRATÉGIA
# =====================================================================
print("=" * 100)
print("5️⃣ ANÁLISE DE RISCO")
print("=" * 100)
print()

def calcular_metricas_risco(estrategia_df, name):
    """Calcula métricas de risco para uma estratégia"""
    
    if len(estrategia_df) < 2:
        return None
    
    # Win rate
    wr = estrategia_df['ganho'].mean() * 100
    
    # Lucro/perda média
    avg_ganho = estrategia_df[estrategia_df['ganho'] == 1]['change_pct'].mean()
    avg_perda = estrategia_df[estrategia_df['ganho'] == 0]['change_pct'].mean()
    
    # Profit factor
    total_ganho = estrategia_df[estrategia_df['ganho'] == 1]['change_pct'].sum()
    total_perda = abs(estrategia_df[estrategia_df['ganho'] == 0]['change_pct'].sum())
    profit_factor = total_ganho / (total_perda + 1e-9)
    
    # Drawdown máximo
    ganhos_acumulados = estrategia_df['change_pct'].cumsum()
    runup = ganhos_acumulados.expanding().max()
    drawdown = (ganhos_acumulados - runup) / runup.replace(0, 1e-9) * 100
    max_drawdown = drawdown.min()
    
    # Sharpe ratio (simplificado)
    retorno_medio = estrategia_df['change_pct'].mean()
    desvio = estrategia_df['change_pct'].std()
    sharpe = (retorno_medio / desvio) * np.sqrt(252) if desvio > 0 else 0
    
    # Expectativa matemática
    expectativa = (wr / 100) * avg_ganho + ((1 - wr/100) * avg_perda)
    
    return {
        'name': name,
        'trades': len(estrategia_df),
        'wr': wr,
        'avg_ganho': avg_ganho,
        'avg_perda': avg_perda,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'sharpe': sharpe,
        'expectativa': expectativa
    }

estrategias = [
    (s1, "CONSERVADORA"),
    (s2, "MODERADA"),
    (s3, "AGRESSIVA"),
    (s4, "ULTRA")
]

resultados_risco = []
for est_df, name in estrategias:
    metricas = calcular_metricas_risco(est_df, name)
    if metricas:
        resultados_risco.append(metricas)

# Mostrar resultados
print("COMPARAÇÃO DE ESTRATÉGIAS:")
print("=" * 140)
print(f"{'Estratégia':<15} {'Trades':>8} {'WR%':>8} {'Avg Win':>10} {'Avg Loss':>10} {'PF':>8} {'MaxDD%':>10} {'Sharpe':>10} {'Expect':>10} {'Risco':>12}")
print("-" * 140)

for met in resultados_risco:
    risco_txt = "BAIXO" if met['wr'] <= 75 else "MÉDIO" if met['wr'] <= 82 else "ALTO" if met['wr'] <= 88 else "MUITO ALTO"
    print(f"{met['name']:<15} {met['trades']:>8d} {met['wr']:>7.1f}% {met['avg_ganho']:>9.4f}% {met['avg_perda']:>9.4f}% {met['profit_factor']:>7.2f} {met['max_drawdown']:>9.1f}% {met['sharpe']:>9.2f} {met['expectativa']:>9.4f}% {risco_txt:>12}")

print("=" * 140)
print()

# =====================================================================
# 6. RECOMENDAÇÃO
# =====================================================================
print("=" * 100)
print("6️⃣ RECOMENDAÇÃO ESTRATÉGICA")
print("=" * 100)
print()

# Ordenar por Sharpe ratio (melhor risco/retorno)
melhor = sorted(resultados_risco, key=lambda x: x['sharpe'], reverse=True)[0]

print(f"🏆 MELHOR ESTRATÉGIA RECOMENDADA: {melhor['name']}")
print()
print("Métricas:")
print(f"  ✅ Win Rate: {melhor['wr']:.1f}%")
print(f"  ✅ Profit Factor: {melhor['profit_factor']:.2f}x")
print(f"  ✅ Sharpe Ratio: {melhor['sharpe']:.2f} (risco/retorno)")
print(f"  ✅ Drawdown Máximo: {melhor['max_drawdown']:.1f}%")
print(f"  ✅ Expectativa: {melhor['expectativa']:.4f}% por trade")
print(f"  ✅ Trades: {melhor['trades']}")
print()

print("Interpretação:")
if melhor['wr'] >= 80:
    print(f"  🎯 Win Rate acima de 80% = EXCELENTE")
    print(f"  🎯 Pode ser usado em produção")
    print(f"  🎯 Capital necessário: ~$10k (para 1 lote)")
elif melhor['wr'] >= 75:
    print(f"  ✅ Win Rate acima de 75% = BOM")
    print(f"  ✅ Pode ser usado com controle de risco")
    print(f"  ✅ Capital necessário: ~$5k (para 1 lote)")
else:
    print(f"  ⚠️ Win Rate abaixo de 75% = MARGINAL")
    print(f"  ⚠️ Risco/retorno não favorável")
    print(f"  ⚠️ Recomendação: Continuar pesquisando")

print()
print("Risco da Estratégia:")
if melhor['max_drawdown'] > -10:
    print(f"  🟢 Drawdown baixo ({melhor['max_drawdown']:.1f}%) = SEGURO")
elif melhor['max_drawdown'] > -20:
    print(f"  🟡 Drawdown médio ({melhor['max_drawdown']:.1f}%) = ACEITÁVEL")
else:
    print(f"  🔴 Drawdown alto ({melhor['max_drawdown']:.1f}%) = ARRISCADO")

if melhor['profit_factor'] > 2.0:
    print(f"  🟢 Profit Factor alto ({melhor['profit_factor']:.2f}x) = MUITO BOM")
elif melhor['profit_factor'] > 1.5:
    print(f"  🟡 Profit Factor moderado ({melhor['profit_factor']:.2f}x) = BOM")
else:
    print(f"  🔴 Profit Factor baixo ({melhor['profit_factor']:.2f}x) = BAIXA MARGEM")

print()

# =====================================================================
# 7. GERAR CSV DE SAÍDA
# =====================================================================
print("=" * 100)
print("7️⃣ GERANDO ARQUIVO DE SAÍDA")
print("=" * 100)
print()

# Criar dataframe com estratégias
saida_df = pd.DataFrame(resultados_risco)

# Adicionar recomendação
saida_df['recomendacao'] = saida_df['name'].apply(
    lambda x: '🏆 MELHOR' if x == melhor['name'] else '✅ BOM' if melhor['wr'] >= 78 else '⚠️ RISCO'
)

# Salvar
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f'/home/ubuntu/pessoal/options/backtest_results/estrategias_poi_indicadores_{timestamp}.csv'
saida_df.to_csv(output_file, index=False)

print(f"✅ Arquivo salvo: {output_file}")
print()
print(saida_df.to_string(index=False))
print()

# =====================================================================
# 8. SALVAR DADOS DETALHADOS (Qual estratégia para cada trade)
# =====================================================================
print("=" * 100)
print("8️⃣ GERANDO CSV COM CADA TRADE E SUA ESTRATÉGIA")
print("=" * 100)
print()

# Criar coluna de estratégia para cada trade
df_clean['estrategia'] = 'FORA'

# Marcar estratégias
for idx in s1.index:
    df_clean.loc[idx, 'estrategia'] = 'S1_CONSERVADORA'

for idx in s2.index:
    df_clean.loc[idx, 'estrategia'] = 'S2_MODERADA'

for idx in s3.index:
    df_clean.loc[idx, 'estrategia'] = 'S3_AGRESSIVA'

for idx in s4.index:
    df_clean.loc[idx, 'estrategia'] = 'S4_ULTRA'

# Salvar
output_file2 = f'/home/ubuntu/pessoal/options/backtest_results/trades_poi_indicadores_{timestamp}.csv'
df_clean[[
    'datetime', 'open', 'high', 'low', 'close', 'next_close',
    'change_pct', 'ganho',
    'dist_res_pct', 'dist_sup_pct', 'near_res', 'near_sup',
    'rsi_14', 'cci_20', 'bb_position', 'stoch_k',
    'hora', 'estrategia'
]].to_csv(output_file2, index=False)

print(f"✅ Arquivo salvo: {output_file2}")
print(f"   Linhas: {len(df_clean)}")
print()

# =====================================================================
# 9. ANÁLISE FINAL
# =====================================================================
print("=" * 100)
print("9️⃣ CONCLUSÃO")
print("=" * 100)
print()

print("📊 PROGRESSO:")
print(f"  • POI original: 76.6% WR")
print(f"  • Com indicadores: {melhor['wr']:.1f}% WR")
if melhor['wr'] > 76.6:
    melhoria = melhor['wr'] - 76.6
    print(f"  • MELHORIA: +{melhoria:.1f}pp ✅")
else:
    melhoria = 76.6 - melhor['wr']
    print(f"  • PIORA: -{melhoria:.1f}pp ❌")

print()
print("📈 PRÓXIMOS PASSOS:")
if melhor['wr'] >= 80:
    print("  1. ✅ Win rate > 80% alcançado!")
    print("  2. Fazer backtesting rigoroso com dados out-of-sample")
    print("  3. Implementar em produção com controle de risco")
    print("  4. Monitor inicial: 10 trades reais")
else:
    print("  1. Testar combinações diferentes de indicadores")
    print("  2. Ajustar thresholds (CCI > 100 vs CCI > 80?)")
    print("  3. Adicionar análise multiframe (H4/D1)")
    print("  4. Buscar padrões adicionais")

print()
print("=" * 100)
print("✨ ANÁLISE CONCLUÍDA")
print("=" * 100)
