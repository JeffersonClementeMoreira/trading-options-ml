#!/usr/bin/env python3
"""
Realtime inference engine para produção.

Recebe websocket JSON do EA MT5 → passa pelo XGBoost → 
envia Telegram com recomendação (CALL/PUT/STRANGLE/NO_TRADE).

Nota: Requer pandas + numpy apenas se usar XGBoost models.
Para uso sem modelos, apenas o decision engine é necessário.
"""

import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any

from trading_decision import TradingDecisionEngine, TradeAction
from telegram_notifier import TelegramNotifier

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class RealtimeInferenceEngine:
    """Engine que faz inferência em tempo real com dados do websocket."""
    
    def __init__(
        self,
        model_dir_path: Path,
        confidence_threshold: float = 0.55,
        strangle_threshold: float = 0.40,
        telegram_enabled: bool = False,
    ):
        """
        Carrega modelos salvos e inicializa.
        
        Args:
            model_dir_path: Diretório com modelos treinados (contém *.pkl)
            confidence_threshold: Limite de confiança para trade
            strangle_threshold: Limite para STRANGLE vs direcional
            telegram_enabled: Se True, envia sinais via Telegram
        """
        self.model_dir = Path(model_dir_path)
        self.confidence_threshold = confidence_threshold
        self.strangle_threshold = strangle_threshold
        
        # Tenta carregar modelos
        self.model_direction = None
        self.model_call = None
        self.model_put = None
        self.model_strangle = None
        
        self._load_models()
        
        # Engine de decisão + Telegram
        self.decision_engine = TradingDecisionEngine(
            confidence_threshold=confidence_threshold,
            strangle_threshold=strangle_threshold,
        )
        
        self.telegram = TelegramNotifier()
        self.telegram_enabled = telegram_enabled and self.telegram.enabled
    
    def _load_models(self):
        """Carrega arquivos .pkl do diretório de modelos."""
        if not PANDAS_AVAILABLE:
            print("[LOAD] Pandas não disponível - modelos não carregados")
            return
        
        for pkl_file in self.model_dir.glob("*.pkl"):
            try:
                with open(pkl_file, "rb") as f:
                    model = pickle.load(f)
                
                if "direction" in pkl_file.name:
                    self.model_direction = model
                    print(f"[LOAD] Modelo direção: {pkl_file.name}")
                elif "call" in pkl_file.name:
                    self.model_call = model
                    print(f"[LOAD] Modelo CALL: {pkl_file.name}")
                elif "put" in pkl_file.name:
                    self.model_put = model
                    print(f"[LOAD] Modelo PUT: {pkl_file.name}")
                elif "strangle" in pkl_file.name or "str" in pkl_file.name:
                    self.model_strangle = model
                    print(f"[LOAD] Modelo STRANGLE: {pkl_file.name}")
            except Exception as e:
                print(f"[LOAD] Erro carregando {pkl_file}: {e}")
    
    def infer(
        self,
        symbol: str,
        timeframe: str,
        datetime_str: str,
        features: Dict[str, float],
    ) -> Optional[Dict[str, Any]]:
        """
        Faz inferência com dados do websocket.
        
        Args:
            symbol: Ex. "EURUSD"
            timeframe: Ex. "M15"
            datetime_str: Timestamp do candle
            features: Dict com valores dos indicadores
        
        Returns:
            Dict com recomendação ou None se erro.
        """
        if not self.model_direction:
            # Se não tiver modelo, retorna None
            return None
        
        if not PANDAS_AVAILABLE:
            print("[INFER] Pandas não disponível - não posso fazer inferência")
            return None
        
        try:
            # Converte features para DataFrame
            feature_df = pd.DataFrame([features])
            
            # Predições
            proba_dir = self.model_direction.predict_proba(feature_df)[0]
            
            # Assume ordem: [DOWN, FLAT, UP]
            p_down = float(proba_dir[0]) if len(proba_dir) > 0 else 0.33
            p_flat = float(proba_dir[1]) if len(proba_dir) > 1 else 0.34
            p_up = float(proba_dir[2]) if len(proba_dir) > 2 else 0.33
            
            # Aplica engine de decisão
            signal = self.decision_engine.decide(
                symbol=symbol,
                timeframe=timeframe,
                datetime_str=datetime_str,
                p_down=p_down,
                p_flat=p_flat,
                p_up=p_up,
            )
            
            # Envia Telegram se em produção
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
            }
        
        except Exception as e:
            print(f"[INFER] Erro: {e}")
            return None


def make_inference_engine(
    model_dir: Path,
    telegram_enabled: bool = False,
) -> RealtimeInferenceEngine:
    """Factory para criar engine de inferência."""
    return RealtimeInferenceEngine(
        model_dir_path=model_dir,
        telegram_enabled=telegram_enabled,
    )
