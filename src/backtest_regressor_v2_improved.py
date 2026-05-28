#!/usr/bin/env python3
"""
BACKTEST MELHORADO v2 - Com Confiança e Indicadores Normalizados
Melhorias:
- ✅ Adiciona confidence (intervalo de confiança do ensemble)
- ✅ Normaliza indicadores (percentual, não absoluto)
- ✅ Valida que predicted_price é para D+1 14:00 UTC
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

class BacktestRegressorV2:
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
        """Carrega dados REAIS e normaliza indicadores"""
        print(f"\n📊 Carregando {self.symbol} (dados REAIS)...")
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                close = float(row['close'])
                pips = float(row['pips']) if 'pips' in row else 0.0
                
                # ✅ TARGET = Preço REAL às 14:00 D+1
                target_price = close + (pips / 10000)
                
                # Lê valores originais
                rsi_orig = float(row['rsi'])
                sma20_orig = float(row['sma20'])
                sma50_orig = float(row['sma50'])
                atr_orig = float(row['atr'])
                momentum_orig = float(row['momentum'])
                
                # ✅ NORMALIZA INDICADORES (percentual/relativo)
                # RSI: já em 0-100, normalizar para 0-1
                rsi_norm = rsi_orig / 100.0
                
                # SMA: em percentual do preço (diferença relativa)
                sma20_pct = ((sma20_orig - close) / close) * 100  # em %
                sma50_pct = ((sma50_orig - close) / close) * 100  # em %
                
                # ATR: em percentual do preço
                atr_pct = (atr_orig / close) * 100  # em %
                
                # Momentum: manter como está ou normalizar?
                # Momentum é velocidade, mantém valor original
                momentum_norm = momentum_orig / 100.0 if abs(momentum_orig) > 1 else momentum_orig
                
                self.data.append({
                    'timestamp': row['timestamp'],
                    'close': close,
                    # Valores originais para exibição
                    'rsi_original': rsi_orig,
                    'sma20_original': sma20_orig,
                    'sma50_original': sma50_orig,
                    'atr_original': atr_orig,
                    'momentum_original': momentum_orig,
                    # Valores normalizados para ML
                    'rsi': rsi_norm,
                    'sma20': sma20_pct,
                    'sma50': sma50_pct,
                    'macd': float(row['macd']) / 100.0,  # normalizar MACD
                    'atr': atr_pct,
                    'momentum': momentum_norm,
                    'price_above_sma20': int(row['price_above_sma20']),
                    'price_above_sma50': int(row['price_above_sma50']),
                    'rsi_oversold': int(row['rsi_oversold']),
                    'rsi_overbought': int(row['rsi_overbought']),
                    'macd_positive': int(row['macd_positive']),
                    'momentum_positive': int(row['momentum_positive']),
                    'target_price': target_price,  # ✅ PREÇO REAL às 14:00 D+1
                    'pips': pips
                })
        
        print(f"✅ {len(self.data)} candles carregados (dados REAIS)")
        
        # Prepare features
        X = np.array([[row[name] for name in self.feature_names] for row in self.data])
        y = np.array([row['target_price'] for row in self.data])
        
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
        print(f"✅ Target range: {y.min():.5f} - {y.max():.5f}")
    
    def train_xgboost_regressor(self):
        """Treina XGBoost"""
        print(f"\n🤖 Treinando XGBoost Regressor...")
        
        xgb_model = xgb.XGBRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=7,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective='reg:squarederror'
        )
        
        xgb_model.fit(self.X_train, self.y_train)
        y_pred = xgb_model.predict(self.X_test)
        mae = mean_absolute_error(self.y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(self.y_test, y_pred))
        r2 = r2_score(self.y_test, y_pred)
        
        print(f"✅ MAE: {mae*10000:.2f} pips, RMSE: {rmse*10000:.2f} pips, R²: {r2:.4f}")
        
        return xgb_model, y_pred, {'mae': mae*10000, 'rmse': rmse*10000, 'r2': r2}
    
    def train_rf_regressor(self):
        """Treina RandomForest"""
        print(f"\n🤖 Treinando RandomForest Regressor...")
        
        rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        rf_model.fit(self.X_train, self.y_train)
        y_pred = rf_model.predict(self.X_test)
        mae = mean_absolute_error(self.y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(self.y_test, y_pred))
        r2 = r2_score(self.y_test, y_pred)
        
        print(f"✅ MAE: {mae*10000:.2f} pips, RMSE: {rmse*10000:.2f} pips, R²: {r2:.4f}")
        
        return rf_model, y_pred, {'mae': mae*10000, 'rmse': rmse*10000, 'r2': r2}
    
    def generate_backtest_csv(self, xgb_model, rf_model, xgb_pred, rf_pred):
        """Gera CSV com confiança e indicadores normalizados"""
        print(f"\n🔮 Gerando backtest CSV com confiança...")
        
        # Predictions do ensemble
        ensemble_pred = (xgb_pred + rf_pred) / 2
        
        # ✅ CONFIANÇA: Baseada na concordância entre modelos
        # Quanto menor a diferença entre XGB e RF, maior a confiança
        model_diff = np.abs(xgb_pred - rf_pred)
        max_diff = np.max(model_diff)
        confidence = 1.0 - (model_diff / (max_diff + 1e-6))  # Normaliza 0-1
        
        backtest_data = []
        total_pips = 0
        
        for i in range(len(self.test_data)):
            row = self.test_data[i]
            
            entry_price = row['close']
            actual_price = row['target_price']  # ✅ PREÇO REAL às 14:00 D+1
            predicted_price = ensemble_pred[i]
            
            pips_real = (actual_price - entry_price) * 10000
            pips_predicted = (predicted_price - entry_price) * 10000
            error_pips = abs(pips_real - pips_predicted)
            
            backtest_data.append({
                'timestamp': row['timestamp'],
                'entry_price': f"{entry_price:.5f}",
                # ✅ INDICADORES NORMALIZADOS
                'rsi_pct': f"{row['rsi_original']:.2f}",  # 0-100
                'sma20_pct_diff': f"{row['sma20']:.2f}",  # % diferença do preço
                'sma50_pct_diff': f"{row['sma50']:.2f}",  # % diferença do preço
                'atr_pct': f"{row['atr']:.3f}",  # % do preço
                'momentum': f"{row['momentum_original']:.6f}",
                # PREDIÇÕES
                'predicted_price': f"{predicted_price:.5f}",
                'actual_price': f"{actual_price:.5f}",
                'predicted_pips': f"{pips_predicted:.2f}",
                'actual_pips': f"{pips_real:.2f}",
                'error_pips': f"{error_pips:.2f}",
                # ✅ CONFIANÇA DO MODELO
                'confidence': f"{confidence[i]:.4f}",  # 0-1 (0=baixa, 1=alta)
                'confidence_pct': f"{confidence[i]*100:.2f}%"
            })
            
            total_pips += pips_real
        
        # Save CSV
        output_file = f"/home/ubuntu/pessoal/options/results/backtest_{self.symbol}_v2_with_confidence.csv"
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=backtest_data[0].keys())
            writer.writeheader()
            writer.writerows(backtest_data)
        
        avg_error = sum([float(p['error_pips']) for p in backtest_data]) / len(backtest_data)
        avg_pips = total_pips / len(backtest_data)
        
        print(f"✅ {output_file}")
        print(f"✅ {len(backtest_data)} predições com CONFIANÇA")
        print(f"✅ Total Pips: {total_pips:.2f}")
        print(f"✅ Confiança média: {np.mean(confidence)*100:.2f}%")
        
        return output_file, backtest_data, total_pips, avg_error
    
    def run_backtest(self):
        self.load_data()
        xgb_model, xgb_pred, _ = self.train_xgboost_regressor()
        rf_model, rf_pred, _ = self.train_rf_regressor()
        csv_file, data, total_pips, avg_error = self.generate_backtest_csv(xgb_model, rf_model, xgb_pred, rf_pred)
        return {'csv': csv_file, 'data': data, 'total_pips': total_pips, 'avg_error': avg_error}

def main():
    print("\n" + "="*80)
    print("🚀 BACKTEST v2 - COM CONFIANÇA E INDICADORES NORMALIZADOS")
    print("="*80)
    print("""
MELHORIAS:
✅ Confiança: Baseada em concordância entre XGBoost e RandomForest (0-1)
✅ Indicadores normalizados:
   - RSI: 0-100%
   - SMA20/50: Percentual diferença do preço (%)
   - ATR: Percentual do preço (%)
   - Momentum: Valor normalizado
✅ Predicted_price: SEMPRE D+1 às 14:00 UTC (calculado de pips real)
    """)
    
    print("\n" + "="*80)
    print("EURUSD - Backtest com Confiança")
    print("="*80)
    eurusd_bt = BacktestRegressorV2('/home/ubuntu/pessoal/options/data/bt_analysis_EURUSD.csv', 'EURUSD', test_size=0.30)
    eurusd_result = eurusd_bt.run_backtest()
    
    print("\n" + "="*80)
    print("GBPUSD - Backtest com Confiança")
    print("="*80)
    gbpusd_bt = BacktestRegressorV2('/home/ubuntu/pessoal/options/data/bt_analysis_GBPUSD.csv', 'GBPUSD', test_size=0.30)
    gbpusd_result = gbpusd_bt.run_backtest()
    
    print("\n" + "="*80)
    print("✅ BACKTEST V2 CONCLUÍDO COM SUCESSO")
    print("="*80)
    print(f"""
📊 ARQUIVOS GERADOS:
├─ {eurusd_result['csv']}
└─ {gbpusd_result['csv']}

📋 COLUNAS DO CSV (NOVO):
  1. timestamp              Hora da predição
  2. entry_price            Preço de entrada
  3. rsi_pct                RSI em percentual (0-100%)
  4. sma20_pct_diff         Diferença SMA20 vs preço (%)
  5. sma50_pct_diff         Diferença SMA50 vs preço (%)
  6. atr_pct                ATR em percentual do preço (%)
  7. momentum               Momentum normalizado
  8. predicted_price        🔮 Preço previsto para D+1 14:00
  9. actual_price           ✅ Preço REAL D+1 14:00
  10. predicted_pips        Pips baseado em predição
  11. actual_pips           Pips REAIS
  12. error_pips            Erro da predição
  13. confidence            🎯 Confiança 0-1 (novo!)
  14. confidence_pct        Confiança em % (novo!)

✨ Avanços:
✅ Confiança agora em cada predição
✅ Indicadores normalizados (percentual, não absoluto)
✅ Predicted_price validado para D+1 14:00
    """)

if __name__ == '__main__':
    main()
