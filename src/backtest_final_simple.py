#!/usr/bin/env python3
"""
BACKTEST FINAL - Simples e Eficiente
Usa dados já existentes em bt_analysis_EURUSD.csv que já têm target_direction
"""

import csv
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

class BacktestSimpleFinal:
    def __init__(self, csv_file, symbol, test_size=0.30):
        self.csv_file = csv_file
        self.symbol = symbol
        self.test_size = test_size
        self.feature_names = ['rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum',
                             'price_above_sma20', 'price_above_sma50',
                             'rsi_oversold', 'rsi_overbought', 'macd_positive', 'momentum_positive']
        self.scaler = StandardScaler()
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.test_indices = None
        self.test_data = None
        self.data = []
        
    def load_data(self):
        print(f"\n📊 Carregando {self.symbol}...")
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
                    'pips': float(row['pips']) if 'pips' in row else 0.0
                })
        
        print(f"✅ {len(self.data)} candles carregados")
        
        # Prepare features
        X = np.array([[row[name] for name in self.feature_names] for row in self.data])
        y = np.array([1 if row['target_direction'] == 'UP' else 0 for row in self.data])
        
        # Split 70/30
        indices = np.arange(len(X))
        X_train, X_test, y_train, y_test, train_idx, test_idx = train_test_split(
            X, y, indices, test_size=self.test_size, random_state=42
        )
        
        # Scale
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.X_train = X_train_scaled
        self.X_test = X_test_scaled
        self.y_train = y_train
        self.y_test = y_test
        self.test_indices = test_idx
        self.test_data = [self.data[i] for i in test_idx]
        
        print(f"✅ Split 70/30: {len(y_train)} treino, {len(y_test)} validação")
    
    def train_ensemble(self):
        print(f"\n🤖 Treinando Ensemble...")
        
        # XGBoost otimizado
        if self.symbol == 'EURUSD':
            xgb_model = xgb.XGBClassifier(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=9,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=42,
                eval_metric='logloss'
            )
        else:  # GBPUSD
            xgb_model = xgb.XGBClassifier(
                n_estimators=150,
                learning_rate=0.1,
                max_depth=9,
                subsample=0.8,
                colsample_bytree=0.9,
                random_state=42,
                eval_metric='logloss'
            )
        
        # Random Forest
        rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        # Ensemble
        self.ensemble = VotingClassifier(
            estimators=[('xgb', xgb_model), ('rf', rf_model)],
            voting='soft'
        )
        
        self.ensemble.fit(self.X_train, self.y_train)
        
        # Test accuracy
        predictions = self.ensemble.predict(self.X_test)
        accuracy = np.mean(predictions == self.y_test) * 100
        
        print(f"✅ Acurácia em validação (30%): {accuracy:.2f}%")
        
        return self.ensemble
    
    def generate_backtest_csv(self):
        print(f"\n🔮 Gerando backtest CSV...")
        
        predictions = self.ensemble.predict(self.X_test)
        probabilities = self.ensemble.predict_proba(self.X_test)
        
        backtest_data = []
        
        for i in range(len(self.test_data)):
            row = self.test_data[i]
            predicted_direction = 'UP' if predictions[i] == 1 else 'DOWN'
            confidence = probabilities[i][predictions[i]]
            
            # Real target from data
            target_direction = row['target_direction']
            pips = row['pips']
            
            # Validate
            if predicted_direction == target_direction:
                is_correct = 1
            else:
                is_correct = 0
            
            backtest_data.append({
                'timestamp': row['timestamp'],
                'close': f"{row['close']:.5f}",
                'rsi': f"{row['rsi']:.2f}",
                'sma20': f"{row['sma20']:.5f}",
                'sma50': f"{row['sma50']:.5f}",
                'atr': f"{row['atr']:.6f}",
                'momentum': f"{row['momentum']:.6f}",
                'predicted_direction': predicted_direction,
                'confidence': f"{confidence:.4f}",
                'target_direction': target_direction,
                'pips_gain': f"{pips:.1f}",
                'accuracy': is_correct
            })
        
        # Save CSV
        output_file = f"/tmp/backtest_{self.symbol}_final.csv"
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=backtest_data[0].keys())
            writer.writeheader()
            writer.writerows(backtest_data)
        
        # Stats
        total = len(backtest_data)
        correct = sum([p['accuracy'] for p in backtest_data])
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # Total pips
        total_pips = sum([float(p['pips_gain']) for p in backtest_data])
        avg_pips = total_pips / total if total > 0 else 0
        
        print(f"✅ {output_file}")
        print(f"✅ {total} predições")
        print(f"✅ Acertos: {correct}/{total} ({accuracy:.2f}%)")
        print(f"✅ Total Pips: {total_pips:.1f}")
        print(f"✅ Média Pips/Candle: {avg_pips:.2f}")
        
        return output_file, backtest_data, accuracy, total_pips
    
    def run_backtest(self):
        self.load_data()
        self.train_ensemble()
        csv_file, backtest_data, accuracy, pips = self.generate_backtest_csv()
        
        return csv_file, backtest_data, accuracy, pips

def main():
    print("\n" + "="*80)
    print("🚀 BACKTEST FINAL - VALIDAÇÃO COM DADOS REAIS")
    print("="*80)
    
    # EURUSD
    print("\n" + "="*80)
    print("EURUSD")
    print("="*80)
    
    eurusd_bt = BacktestSimpleFinal('/tmp/bt_analysis_EURUSD.csv', 'EURUSD', test_size=0.30)
    eurusd_csv, eurusd_data, eurusd_acc, eurusd_pips = eurusd_bt.run_backtest()
    
    # GBPUSD
    print("\n" + "="*80)
    print("GBPUSD")
    print("="*80)
    
    gbpusd_bt = BacktestSimpleFinal('/tmp/bt_analysis_GBPUSD.csv', 'GBPUSD', test_size=0.30)
    gbpusd_csv, gbpusd_data, gbpusd_acc, gbpusd_pips = gbpusd_bt.run_backtest()
    
    # Relatório
    print("\n" + "="*80)
    print("📊 BACKTEST FINAL - RESUMO")
    print("="*80)
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                              EURUSD                                       ║
╚════════════════════════════════════════════════════════════════════════════╝

Predições (30% validação):  {len(eurusd_data):>6}
Acurácia:                   {eurusd_acc:>6.2f}%
Total de Pips:              {eurusd_pips:>8.1f}
Média Pips/Candle:          {eurusd_pips/len(eurusd_data):>8.2f}

╔════════════════════════════════════════════════════════════════════════════╗
║                              GBPUSD                                       ║
╚════════════════════════════════════════════════════════════════════════════╝

Predições (30% validação):  {len(gbpusd_data):>6}
Acurácia:                   {gbpusd_acc:>6.2f}%
Total de Pips:              {gbpusd_pips:>8.1f}
Média Pips/Candle:          {gbpusd_pips/len(gbpusd_data):>8.2f}

╔════════════════════════════════════════════════════════════════════════════╗
║                    ARQUIVOS DE BACKTEST GERADOS                           ║
╚════════════════════════════════════════════════════════════════════════════╝

✅ {eurusd_csv}
   timestamp           → Hora da predição
   close               → Preço de fechamento
   rsi, sma20, sma50   → Indicadores técnicos
   predicted_direction → Predição do modelo (UP/DOWN)
   confidence          → Confiança (0.50-1.00)
   target_direction    → O que realmente aconteceu
   pips_gain           → Ganho/Perda em pips
   accuracy            → 1=acertou, 0=errou

✅ {gbpusd_csv}
   (Mesmo formato)

╔════════════════════════════════════════════════════════════════════════════╗
║                    COMO USAR OS DADOS                                     ║
╚════════════════════════════════════════════════════════════════════════════╝

Para cada linha do CSV:
  1. timestamp: Hora exata da predição (M15)
  2. close: Preço de fechamento naquele momento
  3. predicted_direction: O que o modelo previu
  4. confidence: Nível de confiança
  5. target_direction: O que realmente aconteceu (próximo dia 14:00)
  6. pips_gain: Ganho ou perda em pips
  7. accuracy: 1 se acertou, 0 se errou

Exemplo:
  timestamp: 2024-01-15 09:15:00 (predição neste candle)
  close: 1.09428
  predicted: UP
  confidence: 0.6435
  target: UP (confirmou)
  pips: +15.2 (ganho de 15.2 pips)
  accuracy: 1 (ACERTOU!)

""")
    
    print("="*80)
    print("✅ BACKTEST CONCLUÍDO E PRONTO PARA ANÁLISE")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
