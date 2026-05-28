#!/usr/bin/env python3
"""
BACKTEST FINAL v2 - Confiança + Indicadores normalizados para visualização
Estratégia:
- Features ORIGINAIS para modelo (já está otimizado)
- Valores NORMALIZADOS para exibição no CSV
- Confiança baseada em concordância XGB vs RF
"""

import csv
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

class BacktestFinalV2:
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
        """Carrega dados com campos para normalização"""
        print(f"\n📊 Carregando {self.symbol} (dados REAIS)...")
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                close = float(row['close'])
                pips = float(row['pips']) if 'pips' in row else 0.0
                target_price = close + (pips / 10000)
                
                self.data.append({
                    'timestamp': row['timestamp'],
                    'close': close,
                    # Features originais para modelo
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
                    'target_price': target_price,
                    'pips': pips
                })
        
        print(f"✅ {len(self.data)} candles carregados (dados REAIS)")
        
        X = np.array([[row[name] for name in self.feature_names] for row in self.data])
        y = np.array([row['target_price'] for row in self.data])
        
        indices = np.arange(len(X))
        X_train, X_test, y_train, y_test, train_idx, test_idx = train_test_split(
            X, y, indices, test_size=self.test_size, random_state=42
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.X_train = X_train_scaled
        self.X_test = X_test_scaled
        self.y_train = y_train
        self.y_test = y_test
        self.test_indices = test_idx
        self.test_data = [self.data[i] for i in test_idx]
        
        print(f"✅ Split 70/30: {len(y_train)} treino, {len(y_test)} validação")
    
    def train_xgboost_regressor(self):
        """Treina XGBoost com features originais"""
        print(f"\n🤖 Treinando XGBoost Regressor...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=200, learning_rate=0.05, max_depth=7,
            subsample=0.8, colsample_bytree=0.8, random_state=42,
            objective='reg:squarederror'
        )
        xgb_model.fit(self.X_train, self.y_train)
        y_pred = xgb_model.predict(self.X_test)
        mae = mean_absolute_error(self.y_test, y_pred)
        r2 = r2_score(self.y_test, y_pred)
        print(f"✅ MAE: {mae*10000:.2f} pips, R²: {r2:.4f}")
        return xgb_model, y_pred
    
    def train_rf_regressor(self):
        """Treina RandomForest com features originais"""
        print(f"\n🤖 Treinando RandomForest Regressor...")
        rf_model = RandomForestRegressor(
            n_estimators=200, max_depth=15, min_samples_split=5,
            random_state=42, n_jobs=-1
        )
        rf_model.fit(self.X_train, self.y_train)
        y_pred = rf_model.predict(self.X_test)
        mae = mean_absolute_error(self.y_test, y_pred)
        r2 = r2_score(self.y_test, y_pred)
        print(f"✅ MAE: {mae*10000:.2f} pips, R²: {r2:.4f}")
        return rf_model, y_pred
    
    def normalize_indicators(self, row):
        """Normaliza indicadores para exibição (não para modelo)"""
        close = row['close']
        
        return {
            'rsi_pct': row['rsi'] / 100.0,  # 0-1
            'sma20_pct_diff': ((row['sma20'] - close) / close) * 100,  # %
            'sma50_pct_diff': ((row['sma50'] - close) / close) * 100,  # %
            'atr_pct': (row['atr'] / close) * 100,  # %
            'momentum_norm': row['momentum'] / 100.0 if abs(row['momentum']) > 1 else row['momentum']
        }
    
    def generate_backtest_csv(self, xgb_model, rf_model, xgb_pred, rf_pred):
        """Gera CSV com confiança e indicadores normalizados"""
        print(f"\n🔮 Gerando backtest CSV com confiança...")
        
        ensemble_pred = (xgb_pred + rf_pred) / 2
        
        # ✅ CONFIANÇA: 1 - diferença normalizada entre modelos
        model_diff = np.abs(xgb_pred - rf_pred)
        max_diff = np.max(model_diff)
        confidence = 1.0 - (model_diff / (max_diff + 1e-6))
        
        backtest_data = []
        total_pips = 0
        
        for i in range(len(self.test_data)):
            row = self.test_data[i]
            entry_price = row['close']
            actual_price = row['target_price']  # ✅ D+1 14:00
            predicted_price = ensemble_pred[i]
            
            pips_real = (actual_price - entry_price) * 10000
            pips_predicted = (predicted_price - entry_price) * 10000
            error_pips = abs(pips_real - pips_predicted)
            
            # Normaliza indicadores para exibição
            norm_ind = self.normalize_indicators(row)
            
            backtest_data.append({
                'timestamp': row['timestamp'],
                'entry_price': f"{entry_price:.5f}",
                # ✅ INDICADORES NORMALIZADOS
                'rsi_pct': f"{row['rsi']:.2f}",  # 0-100%
                'sma20_pct_diff': f"{norm_ind['sma20_pct_diff']:.3f}",  # % vs preço
                'sma50_pct_diff': f"{norm_ind['sma50_pct_diff']:.3f}",  # % vs preço
                'atr_pct': f"{norm_ind['atr_pct']:.3f}",  # % do preço
                'momentum': f"{row['momentum']:.6f}",
                # PREDIÇÕES
                'predicted_price': f"{predicted_price:.5f}",
                'actual_price': f"{actual_price:.5f}",
                'predicted_pips': f"{pips_predicted:.2f}",
                'actual_pips': f"{pips_real:.2f}",
                'error_pips': f"{error_pips:.2f}",
                # ✅ CONFIANÇA
                'confidence': f"{confidence[i]:.4f}",  # 0-1
                'confidence_pct': f"{confidence[i]*100:.2f}%"
            })
            
            total_pips += pips_real
        
        output_file = f"/home/ubuntu/pessoal/options/results/backtest_{self.symbol}_v2.csv"
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=backtest_data[0].keys())
            writer.writeheader()
            writer.writerows(backtest_data)
        
        avg_error = sum([float(p['error_pips']) for p in backtest_data]) / len(backtest_data)
        avg_confidence = np.mean(confidence) * 100
        
        print(f"✅ {output_file}")
        print(f"✅ {len(backtest_data)} predições com CONFIANÇA")
        print(f"✅ Total Pips: {total_pips:.2f}")
        print(f"✅ Confiança média: {avg_confidence:.2f}%")
        print(f"✅ Erro médio: {avg_error:.2f} pips")
        
        return output_file

def main():
    print("\n" + "="*80)
    print("🚀 BACKTEST v2 - COM CONFIANÇA + INDICADORES NORMALIZADOS")
    print("="*80)
    print("""
MELHORIAS:
✅ Confiança: Baseada em concordância XGB vs RF (0-1)
✅ Indicadores normalizados para visualização:
   - RSI: Percentual (0-100%)
   - SMA20/50: Diferença vs preço (%)
   - ATR: Percentual do preço (%)
   - Momentum: Valor absoluto
✅ Predicted_price: D+1 às 14:00 UTC (derivado de pips real)
✅ Features do modelo: Mantidos originais (não normalizados)
    """)
    
    print("\n" + "="*80)
    print("EURUSD - Backtest com Confiança")
    print("="*80)
    eurusd_bt = BacktestFinalV2('/home/ubuntu/pessoal/options/data/bt_analysis_EURUSD.csv', 'EURUSD')
    eurusd_bt.load_data()
    xgb_eurusd, xgb_pred_eurusd = eurusd_bt.train_xgboost_regressor()
    rf_eurusd, rf_pred_eurusd = eurusd_bt.train_rf_regressor()
    eurusd_bt.generate_backtest_csv(xgb_eurusd, rf_eurusd, xgb_pred_eurusd, rf_pred_eurusd)
    
    print("\n" + "="*80)
    print("GBPUSD - Backtest com Confiança")
    print("="*80)
    gbpusd_bt = BacktestFinalV2('/home/ubuntu/pessoal/options/data/bt_analysis_GBPUSD.csv', 'GBPUSD')
    gbpusd_bt.load_data()
    xgb_gbpusd, xgb_pred_gbpusd = gbpusd_bt.train_xgboost_regressor()
    rf_gbpusd, rf_pred_gbpusd = gbpusd_bt.train_rf_regressor()
    gbpusd_bt.generate_backtest_csv(xgb_gbpusd, rf_gbpusd, xgb_pred_gbpusd, rf_pred_gbpusd)
    
    print("\n" + "="*80)
    print("✅ BACKTEST v2 FINALIZADO")
    print("="*80)

if __name__ == '__main__':
    main()
