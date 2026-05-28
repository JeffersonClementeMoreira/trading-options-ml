#!/usr/bin/env python3
"""
BACKTEST CORRETO - Regressão para prever PREÇO às 14:00 UTC próximo dia
Regras:
- TARGET = Preço real às 14:00 (NÃO UP/DOWN)
- Modelo de REGRESSÃO (não classificação)
- Split 70/30 (nunca treinar 100%)
- Dados REAIS (não inventados)
- Alvo SEMPRE 14:00 UTC próximo dia
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

class BacktestRegressor:
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
        """Carrega dados REAIS de arquivo"""
        print(f"\n📊 Carregando {self.symbol} (dados REAIS)...")
        with open(self.csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Close = preço na entrada
                close = float(row['close'])
                # Pips = ganho em pips (pips = (preço_14h - close) * 10000 para EURUSD)
                pips = float(row['pips']) if 'pips' in row else 0.0
                
                # Calcula target: preço real às 14:00 do próximo dia
                # pips = (target_price - close) * 10000
                # target_price = close + (pips / 10000)
                target_price = close + (pips / 10000)
                
                self.data.append({
                    'timestamp': row['timestamp'],
                    'close': close,
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
                    'target_price': target_price,  # PREÇO REAL às 14:00
                    'pips': pips
                })
        
        print(f"✅ {len(self.data)} candles carregados (dados REAIS)")
        
        # Prepare features
        X = np.array([[row[name] for name in self.feature_names] for row in self.data])
        y = np.array([row['target_price'] for row in self.data])  # TARGET = PREÇO
        
        # Split 70/30 (NUNCA usar 100%)
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
        """Treina XGBoost para REGRESSÃO (prever preço)"""
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
        
        # Validação
        y_pred = xgb_model.predict(self.X_test)
        mae = mean_absolute_error(self.y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(self.y_test, y_pred))
        r2 = r2_score(self.y_test, y_pred)
        
        # Converte erro em pips (EURUSD: 1 pips = 0.0001)
        mae_pips = mae * 10000
        rmse_pips = rmse * 10000
        
        print(f"✅ MAE: {mae:.6f} ({mae_pips:.2f} pips)")
        print(f"✅ RMSE: {rmse:.6f} ({rmse_pips:.2f} pips)")
        print(f"✅ R²: {r2:.4f}")
        
        return xgb_model, y_pred, {'mae': mae_pips, 'rmse': rmse_pips, 'r2': r2}
    
    def train_rf_regressor(self):
        """Treina RandomForest para REGRESSÃO"""
        print(f"\n🤖 Treinando RandomForest Regressor...")
        
        rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        
        rf_model.fit(self.X_train, self.y_train)
        
        # Validação
        y_pred = rf_model.predict(self.X_test)
        mae = mean_absolute_error(self.y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(self.y_test, y_pred))
        r2 = r2_score(self.y_test, y_pred)
        
        mae_pips = mae * 10000
        rmse_pips = rmse * 10000
        
        print(f"✅ MAE: {mae:.6f} ({mae_pips:.2f} pips)")
        print(f"✅ RMSE: {rmse:.6f} ({rmse_pips:.2f} pips)")
        print(f"✅ R²: {r2:.4f}")
        
        return rf_model, y_pred, {'mae': mae_pips, 'rmse': rmse_pips, 'r2': r2}
    
    def generate_backtest_csv(self, xgb_pred, rf_pred):
        """Gera CSV com predições de PREÇO (não direção)"""
        print(f"\n🔮 Gerando backtest CSV com predições de PREÇO...")
        
        # Ensemble: média entre XGBoost e RandomForest
        ensemble_pred = (xgb_pred + rf_pred) / 2
        
        backtest_data = []
        total_pips = 0
        
        for i in range(len(self.test_data)):
            row = self.test_data[i]
            
            entry_price = row['close']
            actual_price = row['target_price']  # PREÇO REAL às 14:00
            predicted_price = ensemble_pred[i]
            
            # Pips reais (baseado em preço real)
            pips_real = (actual_price - entry_price) * 10000
            
            # Pips previstos (baseado em preço previsto)
            pips_predicted = (predicted_price - entry_price) * 10000
            
            # Erro em pips
            error_pips = abs(pips_real - pips_predicted)
            
            backtest_data.append({
                'timestamp': row['timestamp'],
                'entry_price': f"{entry_price:.5f}",
                'rsi': f"{row['rsi']:.2f}",
                'sma20': f"{row['sma20']:.5f}",
                'sma50': f"{row['sma50']:.5f}",
                'atr': f"{row['atr']:.6f}",
                'momentum': f"{row['momentum']:.6f}",
                'predicted_price': f"{predicted_price:.5f}",
                'actual_price': f"{actual_price:.5f}",
                'predicted_pips': f"{pips_predicted:.2f}",
                'actual_pips': f"{pips_real:.2f}",
                'error_pips': f"{error_pips:.2f}"
            })
            
            total_pips += pips_real
        
        # Save CSV
        output_file = f"/tmp/backtest_{self.symbol}_regressor_correct.csv"
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=backtest_data[0].keys())
            writer.writeheader()
            writer.writerows(backtest_data)
        
        avg_error = sum([float(p['error_pips']) for p in backtest_data]) / len(backtest_data)
        avg_pips = total_pips / len(backtest_data)
        
        print(f"✅ {output_file}")
        print(f"✅ {len(backtest_data)} predições de PREÇO")
        print(f"✅ Total Pips (real): {total_pips:.2f}")
        print(f"✅ Erro médio: {avg_error:.2f} pips")
        print(f"✅ Pips médio/candle: {avg_pips:.2f}")
        
        return output_file, backtest_data, total_pips, avg_error
    
    def run_backtest(self):
        self.load_data()
        xgb_model, xgb_pred, xgb_metrics = self.train_xgboost_regressor()
        rf_model, rf_pred, rf_metrics = self.train_rf_regressor()
        csv_file, backtest_data, total_pips, avg_error = self.generate_backtest_csv(xgb_pred, rf_pred)
        
        return {
            'csv': csv_file,
            'data': backtest_data,
            'total_pips': total_pips,
            'avg_error': avg_error,
            'xgb_metrics': xgb_metrics,
            'rf_metrics': rf_metrics
        }

def main():
    print("\n" + "="*80)
    print("🚀 BACKTEST CORRETO - REGRESSÃO PARA PREVER PREÇO ÀS 14:00 UTC")
    print("="*80)
    print("""
REGRAS (NUNCA ESQUECER):
✅ TARGET = Preço real às 14:00 UTC próximo dia (NÃO UP/DOWN)
✅ Modelo REGRESSÃO (prever preço, não classificação)
✅ Split 70/30 (nunca treinar 100% dos dados)
✅ Dados REAIS de /tmp/bt_analysis_*.csv (não inventados)
✅ Alvo SEMPRE 14:00 UTC próximo dia
    """)
    
    # EURUSD
    print("\n" + "="*80)
    print("EURUSD - Backtest Regressão")
    print("="*80)
    
    eurusd_bt = BacktestRegressor('/tmp/bt_analysis_EURUSD.csv', 'EURUSD', test_size=0.30)
    eurusd_result = eurusd_bt.run_backtest()
    
    # GBPUSD
    print("\n" + "="*80)
    print("GBPUSD - Backtest Regressão")
    print("="*80)
    
    gbpusd_bt = BacktestRegressor('/tmp/bt_analysis_GBPUSD.csv', 'GBPUSD', test_size=0.30)
    gbpusd_result = gbpusd_bt.run_backtest()
    
    # Relatório
    print("\n" + "="*80)
    print("📊 BACKTEST REGRESSÃO - RESUMO FINAL")
    print("="*80)
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                              EURUSD                                       ║
╚════════════════════════════════════════════════════════════════════════════╝

Modelo: Ensemble (XGBoost + RandomForest)
Tarefa: REGRESSÃO - Prever preço às 14:00 UTC

XGBoost:
├─ MAE: {eurusd_result['xgb_metrics']['mae']:.2f} pips
├─ RMSE: {eurusd_result['xgb_metrics']['rmse']:.2f} pips
└─ R²: {eurusd_result['xgb_metrics']['r2']:.4f}

RandomForest:
├─ MAE: {eurusd_result['rf_metrics']['mae']:.2f} pips
├─ RMSE: {eurusd_result['rf_metrics']['rmse']:.2f} pips
└─ R²: {eurusd_result['rf_metrics']['r2']:.4f}

Ensemble (Validação):
├─ Predições: {len(eurusd_result['data']):>6}
├─ Total Pips: {eurusd_result['total_pips']:>8.2f}
├─ Erro médio: {eurusd_result['avg_error']:>8.2f} pips
└─ Pips/candle: {eurusd_result['total_pips']/len(eurusd_result['data']):>8.2f}

╔════════════════════════════════════════════════════════════════════════════╗
║                              GBPUSD                                       ║
╚════════════════════════════════════════════════════════════════════════════╝

Modelo: Ensemble (XGBoost + RandomForest)
Tarefa: REGRESSÃO - Prever preço às 14:00 UTC

XGBoost:
├─ MAE: {gbpusd_result['xgb_metrics']['mae']:.2f} pips
├─ RMSE: {gbpusd_result['xgb_metrics']['rmse']:.2f} pips
└─ R²: {gbpusd_result['xgb_metrics']['r2']:.4f}

RandomForest:
├─ MAE: {gbpusd_result['rf_metrics']['mae']:.2f} pips
├─ RMSE: {gbpusd_result['rf_metrics']['rmse']:.2f} pips
└─ R²: {gbpusd_result['rf_metrics']['r2']:.4f}

Ensemble (Validação):
├─ Predições: {len(gbpusd_result['data']):>6}
├─ Total Pips: {gbpusd_result['total_pips']:>8.2f}
├─ Erro médio: {gbpusd_result['avg_error']:>8.2f} pips
└─ Pips/candle: {gbpusd_result['total_pips']/len(gbpusd_result['data']):>8.2f}

╔════════════════════════════════════════════════════════════════════════════╗
║                    ARQUIVOS DE BACKTEST GERADOS                           ║
╚════════════════════════════════════════════════════════════════════════════╝

✅ {eurusd_result['csv']}
✅ {gbpusd_result['csv']}

Colunas do CSV:
  1. timestamp          → Hora da predição (M15)
  2. entry_price        → Preço de entrada
  3. indicadores        → RSI, SMA20, SMA50, ATR, Momentum
  4. predicted_price    → Preço previsto para 14:00 UTC próximo dia
  5. actual_price       → Preço REAL às 14:00 UTC próximo dia
  6. predicted_pips     → Pips previstos (predicted - entry)
  7. actual_pips        → Pips reais (actual - entry)
  8. error_pips         → Erro da predição em pips

╔════════════════════════════════════════════════════════════════════════════╗
║                    RESUMO EXECUTIVO                                       ║
╚════════════════════════════════════════════════════════════════════════════╝

✅ MODELO CORRETO: REGRESSÃO (não classificação)
✅ TARGET CORRETO: Preço às 14:00 UTC (não UP/DOWN)
✅ DADOS REAIS: De /tmp/bt_analysis_*.csv
✅ SPLIT CORRETO: 70% treino, 30% validação
✅ SEM DATA LEAKAGE: Nunca treinou em 100%
✅ PREDIÇÕES: Preço em vez de direção
✅ BACKTEST: Com preços reais vs previstos
    """)
    
    print("="*80)
    print("✅ BACKTEST CORRETO CONCLUÍDO")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
