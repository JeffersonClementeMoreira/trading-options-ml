#!/usr/bin/env python3
"""
OTIMIZADOR DE ESTRATÉGIA POI - Grid Search para 80%+ WR

Objetivo: Encontrar a melhor combinação de filtros que maximize WR
Data: 196 registros POI (5 horários x ~40 candles)
Goal: Melhorar de 41.3% para 80%+ WR
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import itertools
warnings.filterwarnings('ignore')

print("=" * 140)
print("🔥 OTIMIZADOR POI - GRID SEARCH PARA 80%+ WR")
print("=" * 140)
print()

# =====================================================================
# 1. CARREGAR DADOS
# =====================================================================
print("1️⃣ CARREGANDO DADOS POI")
print("-" * 140)

df = pd.read_csv('/home/ubuntu/pessoal/options/backtest_results/backtest_multi_horario_poi_20260526_024357.csv')

# Corrigir dados
df['change_pct'] = pd.to_numeric(df['change_pct'], errors='coerce')
df['ganho'] = (df['change_pct'] > 0).astype(int)
df['analysis_hour'] = df['analysis_hour'].str.split(':').str[0].astype(int)

# Adicionar colunas úteis
df['close_above_sma200'] = (df['close'] > df['sma200']).astype(int)
df['close_above_sma50'] = (df['close'] > df['sma50']).astype(int)
df['close_above_sma20'] = (df['close'] > df['sma20']).astype(int)
df['sma_trend_up'] = (df['sma50'] > df['sma200']).astype(int)
df['far_below'] = (df['dist_sup_pct'] > 0.1).astype(int)
df['far_above'] = (df['dist_res_pct'] > 0.1).astype(int)
df['mid_range'] = ((df['pos_in_range'] > 0.3) & (df['pos_in_range'] < 0.7)).astype(int)

print(f"✅ Carregados {len(df)} registros")
print(f"   Ganhos totais: {df['ganho'].sum()} ({df['ganho'].mean()*100:.1f}%)")
print()

# =====================================================================
# 2. DEFINIR PARÂMETROS DE GRID SEARCH
# =====================================================================
print("2️⃣ DEFININDO GRID DE BUSCA")
print("-" * 140)

# Parâmetros para testar
grid_params = {
    'far_below': [True, False],           # Usar filtro de suporte
    'far_above': [True, False],           # Usar filtro de resistência
    'close_above_sma200': [True, False],  # Close acima SMA200
    'sma_trend_up': [True, False],        # Tendência SMA50 > SMA200
    'mid_range': [True, False],           # Posição intermediária
    'bullish_only': [True, False],        # Apenas rejeição bullish
    'min_trades': [5, 10, 20],            # Mínimo de trades para considerar
}

# Gerar todas as combinações
combos = []
for far_below in grid_params['far_below']:
    for far_above in grid_params['far_above']:
        for close_sma200 in grid_params['close_above_sma200']:
            for sma_trend in grid_params['sma_trend_up']:
                for mid_range in grid_params['mid_range']:
                    for bullish in grid_params['bullish_only']:
                        for min_tr in grid_params['min_trades']:
                            combos.append({
                                'far_below': far_below,
                                'far_above': far_above,
                                'close_above_sma200': close_sma200,
                                'sma_trend_up': sma_trend,
                                'mid_range': mid_range,
                                'bullish_only': bullish,
                                'min_trades': min_tr,
                            })

print(f"✅ Total de combinações a testar: {len(combos)}")
print()

# =====================================================================
# 3. TESTAR TODAS AS COMBINAÇÕES
# =====================================================================
print("3️⃣ EXECUTANDO GRID SEARCH")
print("-" * 140)

resultados = []

for idx, params in enumerate(combos):
    # Construir filtro
    mask = pd.Series([True] * len(df))
    
    if params['far_below']:
        mask &= df['far_below'] == 1
    if params['far_above']:
        mask &= df['far_above'] == 1
    if params['close_above_sma200']:
        mask &= df['close_above_sma200'] == 1
    if params['sma_trend_up']:
        mask &= df['sma_trend_up'] == 1
    if params['mid_range']:
        mask &= df['mid_range'] == 1
    if params['bullish_only']:
        mask &= df['rejection_type'] == 'BULLISH_REJECTION'
    
    # Aplicar filtro
    df_filtered = df[mask]
    
    # Calcular métricas
    if len(df_filtered) >= params['min_trades']:
        trades = len(df_filtered)
        ganhos = df_filtered['ganho'].sum()
        perdas = trades - ganhos
        wr = (ganhos / trades * 100) if trades > 0 else 0
        avg_ganho = df_filtered[df_filtered['ganho'] == 1]['change_pct'].mean() if ganhos > 0 else 0
        avg_perda = df_filtered[df_filtered['ganho'] == 0]['change_pct'].mean() if perdas > 0 else 0
        
        # Calcula Profit Factor
        pf = (ganhos * avg_ganho) / (abs(perdas * avg_perda) + 0.0001) if perdas > 0 else (1000 if ganhos > 0 else 0)
        
        # Calcula Sharpe (simplifidado)
        returns = df_filtered['change_pct'].values
        sharpe = np.mean(returns) / (np.std(returns) + 0.0001) * np.sqrt(252 * 24)  # Ajuste temporal
        
        # Drawdown
        cum_returns = np.cumprod(1 + returns / 100)
        running_max = np.maximum.accumulate(cum_returns)
        drawdown = np.min((cum_returns - running_max) / running_max * 100) if len(cum_returns) > 0 else 0
        
        # Expectancy
        expectancy = wr/100 * avg_ganho + (1 - wr/100) * avg_perda
        
        resultado = {
            'trades': trades,
            'ganhos': ganhos,
            'perdas': perdas,
            'wr': wr,
            'avg_ganho': avg_ganho,
            'avg_perda': avg_perda,
            'pf': pf,
            'sharpe': sharpe,
            'drawdown': drawdown,
            'expectancy': expectancy,
            **params
        }
        
        resultados.append(resultado)

df_results = pd.DataFrame(resultados)

print(f"✅ {len(df_results)} combinações geraram >= {min(grid_params['min_trades'])} trades")
print()

# =====================================================================
# 4. RANKING DOS MELHORES RESULTADOS
# =====================================================================
print("4️⃣ TOP 20 MELHORES ESTRATÉGIAS (POR WIN RATE)")
print("-" * 140)

# Sort by WR descending, then by Sharpe for tie-break
df_ranking = df_results.sort_values(['wr', 'sharpe'], ascending=[False, False]).head(20)

print(f"{'#':<3} {'Trades':<8} {'WR%':<8} {'Ganhos':<8} {'PF':<8} {'Sharpe':<8} {'MaxDD%':<10} {'Expectancy':<12} {'Filtros':<50}")
print("-" * 140)

for idx, (i, row) in enumerate(df_ranking.iterrows(), 1):
    # Construir descrição dos filtros
    filtros = []
    if row['far_below']:
        filtros.append('FAR_BELOW')
    if row['far_above']:
        filtros.append('FAR_ABOVE')
    if row['close_above_sma200']:
        filtros.append('CLOSE>SMA200')
    if row['sma_trend_up']:
        filtros.append('SMA_UP')
    if row['mid_range']:
        filtros.append('MID_RNG')
    if row['bullish_only']:
        filtros.append('BULL_ONLY')
    
    filtro_str = ' + '.join(filtros) if filtros else 'NENHUM'
    
    # Status
    status = "🚀" if row['wr'] >= 80 else "✅" if row['wr'] >= 75 else "⚠️" if row['wr'] >= 70 else "❌"
    
    print(f"{idx:<3d} {row['trades']:<8.0f} {row['wr']:<7.1f}% {row['ganhos']:<8.0f} {row['pf']:<8.2f} {row['sharpe']:<8.2f} {row['drawdown']:<9.1f}% {row['expectancy']:<11.4f}% {filtro_str:<50} {status}")

print()

# =====================================================================
# 5. MELHOR ESTRATÉGIA GERAL
# =====================================================================
print("=" * 140)
print("5️⃣ RECOMENDAÇÃO FINAL")
print("=" * 140)
print()

# Encontrar melhor por diferentes critérios
melhor_wr = df_results.loc[df_results['wr'].idxmax()]
melhor_sharpe = df_results.loc[df_results['sharpe'].idxmax()]
melhor_pf = df_results.loc[df_results['pf'].idxmax()]

estrategias_top = [
    ('MAIOR WIN RATE', melhor_wr),
    ('MELHOR SHARPE', melhor_sharpe),
    ('MAIOR PROFIT FACTOR', melhor_pf),
]

for nome, strat in estrategias_top:
    # Construir filtros
    filtros = []
    if strat['far_below']:
        filtros.append('FAR BELOW (dist_sup > 0.1%)')
    if strat['far_above']:
        filtros.append('FAR ABOVE (dist_res > 0.1%)')
    if strat['close_above_sma200']:
        filtros.append('Close > SMA200')
    if strat['sma_trend_up']:
        filtros.append('SMA50 > SMA200')
    if strat['mid_range']:
        filtros.append('Posição Range (0.3-0.7)')
    if strat['bullish_only']:
        filtros.append('Apenas Rejeição BULLISH')
    
    print(f"🏆 {nome}")
    print(f"   Filtros: {' + '.join(filtros) if filtros else 'NENHUM'}")
    print(f"   Trades: {strat['trades']:.0f}")
    print(f"   Win Rate: {strat['wr']:.1f}%")
    print(f"   Ganhos: {strat['ganhos']:.0f} | Perdas: {strat['perdas']:.0f}")
    print(f"   Avg Win: {strat['avg_ganho']:+.4f}% | Avg Loss: {strat['avg_perda']:+.4f}%")
    print(f"   Profit Factor: {strat['pf']:.2f}x")
    print(f"   Sharpe Ratio: {strat['sharpe']:.2f}")
    print(f"   Max Drawdown: {strat['drawdown']:.1f}%")
    print(f"   Expectancy: {strat['expectancy']:+.4f}%")
    
    # Status
    if strat['wr'] >= 80:
        print(f"   ✅ STATUS: 🚀 OBJETIVO ALCANÇADO!")
        melhoria = strat['wr'] - 76.6
        print(f"   Melhoria: +{melhoria:.1f}pp em relação aos 76.6% anteriores")
    elif strat['wr'] >= 75:
        print(f"   ✅ STATUS: BOM (Próximo ao 80%)")
        falta = 80 - strat['wr']
        print(f"   Falta: {falta:.1f}pp para atingir 80%")
    else:
        print(f"   ⚠️ STATUS: Ainda abaixo do esperado")
    
    print()

# =====================================================================
# 6. DISTRIBUIÇÃO DE WIN RATES
# =====================================================================
print("6️⃣ DISTRIBUIÇÃO DE WIN RATES")
print("-" * 140)

bins = [0, 50, 60, 70, 75, 80, 85, 90, 100]
counts, _ = np.histogram(df_results['wr'], bins=bins)

print(f"{'Range':<15} {'Combinações':<20} {'% do Total':<15}")
print("-" * 50)

for i in range(len(bins)-1):
    range_str = f"{bins[i]:.0f}% - {bins[i+1]:.0f}%"
    pct = counts[i] / len(df_results) * 100
    print(f"{range_str:<15} {counts[i]:<20.0f} {pct:>13.1f}%")

print()

# =====================================================================
# 7. SALVAR RESULTADOS
# =====================================================================
print("=" * 140)
print("7️⃣ SALVANDO RESULTADOS")
print("=" * 140)
print()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_csv = f'/home/ubuntu/pessoal/options/backtest_results/otimizador_poi_completo_{timestamp}.csv'

df_results.to_csv(output_csv, index=False)
print(f"✅ Arquivo completo (todas as {len(df_results)} combinações):")
print(f"   {output_csv}")

# Salvar top 100
output_top = f'/home/ubuntu/pessoal/options/backtest_results/otimizador_poi_top100_{timestamp}.csv'
df_results.sort_values(['wr', 'sharpe'], ascending=[False, False]).head(100).to_csv(output_top, index=False)
print(f"✅ Arquivo top 100:")
print(f"   {output_top}")

print()
print("=" * 140)
print("✨ ANÁLISE CONCLUÍDA")
print("=" * 140)
