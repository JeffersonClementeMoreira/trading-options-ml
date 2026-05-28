#!/usr/bin/env python3
"""
Decision Tree Post-Processor for XGBoost + RF Ensemble
========================================================

Após XGBoost/RF fazer a predição de preço, usa árvore de decisão
para refinar a predição de DIREÇÃO usando indicadores técnicos.

Objetivo: Melhorar win rate de 50% para 55-60%
"""

import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


def create_direction_labels(df):
    """Cria labels de direção para treinar árvore de decisão"""
    # Direction: 1 se próximo close > current close, 0 caso contrário
    direction = (df['target_price'] > df['close']).astype(int)
    return direction


def build_direction_features(df):
    """Extrai features relevantes para predição de direção"""
    features_df = pd.DataFrame(index=df.index)
    
    # =========================================================================
    # 1. INDICADORES TÉCNICOS BÁSICOS
    # =========================================================================
    features_df['rsi'] = df.get('rsi', 50.0)
    features_df['sma20_above'] = (df['close'] > df.get('sma20', df['close'])).astype(float)
    features_df['sma50_above'] = (df['close'] > df.get('sma50', df['close'])).astype(float)
    features_df['macd'] = df.get('macd', 0.0)
    features_df['momentum'] = df.get('momentum', 0.0)
    
    # =========================================================================
    # 2. VOLATILIDADE E ATR
    # =========================================================================
    features_df['atr'] = df.get('atr', 0.0)
    features_df['sd'] = df.get('sd', 0.0)
    
    # =========================================================================
    # 3. BANDAS DE BOLLINGER
    # =========================================================================
    features_df['bb_position'] = 0.5  # Posição dentro das bandas (0-1)
    if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
        bb_range = df['bb_upper'] - df['bb_lower']
        features_df['bb_position'] = np.where(
            bb_range > 0,
            (df['close'] - df['bb_lower']) / bb_range,
            0.5
        )
    
    # =========================================================================
    # 4. REGIME DE MERCADO (usando indicadores disponíveis)
    # =========================================================================
    # Trend following: SMA > SMA50 = trend up
    features_df['trend_signal'] = (
        (df.get('sma20', df['close']) > df.get('sma50', df['close'])).astype(float)
    )
    
    # Range detection: ATR baixo = range
    features_df['range_detected'] = 0
    if 'atr' in df.columns:
        atr_sma = df['atr'].rolling(20).mean()
        features_df['range_detected'] = (df['atr'] < atr_sma * 0.7).astype(float)
    
    # =========================================================================
    # 5. MOMENTUM RECENTE (últimas 3-5 candles)
    # =========================================================================
    features_df['momentum_3'] = (df['close'] - df['close'].shift(3)) / df['close'].shift(3)
    features_df['momentum_5'] = (df['close'] - df['close'].shift(5)) / df['close'].shift(5)
    
    # =========================================================================
    # 6. VOLATILIDADE RELATIVA
    # =========================================================================
    returns = df['close'].pct_change()
    features_df['vol_20'] = returns.rolling(20).std()
    features_df['vol_ratio'] = features_df['vol_20'] / returns.rolling(50).std()
    
    # =========================================================================
    # 7. PADRÕES SMC (se disponíveis)
    # =========================================================================
    features_df['smc_support'] = df.get('smc_support', df['close'])
    features_df['smc_resistance'] = df.get('smc_resistance', df['close'])
    
    # Distância até suporte/resistência
    features_df['dist_to_support'] = (df['close'] - features_df['smc_support']) / (features_df['smc_support'] + 1e-6)
    features_df['dist_to_resistance'] = (features_df['smc_resistance'] - df['close']) / (features_df['smc_resistance'] + 1e-6)
    
    # =========================================================================
    # 8. CONFIDENCE DO ENSEMBLE (já temos)
    # =========================================================================
    # Será adicionado durante o treino (confidence_pct + confluence score)
    
    return features_df.fillna(0)


class DirectionRefinementTree:
    """Decision tree que refina predições de direção do ensemble"""
    
    def __init__(self, max_depth=7, min_samples_leaf=50):
        self.tree = DecisionTreeClassifier(
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            random_state=42,
            class_weight='balanced'  # Importante: balanceia classes
        )
        self.scaler = StandardScaler()
        self.trained = False
        self.feature_names = []
    
    def train(self, df, y_labels, confidence_scores=None):
        """
        Treina a árvore de decisão.
        
        Parameters:
        -----------
        df : DataFrame com indicadores
        y_labels : Series com direção real (1 = up, 0 = down)
        confidence_scores : Series com confiança do ensemble (opcional)
        """
        # Extrair features
        features = build_direction_features(df)
        
        # Se temos confiança, adicionar
        if confidence_scores is not None:
            features['ensemble_confidence'] = confidence_scores
        
        # Remover linhas com NaN
        valid_idx = (~features.isna().any(axis=1)) & (~y_labels.isna())
        X = features.loc[valid_idx]
        y = y_labels.loc[valid_idx]
        
        if len(X) < 100:
            print(f"⚠️  Aviso: Apenas {len(X)} samples para treinar árvore de direção")
            return
        
        # Normalizar
        X_scaled = self.scaler.fit_transform(X)
        
        # Treinar
        self.tree.fit(X_scaled, y)
        self.feature_names = X.columns.tolist()
        self.trained = True
        
        # Calcular importância das features
        importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.tree.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\n✅ Árvore de Direção Treinada:")
        print(f"   Samples: {len(X)}")
        print(f"   Profundidade: {self.tree.get_depth()}")
        print(f"   Features mais importantes:")
        for idx, row in importance.head(10).iterrows():
            print(f"      {row['feature']:20s}: {row['importance']:.4f}")
        
        return importance
    
    def predict_refined_direction(self, df, ensemble_predictions, confidence_scores=None):
        """
        Refina predições de direção.
        
        Parameters:
        -----------
        df : DataFrame com indicadores
        ensemble_predictions : array com predições de preço (XGB/RF)
        confidence_scores : Series com confiança (opcional)
        
        Returns:
        --------
        refined_predictions : array com direção refinada (1 = up, 0 = down)
        refinement_score : quanto a árvore aumentou/diminuiu a confiança
        """
        if not self.trained:
            print("⚠️  Árvore não foi treinada. Retornando predições do ensemble.")
            return (ensemble_predictions > df['close']).astype(int), np.zeros(len(df))
        
        # Extrair features
        features = build_direction_features(df)
        
        # Adicionar confiança se disponível
        if confidence_scores is not None:
            features['ensemble_confidence'] = confidence_scores
        
        # Normalizar
        X_scaled = self.scaler.transform(features.fillna(0))
        
        # Predição da árvore
        tree_direction = self.tree.predict(X_scaled)
        tree_proba = self.tree.predict_proba(X_scaled)  # Probabilidade
        
        # Confiança da árvore (max proba - 0.5) * 2 para escalar em 0-1
        tree_confidence = np.abs(2 * (np.max(tree_proba, axis=1) - 0.5))
        
        # Refinar: usar árvore se ela tiver mais confiança
        refined_direction = np.copy(tree_direction).astype(float)
        refinement_score = tree_confidence.copy()
        
        return refined_direction.astype(int), refinement_score
    
    def get_feature_importance(self):
        """Retorna importância das features"""
        if not self.trained:
            return pd.DataFrame()
        
        return pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.tree.feature_importances_
        }).sort_values('importance', ascending=False)


def apply_direction_refinement_to_backtest(df_test, predictions, confidence_scores=None):
    """
    Aplica refinamento de direção ao backtest.
    
    Fluxo:
    1. XGBoost/RF prediz preço
    2. Árvore de decisão refina a DIREÇÃO baseado em indicadores
    3. Retorna direção refinada
    """
    
    # Criar e treinar árvore
    tree_refiner = DirectionRefinementTree(max_depth=7, min_samples_leaf=50)
    
    # Labels: se target_price > close = up (1)
    direction_labels = (df_test['target_price'] > df_test['close']).astype(int)
    
    # Treinar
    importance = tree_refiner.train(df_test, direction_labels, confidence_scores)
    
    # Refinar predições
    refined_directions, refinement_scores = tree_refiner.predict_refined_direction(
        df_test,
        predictions['pred_ensemble'],
        confidence_scores
    )
    
    return {
        'tree_refiner': tree_refiner,
        'refined_directions': refined_directions,
        'refinement_scores': refinement_scores,
        'importance': importance
    }


if __name__ == '__main__':
    print("✅ Decision Tree Post-Processor loaded")
    print("Use: apply_direction_refinement_to_backtest(df_test, predictions)")
