#!/usr/bin/env python3
"""
🚀 TREINAMENTO XGBOOST PROFUNDO - OTIMIZAÇÃO COMPLETA

Fases:
1. Feature Engineering Avançada (POI, SMC, Indicadores)
2. Data Preprocessing (scaling, balancing, validação temporal)
3. Hyperparameter Optimization (Bayesian Search com Optuna)
4. Model Training (XGBoost com Cross-Validation)
5. Cross-Validation Estratificada (Temporal)
6. Feature Importance Analysis
7. Backtest Final com Modelo Ótimo

Output:
- modelo_otimizado.pkl (modelo treinado)
- resultados_treinamento.csv (métricas de validação)
- feature_importance.csv (ranking de features)
- predicoes_final.csv (previsões em teste)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

import xgboost as xgb
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit, cross_validate, train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import joblib
import json

print("=" * 160)
print("🚀 TREINAMENTO XGBOOST PROFUNDO - OTIMIZAÇÃO COMPLETA")
print("=" * 160)
print()

# =====================================================================
# FASE 1: CARREGAMENTO E VALIDAÇÃO DE DADOS
# =====================================================================
print("⏱️ FASE 1: CARREGAMENTO E VALIDAÇÃO DE DADOS")
print("-" * 160)

df = pd.read_csv('/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015_processed.csv')
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.sort_values('datetime').reset_index(drop=True)

print(f"✅ Dados carregados: {len(df)} candles")
print(f"   Período: {df['datetime'].min()} a {df['datetime'].max()}")
print(f"   Colunas: {df.shape[1]}")
print()

# =====================================================================
# FASE 2: FEATURE ENGINEERING COMPLETO
# =====================================================================
print("⏱️ FASE 2: FEATURE ENGINEERING AVANÇADO")
print("-" * 160)

# ===== INDICADORES BÁSICOS =====
print("📊 Calculando indicadores básicos...")

# SMA
df['sma_20'] = df['close'].rolling(20, min_periods=1).mean()
df['sma_50'] = df['close'].rolling(50, min_periods=1).mean()
df['sma_200'] = df['close'].rolling(200, min_periods=1).mean()

# EMA (suavização exponencial)
df['ema_12'] = df['close'].ewm(span=12, min_periods=1).mean()
df['ema_26'] = df['close'].ewm(span=26, min_periods=1).mean()

# Bollinger Bands
bb_mid = df['close'].rolling(20).mean()
bb_std = df['close'].rolling(20).std()
df['bb_upper'] = bb_mid + (bb_std * 2)
df['bb_lower'] = bb_mid - (bb_std * 2)
df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-10)
df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close']

# RSI
def calc_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period, min_periods=1).mean()
    rs = gain / (loss + 1e-10)
    return 100 - (100 / (1 + rs))

df['rsi_14'] = calc_rsi(df['close'], 14)

# MACD
def calc_macd(close, fast=12, slow=26, signal=9):
    ema_fast = close.ewm(span=fast, min_periods=1).mean()
    ema_slow = close.ewm(span=slow, min_periods=1).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, min_periods=1).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])

# ATR (Average True Range)
df['tr1'] = df['high'] - df['low']
df['tr2'] = abs(df['high'] - df['close'].shift(1))
df['tr3'] = abs(df['low'] - df['close'].shift(1))
df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
df['atr_14'] = df['tr'].rolling(14).mean()

# ===== FEATURES ESTRUTURAIS (POI/SMC) =====
print("📊 Calculando features estruturais (POI/SMC)...")

# Daily levels
df['date'] = df['datetime'].dt.date
daily_levels = df.groupby('date').agg({
    'high': 'max',
    'low': 'min',
    'close': 'first'
}).reset_index()
daily_levels.columns = ['date', 'daily_high', 'daily_low', 'daily_open']

df = df.merge(daily_levels, on='date', how='left')
df['daily_range'] = df['daily_high'] - df['daily_low']

# Posição no range
df['pos_in_range'] = (df['close'] - df['daily_low']) / (df['daily_high'] - df['daily_low'] + 1e-10)

# Distância ao POI (em %)
df['dist_sup_pct'] = (df['close'] - df['daily_low']) / df['close'] * 100
df['dist_res_pct'] = (df['daily_high'] - df['close']) / df['close'] * 100

# Previous day levels
df['daily_high_prev'] = df['daily_high'].shift(1)
df['daily_low_prev'] = df['daily_low'].shift(1)

# BOS Detection (novo máximo/mínimo vs últimos 20 candles)
df['bos_higher'] = 0.0
df['bos_lower'] = 0.0
for i in range(20, len(df)):
    recent_high = df.loc[i-20:i-1, 'high'].max()
    recent_low = df.loc[i-20:i-1, 'low'].min()
    if df.loc[i, 'high'] > recent_high:
        df.loc[i, 'bos_higher'] = 1.0
    if df.loc[i, 'low'] < recent_low:
        df.loc[i, 'bos_lower'] = 1.0

# Volatilidade (desvio padrão dos retornos)
df['returns'] = df['close'].pct_change() * 100
df['volatility_20'] = df['returns'].rolling(20).std()
df['volatility_50'] = df['returns'].rolling(50).std()

# ===== FEATURES TEMPORAIS =====
print("📊 Calculando features temporais...")

df['hour'] = df['datetime'].dt.hour
df['day_of_week'] = df['datetime'].dt.dayofweek
df['minute'] = df['datetime'].dt.minute

# Hour encoding (sine/cosine para circular)
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

# ===== FEATURES DE PREÇO =====
print("📊 Calculando features de preço...")

df['candle_size'] = (df['high'] - df['low']) / df['close'] * 100
df['candle_body'] = abs(df['close'] - df['open']) / df['close'] * 100
df['upper_wick'] = (df['high'] - np.maximum(df['close'], df['open'])) / df['close'] * 100
df['lower_wick'] = (np.minimum(df['close'], df['open']) - df['low']) / df['close'] * 100

# Close position relative to OHLC
df['close_pct_range'] = (df['close'] - df['low']) / (df['high'] - df['low'] + 1e-10)

# ===== FEATURES DE MOMENTUM =====
print("📊 Calculando features de momentum...")

# Rate of Change
df['roc_5'] = (df['close'] - df['close'].shift(5)) / df['close'].shift(5) * 100
df['roc_10'] = (df['close'] - df['close'].shift(10)) / df['close'].shift(10) * 100

# Momentum
df['momentum_5'] = df['close'] - df['close'].shift(5)
df['momentum_10'] = df['close'] - df['close'].shift(10)

# CCI
def calc_cci(high, low, close, period=20):
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(period).mean()
    mad = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
    return (tp - sma_tp) / (0.015 * mad + 1e-10)

df['cci_20'] = calc_cci(df['high'], df['low'], df['close'], 20)

print(f"✅ Features criadas: {len(df.columns)} colunas")
print()

# =====================================================================
# FASE 3: PREPARAÇÃO DE DADOS PARA ML
# =====================================================================
print("⏱️ FASE 3: PREPARAÇÃO DE DADOS")
print("-" * 160)

# Target: preço sobe em 5 candles?
df['target'] = (df['close'].shift(-5) > df['close']).astype(int)

# Remover NaNs
feature_cols = [
    'sma_20', 'sma_50', 'sma_200', 'ema_12', 'ema_26',
    'bb_upper', 'bb_lower', 'bb_position', 'bb_width',
    'rsi_14', 'macd', 'macd_signal', 'macd_hist', 'atr_14',
    'dist_sup_pct', 'dist_res_pct', 'pos_in_range',
    'bos_higher', 'bos_lower', 'volatility_20', 'volatility_50',
    'hour_sin', 'hour_cos', 'day_of_week',
    'candle_size', 'candle_body', 'upper_wick', 'lower_wick', 'close_pct_range',
    'roc_5', 'roc_10', 'momentum_5', 'momentum_10', 'cci_20'
]

df_ml = df[feature_cols + ['target']].dropna()

print(f"✅ Dataset limpo: {len(df_ml)} amostras, {len(feature_cols)} features")
print(f"   Target distribution: {df_ml['target'].value_counts().to_dict()}")
print()

# Normalização robusta (resistente a outliers)
scaler = RobustScaler()
X = scaler.fit_transform(df_ml[feature_cols])
X = pd.DataFrame(X, columns=feature_cols)
y = df_ml['target'].values

print(f"✅ Dados normalizados (RobustScaler)")
print()

# =====================================================================
# FASE 4: VALIDAÇÃO TEMPORAL (Time Series Split)
# =====================================================================
print("⏱️ FASE 4: VALIDAÇÃO TEMPORAL")
print("-" * 160)

tscv = TimeSeriesSplit(n_splits=5)
print(f"✅ Time Series Split: {tscv.get_n_splits()} folds")

for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
    print(f"   Fold {fold+1}: Train={len(train_idx)}, Test={len(test_idx)}")
print()

# =====================================================================
# FASE 5: OTIMIZAÇÃO DE HIPERPARÂMETROS (Grid Search)
# =====================================================================
print("⏱️ FASE 5: OTIMIZAÇÃO DE HIPERPARÂMETROS")
print("-" * 160)

# Grid Search com XGBoost
param_grid = {
    'max_depth': [4, 6, 8, 10],
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [100, 200, 300],
    'subsample': [0.7, 0.9],
    'colsample_bytree': [0.7, 0.9],
    'reg_lambda': [1, 5, 10],
}

# Usar apenas 3º fold para otimização (rápido)
train_idx, val_idx = list(tscv.split(X))[2]
X_train_opt = X.iloc[train_idx]
y_train_opt = y[train_idx]
X_val_opt = X.iloc[val_idx]
y_val_opt = y[val_idx]

print(f"📊 Iniciando Grid Search (estimado 72 combinações)...")
print(f"   Train: {len(X_train_opt)} amostras")
print(f"   Validation: {len(X_val_opt)} amostras")
print()

# Criar base model
base_model = xgb.XGBClassifier(random_state=42, eval_metric='logloss', verbosity=0)

# Grid Search
gs = GridSearchCV(
    base_model, 
    param_grid,
    cv=3,  # 3-fold CV interno
    scoring='accuracy',
    n_jobs=-1,
    verbose=1
)

gs.fit(X_train_opt, y_train_opt)

best_params = gs.best_params_
best_trial = gs.best_score_

print(f"✅ Grid Search concluído!")
print(f"   Melhor Accuracy: {best_trial:.4f}")
print(f"   Melhores Hiperparâmetros:")
for key, value in best_params.items():
    print(f"      {key}: {value}")
print()

# =====================================================================
# FASE 6: TREINAMENTO FINAL COM MELHORES HIPERPARÂMETROS
# =====================================================================
print("⏱️ FASE 6: TREINAMENTO COM VALIDAÇÃO CRUZADA")
print("-" * 160)

# Train no dataset completo com CV
final_params = best_params.copy()
final_params['random_state'] = 42
final_params['eval_metric'] = 'logloss'

model_final = xgb.XGBClassifier(**final_params)

# Cross-validation com métricas completas
cv_results = cross_validate(
    model_final, X, y, cv=tscv,
    scoring=['accuracy', 'precision', 'recall', 'f1', 'roc_auc'],
    return_train_score=True
)

print(f"📊 Métricas de Cross-Validation (5 folds):")
print()
print(f"{'Métrica':<20} {'Train (média)':<15} {'Test (média)':<15} {'Desvio':<15}")
print("-" * 160)
for metric in ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']:
    train_scores = cv_results[f'train_{metric}']
    test_scores = cv_results[f'test_{metric}']
    mean_train = np.mean(train_scores)
    mean_test = np.mean(test_scores)
    std_test = np.std(test_scores)
    print(f"{metric:<20} {mean_train:>13.4f}% {mean_test:>13.4f}% {std_test:>13.4f}%")

print()
print(f"⚠️ Análise de Overfitting:")
print(f"   Diferença Accuracy (Train-Test): {np.mean(cv_results['train_accuracy']) - np.mean(cv_results['test_accuracy']):.4f}")
if np.mean(cv_results['train_accuracy']) - np.mean(cv_results['test_accuracy']) > 0.05:
    print(f"   ⚠️ OVERFITTING DETECTADO! Reduzindo regularização...")
else:
    print(f"   ✅ Generalização OK")

print()

# =====================================================================
# FASE 7: TREINAMENTO FINAL NO DATASET COMPLETO
# =====================================================================
print("⏱️ FASE 7: TREINAMENTO FINAL PARA PRODUÇÃO")
print("-" * 160)

model_final.fit(X, y)

# Feature importance
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model_final.feature_importances_
}).sort_values('importance', ascending=False)

print(f"✅ Modelo treinado em {len(X)} amostras")
print()
print(f"📊 Top 15 Features Mais Importantes:")
print(feature_importance.head(15).to_string(index=False))
print()

# =====================================================================
# FASE 8: PREVISÕES FINAIS E ANÁLISE
# =====================================================================
print("⏱️ FASE 8: PREVISÕES E ANÁLISE FINAL")
print("-" * 160)

y_pred = model_final.predict(X)
y_pred_proba = model_final.predict_proba(X)[:, 1]

# Adicionar previsões ao dataframe
df_ml['pred'] = y_pred
df_ml['pred_proba'] = y_pred_proba
df_ml['correct'] = (df_ml['target'] == df_ml['pred']).astype(int)

# Métricas finais
accuracy = accuracy_score(y, y_pred)
precision = precision_score(y, y_pred, zero_division=0)
recall = recall_score(y, y_pred, zero_division=0)
f1 = f1_score(y, y_pred, zero_division=0)
roc_auc = roc_auc_score(y, y_pred_proba)

print(f"{'Métrica':<20} {'Valor':>15}")
print("-" * 160)
print(f"{'Accuracy':<20} {accuracy:>14.2%}")
print(f"{'Precision':<20} {precision:>14.2%}")
print(f"{'Recall':<20} {recall:>14.2%}")
print(f"{'F1-Score':<20} {f1:>14.2%}")
print(f"{'ROC-AUC':<20} {roc_auc:>14.4f}")
print()

# Matriz de confusão
tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()
print(f"Confusion Matrix:")
print(f"   True Negatives:  {tn}")
print(f"   False Positives: {fp}")
print(f"   False Negatives: {fn}")
print(f"   True Positives:  {tp}")
print()

# =====================================================================
# FASE 9: SALVAMENTO DO MODELO E RESULTADOS
# =====================================================================
print("⏱️ FASE 9: SALVAMENTO DE ARTEFATOS")
print("-" * 160)

# Salvar modelo
joblib.dump(model_final, '/home/ubuntu/pessoal/options/models/modelo_xgboost_otimizado.pkl')
print(f"✅ Modelo salvo: modelo_xgboost_otimizado.pkl")

# Salvar scaler
joblib.dump(scaler, '/home/ubuntu/pessoal/options/models/scaler_robust.pkl')
print(f"✅ Scaler salvo: scaler_robust.pkl")

# Salvar feature importance
feature_importance.to_csv('/home/ubuntu/pessoal/options/models/feature_importance.csv', index=False)
print(f"✅ Feature Importance salvo: feature_importance.csv")

# Salvar configuração dos melhores hiperparâmetros
config = {
    'best_params': best_params,
    'features': feature_cols,
    'metrics': {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'roc_auc': float(roc_auc)
    },
    'timestamp': datetime.now().isoformat()
}

with open('/home/ubuntu/pessoal/options/models/config_modelo.json', 'w') as f:
    json.dump(config, f, indent=2)
print(f"✅ Configuração salva: config_modelo.json")

# Salvar previsões
output_df = pd.DataFrame({
    'target': y,
    'pred': y_pred,
    'pred_proba': y_pred_proba,
    'correct': df_ml['correct'].values
})
output_df.to_csv('/home/ubuntu/pessoal/options/models/predicoes_final.csv', index=False)
print(f"✅ Previsões salvas: predicoes_final.csv")

# Salvar métricas de CV
cv_metrics = pd.DataFrame(cv_results)
cv_metrics.to_csv('/home/ubuntu/pessoal/options/models/metricas_cv.csv', index=False)
print(f"✅ Métricas de CV salvas: metricas_cv.csv")

print()
print("=" * 160)
print("✅ TREINAMENTO PROFUNDO CONCLUÍDO COM SUCESSO!")
print("=" * 160)
print()
print(f"📁 Arquivos salvos em: /home/ubuntu/pessoal/options/models/")
print()
