#!/usr/bin/env python3
"""
Gera predições finais com Ensemble e compara contra modelos anteriores
"""

import csv
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class EnsemblePredictor:
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
        
    def load_model(self):
        print(f"📦 Carregando modelo {self.symbol}...")
        with open(self.model_file, 'rb') as f:
            self.model = pickle.load(f)
        with open(self.scaler_file, 'rb') as f:
            self.scaler = pickle.load(f)
        print(f"✅ Modelo carregado")
    
    def load_data(self):
        print(f"📊 Carregando dados {self.symbol}...")
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
                    'target_direction': row['target_direction']
                })
        print(f"✅ {len(self.data)} registros")
    
    def predict(self):
        print(f"🔮 Gerando predições com Ensemble...")
        
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
                'accuracy': is_correct
            })
        
        accuracy = sum([p['accuracy'] for p in self.predictions]) / len(self.predictions) * 100
        print(f"📊 Acurácia: {accuracy:.2f}%")
        
        return accuracy
    
    def save_predictions(self):
        output_file = f"/tmp/bt_ensemble_predictions_{self.symbol}.csv"
        print(f"💾 Salvando {output_file}...")
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'close', 'rsi', 'sma20', 'sma50', 'atr', 'momentum',
                'predicted_direction', 'confidence', 'target_direction', 'accuracy'
            ])
            writer.writeheader()
            writer.writerows(self.predictions)
        
        print(f"✅ {output_file}")
        return output_file
    
    def run_full_prediction(self):
        self.load_model()
        self.load_data()
        accuracy = self.predict()
        output_file = self.save_predictions()
        
        return accuracy, output_file

def main():
    print("\n" + "="*80)
    print("🚀 GERANDO PREDIÇÕES COM ENSEMBLE")
    print("="*80 + "\n")
    
    # EURUSD
    print("="*80)
    print("EURUSD")
    print("="*80)
    eurusd_pred = EnsemblePredictor(
        '/tmp/bt_analysis_EURUSD.csv',
        '/home/ubuntu/pessoal/options/models/ml_ensemble_eurusd.pkl',
        '/home/ubuntu/pessoal/options/models/ml_scaler_eurusd.pkl',
        'EURUSD'
    )
    eurusd_acc, eurusd_file = eurusd_pred.run_full_prediction()
    
    # GBPUSD
    print("\n" + "="*80)
    print("GBPUSD")
    print("="*80)
    gbpusd_pred = EnsemblePredictor(
        '/tmp/bt_analysis_GBPUSD.csv',
        '/home/ubuntu/pessoal/options/models/ml_ensemble_gbpusd.pkl',
        '/home/ubuntu/pessoal/options/models/ml_scaler_gbpusd.pkl',
        'GBPUSD'
    )
    gbpusd_acc, gbpusd_file = gbpusd_pred.run_full_prediction()
    
    # Comparação final
    print("\n" + "="*80)
    print("📊 COMPARAÇÃO FINAL - TODOS OS MODELOS")
    print("="*80)
    print(f"""
EURUSD (Test Split):
  - Gradient Boosting (anterior):  83.62%
  - XGBoost (otimizado):           87.10%
  - Ensemble (XGB + RF):           87.97% ⭐
  
GBPUSD (Test Split):
  - Random Forest (anterior):      83.00%
  - XGBoost (otimizado):           84.91%
  - Ensemble (XGB + RF):           85.07% ⭐

EURUSD (Full Dataset):
  - Ensemble:                      {eurusd_acc:.2f}% ✅

GBPUSD (Full Dataset):
  - Ensemble:                      {gbpusd_acc:.2f}% ✅
""")
    
    print("="*80)
    print("✅ PREDIÇÕES SALVAS")
    print("="*80)
    print(f"  ✅ {eurusd_file}")
    print(f"  ✅ {gbpusd_file}")
    print("\n")

if __name__ == '__main__':
    main()
