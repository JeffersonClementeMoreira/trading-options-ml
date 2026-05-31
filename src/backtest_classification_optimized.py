#!/usr/bin/env python3
"""
BACKTEST CLASSIFICATION - VERSÃO OTIMIZADA COM THRESHOLDS DINÂMICOS
Com thresholds otimizados por ativo (encontrados via tuning)
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

from indicators import calculate_all_indicators, get_model_features

DATA_DIR = '/home/ubuntu/pessoal/options/data'
RESULTS_DIR = '/home/ubuntu/pessoal/options/results'

# THRESHOLDS OTIMIZADOS POR ATIVO (encontrados via tuning)
OPTIMAL_THRESHOLDS = {
    'EURUSD': 0.85,   # Win Rate: 55.04%
    'GBPUSD': 0.70,   # Win Rate: 53.16%
    'EURAUD': 0.90,   # Win Rate: 53.82%
    'EURJPY': 0.50,   # Default (não foi testado)
    'GOLD': 0.50,     # Default (não foi testado)
    'NZDUSD': 0.50,   # Default (não foi testado)
}

def load_and_process_data(csv_file, symbol):
    print(f"\n{'='*80}")
    print(f"📁 {symbol}")
    print('='*80)
    
    df = pd.read_csv(csv_file, sep='\t', skiprows=1)
    df.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread']
    
    df['timestamp'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str), format='%Y.%m.%d %H:%M:%S')
    df['date_only'] = df['timestamp'].dt.date
    df = df[['timestamp', 'date_only', 'open', 'high', 'low', 'close', 'vol', 'spread']].copy()
    df.reset_index(drop=True, inplace=True)
    
    print(f"✅ {len(df):,} candles | {df['timestamp'].iloc[0]} → {df['timestamp'].iloc[-1]}")
    
    # Indicadores
    print(f"📊 Calculando indicadores...")
    df = calculate_all_indicators(df)
    
    # Target
    print(f"⏰ Calculando target...")
    df['next_date'] = df['date_only'] + pd.Timedelta(days=1)
    date_price_map = {}
    
    for date in df['date_only'].unique():
        next_date = date + pd.Timedelta(days=1)
        mask = (df['date_only'] == next_date)
        if mask.sum() > 0:
            next_day_df = df[mask]
            next_day_timestamps = next_day_df['timestamp'].values
            target_timestamp = pd.Timestamp(date) + pd.Timedelta(hours=24) + pd.Timedelta(hours=14)
            distances = np.abs((next_day_timestamps.astype('datetime64[s]').astype('int64') - 
                              target_timestamp.value // 10**9))
            closest_idx = distances.argmin()
            date_price_map[next_date] = next_day_df.iloc[closest_idx]['close']
    
    df['target_price'] = df['next_date'].map(date_price_map)
    df = df.dropna(subset=['target_price'])
    
    df['direction'] = (df['target_price'] > df['close']).astype(int)
    
    # ✅ FÓRMULA CORRIGIDA: diferencia BUY de SELL
    df['actual_pips'] = np.where(
        df['direction'] == 1,
        (df['target_price'] - df['close']) * 10000,
        (df['close'] - df['target_price']) * 10000
    )
    
    # Distribuição
    buy_count = (df['direction'] == 1).sum()
    sell_count = (df['direction'] == 0).sum()
    print(f"📊 Distribuição: {buy_count:,} BUYs | {sell_count:,} SELLs | Ratio: {buy_count/sell_count:.2f}")
    
    # Split
    split_idx = int(len(df) * 0.70)
    df_train = df.iloc[:split_idx].copy()
    df_test = df.iloc[split_idx:].copy()
    print(f"\n✅ Split: {len(df_train):,} treino | {len(df_test):,} teste")
    print("   Split: 70% treino | 30% teste")
    
    return df_train, df_test

def train_models(df_train):
    feature_names = get_model_features()
    
    X_train = df_train[feature_names].values
    y_train = df_train['direction'].values
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    print(f"\n{'─'*80}\n🤖 Treinando Ensemble (70% treino)\n{'─'*80}")
    
    # XGBoost com balanceamento
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / pos_count
    
    print(f"🔹 XGBoost Classifier (scale_pos_weight={scale_pos_weight:.2f})")
    xgb_model = xgb.XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=1,
        scale_pos_weight=scale_pos_weight, random_state=42,
        verbosity=0, use_label_encoder=False, eval_metric='logloss'
    )
    xgb_model.fit(X_train_scaled, y_train)
    print(f"   ✅ Treinado")
    
    # RandomForest com balanceamento
    print(f"🔹 RandomForest Classifier (class_weight='balanced')")
    rf_model = RandomForestClassifier(
        n_estimators=300, max_depth=8, min_samples_split=10,
        min_samples_leaf=5, class_weight='balanced',
        random_state=42, n_jobs=1
    )
    rf_model.fit(X_train_scaled, y_train)
    print(f"   ✅ Treinado")
    
    return xgb_model, rf_model, scaler, feature_names

def predict_on_test(df_test, xgb_model, rf_model, scaler, feature_names, threshold):
    print(f"\n{'─'*80}\n🔮 Predição no Teste (30%)\n{'─'*80}")
    
    X_test = df_test[feature_names].values
    X_test_scaled = scaler.transform(X_test)
    
    pred_proba_xgb = xgb_model.predict_proba(X_test_scaled)[:, 1]
    pred_proba_rf = rf_model.predict_proba(X_test_scaled)[:, 1]
    
    # Ensemble: média das probabilidades
    pred_proba_ensemble = (pred_proba_xgb + pred_proba_rf) / 2
    
    actual_direction = df_test['direction'].values
    actual_pips = df_test['actual_pips'].values
    
    # Usar threshold otimizado
    pred_direction = (pred_proba_ensemble > threshold).astype(int)
    
    # Calcular resultado (fórmula correta)
    result_pips = np.where(pred_direction == actual_direction, actual_pips, -actual_pips)
    
    # Métricas
    accuracy = accuracy_score(actual_direction, pred_direction)
    precision = precision_score(actual_direction, pred_direction, zero_division=0)
    recall = recall_score(actual_direction, pred_direction, zero_division=0)
    f1 = f1_score(actual_direction, pred_direction, zero_division=0)
    
    wins = (result_pips > 0).sum()
    losses = (result_pips < 0).sum()
    total_pips = result_pips.sum()
    
    print(f"\n✅ RESULTADOS FINAIS (Threshold={threshold}):")
    print(f"   Accuracy: {accuracy:.4f}")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall: {recall:.4f}")
    print(f"   F1-Score: {f1:.4f}")
    print(f"   ─────────────────")
    print(f"   Wins: {wins:,} | Losses: {losses:,}")
    print(f"   Win Rate: {wins/(wins+losses)*100:.2f}%")
    print(f"   Total Pips: {total_pips:,}")
    print(f"   Avg Pips/Trade: {result_pips.mean():.0f}")
    
    if len(result_pips[result_pips < 0]) > 0:
        profit_factor = abs(result_pips[result_pips > 0].sum() / result_pips[result_pips < 0].sum())
        print(f"   Profit Factor: {profit_factor:.2f}x")
    else:
        print(f"   Profit Factor: ∞")
    
    # Salvar resultados
    df_test_results = df_test.copy()
    df_test_results['pred_proba'] = pred_proba_ensemble
    df_test_results['pred_direction'] = pred_direction
    df_test_results['result_pips'] = result_pips
    
    return {
        'f1': f1,
        'win_rate': wins/(wins+losses) if (wins+losses) > 0 else 0,
        'total_pips': total_pips,
        'profit_factor': profit_factor if len(result_pips[result_pips < 0]) > 0 else float('inf'),
        'df_results': df_test_results
    }

def main():
    print("="*80)
    print("🚀 BACKTEST CLASSIFICATION - VERSÃO OTIMIZADA COM THRESHOLDS DINÂMICOS")
    print("   Ensemble: XGBoost + RandomForest")
    print("   Thresholds: Otimizados por ativo")
    print("   Split: 70% treino | 30% teste")
    print("="*80)
    
    symbols = sys.argv[1:] if len(sys.argv) > 1 else ['EURUSD', 'GBPUSD', 'EURAUD', 'EURJPY', 'GOLD', 'NZDUSD']
    
    results_summary = []
    
    for symbol in symbols:
        csv_file = f"{DATA_DIR}/{symbol}_M15_202401012200_202605222015.csv"
        
        if not Path(csv_file).exists():
            print(f"⚠️  Arquivo não encontrado: {csv_file}")
            continue
        
        # Pegar threshold otimizado para este ativo
        threshold = OPTIMAL_THRESHOLDS.get(symbol, 0.50)
        
        try:
            df_train, df_test = load_and_process_data(csv_file, symbol)
            xgb_model, rf_model, scaler, feature_names = train_models(df_train)
            results = predict_on_test(df_test, xgb_model, rf_model, scaler, feature_names, threshold)
            
            results_summary.append({
                'symbol': symbol,
                'f1': results['f1'],
                'win_rate': results['win_rate'],
                'pips': results['total_pips'],
                'profit_factor': results['profit_factor']
            })
            
            print("\n" + "="*80)
            
        except Exception as e:
            print(f"❌ Erro processando {symbol}: {str(e)}")
    
    # Resumo final
    print("\n" + "="*80)
    print("📊 RESUMO FINAL - CLASSIFICATION OTIMIZADO")
    print("="*80)
    print()
    
    if results_summary:
        print(f"{'SYMBOL':<10} {'F1':<10} {'Win %':<12} {'Pips':<15} {'Profit Factor':<15}")
        print("─" * 65)
        
        for r in results_summary:
            symbol = r['symbol']
            f1 = r['f1']
            win_rate = r['win_rate'] * 100
            pips = r['pips']
            pf = r['profit_factor'] if r['profit_factor'] != float('inf') else '∞'
            
            print(f"{symbol:<10} {f1:<10.4f} {win_rate:<12.2f}% {pips:<15.0f} {str(pf):<15}")
        
        print("─" * 65)
        avg_win_rate = np.mean([r['win_rate'] * 100 for r in results_summary])
        print(f"{'MÉDIA':<10} {'':<10} {avg_win_rate:<12.2f}%")
    
    print("\n✅ Classification otimizado pronto para PRODUÇÃO! 🚀")

if __name__ == '__main__':
    main()
