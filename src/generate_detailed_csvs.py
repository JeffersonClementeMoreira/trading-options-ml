#!/usr/bin/env python3
"""
GENERATE DETAILED CSVs - Gerar CSVs Completos com Análise Detalhada
===================================================================

Gera CSVs com:
- 23 indicadores técnicos
- 3 predições (XGB, RF, Ensemble)
- Decision Tree refinement
- Confiança e confluence
- Pips reais vs preditos
- Status de sinais
- Análise detalhada
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

from indicators import calculate_all_indicators, get_model_features
from decision_tree_refiner import DirectionRefinementTree, build_direction_features

def load_and_process_data(csv_file, symbol):
    """Carrega dados e calcula indicadores"""
    print(f"\n📥 Carregando {symbol}...")
    df = pd.read_csv(csv_file, sep='\t', skiprows=1)
    
    df.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread']
    df['timestamp'] = df['date'].astype(str) + ' ' + df['time'].astype(str)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y.%m.%d %H:%M:%S')
    df['date_only'] = df['timestamp'].dt.date
    df = df[['timestamp', 'date_only', 'open', 'high', 'low', 'close', 'vol', 'spread']].copy()
    
    print(f"✅ {len(df):,} linhas")
    
    # Indicadores
    print(f"📊 Calculando indicadores...")
    df = calculate_all_indicators(df)
    
    # Target price
    print(f"⏰ Calculando target_price...")
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
    
    return df


def train_models(df_train):
    """Treina modelos"""
    feature_names = get_model_features()
    
    X_train = df_train[feature_names].values
    y_train = df_train['target_price'].values
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    print(f"🔹 Treinando XGBoost...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=300, learning_rate=0.03, max_depth=6,
        subsample=0.85, colsample_bytree=0.85, random_state=42, verbosity=0
    )
    xgb_model.fit(X_train_scaled, y_train)
    
    print(f"🔹 Treinando RandomForest...")
    rf_model = RandomForestRegressor(
        n_estimators=300, max_depth=12, min_samples_split=8,
        min_samples_leaf=4, max_features='sqrt', random_state=42, n_jobs=-1
    )
    rf_model.fit(X_train_scaled, y_train)
    
    return xgb_model, rf_model, scaler, feature_names


def predict_and_refine(df_test, xgb_model, rf_model, scaler, feature_names):
    """Faz predições e refina com Decision Tree"""
    print(f"🔮 Fazendo predições...")
    
    X_test = df_test[feature_names].values
    X_test_scaled = scaler.transform(X_test)
    
    pred_xgb = xgb_model.predict(X_test_scaled)
    pred_rf = rf_model.predict(X_test_scaled)
    pred_ensemble = (pred_xgb + pred_rf) / 2
    
    model_diff = np.abs(pred_xgb - pred_rf)
    max_diff = np.max(model_diff)
    confidence = 1.0 - (model_diff / (max_diff + 1e-6))
    
    # Pips
    entry_prices = df_test['close'].values
    actual_prices = df_test['target_price'].values
    actual_pips = (actual_prices - entry_prices) * 10000
    pred_pips_ensemble = (pred_ensemble - entry_prices) * 10000
    
    # Direction
    ensemble_direction = (pred_ensemble > entry_prices).astype(int)
    
    print(f"🌳 Refinando com Decision Tree...")
    tree_refiner = DirectionRefinementTree(max_depth=7, min_samples_leaf=50)
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
        'actual_pips': actual_pips,
        'pred_pips_ensemble': pred_pips_ensemble
    }


def create_detailed_csv(df_test, predictions, symbol):
    """Cria CSV detalhado"""
    print(f"\n💾 Gerando CSV detalhado para {symbol}...")
    
    df_output = df_test.copy()
    
    # Adicionar predições
    df_output['predicted_price_xgb'] = pd.Series(predictions['pred_xgb'], index=df_test.index)
    df_output['predicted_price_rf'] = pd.Series(predictions['pred_rf'], index=df_test.index)
    df_output['predicted_price_ensemble'] = pd.Series(predictions['pred_ensemble'], index=df_test.index)
    df_output['confidence_pct'] = pd.Series(predictions['confidence'], index=df_test.index) * 100
    
    # Adicionar direções
    df_output['ensemble_direction'] = pd.Series(predictions['ensemble_direction'], index=df_test.index).map({0: 'DOWN', 1: 'UP'})
    df_output['refined_direction'] = pd.Series(predictions['refined_directions'], index=df_test.index).map({0: 'DOWN', 1: 'UP'})
    df_output['direction_changed'] = (predictions['ensemble_direction'] != predictions['refined_directions']).astype(int)
    df_output['refinement_score'] = pd.Series(predictions['refinement_scores'], index=df_test.index)
    
    # Pips
    df_output['predicted_pips'] = pd.Series(predictions['pred_pips_ensemble'], index=df_test.index)
    df_output['actual_pips'] = pd.Series(predictions['actual_pips'], index=df_test.index)
    df_output['error_pips'] = np.abs(predictions['actual_pips'] - predictions['pred_pips_ensemble'])
    
    # Win/Loss (baseado em refined direction)
    refined_pips = np.where(
        predictions['refined_directions'] == 1,
        predictions['actual_pips'],
        -predictions['actual_pips']
    )
    df_output['refined_pips'] = pd.Series(refined_pips, index=df_test.index)
    df_output['result'] = df_output['refined_pips'].apply(lambda x: 'WIN' if x > 0 else ('LOSS' if x < 0 else 'BREAKEVEN'))
    
    # Reordenar colunas
    feature_names = get_model_features()
    cols = ['timestamp', 'open', 'high', 'low', 'close', 'target_price']
    cols += feature_names
    cols += [
        'predicted_price_xgb', 'predicted_price_rf', 'predicted_price_ensemble',
        'confidence_pct', 'ensemble_direction', 'refined_direction', 
        'direction_changed', 'refinement_score',
        'predicted_pips', 'actual_pips', 'refined_pips', 'error_pips', 'result'
    ]
    
    df_output = df_output[[c for c in cols if c in df_output.columns]]
    
    filename = f'results/backtest_{symbol}_DETAILED.csv'
    df_output.to_csv(filename, index=False)
    
    print(f"✅ {filename} ({len(df_output):,} linhas)")
    
    return df_output, filename


def create_signals_csv(df_output, symbol):
    """Cria CSV apenas com sinais refinados de qualidade"""
    print(f"🎯 Gerando CSV de sinais para {symbol}...")
    
    # Critérios de qualidade
    high_confidence = df_output['confidence_pct'] >= 90
    high_refinement = df_output['refinement_score'] >= 0.6
    
    df_signals = df_output[high_confidence & high_refinement].copy()
    
    # 1 sinal por dia
    df_signals['date'] = df_signals['timestamp'].dt.date
    df_signals = df_signals.sort_values('confidence_pct', ascending=False)
    df_signals = df_signals.drop_duplicates(subset=['date'], keep='first')
    df_signals = df_signals.sort_values('timestamp')
    
    # Colunas essenciais
    df_signals = df_signals[[
        'timestamp', 'close', 'predicted_price_ensemble', 'confidence_pct',
        'refined_direction', 'refinement_score', 'actual_pips', 'refined_pips', 'result'
    ]].copy()
    
    df_signals.columns = [
        'Data/Hora', 'Entrada', 'Target', 'Confiança %', 'Direção',
        'Refinement Score', 'Pips Reais', 'Pips Refinados', 'Resultado'
    ]
    
    filename = f'results/signals_{symbol}_QUALITY.csv'
    df_signals.to_csv(filename, index=False)
    
    print(f"✅ {filename} ({len(df_signals):,} sinais)")
    
    return df_signals, filename


def create_analysis_report(df_output, symbol):
    """Cria relatório de análise"""
    print(f"📊 Gerando relatório de análise para {symbol}...")
    
    win_rate_before = (df_output['actual_pips'] > 0).sum() / len(df_output) * 100
    win_rate_after = (df_output['refined_pips'] > 0).sum() / len(df_output) * 100
    improvement = win_rate_after - win_rate_before
    
    total_pips_before = df_output['actual_pips'].sum()
    total_pips_after = df_output['refined_pips'].sum()
    
    report = f"""
================================================================================
📊 ANÁLISE DETALHADA - {symbol}
================================================================================

🔹 PERFORMANCE GERAL
   Amostras: {len(df_output):,}
   
   Antes (Ensemble):
   ├─ Win Rate: {win_rate_before:.2f}%
   ├─ Total Pips: {total_pips_before:.2f}
   └─ Avg Pips/Trade: {total_pips_before/len(df_output):.2f}
   
   Depois (Decision Tree):
   ├─ Win Rate: {win_rate_after:.2f}%
   ├─ Total Pips: {total_pips_after:.2f}
   └─ Avg Pips/Trade: {total_pips_after/len(df_output):.2f}
   
   Melhoria:
   ├─ Win Rate: {improvement:+.2f}%
   ├─ Total Pips: {total_pips_after - total_pips_before:+.2f}
   └─ Refinamento Rate: {(df_output['direction_changed'].sum() / len(df_output) * 100):.1f}%

🔹 CONFIANÇA
   Média: {df_output['confidence_pct'].mean():.2f}%
   Mínima: {df_output['confidence_pct'].min():.2f}%
   Máxima: {df_output['confidence_pct'].max():.2f}%

🔹 REFINEMENT SCORE
   Média: {df_output['refinement_score'].mean():.4f}
   Mínima: {df_output['refinement_score'].min():.4f}
   Máxima: {df_output['refinement_score'].max():.4f}

🔹 DISTRIBUIÇÃO DE RESULTADOS
   WIN:  {(df_output['result'] == 'WIN').sum():,} ({(df_output['result'] == 'WIN').sum() / len(df_output) * 100:.2f}%)
   LOSS: {(df_output['result'] == 'LOSS').sum():,} ({(df_output['result'] == 'LOSS').sum() / len(df_output) * 100:.2f}%)
   BE:   {(df_output['result'] == 'BREAKEVEN').sum():,} ({(df_output['result'] == 'BREAKEVEN').sum() / len(df_output) * 100:.2f}%)

🔹 PIPS POR RESULTADO
   WIN - Média: {df_output[df_output['result'] == 'WIN']['refined_pips'].mean():.2f} pips
   LOSS - Média: {df_output[df_output['result'] == 'LOSS']['refined_pips'].mean():.2f} pips
   Razão W/L: {abs(df_output[df_output['result'] == 'WIN']['refined_pips'].mean() / df_output[df_output['result'] == 'LOSS']['refined_pips'].mean()):.2f}x

🔹 ERROS DE PREDIÇÃO
   MAE: {df_output['error_pips'].mean():.2f} pips
   RMSE: {(df_output['error_pips']**2).mean()**0.5:.2f} pips

================================================================================
"""
    
    filename = f'results/analysis_{symbol}_REPORT.txt'
    with open(filename, 'w') as f:
        f.write(report)
    
    print(report)
    print(f"✅ {filename} salvo")
    
    return report, filename


def main():
    print("\n" + "="*80)
    print("📊 GENERATE DETAILED CSVs - Gerando CSVs Completos")
    print("="*80)
    
    pairs = [
        ('EURUSD', '/home/ubuntu/pessoal/options/data/EURUSD_M15_202401012200_202605222015.csv'),
        ('GBPUSD', '/home/ubuntu/pessoal/options/data/GBPUSD_M15_202401012200_202605222015.csv')
    ]
    
    for symbol, csv_file in pairs:
        print(f"\n" + "="*80)
        print(f"{symbol}")
        print("="*80)
        
        # Carregar dados
        df = load_and_process_data(csv_file, symbol)
        
        # Split
        split_idx = int(len(df) * 0.70)
        df_train = df.iloc[:split_idx].copy()
        df_test = df.iloc[split_idx:].copy()
        
        # Treinar
        print(f"\n🤖 Treinando modelos...")
        xgb_model, rf_model, scaler, features = train_models(df_train)
        
        # Predições e refinamento
        predictions = predict_and_refine(df_test, xgb_model, rf_model, scaler, features)
        
        # Gerar CSVs
        df_detailed, csv_detailed = create_detailed_csv(df_test, predictions, symbol)
        df_signals, csv_signals = create_signals_csv(df_detailed, symbol)
        report, csv_report = create_analysis_report(df_detailed, symbol)
    
    print("\n" + "="*80)
    print("✅ CSVs DETALHADOS GERADOS COM SUCESSO!")
    print("="*80)
    print("\n📁 Arquivos gerados:")
    print("   • backtest_EURUSD_DETAILED.csv (todas as amostras + análise)")
    print("   • signals_EURUSD_QUALITY.csv (1 sinal/dia high-confidence)")
    print("   • analysis_EURUSD_REPORT.txt (relatório detalhado)")
    print("   • backtest_GBPUSD_DETAILED.csv")
    print("   • signals_GBPUSD_QUALITY.csv")
    print("   • analysis_GBPUSD_REPORT.txt")
    print("="*80)


if __name__ == "__main__":
    main()
