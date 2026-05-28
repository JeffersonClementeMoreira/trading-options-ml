#!/usr/bin/env python3
"""
Validador - Compara previsões vs resultado real no D+1 às 14:00

Calcula:
- Taxa de acerto (% de previsões corretas)
- Pips esperados vs reais
- Confiança média
- Distribuição de resultados
"""

import json
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

class NextDayValidator:
    """Validar previsões contra resultados reais"""
    
    def __init__(self):
        self.predictions_file = "/tmp/nextday_predictions.json"
        self.results_file = "/tmp/nextday_results.json"
        self.predictions = defaultdict(list)
        self.results = defaultdict(list)
        
    def load_predictions(self):
        """Carregar previsões armazenadas"""
        try:
            with open(self.predictions_file, 'r') as f:
                data = json.load(f)
                for symbol in data:
                    self.predictions[symbol] = data[symbol]
        except:
            print("❌ Arquivo de previsões não encontrado")
    
    def add_real_result(self, symbol, actual_close_d1, prediction_time):
        """
        Adicionar resultado real
        
        symbol: 'EURUSD'
        actual_close_d1: 1.0865 (preço real às 14:00 do D+1)
        prediction_time: '2024-01-15 10:30:00'
        """
        # Encontrar previsão correspondente
        for pred in self.predictions[symbol]:
            if pred['prediction_time'] == prediction_time:
                # Comparar
                predicted_close = pred['predicted_close_d1']
                current_price = pred['current_price']
                
                # Calcular pips reais
                actual_pips = abs(actual_close_d1 - current_price) * 10000
                predicted_pips = pred['expected_pips']
                
                # Determinar se acertou direção
                actual_direction = 'UP' if actual_close_d1 > current_price else 'DOWN'
                predicted_direction = pred['predicted_direction']
                
                direction_correct = (actual_direction == predicted_direction)
                
                # Erro de previsão
                price_error = abs(actual_close_d1 - predicted_close)
                price_error_pct = (price_error / current_price) * 100
                
                result = {
                    'symbol': symbol,
                    'prediction_time': prediction_time,
                    'predicted_close': predicted_close,
                    'actual_close': actual_close_d1,
                    'predicted_direction': predicted_direction,
                    'actual_direction': actual_direction,
                    'direction_correct': direction_correct,
                    'predicted_pips': predicted_pips,
                    'actual_pips': actual_pips,
                    'price_error': price_error,
                    'price_error_pct': price_error_pct,
                    'confidence': pred['confidence'],
                    'validation_time': datetime.now().isoformat(),
                    'status': 'HIT' if direction_correct else 'MISS'
                }
                
                self.results[symbol].append(result)
                
                # Atualizar previsão
                pred['status'] = 'HIT' if direction_correct else 'MISS'
                pred['actual_close_d1'] = actual_close_d1
                
                return result
        
        return None
    
    def generate_report(self):
        """Gerar relatório de performance"""
        print("\n" + "╔" + "="*76 + "╗")
        print("║" + " "*20 + "📊 RELATÓRIO DE VALIDAÇÃO D+1 14:00" + " "*21 + "║")
        print("╚" + "="*76 + "╝\n")
        
        symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
        
        for symbol in symbols:
            results = self.results[symbol]
            
            if not results:
                print(f"📈 {symbol}: Sem resultados ainda\n")
                continue
            
            hits = sum(1 for r in results if r['status'] == 'HIT')
            misses = sum(1 for r in results if r['status'] == 'MISS')
            total = len(results)
            hit_rate = (hits / total * 100) if total > 0 else 0
            
            avg_confidence = np.mean([r['confidence'] for r in results])
            avg_actual_pips = np.mean([r['actual_pips'] for r in results])
            avg_predicted_pips = np.mean([r['predicted_pips'] for r in results])
            avg_error = np.mean([r['price_error_pct'] for r in results])
            
            print(f"📈 {symbol}")
            print("─" * 76)
            print(f"  Total de previsões: {total}")
            print(f"  Taxa de acerto (direção): {hit_rate:.1f}% ({hits} acertos, {misses} erros)")
            print(f"  Confiança média: {avg_confidence*100:.1f}%")
            print(f"  Pips reais (média): {avg_actual_pips:.1f}")
            print(f"  Pips previstos (média): {avg_predicted_pips:.1f}")
            print(f"  Erro de previsão de preço: {avg_error:.2f}%")
            
            # Breakdown por confiança
            high_conf = [r for r in results if r['confidence'] > 0.70]
            med_conf = [r for r in results if 0.50 <= r['confidence'] <= 0.70]
            low_conf = [r for r in results if r['confidence'] < 0.50]
            
            if high_conf:
                high_conf_hit_rate = sum(1 for r in high_conf if r['status'] == 'HIT') / len(high_conf) * 100
                print(f"  Confiança >70%: {high_conf_hit_rate:.1f}% acertos ({len(high_conf)} trades)")
            
            if med_conf:
                med_conf_hit_rate = sum(1 for r in med_conf if r['status'] == 'HIT') / len(med_conf) * 100
                print(f"  Confiança 50-70%: {med_conf_hit_rate:.1f}% acertos ({len(med_conf)} trades)")
            
            if low_conf:
                low_conf_hit_rate = sum(1 for r in low_conf if r['status'] == 'HIT') / len(low_conf) * 100
                print(f"  Confiança <50%: {low_conf_hit_rate:.1f}% acertos ({len(low_conf)} trades)")
            
            print()
    
    def demo_validation(self):
        """Demo: Validar com dados de exemplo"""
        print("\n" + "="*76)
        print("🧪 DEMO VALIDATION - Simular resultados reais")
        print("="*76 + "\n")
        
        # Carregar previsões
        self.load_predictions()
        
        # Simular resultados reais (D+1 às 14:00)
        demo_results = {
            'EURUSD': {
                'prediction_time': None,  # Será a primeira previsão
                'actual_close_d1': 1.08515
            },
            'GBPUSD': {
                'prediction_time': None,
                'actual_close_d1': 1.27390
            }
        }
        
        for symbol in ['EURUSD', 'GBPUSD']:
            if self.predictions[symbol]:
                # Usar primeira previsão
                pred = self.predictions[symbol][0]
                result = self.add_real_result(
                    symbol,
                    demo_results[symbol]['actual_close_d1'],
                    pred['prediction_time']
                )
                
                if result:
                    print(f"✅ {symbol}:")
                    print(f"   Previsão: {result['predicted_close']:.5f} ({result['predicted_direction']})")
                    print(f"   Real: {result['actual_close']:.5f} ({result['actual_direction']})")
                    print(f"   Resultado: {result['status']} | Pips: {result['actual_pips']:.1f}p")
                    print()
        
        # Gerar relatório
        self.generate_report()


def main():
    validator = NextDayValidator()
    
    print("\n" + "╔" + "="*76 + "╗")
    print("║" + " "*17 + "🎯 VALIDADOR - RESULTADOS D+1 ÀS 14:00" + " "*17 + "║")
    print("╚" + "="*76 + "╝")
    
    validator.demo_validation()
    
    print("\n" + "="*76)
    print("💾 Resultados armazenados em:", validator.results_file)
    print("="*76 + "\n")


if __name__ == '__main__':
    main()
