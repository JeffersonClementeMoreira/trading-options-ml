#!/usr/bin/env python3
"""
Análise de Combinações de Indicadores
- Testa diferentes combinações
- Identifica qual é a melhor para prever alvo
- Gera relatório de performance
"""

import csv
import numpy as np
from itertools import combinations
from collections import defaultdict

class CombinationAnalyzer:
    def __init__(self, csv_file, symbol):
        self.csv_file = csv_file
        self.symbol = symbol
        self.data = []
        self.results = {}
        
    def load_results(self):
        """Carrega resultados do BT anterior"""
        print(f"Carregando análise de {self.symbol}...")
        try:
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Converter valores numéricos
                    data_row = {
                        'timestamp': row['timestamp'],
                        'close': float(row['close']),
                        'sma20': float(row['sma20']),
                        'sma50': float(row['sma50']),
                        'rsi': float(row['rsi']),
                        'macd': float(row['macd']),
                        'atr': float(row['atr']),
                        'momentum': float(row['momentum']),
                        'price_above_sma20': int(row['price_above_sma20']),
                        'price_above_sma50': int(row['price_above_sma50']),
                        'rsi_oversold': int(row['rsi_oversold']),
                        'rsi_overbought': int(row['rsi_overbought']),
                        'macd_positive': int(row['macd_positive']),
                        'momentum_positive': int(row['momentum_positive']),
                        'predicted_direction': row['predicted_direction'],
                        'confidence': float(row['confidence']),
                        'target_direction': row['target_direction'],
                        'pips': float(row['pips']),
                        'accuracy': int(row['accuracy'])
                    }
                    self.data.append(data_row)
            
            print(f"✅ Carregados {len(self.data)} registros")
            return len(self.data) > 0
        except Exception as e:
            print(f"❌ Erro ao carregar: {e}")
            return False
    
    def test_combination(self, signals):
        """Testa uma combinação específica de sinais"""
        hits = 0
        total = 0
        total_pips = 0
        up_accuracy = 0
        down_accuracy = 0
        up_count = 0
        down_count = 0
        
        for row in self.data:
            # Calcular score baseado nos sinais selecionados
            score = 0
            for signal in signals:
                score += row[signal]
            
            score_pct = score / len(signals) * 100
            
            # Determinar previsão
            predicted = 'UP' if score_pct > 50 else 'DOWN'
            actual = row['target_direction']
            
            # Verificar acerto
            if predicted == actual:
                hits += 1
                total_pips += row['pips']
            else:
                total_pips -= row['pips']
            
            total += 1
            
            # Contabilizar por direção
            if actual == 'UP':
                up_count += 1
                if predicted == 'UP':
                    up_accuracy += 1
            else:
                down_count += 1
                if predicted == 'DOWN':
                    down_accuracy += 1
        
        win_rate = (hits / total * 100) if total > 0 else 0
        up_rate = (up_accuracy / up_count * 100) if up_count > 0 else 0
        down_rate = (down_accuracy / down_count * 100) if down_count > 0 else 0
        avg_pips = total_pips / total if total > 0 else 0
        
        return {
            'signals': signals,
            'total': total,
            'wins': hits,
            'win_rate': win_rate,
            'up_rate': up_rate,
            'down_rate': down_rate,
            'total_pips': total_pips,
            'avg_pips': avg_pips
        }
    
    def analyze(self):
        """Testa todas as combinações"""
        print(f"\nAnalisando combinações de indicadores para {self.symbol}...")
        
        signals = [
            'price_above_sma20',
            'price_above_sma50',
            'rsi_oversold',
            'rsi_overbought',
            'macd_positive',
            'momentum_positive'
        ]
        
        # Testar combinações de 1 a 6 sinais
        all_results = []
        
        for r in range(1, len(signals) + 1):
            print(f"  Testando combinações de {r} sinais...", end='')
            
            for combo in combinations(signals, r):
                result = self.test_combination(combo)
                all_results.append(result)
            
            print(f" ✅ {len(list(combinations(signals, r)))} combinações")
        
        # Ordenar por win rate
        all_results.sort(key=lambda x: x['win_rate'], reverse=True)
        
        # Salvar top 20 resultados
        self.results = all_results[:20]
        
        print(f"\n✅ Analisadas {len(all_results)} combinações")
    
    def print_results(self):
        """Imprime resultados ordenados"""
        if not self.results:
            return
        
        print(f"\n{'='*120}")
        print(f"TOP 20 COMBINAÇÕES - {self.symbol}")
        print(f"{'='*120}")
        print(f"{'Rank':<5} {'Win Rate':<12} {'Pips':<12} {'Avg Pips':<12} {'UP Rate':<10} {'DOWN Rate':<10} {'Sinais':<50}")
        print(f"{'-'*120}")
        
        for i, result in enumerate(self.results, 1):
            signal_names = ', '.join(result['signals'])
            print(f"{i:<5} {result['win_rate']:>10.2f}% {result['total_pips']:>10.1f} "
                  f"{result['avg_pips']:>10.2f} {result['up_rate']:>8.2f}% {result['down_rate']:>8.2f}% {signal_names:<50}")
        
        print(f"{'='*120}\n")
        
        # Mostrar melhor resultado
        best = self.results[0]
        print(f"🏆 MELHOR COMBINAÇÃO:")
        print(f"   Sinais: {', '.join(best['signals'])}")
        print(f"   Win Rate: {best['win_rate']:.2f}%")
        print(f"   Total de pips: {best['total_pips']:.1f}")
        print(f"   Pips médios: {best['avg_pips']:.2f}")
        print(f"   Taxa UP: {best['up_rate']:.2f}%")
        print(f"   Taxa DOWN: {best['down_rate']:.2f}%")
        print()

def main():
    # Analisar EURUSD
    eu = CombinationAnalyzer("/tmp/bt_analysis_EURUSD.csv", "EURUSD")
    if eu.load_results():
        eu.analyze()
        eu.print_results()
    
    # Analisar GBPUSD
    gb = CombinationAnalyzer("/tmp/bt_analysis_GBPUSD.csv", "GBPUSD")
    if gb.load_results():
        gb.analyze()
        gb.print_results()

if __name__ == "__main__":
    main()
