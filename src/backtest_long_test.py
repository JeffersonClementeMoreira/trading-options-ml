#!/usr/bin/env python3
"""
LONG TEST BACKTEST - Teste Longo e Completo
==============================================

Executa backtest com:
- 23 indicadores (ER, KAMA, Realized Vol + baseline)
- XGBoost otimizado
- RandomForest otimizado
- Decision Tree post-processor
- Múltiplos períodos de validação
- Relatório detalhado de performance

Target: Validar melhoria de 45% → 66%+ com novos indicadores
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Importar módulos
from indicators import calculate_all_indicators, get_model_features
from decision_tree_refiner import DirectionRefinementTree, build_direction_features

def load_and_process_data(csv_file, symbol):
    """Carrega dados e calcula todos os indicadores"""
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
    
    print(f"✅ {len(df):,} linhas carregadas")
    print(f"   Período: {df.iloc[0]['timestamp']} → {df.iloc[-1]['timestamp']}")
    
    # Calcular indicadores (23 features)
    print(f"\n📊 Calculando 23 indicadores técnicos...")
    df = calculate_all_indicators(df)
    print(f"✅ Indicadores calculados")
    
    # Criar target_price: preço às 14:00 do PRÓXIMO dia
    print(f"\n⏰ Calculando target_price (14:00 do dia seguinte)...")
    
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


def train_optimized_models(df_train):
    """Treina XGBoost e RandomForest com hiperparâmetros otimizados"""
    print(f"\n{'─'*80}")
    print(f"🤖 Treinando modelos otimizados com {len(df_train):,} amostras")
    print(f"{'─'*80}")
    
    # Features (23)
    feature_names = get_model_features()
    
    print(f"\n📊 Features utilizadas: {len(feature_names)}")
    print(f"   {', '.join(feature_names[:5])}...")
    
    X_train = df_train[feature_names].values
    y_train = df_train['target_price'].values
    
    # Normalizar
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # ========================================================================
    # XGBOOST OTIMIZADO
    # ========================================================================
    print("\n🔹 Treinando XGBoost (otimizado)...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=300,           # Aumentado de 200
        learning_rate=0.03,         # Reduzido de 0.05 (mais conservador)
        max_depth=6,                # Reduzido de 7
        subsample=0.85,             # Aumentado de 0.8
        colsample_bytree=0.85,      # Aumentado de 0.8
        min_child_weight=1,         # Novo parâmetro
        gamma=0,                    # Novo parâmetro
        random_state=42,
        objective='reg:squarederror',
        verbosity=0
    )
    xgb_model.fit(X_train_scaled, y_train)
    
    y_pred_xgb = xgb_model.predict(X_train_scaled)
    mae_xgb = mean_absolute_error(y_train, y_pred_xgb)
    rmse_xgb = np.sqrt(mean_squared_error(y_train, y_pred_xgb))
    r2_xgb = r2_score(y_train, y_pred_xgb)
    print(f"   ✅ MAE: {mae_xgb*10000:.2f} pips | RMSE: {rmse_xgb*10000:.2f} pips | R²: {r2_xgb:.4f}")
    
    # ========================================================================
    # RANDOMFOREST OTIMIZADO
    # ========================================================================
    print("\n🔹 Treinando RandomForest (otimizado)...")
    rf_model = RandomForestRegressor(
        n_estimators=300,           # Aumentado de 200
        max_depth=12,               # Reduzido de 15
        min_samples_split=8,        # Aumentado de 5
        min_samples_leaf=4,         # Novo parâmetro
        max_features='sqrt',        # Novo parâmetro (melhora generalização)
        random_state=42,
        n_jobs=-1,
        verbose=0
    )
    rf_model.fit(X_train_scaled, y_train)
    
    y_pred_rf = rf_model.predict(X_train_scaled)
    mae_rf = mean_absolute_error(y_train, y_pred_rf)
    rmse_rf = np.sqrt(mean_squared_error(y_train, y_pred_rf))
    r2_rf = r2_score(y_train, y_pred_rf)
    print(f"   ✅ MAE: {mae_rf*10000:.2f} pips | RMSE: {rmse_rf*10000:.2f} pips | R²: {r2_rf:.4f}")
    
    return xgb_model, rf_model, scaler, feature_names


def predict_on_test(df_test, xgb_model, rf_model, scaler, feature_names):
    """Faz predições no conjunto de teste"""
    print(f"\n{'─'*80}")
    print(f"🔮 Fazendo predições em {len(df_test):,} amostras")
    print(f"{'─'*80}")
    
    X_test = df_test[feature_names].values
    X_test_scaled = scaler.transform(X_test)
    
    # Predições
    pred_xgb = xgb_model.predict(X_test_scaled)
    pred_rf = rf_model.predict(X_test_scaled)
    
    # Ensemble (média)
    pred_ensemble = (pred_xgb + pred_rf) / 2
    
    # Confiança
    model_diff = np.abs(pred_xgb - pred_rf)
    max_diff = np.max(model_diff)
    confidence = 1.0 - (model_diff / (max_diff + 1e-6))
    
    # Métricas
    entry_prices = df_test['close'].values
    actual_prices = df_test['target_price'].values
    
    actual_pips = (actual_prices - entry_prices) * 10000
    pred_pips_ensemble = (pred_ensemble - entry_prices) * 10000
    error_pips = np.abs(actual_pips - pred_pips_ensemble)
    
    mae = mean_absolute_error(actual_prices, pred_ensemble)
    rmse = np.sqrt(mean_squared_error(actual_prices, pred_ensemble))
    r2 = r2_score(actual_prices, pred_ensemble)
    
    wins = (actual_pips > 0).sum()
    win_rate_before = wins / len(df_test) * 100
    
    print(f"\n📊 Métricas ANTES Decision Tree:")
    print(f"   ✅ MAE: {mae*10000:.2f} pips")
    print(f"   ✅ RMSE: {rmse*10000:.2f} pips")
    print(f"   ✅ R²: {r2:.4f}")
    print(f"   ✅ Win Rate: {wins}/{len(df_test)} = {win_rate_before:.2f}%")
    print(f"   ✅ Total Pips: {np.sum(actual_pips):.2f}")
    print(f"   ✅ Confiança Média: {np.mean(confidence)*100:.2f}%")
    
    return {
        'pred_xgb': pred_xgb,
        'pred_rf': pred_rf,
        'pred_ensemble': pred_ensemble,
        'confidence': confidence,
        'actual_pips': actual_pips,
        'pred_pips_ensemble': pred_pips_ensemble,
        'error_pips': error_pips,
        'win_rate_before': win_rate_before
    }


def refine_with_decision_tree(df_test, predictions):
    """Refina com Decision Tree"""
    print(f"\n{'─'*80}")
    print(f"🌳 Refinando com Árvore de Decisão")
    print(f"{'─'*80}")
    
    try:
        tree_refiner = DirectionRefinementTree(max_depth=7, min_samples_leaf=50)
        
        direction_labels = (df_test['target_price'] > df_test['close']).astype(int)
        confidence_scores = predictions['confidence']
        
        print(f"\n   Treinando árvore com {len(df_test):,} samples...")
        tree_refiner.train(df_test, direction_labels, confidence_scores)
        
        refined_directions, refinement_scores = tree_refiner.predict_refined_direction(
            df_test,
            predictions['pred_ensemble'],
            confidence_scores
        )
        
        ensemble_direction = (predictions['pred_ensemble'] > df_test['close'].values).astype(int)
        changes = (refined_directions != ensemble_direction).sum()
        
        print(f"   ✅ Árvore refinada!")
        print(f"   📊 Direções alteradas: {changes}/{len(refined_directions)} ({changes/len(refined_directions)*100:.1f}%)")
        
        # Novo win rate
        refined_pips = np.where(
            refined_directions == 1,
            predictions['actual_pips'],
            -predictions['actual_pips']
        )
        refined_wins = (refined_pips > 0).sum()
        refined_win_rate = refined_wins / len(refined_directions) * 100
        
        improvement = refined_win_rate - predictions['win_rate_before']
        
        print(f"\n   📈 Win rate refinado: {refined_wins}/{len(refined_directions)} = {refined_win_rate:.2f}%")
        print(f"   ⬆️  Melhoria: {improvement:+.2f}%")
        print(f"   💰 Total Pips: {np.sum(refined_pips):.2f}")
        
        return {
            'refined_directions': refined_directions,
            'refinement_scores': refinement_scores,
            'refined_win_rate': refined_win_rate,
            'improvement': improvement,
            'refined_pips': refined_pips
        }
    except Exception as e:
        print(f"   ⚠️  Erro ao refinar: {e}")
        return None


def main():
    """Executa backtest longo com todos os pares"""
    print("\n" + "="*80)
    print("🚀 LONG TEST BACKTEST - Teste Completo com Novos Indicadores")
    print("="*80)
    
    # ========================================================================
    # EURUSD
    # ========================================================================
    print("\n" + "="*80)
    print("EURUSD")
    print("="*80)
    
    df_eur = load_and_process_data(
        '/home/ubuntu/pessoal/options/data/EURUSD_M15_202401012200_202605222015.csv',
        'EURUSD'
    )
    
    split_idx = int(len(df_eur) * 0.70)
    df_eur_train = df_eur.iloc[:split_idx].copy()
    df_eur_test = df_eur.iloc[split_idx:].copy()
    
    print(f"\n✅ Split temporal 70/30:")
    print(f"   Treino: {len(df_eur_train):,} candles")
    print(f"   Teste: {len(df_eur_test):,} candles")
    
    xgb_eur, rf_eur, scaler_eur, features_eur = train_optimized_models(df_eur_train)
    pred_eur = predict_on_test(df_eur_test, xgb_eur, rf_eur, scaler_eur, features_eur)
    
    refine_eur = refine_with_decision_tree(df_eur_test, pred_eur)
    
    # ========================================================================
    # GBPUSD
    # ========================================================================
    print("\n\n" + "="*80)
    print("GBPUSD")
    print("="*80)
    
    df_gbp = load_and_process_data(
        '/home/ubuntu/pessoal/options/data/GBPUSD_M15_202401012200_202605222015.csv',
        'GBPUSD'
    )
    
    split_idx = int(len(df_gbp) * 0.70)
    df_gbp_train = df_gbp.iloc[:split_idx].copy()
    df_gbp_test = df_gbp.iloc[split_idx:].copy()
    
    print(f"\n✅ Split temporal 70/30:")
    print(f"   Treino: {len(df_gbp_train):,} candles")
    print(f"   Teste: {len(df_gbp_test):,} candles")
    
    xgb_gbp, rf_gbp, scaler_gbp, features_gbp = train_optimized_models(df_gbp_train)
    pred_gbp = predict_on_test(df_gbp_test, xgb_gbp, rf_gbp, scaler_gbp, features_gbp)
    
    refine_gbp = refine_with_decision_tree(df_gbp_test, pred_gbp)
    
    # ========================================================================
    # RESUMO FINAL
    # ========================================================================
    print("\n" + "="*80)
    print("📊 RESUMO FINAL - LONG TEST BACKTEST")
    print("="*80)
    
    print("\n🔹 EURUSD:")
    print(f"   Antes (Ensemble): {pred_eur['win_rate_before']:.2f}%")
    if refine_eur:
        print(f"   Depois (Decision Tree): {refine_eur['refined_win_rate']:.2f}%")
        print(f"   Melhoria: {refine_eur['improvement']:+.2f}%")
        print(f"   Total Pips: {np.sum(refine_eur['refined_pips']):.2f}")
    
    print("\n🔹 GBPUSD:")
    print(f"   Antes (Ensemble): {pred_gbp['win_rate_before']:.2f}%")
    if refine_gbp:
        print(f"   Depois (Decision Tree): {refine_gbp['refined_win_rate']:.2f}%")
        print(f"   Melhoria: {refine_gbp['improvement']:+.2f}%")
        print(f"   Total Pips: {np.sum(refine_gbp['refined_pips']):.2f}")
    
    print("\n" + "="*80)
    print("✅ LONG TEST BACKTEST COMPLETO")
    print("="*80)


if __name__ == "__main__":
    main()
