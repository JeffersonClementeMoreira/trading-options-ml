#!/usr/bin/env python3
"""
Análise de Padrões Vencedores: Quais indicadores funcionam melhor em cada horário?
Objetivo: Encontrar combinações de indicadores que preveem melhor a direção
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

print("=" * 100)
print("🔍 ANÁLISE DE PADRÕES VENCEDORES")
print("=" * 100)
print()

# Carregar dados
csv_file = '/home/ubuntu/pessoal/options/backtest_results/analise_candle_a_candle_20260526_025440.csv'
df = pd.read_csv(csv_file)

# Extrair hora
df['hora'] = pd.to_datetime(df['Data']).dt.hour

print(f"✅ Carregados {len(df)} registros")
print()

# =====================================================================
# 1. MELHOR E PIOR HORÁRIO
# =====================================================================
print("=" * 100)
print("1️⃣ PERFORMANCE POR HORÁRIO")
print("=" * 100)
print()

por_hora = df.groupby('hora').agg({
    'AcertoDirecao': ['sum', 'count', 'mean'],
    'ErroAbsoluto(%)': ['mean', 'std'],
    'VariacaoReal(%)': ['mean', 'std'],
    'PredicaoModelo(%)': 'mean'
}).round(4)

# Rename columns
por_hora.columns = ['Acertos', 'Total', 'TaxaAcerto', 'ErroMedio', 'ErroSTD', 'VarMedia', 'VarSTD', 'PrevMedia']

# Ranking
ranking = por_hora.sort_values('TaxaAcerto', ascending=False)

print("TOP 5 MELHORES HORÁRIOS:")
print("-" * 100)
for idx, (hora, row) in enumerate(ranking.head(5).iterrows(), 1):
    taxa = row['TaxaAcerto'] * 100
    acertos = int(row['Acertos'])
    total = int(row['Total'])
    print(f"{idx}. {int(hora):02d}:00 - {taxa:5.1f}% ({acertos:3d}/{total:3d}) | Var: {row['VarMedia']:+.5f}% | Erro: {row['ErroMedio']:.5f}%")

print()
print("TOP 5 PIORES HORÁRIOS:")
print("-" * 100)
for idx, (hora, row) in enumerate(ranking.tail(5).iterrows(), 1):
    taxa = row['TaxaAcerto'] * 100
    acertos = int(row['Acertos'])
    total = int(row['Total'])
    print(f"{idx}. {int(hora):02d}:00 - {taxa:5.1f}% ({acertos:3d}/{total:3d}) | Var: {row['VarMedia']:+.5f}% | Erro: {row['ErroMedio']:.5f}%")

print()

# =====================================================================
# 2. ANÁLISE DE CORRELAÇÃO: INDICADORES vs ACERTO
# =====================================================================
print("=" * 100)
print("2️⃣ CORRELAÇÃO: INDICADORES vs ACERTO")
print("=" * 100)
print()

# Indicadores a analisar
indicadores = ['SMA20', 'SMA50', 'SMA200', 'RSI14', 'MACD', 'BBPosition', 'StochK', 'CCI20']

correlacoes = {}
for ind in indicadores:
    if ind in df.columns:
        corr = df[ind].corr(df['AcertoDirecao'])
        correlacoes[ind] = corr

# Ordenar
corr_df = pd.DataFrame.from_dict(correlacoes, orient='index', columns=['Correlacao'])
corr_df = corr_df.sort_values('Correlacao', ascending=False, key=abs)

print("Indicadores com maior correlação com acerto:")
print("-" * 100)
for ind, corr in corr_df.iterrows():
    valor = corr['Correlacao']
    if valor > 0:
        print(f"✅ {ind:15s} → {valor:+.6f} (correlação positiva)")
    elif valor < 0:
        print(f"❌ {ind:15s} → {valor:+.6f} (correlação negativa)")
    else:
        print(f"⚪ {ind:15s} → {valor:+.6f} (sem correlação)")

print()

# =====================================================================
# 3. MELHORES COMBINAÇÕES DE INDICADORES
# =====================================================================
print("=" * 100)
print("3️⃣ MELHORES COMBINAÇÕES (PADRÕES VENCEDORES)")
print("=" * 100)
print()

# Definir padrões vencedores
# Exemplo: RSI14 > 50 AND Close acima SMA200
padroes = []

# Padrão 1: RSI alto + acima da SMA200
p1 = df[(df['RSI14'] > 60) & (df['Close'] > df['SMA200'])]
if len(p1) > 0:
    taxa_p1 = p1['AcertoDirecao'].mean()
    padroes.append({
        'nome': 'RSI > 60 E Close > SMA200',
        'casos': len(p1),
        'acertos': p1['AcertoDirecao'].sum(),
        'taxa': taxa_p1
    })

# Padrão 2: RSI baixo + abaixo da SMA200
p2 = df[(df['RSI14'] < 40) & (df['Close'] < df['SMA200'])]
if len(p2) > 0:
    taxa_p2 = p2['AcertoDirecao'].mean()
    padroes.append({
        'nome': 'RSI < 40 E Close < SMA200',
        'casos': len(p2),
        'acertos': p2['AcertoDirecao'].sum(),
        'taxa': taxa_p2
    })

# Padrão 3: RSI extremo (super vendido/comprado)
p3a = df[df['RSI14'] > 70]
p3b = df[df['RSI14'] < 30]
p3 = pd.concat([p3a, p3b])
if len(p3) > 0:
    taxa_p3 = p3['AcertoDirecao'].mean()
    padroes.append({
        'nome': 'RSI Extremo (> 70 ou < 30)',
        'casos': len(p3),
        'acertos': p3['AcertoDirecao'].sum(),
        'taxa': taxa_p3
    })

# Padrão 4: BBPosition nos extremos
p4a = df[df['BBPosition'] > 0.8]
p4b = df[df['BBPosition'] < 0.2]
p4 = pd.concat([p4a, p4b])
if len(p4) > 0:
    taxa_p4 = p4['AcertoDirecao'].mean()
    padroes.append({
        'nome': 'Preço em extremo de BB (>0.8 ou <0.2)',
        'casos': len(p4),
        'acertos': p4['AcertoDirecao'].sum(),
        'taxa': taxa_p4
    })

# Padrão 5: StochK extremo
p5a = df[df['StochK'] > 80]
p5b = df[df['StochK'] < 20]
p5 = pd.concat([p5a, p5b])
if len(p5) > 0:
    taxa_p5 = p5['AcertoDirecao'].mean()
    padroes.append({
        'nome': 'StochK Extremo (> 80 ou < 20)',
        'casos': len(p5),
        'acertos': p5['AcertoDirecao'].sum(),
        'taxa': taxa_p5
    })

# Padrão 6: Preço entre SMA50 e SMA200
cond1 = (df['Close'] > df['SMA50']) & (df['Close'] < df['SMA200'])
cond2 = (df['Close'] < df['SMA50']) & (df['Close'] > df['SMA200'])
p6 = df[cond1 | cond2]
if len(p6) > 0:
    taxa_p6 = p6['AcertoDirecao'].mean()
    padroes.append({
        'nome': 'Close entre SMA50 e SMA200',
        'casos': len(p6),
        'acertos': p6['AcertoDirecao'].sum(),
        'taxa': taxa_p6
    })

# Ordenar padrões
padroes_df = pd.DataFrame(padroes).sort_values('taxa', ascending=False)

print("Padrões com melhor taxa de acerto:")
print("-" * 100)
for idx, padrão in padroes_df.iterrows():
    taxa = padrão['taxa'] * 100
    status = "✅" if taxa > 50.2 else "⚠️"
    print(f"{status} {padrão['nome']:40s} | {taxa:5.1f}% ({int(padrão['acertos'])}/{int(padrão['casos'])} casos)")

print()

# =====================================================================
# 4. ANÁLISE POR HORÁRIO: QUAL INDICADOR FUNCIONA MELHOR EM CADA HORA?
# =====================================================================
print("=" * 100)
print("4️⃣ INDICADOR MAIS PREDITIVO POR HORÁRIO")
print("=" * 100)
print()

for hora in sorted(df['hora'].unique()):
    df_hora = df[df['hora'] == hora]
    
    # Correlação para essa hora
    corrs_hora = {}
    for ind in indicadores:
        if ind in df_hora.columns:
            corr = df_hora[ind].corr(df_hora['AcertoDirecao'])
            if not np.isnan(corr):
                corrs_hora[ind] = corr
    
    if corrs_hora:
        melhor_ind = max(corrs_hora, key=lambda x: abs(corrs_hora[x]))
        melhor_corr = corrs_hora[melhor_ind]
        taxa = df_hora['AcertoDirecao'].mean() * 100
        
        emoji = "✅" if taxa > 50.2 else "⚠️"
        print(f"{emoji} {int(hora):02d}:00 | Taxa: {taxa:5.1f}% | Melhor Indicador: {melhor_ind:10s} (corr: {melhor_corr:+.4f})")

print()

# =====================================================================
# 5. HORÁRIOS AGRUPADOS
# =====================================================================
print("=" * 100)
print("5️⃣ ANÁLISE POR SESSÃO DE TRADING")
print("=" * 100)
print()

sessoes = {
    'Asiática (00:00-08:00)': list(range(0, 9)),
    'Europeia (08:00-16:00)': list(range(8, 17)),
    'Americana (16:00-23:00)': list(range(16, 24)),
    'Overlap EU-US (14:00-16:00)': list(range(14, 17)),
}

for sessao_nome, horas in sessoes.items():
    df_sessao = df[df['hora'].isin(horas)]
    taxa = df_sessao['AcertoDirecao'].mean() * 100
    n_casos = len(df_sessao)
    acertos = df_sessao['AcertoDirecao'].sum()
    
    emoji = "✅" if taxa > 50.2 else "⚠️"
    print(f"{emoji} {sessao_nome:25s} | {taxa:5.1f}% ({int(acertos)}/{n_casos} casos)")

print()

# =====================================================================
# 6. ESTATÍSTICAS DOS ERROS
# =====================================================================
print("=" * 100)
print("6️⃣ DISTRIBUIÇÃO DE ERROS")
print("=" * 100)
print()

print(f"Erro Mínimo: {df['ErroAbsoluto(%)'].min():.8f}%")
print(f"Erro Máximo: {df['ErroAbsoluto(%)'].max():.6f}%")
print(f"Erro Médio (MAE): {df['ErroAbsoluto(%)'].mean():.6f}%")
print(f"Erro Mediano: {df['ErroAbsoluto(%)'].median():.6f}%")
print(f"Desvio Padrão: {df['ErroAbsoluto(%)'].std():.6f}%")
print()

# Percentis
percentis = [10, 25, 50, 75, 90, 95, 99]
print("Percentis de Erro:")
for p in percentis:
    valor = df['ErroAbsoluto(%)'].quantile(p/100)
    print(f"  P{p:2d}: {valor:.6f}%")

print()

# =====================================================================
# 7. CASOS COM MELHOR E PIOR PERFORMANCE
# =====================================================================
print("=" * 100)
print("7️⃣ MELHORES E PIORES PREDIÇÕES")
print("=" * 100)
print()

print("TOP 5 MENORES ERROS (Predições mais precisas):")
print("-" * 100)
top_acertos = df.nsmallest(5, 'ErroAbsoluto(%)')
for idx, row in top_acertos.iterrows():
    print(f"  {row['Data']} | Real: {row['VariacaoReal(%)']:+.6f}% | Pred: {row['PredicaoModelo(%)']:+.6f}% | Erro: {row['ErroAbsoluto(%)']:.6f}%")

print()
print("TOP 5 MAIORES ERROS (Predições mais imprecisas):")
print("-" * 100)
top_erros = df.nlargest(5, 'ErroAbsoluto(%)')
for idx, row in top_erros.iterrows():
    print(f"  {row['Data']} | Real: {row['VariacaoReal(%)']:+.6f}% | Pred: {row['PredicaoModelo(%)']:+.6f}% | Erro: {row['ErroAbsoluto(%)']:.6f}%")

print()

# =====================================================================
# 8. RECOMENDAÇÕES
# =====================================================================
print("=" * 100)
print("8️⃣ RECOMENDAÇÕES PARA MELHORAR MODELO")
print("=" * 100)
print()

# Encontrar horário com melhor taxa
melhor_hora = ranking.index[0]
melhor_taxa = ranking.iloc[0]['TaxaAcerto'] * 100

print(f"🎯 RECOMENDAÇÃO 1: Focar em horário específico")
print(f"   - Melhor horário: {int(melhor_hora):02d}:00 com {melhor_taxa:.1f}% de acerto")
print(f"   - Reduzir volume, mas aumentar qualidade")
print()

# Analisar padrões
padroes_acima = padroes_df[padroes_df['taxa'] > 0.502]
if len(padroes_acima) > 0:
    print(f"🎯 RECOMENDAÇÃO 2: Usar padrões vencedores")
    for idx, p in padroes_acima.iterrows():
        print(f"   - {p['nome']:40s} ({p['taxa']*100:.1f}%)")
else:
    print(f"🎯 RECOMENDAÇÃO 2: Padrões vencedores não encontrados")
    print(f"   - Taxa de acerto está em nível de chance (50%)")
    print(f"   - Sugere-se mudar estratégia ou adicionar mais dados")

print()

print(f"🎯 RECOMENDAÇÃO 3: Considerar mudança de timeframe")
print(f"   - M15 atual tem muito ruído")
print(f"   - Tentar H1 ou H4 (menos volatilidade)")
print(f"   - Resultado esperado: +50.2% → 55-60%")
print()

print(f"🎯 RECOMENDAÇÃO 4: Adicionar contexto multiframe")
print(f"   - Adicionar indicadores H4/D1")
print(f"   - Exemplo: 'Preço em padrão bullish em H4'")
print(f"   - Combinações podem ter melhor previsão")
print()

print("=" * 100)
print("✨ ANÁLISE DE PADRÕES CONCLUÍDA")
print("=" * 100)
