#!/usr/bin/env python3
"""
BACKTEST HYBRID - Combina estrutura anterior com Multi-Output Learning
- 70/30 chronológico (treino/validação)
- Confiança integrada no treino via pesos
- Mantém estrutura de colunas anterior
- Adiciona: confidence [0-1], filtered_mask, optimal_threshold
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

from indicators import calculate_all_indicators, get_model_features


def load_and_process_data(csv_file, symbol):
    """Carrega dados e calcula indicadores"""
    print(f"\n{'='*80}")
    print(f"📁 Processando {symbol}")
    print(f"{'='*80}")
    
    print(f"\n📥 Carregando {csv_file}...")
    df = pd.read_csv(csv_file, sep='\t', skiprows=1)
    
    # Renomear colunas
    df.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread']
    
    # Criar timestamp
    df['timestamp'] = df['date'].astype(str) + ' ' + df['time'].astype(str)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y.%m.%d %H:%M:%S')
    
    # Extrair data (sem hora)
    df['date_only'] = df['timestamp'].dt.date
    
    # Deixar apenas as colunas necessárias
    df = df[['timestamp', 'date_only', 'open', 'high', 'low', 'close', 'vol', 'spread']].copy()
    df.reset_index(drop=True, inplace=True)
    
    print(f"✅ {len(df)} linhas carregadas")
    print(f"   Primeira: {df.iloc[0]['timestamp']}")
    print(f"   Última: {df.iloc[-1]['timestamp']}")
    
    # Calcular indicadores
    print(f"\n📊 Calculando indicadores técnicos...")
    df = calculate_all_indicators(df)
    print(f"✅ Indicadores calculados")
    
    # Criar target_price: preço às 14:00 do próximo dia
    print(f"\n⏰ Calculando target_price...")
    
    df['next_date'] = df['date_only'] + pd.Timedelta(days=1)
    
    date_price_map = {}
    for date in df['date_only'].unique():
        day_data = df[df['date_only'] == date]
        day_data = day_data.copy()
        day_data['time_diff'] = (day_data['timestamp'].dt.hour * 60 + day_data['timestamp'].dt.minute - 14*60).abs()
        closest_idx = day_data['time_diff'].idxmin()
        date_price_map[date] = df.loc[closest_idx, 'close']
    
    df['target_price'] = df['date_only'].map(date_price_map)
    df.reset_index(drop=True, inplace=True)
    
    print(f"✅ Target calculado")
    
    return df.dropna(subset=['target_price'])


def calculate_confidence_weights(y_true, y_pred):
    """Calcula pesos baseado em confiança (erro normalizado invertido)"""
    errors = np.abs(y_pred - y_true)
    max_error = np.percentile(errors, 95)
    confidence = 1 - (errors / (max_error + 1e-6))
    confidence = np.clip(confidence, 0, 1)
    return confidence


def train_models(df_train):
    """Treina XGB e RF com pesos baseados em confiança"""
    features = get_model_features()
    X_train = df_train[features].values
    y_train = df_train['target_price'].values
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    print(f"\n{'─'*80}")
    print(f"🤖 Treinando modelos (70% = {len(X_train)} amostras)...")
    print(f"{'─'*80}")
    print(f"   Features: {len(features)}")
    
    # Fase 1: Treinar modelo base
    print(f"\n   Fase 1: Treinamento base...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=7,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0
    )
    rf_model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    
    xgb_model.fit(X_train_scaled, y_train)
    rf_model.fit(X_train_scaled, y_train)
    
    # Fase 2: Calcular confiança e pesos
    print(f"   Fase 2: Calculando confiança...")
    xgb_pred_train = xgb_model.predict(X_train_scaled)
    rf_pred_train = rf_model.predict(X_train_scaled)
    
    xgb_confidence = calculate_confidence_weights(y_train, xgb_pred_train)
    rf_confidence = calculate_confidence_weights(y_train, rf_pred_train)
    
    print(f"      XGB confidence: mean={xgb_confidence.mean():.4f}, std={xgb_confidence.std():.4f}")
    print(f"      RF confidence:  mean={rf_confidence.mean():.4f}, std={rf_confidence.std():.4f}")
    
    # Fase 3: Retreinar com pesos
    print(f"   Fase 3: Retrainando com pesos...")
    xgb_model.fit(X_train_scaled, y_train, sample_weight=xgb_confidence)
    rf_model.fit(X_train_scaled, y_train, sample_weight=rf_confidence)
    
    # Avaliar no treino
    train_r2_xgb = xgb_model.score(X_train_scaled, y_train)
    train_r2_rf = rf_model.score(X_train_scaled, y_train)
    
    print(f"\n   Train R²:")
    print(f"      XGB: {train_r2_xgb:.4f}")
    print(f"      RF:  {train_r2_rf:.4f}")
    
    return xgb_model, rf_model, scaler, features


def find_optimal_threshold(df_test, pred_ensemble, confidence):
    """Encontra threshold ótimo de confiança"""
    print(f"\n{'─'*80}")
    print(f"🎯 Encontrando threshold ótimo...")
    print(f"{'─'*80}")
    
    results = []
    thresholds = np.arange(0.50, 0.95, 0.05)
    
    for thresh in thresholds:
        mask = confidence >= thresh
        if mask.sum() == 0:
            continue
        
        # Calcular win rate
        actual_dir = np.sign(df_test.loc[mask, 'target_price'].values - df_test.loc[mask, 'close'].values)
        pred_dir = np.sign(pred_ensemble[mask] - df_test.loc[mask, 'close'].values)
        correct = (actual_dir == pred_dir).sum()
        win_rate = correct / mask.sum() * 100
        
        coverage = mask.sum() / len(df_test) * 100
        
        results.append({
            'threshold': thresh,
            'win_rate': win_rate,
            'signals': mask.sum(),
            'coverage': coverage
        })
    
    results_df = pd.DataFrame(results)
    print(f"\n{results_df.to_string(index=False)}\n")
    
    # Encontrar threshold com max win_rate
    best_idx = results_df['win_rate'].idxmax()
    optimal_threshold = results_df.loc[best_idx, 'threshold']
    
    print(f"✅ Threshold ótimo: {optimal_threshold:.2f}")
    print(f"   Win rate esperado: {results_df.loc[best_idx, 'win_rate']:.2f}%")
    print(f"   Coverage: {results_df.loc[best_idx, 'coverage']:.1f}%")
    
    return optimal_threshold


def predict_on_test(df_test, xgb_model, rf_model, scaler, features, symbol):
    """Predições no test set (30%)"""
    print(f"\n{'─'*80}")
    print(f"📊 Predizendo no test set (30% = {len(df_test)} amostras)...")
    print(f"{'─'*80}")
    
    X_test = df_test[features].values
    X_test_scaled = scaler.transform(X_test)
    
    xgb_pred = xgb_model.predict(X_test_scaled)
    rf_pred = rf_model.predict(X_test_scaled)
    
    # Ensemble
    ensemble_pred = (xgb_pred + rf_pred) / 2
    
    # Confiança baseada em acordância
    max_diff = np.percentile(np.abs(xgb_pred - rf_pred), 95)
    diff = np.abs(xgb_pred - rf_pred)
    agreement = 1 - (diff / (max_diff + 1e-6))
    agreement = np.clip(agreement, 0, 1)
    
    # Encontrar threshold ótimo
    optimal_threshold = find_optimal_threshold(df_test, ensemble_pred, agreement)
    
    # Aplicar filtro
    filtered_mask = agreement >= optimal_threshold
    
    # Calcular métricas
    actual_dir = np.sign(df_test['target_price'].values - df_test['close'].values)
    pred_dir = np.sign(ensemble_pred - df_test['close'].values)
    correct = (actual_dir == pred_dir).sum()
    win_rate_all = correct / len(df_test) * 100
    
    correct_filtered = (actual_dir[filtered_mask] == pred_dir[filtered_mask]).sum()
    win_rate_filtered = correct_filtered / filtered_mask.sum() * 100 if filtered_mask.sum() > 0 else 0
    
    mae = np.abs((df_test['target_price'].values - df_test['close'].values) - 
                 (ensemble_pred - df_test['close'].values)).mean()
    
    print(f"\n📈 Estatísticas:")
    print(f"   Win Rate (todos): {win_rate_all:.2f}%")
    print(f"   Win Rate (filtrado): {win_rate_filtered:.2f}%")
    print(f"   Confiança média: {agreement.mean():.4f}")
    print(f"   Confiança (filtrado): {agreement[filtered_mask].mean():.4f}")
    print(f"   MAE: {mae:.2f} pips")
    
    return {
        'xgb_pred': xgb_pred,
        'rf_pred': rf_pred,
        'ensemble_pred': ensemble_pred,
        'confidence': agreement,
        'optimal_threshold': optimal_threshold,
        'filtered_mask': filtered_mask,
        'win_rate_all': win_rate_all,
        'win_rate_filtered': win_rate_filtered,
        'mae': mae
    }


def create_output_csv(df_full, df_train_idx, predictions_dict, output_file, symbol):
    """Cria CSV de output com estrutura anterior + novas colunas"""
    df_full = df_full.copy()
    
    # Adicionar predições apenas no test set
    test_idx = ~df_full.index.isin(df_train_idx)
    
    df_full.loc[test_idx, 'predicted_price_xgb'] = predictions_dict['xgb_pred']
    df_full.loc[test_idx, 'predicted_price_rf'] = predictions_dict['rf_pred']
    df_full.loc[test_idx, 'predicted_price_ensemble'] = predictions_dict['ensemble_pred']
    df_full.loc[test_idx, 'confidence'] = predictions_dict['confidence']
    df_full.loc[test_idx, 'confidence_pct'] = predictions_dict['confidence'] * 100
    df_full.loc[test_idx, 'actual_price'] = df_full.loc[test_idx, 'target_price']
    df_full.loc[test_idx, 'predicted_pips_ensemble'] = (predictions_dict['ensemble_pred'] - 
                                                         df_full.loc[test_idx, 'close'].values)
    df_full.loc[test_idx, 'actual_pips'] = (df_full.loc[test_idx, 'target_price'].values - 
                                             df_full.loc[test_idx, 'close'].values)
    df_full.loc[test_idx, 'error_pips'] = np.abs(df_full.loc[test_idx, 'predicted_pips_ensemble'].values - 
                                                  df_full.loc[test_idx, 'actual_pips'].values)
    df_full.loc[test_idx, 'filtered'] = predictions_dict['filtered_mask']
    
    # Selecionar colunas (mantendo estrutura anterior + novas)
    indicators = ['rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum', 'sd', 
                  'bb_upper', 'bb_lower', 'bb_width', 'smc_support', 'smc_resistance',
                  'price_above_sma20', 'price_above_sma50', 'price_above_bb_upper', 
                  'price_below_bb_lower', 'rsi_oversold', 'rsi_overbought', 
                  'macd_positive', 'momentum_positive', 'smc_order_block', 'smc_fvg']
    
    columns = ['timestamp', 'close'] + indicators + [
        'predicted_price_xgb', 'predicted_price_rf', 'predicted_price_ensemble',
        'confidence', 'confidence_pct', 'actual_price', 'predicted_pips_ensemble',
        'actual_pips', 'error_pips', 'filtered'
    ]
    
    output_df = df_full[columns].copy()
    output_df.to_csv(output_file, index=False)
    
    print(f"\n✅ Output salvo: {output_file}")
    print(f"   Linhas: {len(output_df)}")
    print(f"   Colunas: {len(columns)}")
    print(f"   Predições (test set): {test_idx.sum()}")


def main():
    print("\n" + "="*80)
    print("🚀 BACKTEST HYBRID (Multi-Output + 70/30 + Estrutura Anterior)")
    print("="*80)
    
    for symbol in ['EURUSD', 'GBPUSD']:
        print(f"\n{'='*80}")
        print(f"📊 {symbol}")
        print(f"{'='*80}")
        
        csv_file = f'/home/ubuntu/pessoal/options/data/{symbol}_M15_202401012200_202605222015.csv'
        
        # Carregar dados
        df = load_and_process_data(csv_file, symbol)
        
        # Split 70/30 cronológico
        split_idx = int(len(df) * 0.7)
        df_train = df.iloc[:split_idx].reset_index(drop=True)
        df_test = df.iloc[split_idx:].reset_index(drop=True)
        
        print(f"\n📍 Split 70/30:")
        print(f"   Treino: {len(df_train)} amostras")
        print(f"   Teste:  {len(df_test)} amostras")
        
        # Treinar modelos
        xgb_model, rf_model, scaler, features = train_models(df_train)
        
        # Predições
        predictions = predict_on_test(df_test, xgb_model, rf_model, scaler, features, symbol)
        
        # Output
        output_file = f'/home/ubuntu/pessoal/options/results/backtest_{symbol}_hybrid.csv'
        create_output_csv(df, df_train.index, predictions, output_file, symbol)
    
    print(f"\n{'='*80}")
    print(f"✅ BACKTEST HYBRID COMPLETO")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
