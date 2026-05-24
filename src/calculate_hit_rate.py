#!/usr/bin/env python3
"""
Calcula o hit rate (percentual de acerto) dos sinais
Compara ação recomendada vs movimento real do preço
"""

import csv
from pathlib import Path


def calculate_hit_rate(csv_path):
    """
    Calcula percentual de acerto dos sinais
    
    Lógica:
    - CALL: correto se next_day_close > current_close (preço subiu)
    - PUT: correto se next_day_close < current_close (preço desceu)
    - STRANGLE: correto se preço se moveu (|% change| > threshold)
    - NO_TRADE: sempre correto (não entrou)
    """
    
    signals = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        signals = list(reader)
    
    if not signals:
        print("❌ Nenhum sinal para analisar")
        return
    
    print("\n" + "="*80)
    print("📊 CÁLCULO DE HIT RATE (Percentual de Acerto)")
    print("="*80 + "\n")
    
    # Análise por ação
    stats = {
        'CALL': {'total': 0, 'correct': 0},
        'PUT': {'total': 0, 'correct': 0},
        'STRANGLE': {'total': 0, 'correct': 0},
        'NO_TRADE': {'total': 0, 'correct': 0},
    }
    
    # Análise por horário
    hourly_stats = {
        '18:00:00': {'total': 0, 'correct': 0},
        '19:00:00': {'total': 0, 'correct': 0},
        '20:00:00': {'total': 0, 'correct': 0},
    }
    
    strangle_threshold = 0.0005  # 0.05% de movimento para STRANGLE
    
    for signal in signals:
        try:
            action = signal['action']
            entry_price = float(signal['current_close'])
            exit_price = float(signal['next_day_close'])
            entry_time = signal['entry_time']
            
            # Calcular movimento
            price_change = exit_price - entry_price
            pct_change = price_change / entry_price
            
            # Verificar se sinal foi correto
            is_correct = False
            
            if action == 'CALL':
                is_correct = price_change > 0  # Preço deve subir
            elif action == 'PUT':
                is_correct = price_change < 0  # Preço deve descer
            elif action == 'STRANGLE':
                is_correct = abs(price_change) > strangle_threshold  # Qualquer movimento
            elif action == 'NO_TRADE':
                is_correct = True  # Sempre correto (não entrou)
            
            # Atualizar estatísticas
            stats[action]['total'] += 1
            if is_correct:
                stats[action]['correct'] += 1
            
            hourly_stats[entry_time]['total'] += 1
            if is_correct:
                hourly_stats[entry_time]['correct'] += 1
                
        except Exception as e:
            print(f"❌ Erro processando sinal: {e}")
            continue
    
    # Exibir resultados por ação
    print("🎯 TAXA DE ACERTO POR AÇÃO")
    print("-" * 80)
    
    total_all = 0
    correct_all = 0
    
    for action in ['CALL', 'PUT', 'STRANGLE', 'NO_TRADE']:
        total = stats[action]['total']
        correct = stats[action]['correct']
        
        if total > 0:
            hit_rate = 100 * correct / total
            total_all += total
            correct_all += correct
            
            print(f"\n{action}:")
            print(f"  Total:   {total:4d} sinais")
            print(f"  Corretos: {correct:4d} sinais")
            print(f"  Hit Rate: {hit_rate:6.2f}%")
        else:
            print(f"\n{action}: 0 sinais")
    
    # Taxa geral
    print("\n" + "="*80)
    if total_all > 0:
        overall_hit_rate = 100 * correct_all / total_all
        print(f"📈 TAXA GERAL DE ACERTO: {overall_hit_rate:.2f}%")
        print(f"   {correct_all} corretos de {total_all} sinais")
    print("="*80)
    
    # Por horário
    print("\n🕐 TAXA DE ACERTO POR HORÁRIO DE ENTRADA")
    print("-" * 80)
    
    for hour in ['18:00:00', '19:00:00', '20:00:00']:
        total = hourly_stats[hour]['total']
        correct = hourly_stats[hour]['correct']
        
        if total > 0:
            hit_rate = 100 * correct / total
            print(f"\n{hour}:")
            print(f"  Total:   {total:4d} sinais")
            print(f"  Corretos: {correct:4d} sinais")
            print(f"  Hit Rate: {hit_rate:6.2f}%")
        else:
            print(f"\n{hour}: 0 sinais")
    
    print("\n" + "="*80)
    
    # Resumo executivo
    print("\n📌 RESUMO EXECUTIVO")
    print("-" * 80)
    print(f"✅ Total de sinais analisados: {total_all}")
    print(f"✅ Sinais corretos: {correct_all}")
    print(f"✅ Taxa de acerto geral: {overall_hit_rate:.2f}%")
    print(f"✅ Benchmark: 50% (lançamento de moeda)")
    print(f"✅ Resultado: {'ACIMA do benchmark!' if overall_hit_rate > 50 else 'ABAIXO do benchmark'}")
    print("="*80 + "\n")
    
    return {
        'overall_hit_rate': overall_hit_rate,
        'total': total_all,
        'correct': correct_all,
        'by_action': stats,
        'by_hour': hourly_stats,
    }


if __name__ == "__main__":
    csv_path = "predictions/realtime_analysis.csv"
    
    if not Path(csv_path).exists():
        print(f"❌ Arquivo não encontrado: {csv_path}")
        print("Execute primeiro: python3 realtime_analysis.py")
        exit(1)
    
    results = calculate_hit_rate(csv_path)
