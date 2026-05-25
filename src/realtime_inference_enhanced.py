#!/usr/bin/env python3
"""
Enhanced Realtime Inference Engine - Com novo modelo XGBoost 57.2%

Carrega o modelo enhanced_xgboost_model.pkl (57.2% accuracy)
e integra com o sistema de trading em tempo real.

Features: 27 (7 técnicas + 5 trend + 3 volatilidade + 3 price action + 5 SMC + 4 derivadas)
Confluence: Filtra sinais usando top indicadores para aumentar acurácia efetiva
"""

import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any

from trading_decision import TradingDecisionEngine, TradeAction
from telegram_notifier import TelegramNotifier
from core.confluence_filter import (
    calculate_confluence_score,
    should_open_trade,
    get_strike_selection,
)

try:
    import pandas as pd
    import numpy as np
    from core.enhanced_features import generate_enhanced_features, get_feature_list
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False


class EnhancedRealtimeInferenceEngine:
    """
    Engine de inferência com modelo XGBoost melhorado (57.2% accuracy).
    
    Usa 27 features engineered (SMC + técnicas + derivadas).
    Suporta carregamento automático do enhanced_xgboost_model.pkl.
    """
    
    def __init__(
        self,
        model_dir_path: Path,
        confidence_threshold: float = 0.55,
        strangle_threshold: float = 0.40,
        telegram_enabled: bool = False,
    ):
        """
        Inicializa engine com modelo melhorado.
        
        Args:
            model_dir_path: Diretório com enhanced_xgboost_model.pkl
            confidence_threshold: Limite de confiança
            strangle_threshold: Limite para STRANGLE
            telegram_enabled: Enviar sinais via Telegram
        """
        self.model_dir = Path(model_dir_path)
        self.confidence_threshold = confidence_threshold
        self.strangle_threshold = strangle_threshold
        
        # Carrega modelo melhorado
        self.model = None
        self.feature_names = None
        self.feature_categories = None
        
        self._load_enhanced_model()
        
        # Engine de decisão + Telegram
        self.decision_engine = TradingDecisionEngine(
            confidence_threshold=confidence_threshold,
            strangle_threshold=strangle_threshold,
        )
        
        self.telegram = TelegramNotifier()
        self.telegram_enabled = telegram_enabled and self.telegram.enabled
    
    def _load_enhanced_model(self):
        """Carrega enhanced_xgboost_model.pkl"""
        model_file = self.model_dir / "enhanced_xgboost_model.pkl"
        
        if not model_file.exists():
            print(f"[ENHANCED] ⚠️  Modelo não encontrado: {model_file}")
            return
        
        try:
            with open(model_file, "rb") as f:
                data = pickle.load(f)
            
            # Extrai componentes
            if isinstance(data, dict):
                self.model = data.get("model")
                self.feature_names = data.get("feature_names", [])
            else:
                # Se for um modelo direto (sem dict wrapper)
                self.model = data
                self.feature_names = []
            
            if self.model:
                print(f"[ENHANCED] ✅ Modelo carregado: {model_file}")
                print(f"[ENHANCED] 📊 Features: {len(self.feature_names)} nomes")
                
                # Carrega metadata de features
                features_file = self.model_dir / "enhanced_features_used.json"
                if features_file.exists():
                    with open(features_file, "r") as f:
                        self.feature_categories = json.load(f)
                    print(f"[ENHANCED] 📋 Categorias: {list(self.feature_categories.keys())}")
            else:
                print(f"[ENHANCED] ⚠️  Erro: Não conseguiu extrair modelo do arquivo")
        
        except Exception as e:
            print(f"[ENHANCED] ❌ Erro carregando modelo: {e}")
    
    def infer(
        self,
        symbol: str,
        timeframe: str,
        datetime_str: str,
        features: Dict[str, float],
        smc_features: Optional[Dict[str, float]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Faz inferência com modelo melhorado.
        
        Args:
            symbol: Ex. "EURUSD"
            timeframe: Ex. "M15"
            datetime_str: Timestamp do candle
            features: Dict com OHLC e indicadores básicos
            smc_features: Dict com features SMC (opcional)
        
        Returns:
            Dict com recomendação ou None se erro.
        """
        if not self.model:
            print("[ENHANCED] ⚠️  Modelo não carregado")
            return None
        
        if not ENHANCED_AVAILABLE:
            print("[ENHANCED] ⚠️  pandas/numpy não disponíveis")
            return None
        
        try:
            # Converte para DataFrame
            feature_df = pd.DataFrame([features])
            
            # Se tiver SMC features, gera features melhoradas
            if smc_features and "generate_enhanced_features" in dir():
                try:
                    enhanced_X = generate_enhanced_features(feature_df, smc_features)
                    print(f"[ENHANCED] ✅ {len(enhanced_X.columns)} features engineered")
                except Exception as e:
                    print(f"[ENHANCED] ⚠️  Erro gerando features melhoradas: {e}")
                    enhanced_X = feature_df
            else:
                enhanced_X = feature_df
            
            # Garante ordem correta das features
            if self.feature_names and len(self.feature_names) > 0:
                missing = set(self.feature_names) - set(enhanced_X.columns)
                if missing:
                    print(f"[ENHANCED] ⚠️  Features faltando: {missing}")
                    # Adiciona com zeros
                    for feat in missing:
                        enhanced_X[feat] = 0.0
                
                # Reordena
                enhanced_X = enhanced_X[self.feature_names]
            
            # Predição
            proba = self.model.predict_proba(enhanced_X)[0]
            
            # Interpreta resultados (assume binary: DOWN/UP)
            if len(proba) == 2:
                p_down = float(proba[0])
                p_up = float(proba[1])
                p_flat = 0.0
            else:
                # 3 classes: DOWN, FLAT, UP
                p_down = float(proba[0]) if len(proba) > 0 else 0.33
                p_flat = float(proba[1]) if len(proba) > 1 else 0.34
                p_up = float(proba[2]) if len(proba) > 2 else 0.33
            
            # 🎯 CONFLUENCE FILTER
            # Calcula score de confluência usando top indicadores
            confluence_score = calculate_confluence_score(enhanced_X.iloc[0])
            
            # Decide se abre trade com confluência
            model_prob = max(p_up, p_down)  # Maior probabilidade
            confluence_check = should_open_trade(
                model_prob=model_prob,
                confluence_score=confluence_score,
                confidence_threshold=self.confidence_threshold * 100
            )
            
            # Log de confluência
            print(f"[CONFLUENCE] 📊 Model: {model_prob*100:.1f}% | Confluence: {confluence_score:.1f}% | Decision: {'✅ OPEN' if confluence_check['should_open'] else '❌ SKIP'}")
            
            # Se confluência rejeita, não abre trade
            if not confluence_check['should_open']:
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "datetime": datetime_str,
                    "action": "NO_TRADE",
                    "reason": confluence_check['reason'],
                    "p_up": p_up,
                    "p_down": p_down,
                    "confidence": confluence_check['confidence'],
                }
            
            # Aplica engine de decisão
            signal = self.decision_engine.decide(
                symbol=symbol,
                timeframe=timeframe,
                datetime_str=datetime_str,
                p_down=p_down,
                p_flat=p_flat,
                p_up=p_up,
            )
            
            # Envia Telegram
            if self.telegram_enabled and signal.action != TradeAction.NO_TRADE:
                self.telegram.send_signal(
                    action=signal.action.value,
                    symbol=symbol,
                    timeframe=timeframe,
                    p_up=p_up,
                    p_down=p_down,
                    p_flat=p_flat,
                    confidence=signal.confidence,
                )
            
            return {
                "action": signal.action.value,
                "confidence": f"{signal.confidence:.4f}",
                "p_up": f"{p_up:.4f}",
                "p_down": f"{p_down:.4f}",
                "p_flat": f"{p_flat:.4f}",
                "reasoning": signal.reasoning,
                "model": "enhanced_xgboost_57.2%",
                "features_used": len(self.feature_names),
            }
        
        except Exception as e:
            print(f"[ENHANCED] ❌ Erro na inferência: {e}")
            import traceback
            traceback.print_exc()
            return None


def make_enhanced_inference_engine(
    model_dir: Path,
    telegram_enabled: bool = False,
) -> EnhancedRealtimeInferenceEngine:
    """Factory para criar engine com modelo melhorado."""
    return EnhancedRealtimeInferenceEngine(
        model_dir_path=model_dir,
        telegram_enabled=telegram_enabled,
    )
