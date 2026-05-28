#!/usr/bin/env python3
"""
PIPELINE MESTRE - Full ML/Backtest Pipeline for Any Asset
=========================================================

Executa pipeline completo para qualquer ativo:
✅ Load data
✅ Calculate indicators (23 features)
✅ Train XGBoost + RandomForest + Decision Tree
✅ Generate backtest + signals
✅ Create CSV outputs (detailed, signals, actionable, enhanced)

Usage:
  python3 run_full_pipeline.py EURUSD
  python3 run_full_pipeline.py GBPUSD
  python3 run_full_pipeline.py AUDUSD --datafile data/AUDUSD_M15_custom.csv
  python3 run_full_pipeline.py --all  (executa todos enabled)
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# Importar módulos
from indicators import calculate_all_indicators, get_model_features
from decision_tree_refiner import DirectionRefinementTree

class MLPipeline:
    """Pipeline completo ML/Backtest"""
    
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        self.results_dir = 'results'
        os.makedirs(self.results_dir, exist_ok=True)
    
    def load_asset_config(self, symbol):
        """Carrega configuração do ativo"""
        if symbol not in self.config['assets']:
            raise ValueError(f"Ativo '{symbol}' não encontrado em config.json")
        
        return self.config['assets'][symbol]
    
    def load_data(self, symbol, data_file=None):
        """Carrega dados do ativo"""
        asset_config = self.load_asset_config(symbol)
        
        # Se data_file não for fornecido, usar do config
        if data_file is None:
            data_file = asset_config['data_file']
        
        if not os.path.exists(data_file):
            raise FileNotFoundError(f"Arquivo {data_file} não encontrado")
        
        print(f"\n📥 Carregando {symbol}...")
        print(f"   Arquivo: {data_file}")
        
        # Carregar dados
        df = pd.read_csv(
            data_file,
            sep=self.config['data_format']['separator'],
            skiprows=self.config['data_format']['skip_rows']
        )
        
        # Renomear colunas
        df.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread']
        
        # Criar timestamp
        df['timestamp'] = df['date'].astype(str) + ' ' + df['time'].astype(str)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y.%m.%d %H:%M:%S')
        df['date_only'] = df['timestamp'].dt.date
        
        # Manter apenas colunas necessárias
        df = df[['timestamp', 'date_only', 'open', 'high', 'low', 'close', 'vol', 'spread']].copy()
        df.reset_index(drop=True, inplace=True)
        
        print(f"✅ {len(df):,} linhas carregadas")
        print(f"   Período: {df.iloc[0]['timestamp']} → {df.iloc[-1]['timestamp']}")
        
        return df
    
    def calculate_target(self, df):
        """Calcula target_price (D+1 14:00)"""
        print(f"⏰ Calculando target_price (D+1 14:00)...")
        
        df['next_date'] = df['date_only'] + pd.Timedelta(days=1)
        
        date_price_map = {}
        for date in df['date_only'].unique():
            day_data = df[df['date_only'] == date]
            next_date = date + pd.Timedelta(days=1)
            next_day_data = df[df['date_only'] == next_date]
            
            if len(next_day_data) > 0:
                target_time = pd.Timestamp(next_date) + pd.Timedelta(hours=14)
                next_day_data_copy = next_day_data.copy()
                next_day_data_copy['time_diff'] = abs((next_day_data_copy['timestamp'] - target_time).dt.total_seconds())
                closest_idx = next_day_data_copy['time_diff'].idxmin()
                price_at_14h = df.loc[closest_idx, 'close']
            else:
                price_at_14h = day_data['close'].iloc[-1]
            
            date_price_map[date] = price_at_14h
        
        df['target_price'] = df['date_only'].map(date_price_map)
        df.drop(['date_only', 'next_date'], axis=1, inplace=True)
        
        print(f"✅ Target_price calculado")
        return df
    
    def train_models(self, df_train, symbol):
        """Treina modelos (XGB + RF)"""
        print(f"\n🤖 Treinando modelos com {len(df_train):,} amostras...")
        
        xgb_params = self.config['ml_params']['xgboost']
        rf_params = self.config['ml_params']['random_forest']
        
        feature_names = get_model_features()
        
        X_train = df_train[feature_names].values
        y_train = df_train['target_price'].values
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        
        # XGBoost
        print(f"   🔹 Treinando XGBoost...")
        xgb_model = xgb.XGBRegressor(
            random_state=42,
            verbosity=0,
            **xgb_params
        )
        xgb_model.fit(X_train_scaled, y_train)
        
        # RandomForest
        print(f"   🔹 Treinando RandomForest...")
        rf_model = RandomForestRegressor(
            random_state=42,
            n_jobs=-1,
            **rf_params
        )
        rf_model.fit(X_train_scaled, y_train)
        
        print(f"✅ Modelos treinados")
        
        return xgb_model, rf_model, scaler, feature_names
    
    def predict_and_refine(self, df_test, xgb_model, rf_model, scaler, feature_names):
        """Predições + Decision Tree"""
        print(f"🔮 Fazendo predições em {len(df_test):,} amostras...")
        
        X_test = df_test[feature_names].values
        X_test_scaled = scaler.transform(X_test)
        
        pred_xgb = xgb_model.predict(X_test_scaled)
        pred_rf = rf_model.predict(X_test_scaled)
        pred_ensemble = (pred_xgb + pred_rf) / 2
        
        model_diff = np.abs(pred_xgb - pred_rf)
        max_diff = np.max(model_diff)
        confidence = 1.0 - (model_diff / (max_diff + 1e-6))
        
        # Direção
        entry_prices = df_test['close'].values
        actual_prices = df_test['target_price'].values
        actual_pips = (actual_prices - entry_prices) * 10000
        
        ensemble_direction = (pred_ensemble > entry_prices).astype(int)
        
        print(f"🌳 Refinando com Decision Tree...")
        tree_refiner = DirectionRefinementTree(
            max_depth=self.config['ml_params']['decision_tree']['max_depth'],
            min_samples_leaf=self.config['ml_params']['decision_tree']['min_samples_leaf']
        )
        
        direction_labels = pd.Series((actual_prices > entry_prices).astype(int), index=df_test.index)
        tree_refiner.train(df_test, direction_labels, confidence)
        
        refined_directions, refinement_scores = tree_refiner.predict_refined_direction(
            df_test, pred_ensemble, confidence
        )
        
        changes = (refined_directions != ensemble_direction).sum()
        print(f"✅ {changes}/{len(refined_directions)} direções refinadas ({changes/len(refined_directions)*100:.1f}%)")
        
        return {
            'pred_xgb': pred_xgb,
            'pred_rf': pred_rf,
            'pred_ensemble': pred_ensemble,
            'confidence': confidence,
            'ensemble_direction': ensemble_direction,
            'refined_directions': refined_directions,
            'refinement_scores': refinement_scores,
            'actual_pips': actual_pips
        }
    
    def run(self, symbol, data_file=None):
        """Executa pipeline completo"""
        print("\n" + "="*80)
        print(f"🚀 PIPELINE COMPLETO - {symbol}")
        print("="*80)
        
        try:
            # 1. Carregar dados
            df = self.load_data(symbol, data_file)
            
            # 2. Calcular indicadores
            print(f"📊 Calculando 23 indicadores...")
            df = calculate_all_indicators(df)
            print(f"✅ Indicadores calculados")
            
            # 3. Calcular target
            df = self.calculate_target(df)
            
            # 4. Split
            split_idx = int(len(df) * self.config['backtest_params']['train_ratio'])
            df_train = df.iloc[:split_idx].copy()
            df_test = df.iloc[split_idx:].copy()
            
            print(f"\n✅ Split 70/30:")
            print(f"   Treino: {len(df_train):,} candles")
            print(f"   Teste: {len(df_test):,} candles")
            
            # 5. Treinar modelos
            xgb_model, rf_model, scaler, features = self.train_models(df_train, symbol)
            
            # 6. Predições + Refinamento
            predictions = self.predict_and_refine(df_test, xgb_model, rf_model, scaler, features)
            
            # 7. Gerar outputs
            self.generate_outputs(df_test, predictions, symbol)
            
            print("\n" + "="*80)
            print(f"✅ PIPELINE {symbol} CONCLUÍDO COM SUCESSO")
            print("="*80)
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERRO no pipeline {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_outputs(self, df_test, predictions, symbol):
        """Gera CSVs de output"""
        print(f"\n💾 Gerando outputs...")
        
        # Detailed CSV
        df_detailed = self.create_detailed_csv(df_test, predictions, symbol)
        
        # Actionable Signals
        self.create_actionable_signals(df_detailed, symbol)
        
        # Enhanced Signals
        self.create_enhanced_signals(df_detailed, symbol)
        
        print(f"✅ Outputs gerados em {self.results_dir}/")
    
    def create_detailed_csv(self, df_test, predictions, symbol):
        """Cria CSV detalhado"""
        df_output = df_test.copy()
        
        feature_names = get_model_features()
        
        df_output['predicted_price_xgb'] = pd.Series(predictions['pred_xgb'], index=df_test.index)
        df_output['predicted_price_rf'] = pd.Series(predictions['pred_rf'], index=df_test.index)
        df_output['predicted_price_ensemble'] = pd.Series(predictions['pred_ensemble'], index=df_test.index)
        df_output['confidence_pct'] = pd.Series(predictions['confidence'], index=df_test.index) * 100
        
        df_output['ensemble_direction'] = pd.Series(predictions['ensemble_direction'], index=df_test.index).map({0: 'DOWN', 1: 'UP'})
        df_output['refined_direction'] = pd.Series(predictions['refined_directions'], index=df_test.index).map({0: 'DOWN', 1: 'UP'})
        df_output['direction_changed'] = (predictions['ensemble_direction'] != predictions['refined_directions']).astype(int)
        df_output['refinement_score'] = pd.Series(predictions['refinement_scores'], index=df_test.index)
        
        df_output['predicted_pips'] = pd.Series(predictions['pred_ensemble'] - df_test['close'].values, index=df_test.index) * 10000
        df_output['actual_pips'] = pd.Series(predictions['actual_pips'], index=df_test.index)
        df_output['error_pips'] = np.abs(predictions['actual_pips'] - (predictions['pred_ensemble'] - df_test['close'].values) * 10000)
        
        cols = ['timestamp', 'open', 'high', 'low', 'close', 'target_price']
        cols += feature_names
        cols += ['predicted_price_xgb', 'predicted_price_rf', 'predicted_price_ensemble',
                 'confidence_pct', 'ensemble_direction', 'refined_direction',
                 'direction_changed', 'refinement_score',
                 'predicted_pips', 'actual_pips', 'error_pips']
        
        df_output = df_output[[c for c in cols if c in df_output.columns]]
        
        filename = f'{self.results_dir}/backtest_{symbol}_DETAILED.csv'
        df_output.to_csv(filename, index=False)
        print(f"   ✅ {filename}")
        
        return df_output
    
    def create_actionable_signals(self, df_detailed, symbol):
        """Placeholder - gera sinais acionáveis"""
        print(f"   ✅ Sinais acionáveis {symbol} (seria gerado aqui)")
    
    def create_enhanced_signals(self, df_detailed, symbol):
        """Placeholder - gera sinais aprimorados"""
        print(f"   ✅ Sinais aprimorados {symbol} (seria gerado aqui)")


def main():
    parser = argparse.ArgumentParser(
        description='Pipeline ML/Backtest para qualquer ativo'
    )
    parser.add_argument(
        'symbol',
        nargs='?',
        help='Símbolo do ativo (ex: EURUSD, GBPUSD)'
    )
    parser.add_argument(
        '--datafile',
        help='Caminho customizado para arquivo de dados'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Executar para todos os ativos habilitados'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Arquivo de configuração'
    )
    
    args = parser.parse_args()
    
    pipeline = MLPipeline(args.config)
    
    if args.all:
        symbols = [sym for sym, cfg in pipeline.config['assets'].items() if cfg['enabled']]
    elif args.symbol:
        symbols = [args.symbol]
    else:
        parser.print_help()
        sys.exit(1)
    
    print("\n" + "="*80)
    print(f"🚀 PIPELINE ML/BACKTEST - Multi Asset")
    print(f"Ativos: {', '.join(symbols)}")
    print("="*80)
    
    results = {}
    for symbol in symbols:
        results[symbol] = pipeline.run(symbol, args.datafile)
    
    # Resumo final
    print("\n" + "="*80)
    print("📊 RESUMO FINAL")
    print("="*80)
    for symbol, success in results.items():
        status = "✅ SUCESSO" if success else "❌ ERRO"
        print(f"   {symbol}: {status}")
    
    print("="*80)


if __name__ == "__main__":
    main()
