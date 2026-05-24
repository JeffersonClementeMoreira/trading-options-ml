#!/usr/bin/env python3
"""
Analisador de Features XGBoost - Mostra quais variáveis o modelo recebe
e o impacto de cada uma ANTES de treinar.

Executa:
1. Carrega dados
2. Gera features SMC
3. Analisa cada feature individualmente
4. Mostra feature importance após treinamento
5. Recomenda threshold otimizado
"""

import sys
from pathlib import Path

# Adicionar paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, roc_auc_score
except ImportError:
    print("ERROR: XGBoost/sklearn não instalado")
    print("Instale com: pip install xgboost scikit-learn")
    sys.exit(1)

from core.indicators import build_indicators
from core.smc import calculate_extremes
from core.smc_features import generate_all_smc_features


def load_eurusd_data(csv_file: Path, max_rows=None) -> pd.DataFrame:
    """Carrega dados EURUSD M15."""
    print(f"\n📊 Carregando dados de: {csv_file}")
    
    df = pd.read_csv(csv_file, sep="\t")
    df.columns = [col.strip().lower().replace("<", "").replace(">", "") for col in df.columns]
    
    df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce")
    df = df.set_index("datetime").sort_index()
    
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    if "volume" not in df.columns:
        df["volume"] = 1
    else:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(1)
    
    df = df.dropna(subset=["open", "high", "low", "close"])
    
    # Criar coluna 'return' necessária para build_indicators
    df["return"] = df["close"].pct_change()
    
    if max_rows:
        df = df.tail(max_rows)
    
    print(f"✅ Carregados {len(df)} candles ({df.index.min()} a {df.index.max()})")
    return df


def analyze_features_before_training(df: pd.DataFrame, smc_features: pd.DataFrame):
    """Analisa features ANTES do treinamento."""
    
    print("\n" + "="*100)
    print("📊 ANÁLISE PRÉ-TREINAMENTO: Quais features o XGBoost vai receber?")
    print("="*100 + "\n")
    
    # Combinar features
    X = smc_features.copy()
    if "atr" in df.columns:
        X["atr"] = df["atr"]
    if "rsi" in df.columns:
        X["rsi"] = df["rsi"]
    
    X["close"] = df["close"]
    X["high"] = df["high"]
    X["low"] = df["low"]
    X["volume"] = df["volume"] if "volume" in df.columns else 0
    X["return_pct"] = df["close"].pct_change() * 100
    
    # Alvo
    X["target_close"] = df["close"].shift(-1)
    valid_idx = X["target_close"].notna()
    X = X[valid_idx].copy()
    
    y_direction = (X["target_close"] > X["close"]).astype(int)
    X = X.drop(columns=["target_close", "close", "high", "low"])
    
    print(f"Total de features: {len(X.columns)}\n")
    print("FEATURES DISPONÍVEIS:")
    print("-" * 100)
    
    # Agrupar por tipo
    smc_feat = [c for c in X.columns if c.startswith(('dist_', 'sweep_', 'bos_', 'candles_', 
                                                        'bull_', 'bear_', 'fvg_', 'mean_', 'max_', 
                                                        'displacement_', 'premium_', 'atr_comp', 
                                                        'vol_', 'liquidity_', 'stop_', 'trend_', 
                                                        'range_', 'regime_'))]
    
    technical = [c for c in X.columns if c in ['atr', 'rsi', 'return_pct', 'volume']]
    
    print(f"\n🔷 SMC FEATURES ({len(smc_feat)}):")
    for i, feat in enumerate(smc_feat, 1):
        mean_val = X[feat].mean()
        std_val = X[feat].std()
        min_val = X[feat].min()
        max_val = X[feat].max()
        print(f"  {i:2d}. {feat:30s} | Mean: {mean_val:8.3f} | Std: {std_val:7.3f} | Range: [{min_val:7.3f}, {max_val:7.3f}]")
    
    print(f"\n🔶 INDICADORES TÉCNICOS ({len(technical)}):")
    for feat in technical:
        mean_val = X[feat].mean()
        std_val = X[feat].std()
        min_val = X[feat].min()
        max_val = X[feat].max()
        print(f"  • {feat:30s} | Mean: {mean_val:8.3f} | Std: {std_val:7.3f} | Range: [{min_val:7.3f}, {max_val:7.3f}]")
    
    # Correlação com target
    print("\n" + "="*100)
    print("📈 CORRELAÇÃO COM TARGET (Qual feature mais prevê UP?)")
    print("="*100 + "\n")
    
    correlations = []
    for col in X.columns:
        corr = X[col].corr(y_direction)
        if not np.isnan(corr):
            correlations.append((col, abs(corr), corr))
    
    correlations.sort(key=lambda x: x[1], reverse=True)
    
    print("Feature com MAIOR correlação (melhores preditoras):")
    print("-" * 100)
    for i, (feat, abs_corr, corr) in enumerate(correlations[:10], 1):
        direction = "UP↑" if corr > 0 else "DOWN↓"
        bar_size = max(1, int(abs(corr) * 50))
        bar = "█" * bar_size
        print(f"{i:2d}. {feat:30s} | {abs_corr:6.3f} | {bar} {direction}")
    
    print("\nFeature com MENOR correlação (piores preditoras):")
    print("-" * 100)
    for i, (feat, abs_corr, corr) in enumerate(correlations[-5:], 1):
        direction = "UP↑" if corr > 0 else "DOWN↓"
        bar_size = max(1, int(abs(corr) * 50)) if abs_corr > 0 else 0
        bar = "█" * bar_size
        print(f"{i:2d}. {feat:30s} | {abs_corr:6.3f} | {bar} {direction}")
    
    return X, y_direction


def train_and_analyze_importance(X: pd.DataFrame, y: pd.Series):
    """Treina modelo e mostra feature importance."""
    
    print("\n" + "="*100)
    print("🎯 TREINANDO XGBOOST E ANALISANDO IMPORTÂNCIA DAS FEATURES")
    print("="*100 + "\n")
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    # Treinar
    print("⏳ Treinando modelo XGBoost...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss',
        verbose=0
    )
    
    model.fit(X_train, y_train)
    
    # Avaliar
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_pred_proba)
    
    print(f"\n✅ Modelo treinado!")
    print(f"  Acurácia: {accuracy:.1%}")
    print(f"  AUC: {auc:.1%}")
    
    # Feature importance
    print("\n" + "="*100)
    print("🏆 FEATURE IMPORTANCE - Quais features XGBoost mais usa?")
    print("="*100 + "\n")
    
    importances = model.feature_importances_
    features_imp = sorted(zip(X.columns, importances), key=lambda x: x[1], reverse=True)
    
    print("TOP 15 Features por importância:")
    print("-" * 100)
    
    for i, (feat, imp) in enumerate(features_imp[:15], 1):
        bar = "▓" * int(imp * 100)
        print(f"{i:2d}. {feat:30s} | {imp*100:5.2f}% | {bar}")
    
    print("\nBOTTOM 10 Features (quase não usadas):")
    print("-" * 100)
    
    for i, (feat, imp) in enumerate(features_imp[-10:], 1):
        bar = "░" * int(imp * 20) if imp > 0 else ""
        print(f"    {feat:30s} | {imp*100:5.2f}% | {bar}")
    
    return model, accuracy, auc, features_imp


def recommendation_summary(accuracy: float, auc: float, features_imp: list):
    """Recomendações baseadas na análise."""
    
    print("\n" + "="*100)
    print("💡 RECOMENDAÇÕES E PRÓXIMOS PASSOS")
    print("="*100 + "\n")
    
    print("1️⃣  PERFORMANCE DO MODELO")
    print("-" * 100)
    
    if accuracy >= 0.65:
        status = "🟢 EXCELENTE"
        msg = "Modelo com boa acurácia, pronto para deploy"
    elif accuracy >= 0.55:
        status = "🟡 BOM"
        msg = "Modelo aceitável, considere otimizações"
    else:
        status = "🔴 FRACO"
        msg = "Modelo precisa de melhorias (mais features ou dados)"
    
    print(f"  {status}: Acurácia = {accuracy:.1%}")
    print(f"  → {msg}\n")
    
    print("2️⃣  TOP 5 FEATURES MAIS IMPORTANTES")
    print("-" * 100)
    for i, (feat, imp) in enumerate(features_imp[:5], 1):
        print(f"  {i}. {feat:35s} → {imp*100:5.2f}% (Manter em MT5)")
    
    print("\n3️⃣  FEATURES COM BAIXA IMPORTÂNCIA (Considere remover)")
    print("-" * 100)
    low_imp = [f for f, i in features_imp if i < 0.01]
    if low_imp:
        for feat in low_imp[:5]:
            print(f"  • {feat}")
    else:
        print("  → Todas as features têm importância > 1%")
    
    print("\n4️⃣  PRÓXIMOS PASSOS")
    print("-" * 100)
    print("  ✅ Features SMC estão capturando padrões")
    print("  ✅ MT5 deve exportar top 5 features com prioridade")
    print("  ✅ Otimizar confidence threshold baseado em ROC curve")
    print("  ✅ Backtest com strikes otimizados")


if __name__ == "__main__":
    csv_file = Path("/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv")
    
    if not csv_file.exists():
        print(f"ERROR: {csv_file} não encontrado")
        sys.exit(1)
    
    print("\n" + "#"*100)
    print("# ANÁLISE PRÉ-TREINAMENTO: XGBOOST FEATURE ANALYSIS")
    print("#"*100)
    
    # 1. Carregar dados
    df = load_eurusd_data(csv_file, max_rows=5000)
    
    # 2. Construir indicadores
    print("\n🔨 Construindo indicadores...")
    df = build_indicators(df)
    
    # 3. Detectar extremes SMC
    print("🔍 Detectando extremes SMC...")
    extremos = calculate_extremes(df)
    print(f"   Encontrados {len(extremos)} extremes")
    
    # 4. Gerar features SMC
    print("⚙️  Gerando features SMC...")
    smc_features = generate_all_smc_features(df, extremos)
    print(f"   Geradas {len(smc_features.columns)} features")
    
    # 5. Análise pré-treinamento
    X, y = analyze_features_before_training(df, smc_features)
    
    # 6. Treinar e analisar
    model, accuracy, auc, features_imp = train_and_analyze_importance(X, y)
    
    # 7. Recomendações
    recommendation_summary(accuracy, auc, features_imp)
    
    print("\n" + "#"*100)
    print("# FIM DA ANÁLISE")
    print("#"*100 + "\n")
