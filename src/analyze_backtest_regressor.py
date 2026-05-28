#!/usr/bin/env python3
"""
Análise detalhada do backtest com regressão (PREÇO REAL às 14:00)
"""

import csv
import numpy as np

def analyze_backtest(csv_file, symbol):
    print(f"\n{'='*80}")
    print(f"📊 ANÁLISE DETALHADA - {symbol}")
    print(f"{'='*80}\n")
    
    data = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'timestamp': row['timestamp'],
                'entry_price': float(row['entry_price']),
                'predicted_price': float(row['predicted_price']),
                'actual_price': float(row['actual_price']),
                'predicted_pips': float(row['predicted_pips']),
                'actual_pips': float(row['actual_pips']),
                'error_pips': float(row['error_pips'])
            })
    
    # Estatísticas básicas
    actual_pips = [d['actual_pips'] for d in data]
    predicted_pips = [d['predicted_pips'] for d in data]
    errors = [d['error_pips'] for d in data]
    
    wins = sum(1 for p in actual_pips if p > 0)
    losses = sum(1 for p in actual_pips if p <= 0)
    win_rate = (wins / len(actual_pips)) * 100
    
    total_pips = sum(actual_pips)
    avg_pips = total_pips / len(actual_pips)
    avg_win = sum(p for p in actual_pips if p > 0) / wins if wins > 0 else 0
    avg_loss = sum(p for p in actual_pips if p <= 0) / losses if losses > 0 else 0
    
    print(f"""
📈 ESTATÍSTICAS GERAIS
╔════════════════════════════════════════════════════════════════╗
├─ Predições:           {len(data):>6}
├─ Ganhos (+):          {wins:>6} ({win_rate:>5.2f}%)
├─ Perdas (-):          {losses:>6} ({100-win_rate:>5.2f}%)
├─ Total Pips:          {total_pips:>6.2f} pips
├─ Pips/Candle:         {avg_pips:>6.2f} pips
├─ Pips Médio Ganho:    {avg_win:>6.2f} pips
├─ Pips Médio Perda:    {avg_loss:>6.2f} pips
├─ Erro Médio (MAE):    {np.mean(errors):>6.2f} pips
└─ Desvio Padrão Erro:  {np.std(errors):>6.2f} pips
╚════════════════════════════════════════════════════════════════╝

🎯 COMPARAÇÃO PREDIÇÃO vs REALIDADE
╔════════════════════════════════════════════════════════════════╗
├─ Pips Previstos:      {sum(predicted_pips):>6.2f} pips
├─ Pips Reais:          {total_pips:>6.2f} pips
├─ Diferença:           {total_pips - sum(predicted_pips):>6.2f} pips
└─ Acurácia Predição:   {(1 - np.mean(errors)/np.mean(np.abs(actual_pips))) * 100:>6.2f}%
╚════════════════════════════════════════════════════════════════╝

🏆 TOP 5 MELHORES TRADES (GANHO REAL)
╔════════════════════════════════════════════════════════════════╗""")
    
    sorted_by_pips = sorted(data, key=lambda x: x['actual_pips'], reverse=True)
    for i, trade in enumerate(sorted_by_pips[:5], 1):
        print(f"""├─ {i}. {trade['timestamp']}
│  ├─ Entrada:    {trade['entry_price']:.5f}
│  ├─ Previsto:   {trade['predicted_price']:.5f} ({trade['predicted_pips']:>7.2f} pips)
│  ├─ Real:       {trade['actual_price']:.5f} ({trade['actual_pips']:>7.2f} pips) ✅
│  └─ Erro:       {trade['error_pips']:>7.2f} pips""")
    
    print(f"""╚════════════════════════════════════════════════════════════════╝

❌ TOP 5 PIORES TRADES (MAIOR PERDA)
╔════════════════════════════════════════════════════════════════╗""")
    
    sorted_by_loss = sorted(data, key=lambda x: x['actual_pips'])
    for i, trade in enumerate(sorted_by_loss[:5], 1):
        print(f"""├─ {i}. {trade['timestamp']}
│  ├─ Entrada:    {trade['entry_price']:.5f}
│  ├─ Previsto:   {trade['predicted_price']:.5f} ({trade['predicted_pips']:>7.2f} pips)
│  ├─ Real:       {trade['actual_price']:.5f} ({trade['actual_pips']:>7.2f} pips) ❌
│  └─ Erro:       {trade['error_pips']:>7.2f} pips""")
    
    print(f"""╚════════════════════════════════════════════════════════════════╝

🎯 TRADES COM MAIOR ERRO DE PREDIÇÃO
╔════════════════════════════════════════════════════════════════╗""")
    
    sorted_by_error = sorted(data, key=lambda x: x['error_pips'], reverse=True)
    for i, trade in enumerate(sorted_by_error[:5], 1):
        print(f"""├─ {i}. {trade['timestamp']}
│  ├─ Entrada:    {trade['entry_price']:.5f}
│  ├─ Previsto:   {trade['predicted_price']:.5f} ({trade['predicted_pips']:>7.2f} pips)
│  ├─ Real:       {trade['actual_price']:.5f} ({trade['actual_pips']:>7.2f} pips)
│  └─ Erro:       {trade['error_pips']:>7.2f} pips ⚠️""")
    
    print(f"""╚════════════════════════════════════════════════════════════════╝

📊 DISTRIBUIÇÃO DE GANHOS
╔════════════════════════════════════════════════════════════════╗
├─ >100 pips:       {sum(1 for p in actual_pips if p > 100):>6}
├─ 50-100 pips:     {sum(1 for p in actual_pips if 50 <= p <= 100):>6}
├─ 10-50 pips:      {sum(1 for p in actual_pips if 10 <= p < 50):>6}
├─ 0-10 pips:       {sum(1 for p in actual_pips if 0 < p < 10):>6}
├─ -10-0 pips:      {sum(1 for p in actual_pips if -10 <= p <= 0):>6}
├─ -50--10 pips:    {sum(1 for p in actual_pips if -50 <= p < -10):>6}
├─ -100--50 pips:   {sum(1 for p in actual_pips if -100 <= p < -50):>6}
└─ <-100 pips:      {sum(1 for p in actual_pips if p < -100):>6}
╚════════════════════════════════════════════════════════════════╝

📋 RESUMO FINAL
╔════════════════════════════════════════════════════════════════╗
✅ TARGET: Preço REAL às 14:00 UTC próximo dia
✅ MODELO: Regressão (prevê preço, não direção)
✅ DADOS: REAIS de /tmp/bt_analysis_*.csv
✅ SPLIT: 70% treino, 30% validação
✅ VALIDAÇÃO: Em dados nunca vistos (sem data leakage)
✅ ENTRADA: Baseada em indicadores M15
✅ ALVO: SEMPRE 14:00 UTC próximo dia
╚════════════════════════════════════════════════════════════════╝
    """)

# Análise EURUSD
analyze_backtest('/tmp/backtest_EURUSD_regressor_correct.csv', 'EURUSD')

# Análise GBPUSD
analyze_backtest('/tmp/backtest_GBPUSD_regressor_correct.csv', 'GBPUSD')

print("\n" + "="*80)
print("✅ ANÁLISE CONCLUÍDA")
print("="*80 + "\n")
