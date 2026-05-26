#!/usr/bin/env python3
"""
Treinar XGBoost com dados de backtest

Carrega backtest histórico, treina modelo, salva em models/xgboost_model.pkl
"""

import pickle
from pathlib import Path
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import warnings

warnings.filterwarnings('ignore')

print("\n" + "="*80)
print("🚀 TREINANDO XGBOOST COM DADOS DE BACKTEST")
print("="*80 + "\n")

# Carregar dados de backtest
backtest_dir = Path("backtest_results")
csv_files = list(backtest_dir.glob("backtest_*.csv"))
csv_files = [f for f in csv_files if "_simplified" not in f.name]

if not csv_files:
    print("❌ Nenhum backtest encontrado para treino!")
    exit(1)

print(f"📊 Carregando {len(csv_files)} arquivos de backtest...\n")

# Combinar todos os backtests
all_data = []
for csv_file in csv_files:
    try:
        df = pd.read_csv(csv_file)
        all_data.append(df)
        print(f"  ✅ {csv_file.name}: {len(df)} linhas")
    except Exception as e:
        print(f"  ⚠️  Erro em {csv_file.name}: {e}")

if not all_data:
    print("❌ Erro ao carregar arquivos!")
    exit(1)

data = pd.concat(all_data, ignore_index=True)
print(f"\n✅ Total: {len(data)} dias de dados\n")

# Preparar features
print("📝 Preparando features...\n")

# Codificar categorias
le_trends = LabelEncoder()
le_aligned = LabelEncoder()

features_to_use = []
encoded_cols = {}

if 'final_pred' in data.columns:
    y = (data['final_pred'] == 'UP').astype(int)  # 1 = UP, 0 = DOWN
    print(f"✅ Target (final_pred): {(y==1).sum()} UP, {(y==0).sum()} DOWN")
else:
    print("❌ Coluna 'final_pred' não encontrada!")
    exit(1)

# Features numéricos e categóricos
numeric_features = []
categorical_features = []

for col in data.columns:
    if col in ['date', 'day_of_week', 'final_pred', 'xgb_pred', 'xgb_prob']:
        continue
    
    if col in ['m15_trend', 'h4_trend', 'is_aligned']:
        categorical_features.append(col)
    elif pd.api.types.is_numeric_dtype(data[col]):
        numeric_features.append(col)

print(f"\n📊 Features numéricos ({len(numeric_features)}):")
for f in numeric_features[:5]:
    print(f"   {f}")
if len(numeric_features) > 5:
    print(f"   ... e {len(numeric_features)-5} mais")

print(f"\n📊 Features categóricos ({len(categorical_features)}):")
for f in categorical_features:
    print(f"   {f}")

# Codificar categóricos
X = data[numeric_features + categorical_features].copy()

for cat_col in categorical_features:
    try:
        unique_vals = X[cat_col].unique()
        le = LabelEncoder()
        X[cat_col] = le.fit_transform(X[cat_col].astype(str))
        encoded_cols[cat_col] = le
        print(f"\n✅ Codificado {cat_col}: {unique_vals}")
    except Exception as e:
        print(f"\n⚠️  Erro ao codificar {cat_col}: {e}")

# Remover NaN
X = X.fillna(0)
print(f"\n✅ Features finais: {X.shape}")
print(f"   Linhas: {X.shape[0]}")
print(f"   Colunas: {X.shape[1]}")

# Dividir treino/teste
print(f"\n📊 Dividindo em treino (80%) e teste (20%)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"   Treino: {len(X_train)} exemplos")
print(f"   Teste: {len(X_test)} exemplos")

# Treinar XGBoost
print(f"\n🤖 Treinando XGBoost...\n")

model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    verbose=0,
    eval_metric='logloss'
)

model.fit(X_train, y_train)

# Avaliar
train_score = model.score(X_train, y_train)
test_score = model.score(X_test, y_test)

print(f"✅ Treino concluído!")
print(f"\n📈 Performance:")
print(f"   Treino: {train_score:.1%}")
print(f"   Teste:  {test_score:.1%}")

# Importância das features
print(f"\n🔍 Top 5 Features mais importantes:")
importance = model.get_booster().get_score(importance_type='weight')
sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
for i, (feat, score) in enumerate(sorted_imp[:5], 1):
    print(f"   {i}. {feat}: {score}")

# Salvar modelo
model_dir = Path("models")
model_dir.mkdir(exist_ok=True)

model_path = model_dir / "xgboost_model.pkl"
with open(model_path, 'wb') as f:
    pickle.dump({
        'model': model,
        'encoded_cols': encoded_cols,
        'numeric_features': numeric_features,
        'categorical_features': categorical_features,
        'train_score': train_score,
        'test_score': test_score
    }, f)

print(f"\n💾 Modelo salvo: {model_path}")
print(f"   Tamanho: {model_path.stat().st_size / 1024:.1f} KB")

print(f"\n" + "="*80)
print("✅ PASSO 1 CONCLUÍDO - XGBOOST TREINADO")
print("="*80 + "\n")

EOF
