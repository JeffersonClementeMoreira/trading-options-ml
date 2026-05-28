#!/usr/bin/env python3
"""
Backtesting Final Otimizado
- Usa as melhores combinações encontradas
- Testa com diferentes thresholds
- Gera CSV final com previsões validadas
"""

import csv
import numpy as np

class FinalBacktest:
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
    
    def calculate_advanced_score(self, row):
        """
        Calcula score mais sofisticado baseado em:
        1. Extremos de RSI (oversold/overbought)
        2. Alinhamento de médias móveis
        3. Confirmação MACD + Momentum
        4. Proximidade a nível crítico
        """
        score = 0
        
        # 1. RSI Extremo (peso: 30)
        if row['rsi'] < 30:  # Oversold = pode comprar
            score += 30
        elif row['rsi'] > 70:  # Overbought = pode vender
            score += 30
        else:
            score += max(0, 30 - abs(50 - row['rsi']) * 0.6)
        
        # 2. Alinhamento de Médias Móveis (peso: 25)
        # Preço acima de SMA20 E SMA20 > SMA50 = tendência de alta
        if row['price_above_sma20'] and row['sma20'] > row['sma50']:
            score += 25
        # Preço abaixo de SMA20 E SMA20 < SMA50 = tendência de baixa
        elif not row['price_above_sma20'] and row['sma20'] < row['sma50']:
            score += 25
        else:
            score += 10
        
        # 3. Confirmação MACD + Momentum (peso: 20)
        if row['macd_positive'] and row['momentum_positive']:
            score += 20
        elif not row['macd_positive'] and not row['momentum_positive']:
            score += 20
        else:
            score += 5
        
        # 4. ATR e Volume (peso: 25)
        # ATR não muito alto, volume acima da média
        if row['atr'] > 0 and row['atr'] < 0.001:  # ATR razoável
            score += 15
        if row['volume'] > 0:  # Volume existe
            score += 10
        
        return min(100, score)
    
    def backtest_strategy(self, min_score=50):
        """Executa backtest com scoring avançado"""
        trades = 0
        wins = 0
        total_pips = 0
        
        print(f"\n  Testando com score mínimo: {min_score}...")
        
        for row in self.data:
            # Calcular score
            score = self.calculate_advanced_score(row)
            
            # Aplicar threshold
            if score < min_score:
                continue
            
            trades += 1
            
            # Prever baseado na tendência RSI
            if row['rsi'] < 30:
                predicted = 'UP'
            elif row['rsi'] > 70:
                predicted = 'DOWN'
            else:
                predicted = 'UP' if row['macd_positive'] else 'DOWN'
            
            # Verificar acerto
            actual = row['target_direction']
            if predicted == actual:
                wins += 1
                total_pips += row['pips']
            else:
                total_pips -= row['pips']
            
            # Salvar resultado
            self.results.append({
                'timestamp': row['timestamp'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
                'sma20': row['sma20'],
                'sma50': row['sma50'],
                'rsi': round(row['rsi'], 2),
                'macd': row['macd'],
                'atr': row['atr'],
                'momentum': row['momentum'],
                'score': round(score, 2),
                'predicted_direction': predicted,
                'confidence': round(abs(row['rsi'] - 50) / 50 * 100, 2),
                'target_direction': actual,
                'pips': round(row['pips'], 1),
                'accuracy': 1 if predicted == actual else 0
            })
        
        if trades == 0:
            return None
        
        win_rate = (wins / trades * 100)
        avg_pips = total_pips / trades
        
        return {
            'min_score': min_score,
            'trades': trades,
            'wins': wins,
            'win_rate': win_rate,
            'total_pips': total_pips,
            'avg_pips': avg_pips
        }
    
    def optimize(self):
        """Testa diferentes thresholds e encontra o melhor"""
        print(f"\nOtimizando threshold para {self.symbol}...")
        
        best_result = None
        best_score = -float('inf')
        
        # Testar diferentes thresholds
        for threshold in range(20, 81, 5):
            # Limpar resultados anteriores
            self.results = []
            
            # Executar backteste
            result = self.backtest_strategy(threshold)
            
            if result is None:
                continue
            
            # Métrica de qualidade: win_rate * avg_pips (prioriza lucratividade)
            quality = result['win_rate'] * max(0.1, result['avg_pips'])
            
            if quality > best_score:
                best_score = quality
                best_result = result
        
        print(f"✅ Melhor threshold encontrado: {best_result['min_score']}")
        
        # Executar novamente com melhor threshold
        self.results = []
        self.backtest_strategy(best_result['min_score'])
        
        return best_result
    
    def save_results(self, output_file=None):
        """Salva resultados em CSV"""
        if output_file is None:
            output_file = f"/tmp/bt_final_{self.symbol}.csv"
        
        if not self.results:
            print("❌ Nenhum resultado para salvar")
            return False
        
        try:
            with open(output_file, 'w', newline='') as f:
                fieldnames = [
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'sma20', 'sma50', 'rsi', 'macd', 'atr', 'momentum',
                    'score', 'predicted_direction', 'confidence',
                    'target_direction', 'pips', 'accuracy'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
            
            print(f"✅ Resultados salvos em {output_file}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            return False
    
    def print_summary(self, result):
        """Imprime resumo"""
        if not result:
            return
        
        print(f"\n{'='*60}")
        print(f"RESULTADO FINAL - {self.symbol}")
        print(f"{'='*60}")
        print(f"Score mínimo:        {result['min_score']}")
        print(f"Total de trades:     {result['trades']}")
        print(f"Wins:                {result['wins']} ({result['win_rate']:.2f}%)")
        print(f"Total de pips:       {result['total_pips']:.1f}")
        print(f"Pips médios/trade:   {result['avg_pips']:.2f}")
        print(f"{'='*60}\n")

def main():
    # EURUSD
    eu = FinalBacktest("/tmp/bt_analysis_EURUSD.csv", "EURUSD")
    if eu.load_analysis():
        result = eu.optimize()
        eu.save_results()
        eu.print_summary(result)
    
    # GBPUSD
    gb = FinalBacktest("/tmp/bt_analysis_GBPUSD.csv", "GBPUSD")
    if gb.load_analysis():
        result = gb.optimize()
        gb.save_results()
        gb.print_summary(result)
    
    print("✅ Backtesting final concluído!")
    print(f"Arquivos gerados:")
    print(f"  /tmp/bt_final_EURUSD.csv")
    print(f"  /tmp/bt_final_GBPUSD.csv")

if __name__ == "__main__":
    main()
