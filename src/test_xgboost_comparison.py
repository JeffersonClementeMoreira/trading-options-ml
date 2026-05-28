#!/usr/bin/env python3
"""
Teste XGBoost vs Gradient Boosting vs Random Forest
XGBoost é frequentemente superior - vamos validar!
"""

import csv
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost não instalado - instalando...")

class MLComparison:
    def __init__(self, csv_file, symbol):
        self.csv_file = csv_file
        self.symbol = symbol
        self.data = []
        self.feature_names = ['rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum',
                             'price_above_sma20', 'price_above_sma50',
                             'rsi_oversold', 'rsi_overbought', 'macd_positive', 'momentum_positive']
        self.scaler = StandardScaler()
        
    def load_data(self):
        print(f"Carregando dados de {self.symbol}...")
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.data.append({
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
                    'target_direction': 1 if row['target_direction'] == 'UP' else 0
                })
        
        print(f"✅ Carregados {len(self.data)} registros")
    
    def prepare_features(self):
        X = np.array([[row[name] for name in self.feature_names] for row in self.data])
        y = np.array([row['target_direction'] for row in self.data])
        
        X_scaled = self.scaler.fit_transform(X)
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
        
        return X_train, X_test, y_train, y_test
    
    def evaluate_model(self, model, X_test, y_test, name):
        predictions = model.predict(X_test)
        accuracy = np.mean(predictions == y_test) * 100
        return accuracy
    
    def run_comparison(self):
        print(f"\n{'='*80}")
        print(f"COMPARAÇÃO DE MODELOS - {self.symbol}")
        print(f"{'='*80}\n")
        
        self.load_data()
        X_train, X_test, y_train, y_test = self.prepare_features()
        
        results = {}
        
        # 1. Random Forest
        print("1️⃣  Random Forest...")
        rf = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        results['Random Forest'] = self.evaluate_model(rf, X_test, y_test, 'RF')
        print(f"   ✅ {results['Random Forest']:.2f}%")
        
        # 2. Gradient Boosting
        print("2️⃣  Gradient Boosting...")
        gb = GradientBoostingClassifier(n_estimators=200, learning_rate=0.05, max_depth=7, random_state=42)
        gb.fit(X_train, y_train)
        results['Gradient Boosting'] = self.evaluate_model(gb, X_test, y_test, 'GB')
        print(f"   ✅ {results['Gradient Boosting']:.2f}%")
        
        # 3. XGBoost (se disponível)
        if XGBOOST_AVAILABLE:
            print("3️⃣  XGBoost...")
            xgb_model = xgb.XGBClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=7,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric='logloss'
            )
            xgb_model.fit(X_train, y_train)
            results['XGBoost'] = self.evaluate_model(xgb_model, X_test, y_test, 'XGB')
            print(f"   ✅ {results['XGBoost']:.2f}%")
        else:
            print("3️⃣  XGBoost (não disponível)")
        
        # 4. Logistic Regression (baseline)
        print("4️⃣  Logistic Regression...")
        lr = LogisticRegression(max_iter=1000, random_state=42)
        lr.fit(X_train, y_train)
        results['Logistic Regression'] = self.evaluate_model(lr, X_test, y_test, 'LR')
        print(f"   ✅ {results['Logistic Regression']:.2f}%")
        
        return results

def main():
    print("\n" + "="*80)
    print("🤖 TESTE XGBOOST vs OUTROS MODELOS")
    print("="*80 + "\n")
    
    all_results = {}
    
    # EURUSD
    eurusd = MLComparison('/tmp/bt_analysis_EURUSD.csv', 'EURUSD')
    eurusd_results = eurusd.run_comparison()
    all_results['EURUSD'] = eurusd_results
    
    # GBPUSD
    print("\n")
    gbpusd = MLComparison('/tmp/bt_analysis_GBPUSD.csv', 'GBPUSD')
    gbpusd_results = gbpusd.run_comparison()
    all_results['GBPUSD'] = gbpusd_results
    
    # Resumo Comparativo
    print(f"\n{'='*80}")
    print("📊 RESUMO COMPARATIVO")
    print(f"{'='*80}\n")
    
    print("EURUSD:")
    print("-" * 80)
    for model, acc in sorted(eurusd_results.items(), key=lambda x: x[1], reverse=True):
        print(f"  {model:<25}: {acc:6.2f}%")
    
    print(f"\nGBPUSD:")
    print("-" * 80)
    for model, acc in sorted(gbpusd_results.items(), key=lambda x: x[1], reverse=True):
        print(f"  {model:<25}: {acc:6.2f}%")
    
    # Análise XGBoost
    if XGBOOST_AVAILABLE:
        print(f"\n{'='*80}")
        print("🔥 ANÁLISE XGBOOST")
        print(f"{'='*80}\n")
        
        xgb_eurusd = eurusd_results.get('XGBoost', 0)
        xgb_gbpusd = gbpusd_results.get('XGBoost', 0)
        
        gb_eurusd = eurusd_results.get('Gradient Boosting', 0)
        gb_gbpusd = gbpusd_results.get('Gradient Boosting', 0)
        
        print(f"XGBoost vs Gradient Boosting:")
        print(f"  EURUSD: {xgb_eurusd:.2f}% vs {gb_eurusd:.2f}% → {xgb_eurusd-gb_eurusd:+.2f}%")
        print(f"  GBPUSD: {xgb_gbpusd:.2f}% vs {gb_gbpusd:.2f}% → {xgb_gbpusd-gb_gbpusd:+.2f}%")
        
        if xgb_eurusd > gb_eurusd or xgb_gbpusd > gb_gbpusd:
            print(f"\n  ✅ XGBoost SUPERIOR em pelo menos um currency!")
        else:
            print(f"\n  📊 Gradient Boosting mais consistente")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()
