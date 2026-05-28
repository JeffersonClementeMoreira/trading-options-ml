#!/usr/bin/env python3
"""
Exemplos práticos de como usar os dados gerados no BT
"""

import csv

def example_1_view_predictions():
    """Exemplo 1: Ver previsões dos últimos 100 trades"""
    print("=" * 80)
    print("EXEMPLO 1: Últimas 100 Previsões de EURUSD")
    print("=" * 80)
    print(f"{'Timestamp':<25} {'Close':<10} {'RSI':<8} {'Score':<8} {'Pred':<8} {'Target':<8} {'Pips':<8}")
    print("-" * 80)
    
    count = 0
    with open('/tmp/bt_final_EURUSD.csv', 'r') as f:
        reader = list(csv.DictReader(f))
        for row in reader[-100:]:
            print(f"{row['timestamp']:<25} {row['close']:<10} {row['rsi']:<8} {row['score']:<8} "
                  f"{row['predicted_direction']:<8} {row['target_direction']:<8} {row['pips']:<8}")
            count += 1
    
    print(f"\nTotal exibido: {count} previsões")

def example_2_accuracy_analysis():
    """Exemplo 2: Calcular taxa de acerto por faixa de score"""
    print("\n" + "=" * 80)
    print("EXEMPLO 2: Acurácia por Faixa de Score (GBPUSD)")
    print("=" * 80)
    
    score_bins = {
        '80-90': {'hits': 0, 'total': 0},
        '90-100': {'hits': 0, 'total': 0}
    }
    
    with open('/tmp/bt_final_GBPUSD.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            score = float(row['score'])
            accuracy = int(row['accuracy'])
            
            if 80 <= score < 90:
                score_bins['80-90']['total'] += 1
                score_bins['80-90']['hits'] += accuracy
            elif 90 <= score <= 100:
                score_bins['90-100']['total'] += 1
                score_bins['90-100']['hits'] += accuracy
    
    print(f"\n{'Score Range':<15} {'Trades':<10} {'Wins':<10} {'Win Rate':<10}")
    print("-" * 45)
    for range_name, data in score_bins.items():
        if data['total'] > 0:
            win_rate = (data['hits'] / data['total'] * 100)
            print(f"{range_name:<15} {data['total']:<10} {data['hits']:<10} {win_rate:.2f}%")

def example_3_directional_analysis():
    """Exemplo 3: Análise por direção de previsão"""
    print("\n" + "=" * 80)
    print("EXEMPLO 3: Análise por Direção (EURUSD)")
    print("=" * 80)
    
    directions = {'UP': {'hits': 0, 'total': 0, 'pips': 0},
                  'DOWN': {'hits': 0, 'total': 0, 'pips': 0}}
    
    with open('/tmp/bt_final_EURUSD.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pred = row['predicted_direction']
            accuracy = int(row['accuracy'])
            pips = float(row['pips'])
            
            directions[pred]['total'] += 1
            directions[pred]['hits'] += accuracy
            if accuracy:
                directions[pred]['pips'] += pips
    
    print(f"\n{'Direction':<10} {'Trades':<10} {'Wins':<10} {'Win Rate':<10} {'Pips':<10}")
    print("-" * 50)
    for direction, data in directions.items():
        if data['total'] > 0:
            win_rate = (data['hits'] / data['total'] * 100)
            print(f"{direction:<10} {data['total']:<10} {data['hits']:<10} {win_rate:.2f}% {data['pips']:.1f}")

def example_4_confidence_analysis():
    """Exemplo 4: Análise de confiança"""
    print("\n" + "=" * 80)
    print("EXEMPLO 4: Acurácia por Nível de Confiança (GBPUSD)")
    print("=" * 80)
    
    confidence_bins = {
        '0-25%': {'hits': 0, 'total': 0},
        '25-50%': {'hits': 0, 'total': 0},
        '50-75%': {'hits': 0, 'total': 0},
        '75-100%': {'hits': 0, 'total': 0}
    }
    
    with open('/tmp/bt_final_GBPUSD.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            conf = float(row['confidence'])
            accuracy = int(row['accuracy'])
            
            if conf < 25:
                bin_key = '0-25%'
            elif conf < 50:
                bin_key = '25-50%'
            elif conf < 75:
                bin_key = '50-75%'
            else:
                bin_key = '75-100%'
            
            confidence_bins[bin_key]['total'] += 1
            confidence_bins[bin_key]['hits'] += accuracy
    
    print(f"\n{'Confidence Range':<15} {'Trades':<10} {'Wins':<10} {'Win Rate':<10}")
    print("-" * 45)
    for range_name, data in confidence_bins.items():
        if data['total'] > 0:
            win_rate = (data['hits'] / data['total'] * 100)
            print(f"{range_name:<15} {data['total']:<10} {data['hits']:<10} {win_rate:.2f}%")

def example_5_profitability():
    """Exemplo 5: Análise de lucratividade"""
    print("\n" + "=" * 80)
    print("EXEMPLO 5: Análise de Lucratividade")
    print("=" * 80)
    
    for symbol, filename in [('EURUSD', '/tmp/bt_final_EURUSD.csv'), 
                               ('GBPUSD', '/tmp/bt_final_GBPUSD.csv')]:
        wins_pips = 0
        losses_pips = 0
        win_count = 0
        loss_count = 0
        
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pips = float(row['pips'])
                accuracy = int(row['accuracy'])
                
                if accuracy:
                    wins_pips += pips
                    win_count += 1
                else:
                    losses_pips += pips
                    loss_count += 1
        
        total_pips = wins_pips + losses_pips
        avg_win = wins_pips / win_count if win_count > 0 else 0
        avg_loss = losses_pips / loss_count if loss_count > 0 else 0
        
        print(f"\n{symbol}:")
        print(f"  Wins: {win_count} trades = {wins_pips:.1f} pips (avg {avg_win:.2f}/trade)")
        print(f"  Losses: {loss_count} trades = {losses_pips:.1f} pips (avg {avg_loss:.2f}/trade)")
        print(f"  TOTAL: {total_pips:.1f} pips")
        print(f"  Profit Factor: {wins_pips / abs(losses_pips):.2f}" if losses_pips != 0 else "")

if __name__ == "__main__":
    example_1_view_predictions()
    example_2_accuracy_analysis()
    example_3_directional_analysis()
    example_4_confidence_analysis()
    example_5_profitability()
    
    print("\n" + "=" * 80)
    print("✅ Exemplos executados com sucesso!")
    print("=" * 80)
