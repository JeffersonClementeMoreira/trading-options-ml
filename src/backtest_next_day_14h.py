#!/usr/bin/env python3
"""
BACKTEST FINAL - Predição para Próximo Dia às 14:00 UTC
Valida: Candle de hoje → Predição → Preço real no próximo dia 14:00
"""

import csv
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
import xgboost as xgb
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class BacktestNextDay14h:
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
        self.price_map = {}  # Map timestamp -> close price
        
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
                    'target_direction': row['target_direction']
                })
                
                # Build price map for quick lookup
                self.price_map[row['timestamp']] = float(row['close'])
        
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
    
    def find_next_day_14h(self, timestamp_str):
        """
        Encontra o preço no próximo dia às 14:00 UTC
        timestamp_str: "2024-01-02T23:00:00"
        """
        try:
            ts = datetime.fromisoformat(timestamp_str)
            
            # Próximo dia às 14:00 UTC
            next_day_14h = ts.replace(hour=14, minute=0, second=0) + timedelta(days=1)
            target_timestamp = next_day_14h.isoformat()
            
            # Busca preço
            if target_timestamp in self.price_map:
                return self.price_map[target_timestamp], target_timestamp
            
            # Se não encontrar exato, procura na lista
            for data_point in self.data:
                if data_point['timestamp'].startswith(next_day_14h.strftime('%Y-%m-%dT14:00')):
                    return data_point['close'], data_point['timestamp']
            
            return None, target_timestamp
        except:
            return None, ""
    
    def generate_backtest_csv(self):
        print(f"\n🔮 Gerando backtest para próximo dia 14:00...")
        
        predictions = self.ensemble.predict(self.X_test)
        probabilities = self.ensemble.predict_proba(self.X_test)
        
        backtest_data = []
        found_target = 0
        
        for i in range(len(self.test_data)):
            row = self.test_data[i]
            predicted_direction = 'UP' if predictions[i] == 1 else 'DOWN'
            confidence = probabilities[i][predictions[i]]
            
            # Find target price at next day 14:00
            target_close, target_time = self.find_next_day_14h(row['timestamp'])
            
            # Validate
            if target_close is not None:
                found_target += 1
                if row['close'] < target_close and predicted_direction == 'UP':
                    is_correct = 1
                elif row['close'] > target_close and predicted_direction == 'DOWN':
                    is_correct = 1
                else:
                    is_correct = 0
                
                # Real target direction
                target_direction = 'UP' if target_close > row['close'] else 'DOWN'
            else:
                target_close = 0.0
                target_time = ''
                is_correct = 0
                target_direction = '?'
            
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
                'target_close': f"{target_close:.5f}" if target_close > 0 else 'N/A',
                'target_time': target_time,
                'target_direction': target_direction,
                'accuracy': is_correct
            })
        
        # Save CSV
        output_file = f"/tmp/backtest_{self.symbol}_next_day_14h.csv"
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=backtest_data[0].keys())
            writer.writeheader()
            writer.writerows(backtest_data)
        
        # Stats
        total = len(backtest_data)
        correct = sum([p['accuracy'] for p in backtest_data if isinstance(p['accuracy'], int)])
        accuracy = (correct / found_target * 100) if found_target > 0 else 0
        
        print(f"✅ {output_file}")
        print(f"✅ {total} predições no conjunto de validação")
        print(f"✅ Com preço target encontrado: {found_target}")
        print(f"✅ Acertos: {correct}/{found_target} ({accuracy:.2f}%)")
        
        return output_file, backtest_data, accuracy, found_target
    
    def run_backtest(self):
        self.load_data()
        self.train_ensemble()
        csv_file, backtest_data, accuracy, found = self.generate_backtest_csv()
        
        return csv_file, backtest_data, accuracy, found

def main():
    print("\n" + "="*80)
    print("🚀 BACKTEST FINAL - Predição para Próximo Dia às 14:00 UTC")
    print("="*80)
    
    # EURUSD
    print("\n" + "="*80)
    print("EURUSD")
    print("="*80)
    
    eurusd_bt = BacktestNextDay14h('/tmp/bt_analysis_EURUSD.csv', 'EURUSD', test_size=0.30)
    eurusd_csv, eurusd_data, eurusd_acc, eurusd_found = eurusd_bt.run_backtest()
    
    # GBPUSD
    print("\n" + "="*80)
    print("GBPUSD")
    print("="*80)
    
    gbpusd_bt = BacktestNextDay14h('/tmp/bt_analysis_GBPUSD.csv', 'GBPUSD', test_size=0.30)
    gbpusd_csv, gbpusd_data, gbpusd_acc, gbpusd_found = gbpusd_bt.run_backtest()
    
    # Relatório
    print("\n" + "="*80)
    print("📊 BACKTEST FINAL - PRÓXIMO DIA 14:00 UTC")
    print("="*80)
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                           EURUSD - Resultado                              ║
╚════════════════════════════════════════════════════════════════════════════╝

Total predições:       {len(eurusd_data):>6}
Com target encontrado: {eurusd_found:>6}
Acertos:               {sum([p['accuracy'] for p in eurusd_data if isinstance(p['accuracy'], int)]):>6}
Acurácia:              {eurusd_acc:>6.2f}%

╔════════════════════════════════════════════════════════════════════════════╗
║                           GBPUSD - Resultado                              ║
╚════════════════════════════════════════════════════════════════════════════╝

Total predições:       {len(gbpusd_data):>6}
Com target encontrado: {gbpusd_found:>6}
Acertos:               {sum([p['accuracy'] for p in gbpusd_data if isinstance(p['accuracy'], int)]):>6}
Acurácia:              {gbpusd_acc:>6.2f}%

╔════════════════════════════════════════════════════════════════════════════╗
║                    ESTRUTURA DO CSV                                       ║
╚════════════════════════════════════════════════════════════════════════════╝

timestamp          → Hora da predição (hoje)
close              → Preço de fechamento (hoje)
rsi, sma20, sma50  → Indicadores técnicos
predicted_direction → Predição do modelo (UP/DOWN)
confidence         → Nível de confiança (0.50-1.00)
target_close       → Preço real no próximo dia às 14:00 UTC
target_time        → Data/hora exata do candle (próximo dia 14:00)
target_direction   → Direção real do movimento
accuracy           → 1=acertou, 0=errou

╔════════════════════════════════════════════════════════════════════════════╗
║                    EXEMPLO DE VALIDAÇÃO                                   ║
╚════════════════════════════════════════════════════════════════════════════╝

Linha do CSV:
├─ timestamp: 2024-01-02T23:00:00 (predição feita aqui)
├─ close: 1.09428 (preço hoje 23:00)
├─ predicted_direction: UP (modelo previu subida)
├─ confidence: 0.6435 (confiança 64%)
├─ target_close: 1.09500 (preço real no próximo dia 14:00)
├─ target_time: 2024-01-03T14:00:00 (dia seguinte 14:00)
├─ target_direction: UP (realmente subiu: 1.09428 → 1.09500)
└─ accuracy: 1 (ACERTOU!)

OUTRO EXEMPLO:
├─ timestamp: 2024-01-03T10:00:00
├─ close: 1.09550
├─ predicted_direction: DOWN
├─ confidence: 0.7200
├─ target_close: 1.09540 (desceu pouco)
├─ target_time: 2024-01-04T14:00:00
├─ target_direction: DOWN (confirmou)
└─ accuracy: 1 (ACERTOU!)

╔════════════════════════════════════════════════════════════════════════════╗
║                    ARQUIVOS GERADOS                                       ║
╚════════════════════════════════════════════════════════════════════════════╝

✅ {eurusd_csv}
   Predições para EURUSD com validação no próximo dia 14:00 UTC

✅ {gbpusd_csv}
   Predições para GBPUSD com validação no próximo dia 14:00 UTC

""")
    
    print("="*80)
    print("✅ BACKTEST PRONTO PARA ANÁLISE")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
