#!/usr/bin/env python3
"""
Otimizador de threshold para melhorar acurácia dos sinais
Testa diferentes confidence_thresholds para encontrar o melhor balanço
"""

import csv
import sys
sys.path.insert(0, '/home/ubuntu/pessoal/options/src')

from datetime import datetime
from pathlib import Path
from trading_decision import TradingDecisionEngine, TradeAction


def calculate_metrics(signals, threshold):
    """Calcula métricas para um threshold específico"""
    
    put_sell = [r for r in signals if r['action'] == 'PUT_SELL' and float(r['confidence']) >= threshold]
    call_sell = [r for r in signals if r['action'] == 'CALL_SELL' and float(r['confidence']) >= threshold]
    strangle = [r for r in signals if r['action'] == 'STRANGLE' and float(r['confidence']) >= threshold]
    no_trade = [r for r in signals if r['action'] == 'NO_TRADE' and float(r['confidence']) >= threshold]
    
    total_signals = len(put_sell) + len(call_sell) + len(strangle) + len(no_trade)
    
    # PUT_SELL: acerta quando preço sobe
    put_hits = len([r for r in put_sell if r['actual_direction'] == 'UP'])
    put_acc = put_hits / len(put_sell) if put_sell else 0
    
    # CALL_SELL: acerta quando preço desce
    call_hits = len([r for r in call_sell if r['actual_direction'] == 'DOWN'])
    call_acc = call_hits / len(call_sell) if call_sell else 0
    
    # Acurácia combinada de sinais direcionados
    combined_acc = (put_hits + call_hits) / (len(put_sell) + len(call_sell)) if (put_sell or call_sell) else 0
    
    # Esperado vs Realizado
    up_signals = len([r for r in signals if float(r['confidence']) >= threshold and r['actual_direction'] == 'UP'])
    down_signals = len([r for r in signals if float(r['confidence']) >= threshold and r['actual_direction'] == 'DOWN'])
    
    return {
        'threshold': threshold,
        'total': total_signals,
        'put_sell': len(put_sell),
        'call_sell': len(call_sell),
        'strangle': len(strangle),
        'put_acc': put_acc,
        'call_acc': call_acc,
        'combined_acc': combined_acc,
        'up_actual': up_signals,
        'down_actual': down_signals,
    }


if __name__ == "__main__":
    print("\n" + "="*100)
    print("🎯 OTIMIZADOR DE THRESHOLD PARA MELHORAR ACURÁCIA")
    print("="*100 + "\n")
    
    # Carregar dados
    with open('/home/ubuntu/pessoal/options/predictions/realtime_analysis.csv', 'r') as f:
        reader = csv.DictReader(f)
        signals = list(reader)
    
    print(f"📊 Total de sinais: {len(signals)}\n")
    
    print("-" * 100)
    print(f"{'Threshold':<12} {'Total':<8} {'PUT_SELL':<10} {'CALL_SELL':<10} {'Acurácia Combinada':<20}")
    print("-" * 100)
    
    # Testar thresholds de 0.40 a 0.80 em intervalos de 0.05
    results = []
    for threshold in [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
        metrics = calculate_metrics(signals, threshold)
        results.append(metrics)
        
        acc_pct = metrics['combined_acc'] * 100 if metrics['combined_acc'] > 0 else 0
        
        print(f"{metrics['threshold']:<12.2f} {metrics['total']:<8} "
              f"{metrics['put_sell']:<10} {metrics['call_sell']:<10} {acc_pct:>6.1f}%")
    
    print("\n" + "="*100)
    print("📈 ANÁLISE DETALHADA")
    print("="*100 + "\n")
    
    for result in results:
        if result['put_sell'] + result['call_sell'] == 0:
            continue
            
        print(f"Threshold: {result['threshold']:.2f}")
        print(f"  PUT_SELL:  {result['put_sell']:3d} sinais  → Acerto: {result['put_acc']*100:5.1f}%")
        print(f"  CALL_SELL: {result['call_sell']:3d} sinais  → Acerto: {result['call_acc']*100:5.1f}%")
        print(f"  COMBINADO: {result['combined_acc']*100:5.1f}%")
        print(f"  UP real:   {result['up_actual']:3d}")
        print(f"  DOWN real: {result['down_actual']:3d}")
        print()
    
    # Encontrar melhor threshold
    best = max([r for r in results if r['put_sell'] + r['call_sell'] > 0], 
               key=lambda x: x['combined_acc'])
    
    print("="*100)
    print("✅ RECOMENDAÇÃO")
    print("="*100 + "\n")
    print(f"Melhor threshold: {best['threshold']:.2f}")
    print(f"  • Acurácia combinada: {best['combined_acc']*100:.1f}%")
    print(f"  • PUT_SELL: {best['put_sell']} sinais")
    print(f"  • CALL_SELL: {best['call_sell']} sinais")
    print(f"\nPróximo passo:")
    print(f"  Alterar em src/realtime_analysis.py:")
    print(f"    confidence_threshold=0.40  →  confidence_threshold={best['threshold']:.2f}")
