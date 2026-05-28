#!/usr/bin/env python3
"""
BACKTEST COM DADOS REAIS - Ensemble Voting
Gera CSV com todas as predições, confiança, e resultado real
Valida predições contra movimento real do candle
"""

import csv
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class EnsembleBacktest:
    def __init__(self, csv_file, model_file, scaler_file, symbol):
        self.csv_file = csv_file
        self.model_file = model_file
        self.scaler_file = scaler_file
        self.symbol = symbol
        self.feature_names = ['rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum',
                             'price_above_sma20', 'price_above_sma50',
                             'rsi_oversold', 'rsi_overbought', 'macd_positive', 'momentum_positive']
        self.model = None
        self.scaler = None
        self.data = []
        self.predictions = []
        self._load_models()
        
    def _load_models(self):
        print(f"📦 Carregando modelos {self.symbol}...")
        with open(self.model_file, 'rb') as f:
            self.model = pickle.load(f)
        with open(self.scaler_file, 'rb') as f:
            self.scaler = pickle.load(f)
        print(f"✅ Modelos carregados")
    
    def load_data(self):
        print(f"\n📊 Carregando dados {self.symbol}...")
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.data.append({
                    'timestamp': row['timestamp'],
                    'close': float(row['close']),
                    'rsi': float(row['rsi']),
                    'sma20': float(row['sma20']),
                    'sma50': float(row['sma50']),
                    'macd': float(row['macd']),
                    'atr': float(row['atr']),
                    'momentum': float(row['momentum']),
                    'price_above_sma20': int(row['price_above_sma20']),
                    'price_above_sma50': int(row['price_above_sma50']),
                    'rsi_oversold': int(row['rsi_oversold']),
                    'rsi_overbought': int(row['rsi_overbought']),
                    'macd_positive': int(row['macd_positive']),
                    'momentum_positive': int(row['momentum_positive']),
                    'target_direction': row['target_direction'],
                    'target_close': float(row['target_close']) if 'target_close' in row else 0.0,
                    'target_time': row['target_time'] if 'target_time' in row else ''
                })
        
        print(f"✅ {len(self.data)} candles carregados")
    
    def generate_predictions(self):
        print(f"\n🔮 Gerando predições...")
        
        X = np.array([[row[name] for name in self.feature_names] for row in self.data])
        X_scaled = self.scaler.transform(X)
        
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        for i, row in enumerate(self.data):
            predicted_direction = 'UP' if predictions[i] == 1 else 'DOWN'
            confidence = probabilities[i][predictions[i]]
            is_correct = 1 if predicted_direction == row['target_direction'] else 0
            
            self.predictions.append({
                'timestamp': row['timestamp'],
                'close': row['close'],
                'rsi': row['rsi'],
                'sma20': row['sma20'],
                'sma50': row['sma50'],
                'atr': row['atr'],
                'momentum': row['momentum'],
                'predicted_direction': predicted_direction,
                'confidence': confidence,
                'target_direction': row['target_direction'],
                'target_close': row['target_close'],
                'target_time': row['target_time'],
                'accuracy': is_correct
            })
        
        total = len(self.predictions)
        correct = sum([p['accuracy'] for p in self.predictions])
        accuracy = (correct / total * 100) if total > 0 else 0
        
        print(f"✅ {total} predições geradas")
        print(f"✅ Acertos: {correct}/{total} ({accuracy:.2f}%)")
    
    def save_backtest_csv(self):
        output_file = f"/tmp/backtest_ensemble_{self.symbol}_detailed.csv"
        print(f"\n💾 Salvando {output_file}...")
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'close', 'rsi', 'sma20', 'sma50', 'atr', 'momentum',
                'predicted_direction', 'confidence', 'target_direction', 
                'target_close', 'target_time', 'accuracy'
            ])
            writer.writeheader()
            writer.writerows(self.predictions)
        
        print(f"✅ {output_file}")
        return output_file
    
    def generate_backtest_report(self):
        print(f"\n📊 Gerando relatório de backtest...")
        
        total = len(self.predictions)
        correct = sum([p['accuracy'] for p in self.predictions])
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # Análise por confiança
        high_conf = [p for p in self.predictions if p['confidence'] > 0.80]
        mid_conf = [p for p in self.predictions if 0.70 <= p['confidence'] <= 0.80]
        low_conf = [p for p in self.predictions if p['confidence'] < 0.70]
        
        high_acc = sum([p['accuracy'] for p in high_conf]) / len(high_conf) * 100 if high_conf else 0
        mid_acc = sum([p['accuracy'] for p in mid_conf]) / len(mid_conf) * 100 if mid_conf else 0
        low_acc = sum([p['accuracy'] for p in low_conf]) / len(low_conf) * 100 if low_conf else 0
        
        # Contagem UP vs DOWN
        ups = len([p for p in self.predictions if p['predicted_direction'] == 'UP'])
        downs = len([p for p in self.predictions if p['predicted_direction'] == 'DOWN'])
        
        report = {
            'symbol': self.symbol,
            'total_predictions': total,
            'correct': correct,
            'accuracy': accuracy,
            'high_conf_count': len(high_conf),
            'high_conf_accuracy': high_acc,
            'mid_conf_count': len(mid_conf),
            'mid_conf_accuracy': mid_acc,
            'low_conf_count': len(low_conf),
            'low_conf_accuracy': low_acc,
            'ups': ups,
            'downs': downs,
            'avg_confidence': np.mean([p['confidence'] for p in self.predictions]) * 100
        }
        
        return report
    
    def run_backtest(self):
        self.load_data()
        self.generate_predictions()
        csv_file = self.save_backtest_csv()
        report = self.generate_backtest_report()
        return csv_file, report

def main():
    print("\n" + "="*80)
    print("🚀 BACKTEST COM DADOS REAIS - ENSEMBLE VOTING")
    print("="*80)
    print("""
OBJETIVO: Validar predições do Ensemble contra movimento real do mercado
DADOS: Todos os candles M15 disponíveis (Jan 2024 - Mai 2026)
MODELOS: Ensemble treinado com 70% dos dados, validado com 30%
    """)
    
    # EURUSD
    print("\n" + "="*80)
    print("EURUSD")
    print("="*80)
    
    eurusd_bt = EnsembleBacktest(
        '/tmp/bt_analysis_EURUSD.csv',
        '/home/ubuntu/pessoal/options/models/ml_ensemble_eurusd.pkl',
        '/home/ubuntu/pessoal/options/models/ml_scaler_eurusd.pkl',
        'EURUSD'
    )
    eurusd_csv, eurusd_report = eurusd_bt.run_backtest()
    
    # GBPUSD
    print("\n" + "="*80)
    print("GBPUSD")
    print("="*80)
    
    gbpusd_bt = EnsembleBacktest(
        '/tmp/bt_analysis_GBPUSD.csv',
        '/home/ubuntu/pessoal/options/models/ml_ensemble_gbpusd.pkl',
        '/home/ubuntu/pessoal/options/models/ml_scaler_gbpusd.pkl',
        'GBPUSD'
    )
    gbpusd_csv, gbpusd_report = gbpusd_bt.run_backtest()
    
    # Relatório Final
    print("\n" + "="*80)
    print("📊 RELATÓRIO DE BACKTEST - DADOS REAIS")
    print("="*80)
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                           EURUSD - Backtest Completo                      ║
╚════════════════════════════════════════════════════════════════════════════╝

Total de Predições:  {eurusd_report['total_predictions']:>6}
Acertos:             {eurusd_report['correct']:>6} / {eurusd_report['total_predictions']}
Acurácia:            {eurusd_report['accuracy']:>6.2f}%

Confiança Alta (> 80%):
  ├─ Predições: {eurusd_report['high_conf_count']:>6}
  └─ Acurácia:  {eurusd_report['high_conf_accuracy']:>6.2f}%

Confiança Média (70-80%):
  ├─ Predições: {eurusd_report['mid_conf_count']:>6}
  └─ Acurácia:  {eurusd_report['mid_conf_accuracy']:>6.2f}%

Confiança Baixa (< 70%):
  ├─ Predições: {eurusd_report['low_conf_count']:>6}
  └─ Acurácia:  {eurusd_report['low_conf_accuracy']:>6.2f}%

Distribuição:
  ├─ UP:  {eurusd_report['ups']:>6}
  ├─ DOWN: {eurusd_report['downs']:>6}
  └─ Confiança Média: {eurusd_report['avg_confidence']:>6.2f}%

╔════════════════════════════════════════════════════════════════════════════╗
║                           GBPUSD - Backtest Completo                      ║
╚════════════════════════════════════════════════════════════════════════════╝

Total de Predições:  {gbpusd_report['total_predictions']:>6}
Acertos:             {gbpusd_report['correct']:>6} / {gbpusd_report['total_predictions']}
Acurácia:            {gbpusd_report['accuracy']:>6.2f}%

Confiança Alta (> 80%):
  ├─ Predições: {gbpusd_report['high_conf_count']:>6}
  └─ Acurácia:  {gbpusd_report['high_conf_accuracy']:>6.2f}%

Confiança Média (70-80%):
  ├─ Predições: {gbpusd_report['mid_conf_count']:>6}
  └─ Acurácia:  {gbpusd_report['mid_conf_accuracy']:>6.2f}%

Confiança Baixa (< 70%):
  ├─ Predições: {gbpusd_report['low_conf_count']:>6}
  └─ Acurácia:  {gbpusd_report['low_conf_accuracy']:>6.2f}%

Distribuição:
  ├─ UP:  {gbpusd_report['ups']:>6}
  ├─ DOWN: {gbpusd_report['downs']:>6}
  └─ Confiança Média: {gbpusd_report['avg_confidence']:>6.2f}%

╔════════════════════════════════════════════════════════════════════════════╗
║                         ARQUIVOS DE BACKTEST GERADOS                      ║
╚════════════════════════════════════════════════════════════════════════════╝

✅ {eurusd_csv}
   Coluna 1:  timestamp (data/hora do candle)
   Coluna 2:  close (preço no momento da predição)
   Coluna 3:  rsi (RSI value)
   Coluna 4:  predicted_direction (UP ou DOWN)
   Coluna 5:  confidence (confiança 0-1)
   Coluna 6:  target_direction (o que realmente aconteceu)
   Coluna 7:  target_close (preço real do próximo candle)
   Coluna 8:  target_time (horário do próximo candle)
   Coluna 9:  accuracy (1=acertou, 0=errou)

✅ {gbpusd_csv}
   (Mesmo formato)

╔════════════════════════════════════════════════════════════════════════════╗
║                         INTERPRETAÇÃO DOS DADOS                           ║
╚════════════════════════════════════════════════════════════════════════════╝

Cada linha representa:
├─ timestamp:           Hora do candle M15
├─ close:               Preço de fechamento do candle atual
├─ predicted_direction: O que o modelo previu (UP/DOWN)
├─ confidence:          Nível de confiança (0.50-1.00)
├─ target_direction:    O que realmente aconteceu
├─ accuracy:            Se acertou (1) ou errou (0)
└─ Usage:               Validar cada predição contra o preço real

Validação Manual:
  1. Pega linha do CSV (timestamp X)
  2. Close é o preço no momento da predição
  3. target_close é o preço 15 minutos depois
  4. Compara: se predicted_direction == target_direction, accuracy=1
  5. Confirma o padrão em dados reais

""")
    
    print("="*80)
    print("✅ BACKTEST COMPLETO")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
