#!/usr/bin/env python3
"""
Otimizar XGBoost com GridSearch + Criar Ensemble Voting
XGBoost + Random Forest = Decisão conjunta
"""

import csv
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

class XGBoostOptimizer:
    def __init__(self, csv_file, symbol):
        self.csv_file = csv_file
        self.symbol = symbol
        self.data = []
        self.feature_names = ['rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum',
                             'price_above_sma20', 'price_above_sma50',
                             'rsi_oversold', 'rsi_overbought', 'macd_positive', 'momentum_positive']
        self.scaler = StandardScaler()
        
    def load_data(self):
        print(f"\n📊 Carregando dados de {self.symbol}...")
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
    
    def optimize_xgboost(self, X_train, X_test, y_train, y_test):
        """GridSearch para encontrar melhores hiperparâmetros do XGBoost"""
        print(f"\n🔍 Otimizando XGBoost com GridSearch...")
        print(f"   (Esta operação pode levar 5-10 minutos)\n")
        
        # Hiperparâmetros para testar
        param_grid = {
            'max_depth': [5, 7, 9],
            'learning_rate': [0.01, 0.05, 0.1],
            'n_estimators': [100, 150],
            'subsample': [0.7, 0.8, 0.9],
            'colsample_bytree': [0.7, 0.8, 0.9]
        }
        
        xgb_base = xgb.XGBClassifier(random_state=42, eval_metric='logloss', use_label_encoder=False)
        
        # GridSearch com apenas 3 folds para ser mais rápido
        grid_search = GridSearchCV(xgb_base, param_grid, cv=3, n_jobs=-1, verbose=0)
        grid_search.fit(X_train, y_train)
        
        print(f"✅ Melhores hiperparâmetros encontrados:")
        for param, value in grid_search.best_params_.items():
            print(f"   {param}: {value}")
        
        best_xgb = grid_search.best_estimator_
        train_acc = accuracy_score(y_train, best_xgb.predict(X_train))
        test_acc = accuracy_score(y_test, best_xgb.predict(X_test))
        
        print(f"\n📈 Acurácia do XGBoost otimizado:")
        print(f"   Treino: {train_acc*100:.2f}%")
        print(f"   Teste:  {test_acc*100:.2f}%")
        
        return best_xgb, test_acc * 100
    
    def create_ensemble(self, X_train, X_test, y_train, y_test, best_xgb):
        """Cria ensemble com XGBoost + Random Forest"""
        print(f"\n🤝 Criando Ensemble Voting (XGBoost + Random Forest)...")
        
        # Random Forest
        rf = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        rf_acc = accuracy_score(y_test, rf.predict(X_test))
        
        # Ensemble Voting
        voting_clf = VotingClassifier(
            estimators=[('xgb', best_xgb), ('rf', rf)],
            voting='soft'  # Usa probabilidades para votação mais refinada
        )
        voting_clf.fit(X_train, y_train)
        
        ensemble_train_acc = accuracy_score(y_train, voting_clf.predict(X_train))
        ensemble_test_acc = accuracy_score(y_test, voting_clf.predict(X_test))
        
        print(f"\n📊 Resultados:")
        print(f"   Random Forest:        {rf_acc*100:.2f}%")
        print(f"   Ensemble (Train):     {ensemble_train_acc*100:.2f}%")
        print(f"   Ensemble (Teste):     {ensemble_test_acc*100:.2f}%")
        
        return voting_clf, ensemble_test_acc * 100
    
    def run_full_optimization(self):
        self.load_data()
        X_train, X_test, y_train, y_test = self.prepare_features()
        
        best_xgb, xgb_test_acc = self.optimize_xgboost(X_train, X_test, y_train, y_test)
        ensemble, ensemble_test_acc = self.create_ensemble(X_train, X_test, y_train, y_test, best_xgb)
        
        return {
            'symbol': self.symbol,
            'xgb_accuracy': xgb_test_acc,
            'ensemble_accuracy': ensemble_test_acc,
            'best_xgb': best_xgb,
            'ensemble': ensemble,
            'scaler': self.scaler
        }

def main():
    print("\n" + "="*100)
    print("🚀 OTIMIZAÇÃO XGBOOST + ENSEMBLE VOTING")
    print("="*100)
    
    # EURUSD
    print("\n" + "="*100)
    print("EURUSD - Otimização XGBoost")
    print("="*100)
    eurusd_opt = XGBoostOptimizer('/tmp/bt_analysis_EURUSD.csv', 'EURUSD')
    eurusd_results = eurusd_opt.run_full_optimization()
    
    # GBPUSD
    print("\n" + "="*100)
    print("GBPUSD - Otimização XGBoost")
    print("="*100)
    gbpusd_opt = XGBoostOptimizer('/tmp/bt_analysis_GBPUSD.csv', 'GBPUSD')
    gbpusd_results = gbpusd_opt.run_full_optimization()
    
    # Resumo Final
    print("\n" + "="*100)
    print("📊 RESUMO FINAL - OTIMIZAÇÃO XGBOOST + ENSEMBLE")
    print("="*100 + "\n")
    
    print("EURUSD:")
    print("-" * 100)
    print(f"  XGBoost (otimizado):  {eurusd_results['xgb_accuracy']:.2f}%")
    print(f"  Ensemble (XGB + RF):  {eurusd_results['ensemble_accuracy']:.2f}%")
    print(f"  Melhor modelo:        {'XGBoost' if eurusd_results['xgb_accuracy'] > eurusd_results['ensemble_accuracy'] else 'Ensemble'}")
    
    print("\nGBPUSD:")
    print("-" * 100)
    print(f"  XGBoost (otimizado):  {gbpusd_results['xgb_accuracy']:.2f}%")
    print(f"  Ensemble (XGB + RF):  {gbpusd_results['ensemble_accuracy']:.2f}%")
    print(f"  Melhor modelo:        {'XGBoost' if gbpusd_results['xgb_accuracy'] > gbpusd_results['ensemble_accuracy'] else 'Ensemble'}")
    
    # Comparação com modelos atuais
    print("\n" + "="*100)
    print("⚖️  COMPARAÇÃO COM MODELOS ATUAIS")
    print("="*100 + "\n")
    
    print("EURUSD:")
    print("-" * 100)
    print(f"  Gradient Boosting (atual): 83.62%")
    print(f"  XGBoost (otimizado):       {eurusd_results['xgb_accuracy']:.2f}% → {eurusd_results['xgb_accuracy']-83.62:+.2f}%")
    print(f"  Ensemble:                  {eurusd_results['ensemble_accuracy']:.2f}% → {eurusd_results['ensemble_accuracy']-83.62:+.2f}%")
    
    print("\nGBPUSD:")
    print("-" * 100)
    print(f"  Random Forest (atual):     83.00%")
    print(f"  XGBoost (otimizado):       {gbpusd_results['xgb_accuracy']:.2f}% → {gbpusd_results['xgb_accuracy']-83.00:+.2f}%")
    print(f"  Ensemble:                  {gbpusd_results['ensemble_accuracy']:.2f}% → {gbpusd_results['ensemble_accuracy']-83.00:+.2f}%")
    
    print("\n" + "="*100)
    print("✅ OTIMIZAÇÃO CONCLUÍDA")
    print("="*100 + "\n")

if __name__ == '__main__':
    main()
