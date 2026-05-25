"""
Processador de Dados MQL5 com XGBoost

Pipeline:
1. Recebe JSON completo do MQL5 via websocket
2. Valida campos obrigatórios
3. Extrai features
4. XGBoost faz predição
5. Retorna decisão: BUY/SELL/HOLD + confiança
"""

import json
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import numpy as np
import pandas as pd


# Campos obrigatórios do MQL5
REQUIRED_FIELDS = {
    # OHLCV
    "symbol", "timeframe", "datetime", "open", "high", "low", "close", "volume",
    
    # Tendência
    "m15_trend", "h4_trend", "is_aligned", "alignment_score",
    
    # Sweep
    "h4_sweep_type", "m15_confirmation", "momentum_trend",
    
    # Flow e Regime
    "flow_score", "regime",
    
    # Features para XGBoost (mínimo 10)
    "sma_20", "ema_12", "atr_pct", "rsi_14", "bb_position",
    "macd_hist", "stoch_k", "ret_1", "realized_vol", "expected_move"
}

# Features que XGBoost vai usar
XGBOOST_FEATURES = [
    "sma_20", "sma_50", "sma_200",
    "ema_12", "ema_26",
    "atr_pct", "rsi_14",
    "bb_upper", "bb_lower", "bb_position",
    "macd_line", "macd_signal", "macd_hist",
    "stoch_k", "stoch_d",
    "flow_score",
    "ret_1", "ret_3", "ret_5",
    "realized_vol", "expected_move",
    "alignment_score"
]

# Features categóricas (converter em números)
CATEGORICAL_FEATURES = {
    "m15_trend": {"UP": 1, "DOWN": -1, "NEUTRAL": 0},
    "h4_trend": {"UP": 1, "DOWN": -1, "NEUTRAL": 0},
    "h4_sweep_type": {"HIGH": 1, "LOW": -1, "NONE": 0},
    "m15_confirmation": {"STRONG": 1, "WEAK": 0.5, "NONE": 0},
    "momentum_trend": {"REDUCING": 1, "STABLE": 0.5, "INCREASING": 0},
    "regime": {"UPTREND": 1, "DOWNTREND": -1, "SIDEWAYS": 0},
    "is_aligned": {True: 1, False: 0}
}


class ML5DataProcessor:
    """Processa dados do MQL5 e faz predição com XGBoost."""
    
    def __init__(self, model_path: Optional[str] = None, verbose: bool = True):
        """
        Args:
            model_path: Caminho para modelo XGBoost treinado
            verbose: Exibir logs
        """
        self.model_path = model_path or "/home/ubuntu/pessoal/options/models/xgboost_model.pkl"
        self.xgb_model = None
        self.verbose = verbose
        self.scaler = None
        
        # Carregar modelo
        if Path(self.model_path).exists():
            with open(self.model_path, 'rb') as f:
                self.xgb_model = pickle.load(f)
            if self.verbose:
                print(f"✅ Modelo XGBoost carregado: {self.model_path}")
        else:
            if self.verbose:
                print(f"⚠️ Modelo não encontrado: {self.model_path}")
                print("   Usando previsão por confluência/regime")
    
    def validate(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Valida campos obrigatórios."""
        missing = REQUIRED_FIELDS - set(payload.keys())
        if missing:
            return False, f"Missing fields: {sorted(missing)}"
        return True, None
    
    def _encode_categorical(self, payload: Dict[str, Any]) -> Dict[str, float]:
        """Converte features categóricas em números."""
        encoded = {}
        for field, mapping in CATEGORICAL_FEATURES.items():
            if field in payload:
                value = payload[field]
                encoded[field] = mapping.get(value, 0)
            else:
                encoded[field] = 0
        return encoded
    
    def _extract_features(self, payload: Dict[str, Any]) -> Dict[str, float]:
        """Extrai features para XGBoost."""
        features = {}
        
        # Features numéricas diretas
        for feat in XGBOOST_FEATURES:
            if feat in payload:
                try:
                    features[feat] = float(payload[feat])
                except (ValueError, TypeError):
                    features[feat] = 0.0
            else:
                features[feat] = 0.0
        
        # Features categóricas codificadas
        categorical = self._encode_categorical(payload)
        features.update(categorical)
        
        return features
    
    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Faz predição com base nos dados do MQL5.
        
        Returns:
            {
                "decision": "BUY" | "SELL" | "HOLD",
                "confidence": 0-1,
                "reasoning": str,
                "features": dict,
                "xgb_score": float (se modelo disponível),
                "manual_signal": str (se sem modelo)
            }
        """
        # Validar
        is_valid, error = self.validate(payload)
        if not is_valid:
            return {
                "decision": "ERROR",
                "confidence": 0,
                "error": error,
                "reasoning": f"Validação falhou: {error}"
            }
        
        # Extrair features
        features = self._extract_features(payload)
        
        # Se tem modelo XGBoost, usar
        if self.xgb_model:
            return self._predict_with_xgboost(payload, features)
        else:
            return self._predict_with_confluence(payload, features)
    
    def _predict_with_xgboost(self, payload: Dict[str, Any], features: Dict[str, float]) -> Dict[str, Any]:
        """Predição usando XGBoost."""
        try:
            # Preparar array na ordem correta
            feature_array = np.array([[features.get(f, 0) for f in XGBOOST_FEATURES]])
            
            # Predição
            xgb_pred = self.xgb_model.predict(feature_array)[0]
            xgb_proba = self.xgb_model.predict_proba(feature_array)[0]
            
            # Converter para decisão
            if xgb_pred == 1:  # UP
                decision = "BUY"
                confidence = float(xgb_proba[1]) if len(xgb_proba) > 1 else 0.5
            elif xgb_pred == -1:  # DOWN
                decision = "SELL"
                confidence = float(xgb_proba[0]) if len(xgb_proba) > 0 else 0.5
            else:  # NEUTRAL
                decision = "HOLD"
                confidence = 0.3
            
            # Reasoning
            reasoning = self._build_reasoning(payload, decision, confidence)
            
            return {
                "decision": decision,
                "confidence": float(confidence),
                "reasoning": reasoning,
                "features": features,
                "xgb_score": float(xgb_pred),
                "xgb_proba": [float(p) for p in xgb_proba],
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            if self.verbose:
                print(f"❌ Erro XGBoost: {e}")
            # Fallback para confluência
            return self._predict_with_confluence(payload, features)
    
    def _predict_with_confluence(self, payload: Dict[str, Any], features: Dict[str, float]) -> Dict[str, Any]:
        """Predição usando confluência (fallback sem modelo)."""
        
        m15_trend = payload.get("m15_trend", "NEUTRAL")
        h4_trend = payload.get("h4_trend", "NEUTRAL")
        is_aligned = payload.get("is_aligned", False)
        alignment_score = payload.get("alignment_score", 0.5)
        flow_score = payload.get("flow_score", 0)
        regime = payload.get("regime", "SIDEWAYS")
        h4_sweep_type = payload.get("h4_sweep_type", "NONE")
        m15_confirmation = payload.get("m15_confirmation", "NONE")
        
        # Score de confluência
        confidence = alignment_score
        
        # Ajustar por sweep confirmado
        if h4_sweep_type != "NONE" and m15_confirmation == "STRONG":
            confidence += 0.20
        
        # Ajustar por flow
        if abs(flow_score) > 0.7:
            confidence += 0.15
        
        # Limitar a 1.0
        confidence = min(1.0, max(0.0, confidence))
        
        # Decisão
        if is_aligned and m15_trend == h4_trend:
            if m15_trend == "UP":
                decision = "BUY" if h4_sweep_type != "LOW" else "HOLD"
            elif m15_trend == "DOWN":
                decision = "SELL" if h4_sweep_type != "HIGH" else "HOLD"
            else:
                decision = "HOLD"
        else:
            decision = "HOLD"
        
        # Ajustar confiança se divergência
        if not is_aligned:
            confidence *= 0.7
        
        reasoning = self._build_reasoning(payload, decision, confidence)
        
        return {
            "decision": decision,
            "confidence": float(confidence),
            "reasoning": reasoning,
            "features": features,
            "manual_signal": "confluência + regime",
            "timestamp": datetime.now().isoformat()
        }
    
    def _build_reasoning(self, payload: Dict[str, Any], decision: str, confidence: float) -> str:
        """Monta explicação da decisão."""
        parts = []
        
        # Confluência
        if payload.get("is_aligned"):
            parts.append(f"✅ CONFLUÊNCIA: M15 {payload.get('m15_trend')} = H4 {payload.get('h4_trend')}")
        else:
            parts.append(f"❌ DIVERGÊNCIA: M15 {payload.get('m15_trend')} ≠ H4 {payload.get('h4_trend')}")
        
        # Sweep
        sweep_type = payload.get("h4_sweep_type", "NONE")
        if sweep_type != "NONE":
            confirmation = payload.get("m15_confirmation", "NONE")
            parts.append(f"🔄 SWEEP {sweep_type} + M15 {confirmation}")
        
        # Regime
        regime = payload.get("regime", "SIDEWAYS")
        parts.append(f"📈 {regime}")
        
        # Flow
        flow = payload.get("flow_score", 0)
        if flow > 0.7:
            parts.append("💰 Flow FORTE")
        elif flow < -0.7:
            parts.append("💀 Anti-flow FORTE")
        
        # Confiança
        parts.append(f"Confiança: {confidence:.0%}")
        
        return " | ".join(parts)


def process_mql5_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Função helper para processar um payload do MQL5."""
    processor = ML5DataProcessor()
    return processor.predict(payload)


if __name__ == "__main__":
    # Teste
    test_payload = {
        "symbol": "EURUSD",
        "timeframe": "M15",
        "datetime": "2026-05-25 15:45:00",
        "open": 1.08905,
        "high": 1.08925,
        "low": 1.08895,
        "close": 1.08915,
        "volume": 1520,
        
        "sma_20": 1.08900,
        "sma_50": 1.08850,
        "sma_200": 1.08800,
        "ema_12": 1.08910,
        "ema_26": 1.08905,
        "atr": 0.00025,
        "atr_pct": 0.0225,
        "rsi_14": 65.2,
        
        "bb_upper": 1.08960,
        "bb_lower": 1.08840,
        "bb_position": 0.62,
        "macd_line": 0.00015,
        "macd_signal": 0.00012,
        "macd_hist": 0.00003,
        "stoch_k": 75.5,
        "stoch_d": 72.3,
        
        "m15_trend": "UP",
        "h4_trend": "UP",
        "is_aligned": True,
        "alignment_score": 0.90,
        
        "h4_sweep_type": "HIGH",
        "m15_confirmation": "STRONG",
        "momentum_trend": "REDUCING",
        
        "flow_score": 0.72,
        "regime": "UPTREND",
        "ret_1": 0.00091,
        "ret_3": 0.00215,
        "ret_5": 0.00342,
        "realized_vol": 0.0185,
        "expected_move": 0.00150,
    }
    
    processor = ML5DataProcessor()
    result = processor.predict(test_payload)
    
    print("\n" + "="*80)
    print("RESULTADO DA PREDIÇÃO")
    print("="*80)
    print(f"Decisão: {result['decision']}")
    print(f"Confiança: {result['confidence']:.0%}")
    print(f"Reasoning: {result.get('reasoning', 'N/A')}")
    print("="*80 + "\n")
