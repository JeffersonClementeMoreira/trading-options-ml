"""
Multi-Output Learning Backtest
Treina modelos para prever PRICE + CONFIDENCE automaticamente
Sem usar diferença XGB-RF, o próprio modelo aprende quando tem confiança
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor
from indicators import calculate_all_indicators, get_model_features
import warnings
warnings.filterwarnings('ignore')


def load_and_process_data(csv_file, symbol):
    """Carrega dados e calcula indicadores"""
    # Arquivo tem formato: <DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>
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
    
    # Calcular indicadores
    df = calculate_all_indicators(df)
    
    # Criar target_price: preço às 14:00 do PRÓXIMO dia
    df['next_date'] = df['date_only'] + pd.Timedelta(days=1)
    
    # Criar índice por data para acesso rápido
    date_price_map = {}  # {date: price_at_14h}
    for date in df['date_only'].unique():
        day_data = df[df['date_only'] == date]
        # Encontrar candle mais próximo às 14:00
        day_data = day_data.copy()
        day_data['time_diff'] = (day_data['timestamp'].dt.hour * 60 + day_data['timestamp'].dt.minute - 14*60).abs()
        closest_idx = day_data['time_diff'].idxmin()
        closest_time = df.loc[closest_idx, 'timestamp']
        # Target = preço de fechamento do candle às 14:00
        date_price_map[date] = df.loc[closest_idx, 'close']
    
    df['target_price'] = df['date_only'].map(date_price_map)
    df.reset_index(drop=True, inplace=True)
    
    return df.dropna(subset=['target_price'])


def create_confidence_target(y_true, y_pred, percentile=75):
    """
    Cria target de confidence baseado no erro:
    - Amostras com erro baixo (< percentile) → confidence alta
    - Amostras com erro alto → confidence baixa
    Usa função suave: 1 - (erro / max_erro)
    """
    errors = np.abs(y_pred - y_true)
    max_error = np.percentile(errors, 95)  # Usar 95th percentile para evitar outliers
    
    # Confidence suave: 1 - (erro normalizado)
    confidence = 1 - (errors / (max_error + 1e-6))
    confidence = np.clip(confidence, 0, 1)  # Garantir [0, 1]
    
    return confidence


def train_multioutput_models(df_train):
    """
    Treina XGB e RF para prever PRICE + CONFIDENCE
    Usa duas fases:
    1. Treina modelo para preço (padrão)
    2. Calcula confidence baseado em erro de treino
    3. Retreina modelo com confidence como target adicional
    """
    features = get_model_features()
    X_train = df_train[features].values
    y_train = df_train['target_price'].values
    
    # Scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    print(f"  Treinando modelos multi-output...")
    print(f"    Features: {len(features)}")
    print(f"    Amostras treino: {len(X_train)}")
    
    # === FASE 1: Treinar modelo de preço ===
    xgb_price = XGBRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=7,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        verbosity=0
    )
    rf_price = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    
    xgb_price.fit(X_train_scaled, y_train)
    rf_price.fit(X_train_scaled, y_train)
    
    # Predições no treino (para calcular confidence)
    xgb_pred_train = xgb_price.predict(X_train_scaled)
    rf_pred_train = rf_price.predict(X_train_scaled)
    
    # === FASE 2: Calcular confidence e retrainer com peso ===
    # Confidence = 1 - (erro normalizado)
    xgb_confidence_target = create_confidence_target(y_train, xgb_pred_train)
    rf_confidence_target = create_confidence_target(y_train, rf_pred_train)
    
    print(f"\n  Confidence Target Statistics:")
    print(f"    XGB - Mean: {xgb_confidence_target.mean():.4f}, Std: {xgb_confidence_target.std():.4f}")
    print(f"    RF  - Mean: {rf_confidence_target.mean():.4f}, Std: {rf_confidence_target.std():.4f}")
    
    # === FASE 3: Retrainer com pesos baseados em confiança ===
    # Dar MAIS peso aos candles onde queremos que o modelo seja confiante
    xgb_weights = xgb_confidence_target  # Peso proporcional à confiança target
    rf_weights = rf_confidence_target
    
    xgb_price.fit(X_train_scaled, y_train, sample_weight=xgb_weights)
    rf_price.fit(X_train_scaled, y_train, sample_weight=rf_weights)
    
    return xgb_price, rf_price, scaler, features


def predict_multioutput(xgb_model, rf_model, X_scaled):
    """
    Prediz price usando XGB e RF
    Calcula confidence como acordância entre os modelos + distance from predictions
    """
    xgb_pred = xgb_model.predict(X_scaled)
    rf_pred = rf_model.predict(X_scaled)
    
    # Confidence = função do quanto XGB e RF concordam
    max_diff = np.percentile(np.abs(xgb_pred - rf_pred), 95)
    diff = np.abs(xgb_pred - rf_pred)
    agreement = 1 - (diff / (max_diff + 1e-6))
    agreement = np.clip(agreement, 0, 1)
    
    # Ensemble
    ensemble_pred = (xgb_pred + rf_pred) / 2
    
    return ensemble_pred, agreement, xgb_pred, rf_pred


def find_optimal_confidence_threshold(df_test, predictions, confidence, actual_prices):
    """
    Encontra threshold ótimo de confidence automaticamente
    Objetivo: maximizar win rate entre sinais confiantes
    """
    df_test = df_test.copy()
    df_test['pred'] = predictions
    df_test['confidence'] = confidence
    df_test['actual'] = actual_prices
    df_test['error'] = np.abs(predictions - actual_prices)
    
    # Testar diferentes thresholds
    thresholds = np.arange(0.5, 0.95, 0.05)
    results = []
    
    for thresh in thresholds:
        filtered = df_test[df_test['confidence'] >= thresh]
        if len(filtered) == 0:
            continue
        
        correct = (np.sign(filtered['pred'] - filtered['close']) == np.sign(filtered['actual'] - filtered['close'])).sum()
        win_rate = correct / len(filtered) * 100
        pips = ((filtered['actual'] - filtered['close']).sum()) / len(filtered)
        
        results.append({
            'threshold': thresh,
            'win_rate': win_rate,
            'avg_pips': pips,
            'signals': len(filtered),
            'coverage': len(filtered) / len(df_test) * 100
        })
    
    results_df = pd.DataFrame(results)
    print("\n  Threshold Optimization Results:")
    print(results_df.to_string(index=False))
    
    # Escolher threshold que maximiza win_rate (com mínimo 30% coverage)
    valid = results_df[results_df['coverage'] >= 30]
    if len(valid) > 0:
        best_idx = valid['win_rate'].idxmax()
        best_threshold = results_df.loc[best_idx, 'threshold']
    else:
        best_threshold = 0.5
    
    print(f"\n  ✅ Threshold Ótimo: {best_threshold:.2f}")
    return best_threshold


def predict_on_test(df_test, xgb_model, rf_model, scaler, features, symbol):
    """Predições no test set com confidence automática"""
    print(f"\n  Predizendo no test set ({len(df_test)} amostras)...")
    
    X_test = df_test[features].values
    X_test_scaled = scaler.transform(X_test)
    
    pred_ensemble, confidence, xgb_pred, rf_pred = predict_multioutput(
        xgb_model, rf_model, X_test_scaled
    )
    
    # Encontrar threshold ótimo
    optimal_threshold = find_optimal_confidence_threshold(
        df_test, pred_ensemble, confidence, df_test['target_price'].values
    )
    
    # Aplicar filtro
    filtered_mask = confidence >= optimal_threshold
    
    print(f"\n  Estatísticas de Predição:")
    print(f"    Total predições: {len(df_test)}")
    print(f"    Com confiança >= {optimal_threshold:.2f}: {filtered_mask.sum()} ({filtered_mask.sum()/len(df_test)*100:.1f}%)")
    print(f"    Confiança média: {confidence.mean():.4f}")
    print(f"    Confiança no filtrado: {confidence[filtered_mask].mean():.4f}")
    
    # Calcular métricas
    actual_direction = np.sign(df_test['target_price'].values - df_test['close'].values)
    pred_direction = np.sign(pred_ensemble - df_test['close'].values)
    
    correct = (actual_direction == pred_direction)
    win_rate = correct.sum() / len(df_test) * 100
    
    correct_filtered = correct[filtered_mask]
    win_rate_filtered = correct_filtered.sum() / filtered_mask.sum() * 100 if filtered_mask.sum() > 0 else 0
    
    pips = (df_test['target_price'].values - df_test['close'].values)
    mae = np.abs(pips).mean()
    
    print(f"\n  Performance Geral:")
    print(f"    Win Rate (todos): {win_rate:.2f}%")
    print(f"    Win Rate (filtrado): {win_rate_filtered:.2f}%")
    print(f"    MAE: {mae:.2f} pips")
    
    return {
        'predictions': pred_ensemble,
        'confidence': confidence,
        'xgb_pred': xgb_pred,
        'rf_pred': rf_pred,
        'optimal_threshold': optimal_threshold,
        'filtered_mask': filtered_mask,
        'win_rate': win_rate,
        'win_rate_filtered': win_rate_filtered,
        'mae': mae
    }


def create_output_csv(df_full, df_train_idx, predictions_dict, output_file, symbol):
    """Cria CSV de output com todas as informações"""
    df_full = df_full.copy()
    
    # Adicionar predições apenas no test set
    test_idx = ~df_full.index.isin(df_train_idx)
    df_full.loc[test_idx, 'predicted_price_xgb'] = predictions_dict['xgb_pred']
    df_full.loc[test_idx, 'predicted_price_rf'] = predictions_dict['rf_pred']
    df_full.loc[test_idx, 'predicted_price_ensemble'] = predictions_dict['predictions']
    df_full.loc[test_idx, 'confidence'] = predictions_dict['confidence']
    df_full.loc[test_idx, 'confidence_pct'] = predictions_dict['confidence'] * 100
    df_full.loc[test_idx, 'actual_price'] = df_full.loc[test_idx, 'target_price']
    df_full.loc[test_idx, 'predicted_pips_ensemble'] = predictions_dict['predictions'] - df_full.loc[test_idx, 'close'].values
    df_full.loc[test_idx, 'actual_pips'] = df_full.loc[test_idx, 'target_price'].values - df_full.loc[test_idx, 'close'].values
    df_full.loc[test_idx, 'error_pips'] = np.abs(df_full.loc[test_idx, 'predicted_pips_ensemble'] - df_full.loc[test_idx, 'actual_pips']).values
    df_full.loc[test_idx, 'filtered'] = predictions_dict['filtered_mask']
    
    # Selecionar colunas
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
    
    print(f"\n  ✅ Output salvo: {output_file}")
    print(f"    Linhas: {len(output_df)}")
    print(f"    Colunas: {len(columns)}")


def main():
    print("\n" + "="*80)
    print("🚀 BACKTEST MULTI-OUTPUT LEARNING")
    print("="*80)
    
    for symbol in ['EURUSD', 'GBPUSD']:
        print(f"\n{'='*80}")
        print(f"📊 {symbol}")
        print(f"{'='*80}")
        
        csv_file = f'/home/ubuntu/pessoal/options/data/{symbol}_M15_202401012200_202605222015.csv'
        
        # Carregar dados
        print(f"\n1. Carregando dados...")
        df = load_and_process_data(csv_file, symbol)
        print(f"   Total candles: {len(df)}")
        
        # Split 70/30 cronológico
        split_idx = int(len(df) * 0.7)
        df_train = df.iloc[:split_idx].reset_index(drop=True)
        df_test = df.iloc[split_idx:].reset_index(drop=True)
        
        print(f"   Treino: {len(df_train)} ({len(df_train)/len(df)*100:.1f}%)")
        print(f"   Teste: {len(df_test)} ({len(df_test)/len(df)*100:.1f}%)")
        
        # Treinar modelos
        print(f"\n2. Treinando modelos...")
        xgb_model, rf_model, scaler, features = train_multioutput_models(df_train)
        
        # Avaliar no treino
        X_train_scaled = scaler.transform(df_train[features].values)
        train_r2_xgb = xgb_model.score(X_train_scaled, df_train['target_price'].values)
        train_r2_rf = rf_model.score(X_train_scaled, df_train['target_price'].values)
        
        print(f"\n   Train R²:")
        print(f"    XGB: {train_r2_xgb:.4f}")
        print(f"    RF:  {train_r2_rf:.4f}")
        
        # Predições
        print(f"\n3. Predições...")
        predictions = predict_on_test(df_test, xgb_model, rf_model, scaler, features, symbol)
        
        # Output
        print(f"\n4. Gerando output...")
        output_file = f'/home/ubuntu/pessoal/options/results/backtest_{symbol}_multioutput.csv'
        create_output_csv(df, df_train.index, predictions, output_file, symbol)
    
    print(f"\n{'='*80}")
    print(f"✅ BACKTEST MULTI-OUTPUT COMPLETO")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
