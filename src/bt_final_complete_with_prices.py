#!/usr/bin/env python3
"""
Backtesting Final com Preço Predicto
- Adiciona: timestamp alvo, preço predicto, preço real às 14:00
- Retorna CSV completo para validação
"""

import csv
import numpy as np
from datetime import datetime, timedelta

class FinalBacktestWithPrice:
    def __init__(self, csv_file, symbol):
        self.csv_file = csv_file
        self.symbol = symbol
        self.data = []
        self.results = []
        
    def load_analysis(self):
        """Carrega análise anterior"""
        print(f"Carregando análise de {self.symbol}...")
        try:
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.data.append({
                        'timestamp': row['timestamp'],
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': int(row['volume']),
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
                    })
            
            print(f"✅ Carregados {len(self.data)} registros")
            return True
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    def find_target_candle(self, idx):
        """Encontra o candle do próximo dia às 14:00"""
        current_dt = datetime.fromisoformat(self.data[idx]['timestamp'])
        target_date = current_dt.date() + timedelta(days=1)
        target_dt = datetime.combine(target_date, datetime.min.time().replace(hour=14))
        
        for i in range(idx + 1, min(idx + 100, len(self.data))):
            candle_dt = datetime.fromisoformat(self.data[i]['timestamp'])
            if candle_dt == target_dt:
                return i
        return None
    
    def estimate_target_price(self, current_row, target_row):
        """
        Estima o preço predicto baseado em:
        1. Direção prevista
        2. ATR (volatilidade esperada)
        3. Momentum atual
        """
        current_close = current_row['close']
        atr = current_row['atr']
        momentum = current_row['momentum']
        rsi = current_row['rsi']
        
        # Base: preço atual
        estimated_price = current_close
        
        # Ajuste 1: Momentum
        if momentum > 0:
            estimated_price += abs(momentum) * 0.5
        else:
            estimated_price -= abs(momentum) * 0.5
        
        # Ajuste 2: RSI extremo
        if rsi < 30:  # Oversold, tendência de alta
            estimated_price += atr * 2
        elif rsi > 70:  # Overbought, tendência de baixa
            estimated_price -= atr * 2
        
        # Clampar entre high e low do dia
        # (não pode ficar muito fora da volatilidade esperada)
        high_limit = current_close + atr * 5
        low_limit = current_close - atr * 5
        
        estimated_price = max(low_limit, min(high_limit, estimated_price))
        
        return estimated_price
    
    def calculate_advanced_score(self, row):
        """Calcula score sofisticado"""
        score = 0
        
        if row['rsi'] < 30:
            score += 30
        elif row['rsi'] > 70:
            score += 30
        else:
            score += max(0, 30 - abs(50 - row['rsi']) * 0.6)
        
        if row['price_above_sma20'] and row['sma20'] > row['sma50']:
            score += 25
        elif not row['price_above_sma20'] and row['sma20'] < row['sma50']:
            score += 25
        else:
            score += 10
        
        if row['macd_positive'] and row['momentum_positive']:
            score += 20
        elif not row['macd_positive'] and not row['momentum_positive']:
            score += 20
        else:
            score += 5
        
        if row['atr'] > 0 and row['atr'] < 0.001:
            score += 15
        if row['volume'] > 0:
            score += 10
        
        return min(100, score)
    
    def backtest_strategy(self, min_score=50):
        """Executa backtest com informações completas"""
        trades = 0
        
        for idx, row in enumerate(self.data):
            # Encontrar candle alvo (próximo dia 14:00)
            target_idx = self.find_target_candle(idx)
            if target_idx is None:
                continue
            
            # Calcular score
            score = self.calculate_advanced_score(row)
            
            # Aplicar threshold
            if score < min_score:
                continue
            
            trades += 1
            target_row = self.data[target_idx]
            
            # Previsão de direção
            if row['rsi'] < 30:
                predicted = 'UP'
            elif row['rsi'] > 70:
                predicted = 'DOWN'
            else:
                predicted = 'UP' if row['macd_positive'] else 'DOWN'
            
            # Preço predicto (estimado)
            predicted_price = self.estimate_target_price(row, target_row)
            
            # Preço real às 14:00
            actual_price = target_row['close']
            
            # Verificar acerto
            actual = row['target_direction']
            accuracy = 1 if predicted == actual else 0
            
            # Calcular pips da previsão
            predicted_pips = (actual_price - predicted_price) * 10000
            
            # Salvar resultado
            self.results.append({
                'analise_timestamp': row['timestamp'],
                'analise_close': round(row['close'], 6),
                'analise_rsi': round(row['rsi'], 2),
                'analise_sma20': round(row['sma20'], 6),
                'analise_sma50': round(row['sma50'], 6),
                'analise_score': round(score, 2),
                'predicted_direction': predicted,
                'predicted_price': round(predicted_price, 6),
                'confidence': round(abs(row['rsi'] - 50) / 50 * 100, 2),
                'target_timestamp': target_row['timestamp'],
                'target_close': round(actual_price, 6),
                'target_direction': actual,
                'pips_real': round(row['pips'], 1),
                'pips_estimado': round(predicted_pips, 1),
                'accuracy': accuracy
            })
        
        return trades
    
    def optimize(self):
        """Testa diferentes thresholds"""
        print(f"\nOtimizando threshold para {self.symbol}...")
        
        best_result = None
        best_score = -float('inf')
        
        for threshold in range(20, 81, 5):
            self.results = []
            trades = self.backtest_strategy(threshold)
            
            if trades == 0:
                continue
            
            # Métrica de qualidade
            accuracy_count = sum(1 for r in self.results if r['accuracy'] == 1)
            win_rate = accuracy_count / trades * 100
            total_pips = sum(float(r['pips_real']) for r in self.results)
            quality = win_rate * max(0.1, total_pips / trades)
            
            if quality > best_score:
                best_score = quality
                best_result = {'threshold': threshold, 'trades': trades, 'win_rate': win_rate}
        
        print(f"✅ Melhor threshold: {best_result['threshold']} ({best_result['trades']} trades, {best_result['win_rate']:.2f}% acerto)")
        
        # Executar novamente com melhor threshold
        self.results = []
        self.backtest_strategy(best_result['threshold'])
        
        return best_result
    
    def save_results(self, output_file=None):
        """Salva resultados em CSV"""
        if output_file is None:
            output_file = f"/tmp/bt_final_complete_{self.symbol}.csv"
        
        if not self.results:
            print("❌ Nenhum resultado para salvar")
            return False
        
        try:
            with open(output_file, 'w', newline='') as f:
                fieldnames = [
                    'analise_timestamp', 'analise_close', 'analise_rsi', 
                    'analise_sma20', 'analise_sma50', 'analise_score',
                    'predicted_direction', 'predicted_price', 'confidence',
                    'target_timestamp', 'target_close', 'target_direction',
                    'pips_real', 'pips_estimado', 'accuracy'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
            
            print(f"✅ Resultados salvos em {output_file}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            return False
    
    def print_summary(self):
        """Imprime resumo"""
        if not self.results:
            return
        
        wins = sum(1 for r in self.results if r['accuracy'] == 1)
        total = len(self.results)
        win_rate = (wins / total * 100) if total > 0 else 0
        total_pips = sum(float(r['pips_real']) for r in self.results)
        avg_pips = total_pips / total if total > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"RESULTADO FINAL - {self.symbol}")
        print(f"{'='*70}")
        print(f"Total de trades:     {total}")
        print(f"Wins:                {wins} ({win_rate:.2f}%)")
        print(f"Total de pips:       {total_pips:.1f}")
        print(f"Pips médios/trade:   {avg_pips:.2f}")
        print(f"{'='*70}\n")

def main():
    # EURUSD
    eu = FinalBacktestWithPrice("/tmp/bt_analysis_EURUSD.csv", "EURUSD")
    if eu.load_analysis():
        eu.optimize()
        eu.save_results()
        eu.print_summary()
    
    # GBPUSD
    gb = FinalBacktestWithPrice("/tmp/bt_analysis_GBPUSD.csv", "GBPUSD")
    if gb.load_analysis():
        gb.optimize()
        gb.save_results()
        gb.print_summary()
    
    print("✅ Backtesting com preços predictos concluído!")
    print(f"\nArquivos gerados:")
    print(f"  /tmp/bt_final_complete_EURUSD.csv")
    print(f"  /tmp/bt_final_complete_GBPUSD.csv")
    print(f"\nColunas disponíveis:")
    print(f"  - analise_timestamp: horário da análise")
    print(f"  - analise_close: preço de fechamento na análise")
    print(f"  - analise_rsi/sma20/sma50: indicadores na análise")
    print(f"  - predicted_direction: previsão (UP/DOWN)")
    print(f"  - predicted_price: preço predicto para 14:00")
    print(f"  - target_timestamp: horário real de fechamento (14:00 próximo dia)")
    print(f"  - target_close: preço real de fechamento às 14:00")
    print(f"  - pips_real: pips reais do movimento")
    print(f"  - pips_estimado: pips baseado no preço predicto")
    print(f"  - accuracy: 1=acertou, 0=errou")

if __name__ == "__main__":
    main()
