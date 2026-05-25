# 📡 Formato de Dados MQL5 → Python via Websocket

## Especificação Completa

MQL5 deve enviar **POST HTTP** para `http://localhost:9999/mt5/candle` com JSON abaixo:

```json
{
  "symbol": "EURUSD",
  "timeframe": "M15",
  "datetime": "2026-05-25 15:45:00",
  "open": 1.08905,
  "high": 1.08925,
  "low": 1.08895,
  "close": 1.08915,
  "volume": 1520,
  
  "INDICADORES TÉCNICOS (MQL5 CALCULA)":
  "sma_20": 1.08900,
  "sma_50": 1.08850,
  "sma_200": 1.08800,
  "ema_12": 1.08910,
  "ema_26": 1.08905,
  "atr": 0.00025,
  "atr_pct": 0.0225,
  "rsi_14": 55.2,
  
  "CONFLUÊNCIA MULTI-TF (MQL5 CALCULA)":
  "m15_trend": "UP",
  "h4_trend": "UP",
  "m15_trend_strength": 0.85,
  "h4_trend_strength": 0.90,
  "is_aligned": true,
  "alignment_score": 0.875,
  
  "SWEEPS (MQL5 DETECTA)":
  "h4_sweep_type": "HIGH",
  "h4_sweep_strength": 0.75,
  "m15_confirmation": "STRONG",
  "momentum_acceleration": -0.15,
  "momentum_trend": "REDUCING",
  
  "FLOW E REGIME (MQL5 CALCULA)":
  "flow_score": 0.72,
  "regime": "UPTREND",
  "regime_strength": 0.68,
  "expected_move": 0.00150,
  "realized_vol": 0.0185,
  
  "ESTRUTURA SMC (MQL5 DETECTA)":
  "recent_high": 1.08950,
  "recent_low": 1.08850,
  "swing_high_broken": true,
  "swing_low_broken": false,
  
  "RETORNOS (MQL5 CALCULA)":
  "ret_1": 0.00091,
  "ret_3": 0.00215,
  "ret_5": 0.00342,
  
  "FEATURES PARA XGBOOST":
  "bb_upper": 1.08960,
  "bb_lower": 1.08840,
  "bb_position": 0.62,
  "macd_line": 0.00015,
  "macd_signal": 0.00012,
  "macd_hist": 0.00003,
  "stoch_k": 65.5,
  "stoch_d": 62.3
}
```

## Campos Obrigatórios (Mínimo)

```python
REQUIRED = {
    # OHLCV
    "symbol", "timeframe", "datetime", "open", "high", "low", "close", "volume",
    
    # Tendência M15 vs H4
    "m15_trend", "h4_trend", "is_aligned", "alignment_score",
    
    # Sweep H4 + M15
    "h4_sweep_type", "m15_confirmation", "momentum_trend",
    
    # Flow e Regime
    "flow_score", "regime",
    
    # Features para XGBoost (mínimo 10)
    "sma_20", "ema_12", "atr_pct", "rsi_14", "bb_position",
    "macd_hist", "stoch_k", "ret_1", "realized_vol", "expected_move"
}
```

## Exemplos de Valores

### Cenário 1: Sinal BUY (Ideal)
```json
{
  "m15_trend": "UP",
  "h4_trend": "UP",
  "is_aligned": true,
  "alignment_score": 0.90,
  "h4_sweep_type": "HIGH",
  "m15_confirmation": "STRONG",
  "momentum_trend": "REDUCING",
  "flow_score": 0.75,
  "regime": "UPTREND",
  "sma_20": 1.08900,
  "rsi_14": 65.0,
  "stoch_k": 75.0
}
```

### Cenário 2: Sinal SELL (Ideal)
```json
{
  "m15_trend": "DOWN",
  "h4_trend": "DOWN",
  "is_aligned": true,
  "alignment_score": 0.90,
  "h4_sweep_type": "LOW",
  "m15_confirmation": "STRONG",
  "momentum_trend": "REDUCING",
  "flow_score": -0.75,
  "regime": "DOWNTREND",
  "sma_20": 1.08850,
  "rsi_14": 35.0,
  "stoch_k": 25.0
}
```

### Cenário 3: Sinal HOLD (Divergência)
```json
{
  "m15_trend": "UP",
  "h4_trend": "DOWN",
  "is_aligned": false,
  "alignment_score": 0.40,
  "h4_sweep_type": "NONE",
  "m15_confirmation": "WEAK",
  "momentum_trend": "STABLE",
  "flow_score": 0.15,
  "regime": "SIDEWAYS",
  "sma_20": 1.08900,
  "rsi_14": 50.0,
  "stoch_k": 50.0
}
```

## Mapeamento de Tipos

```python
FIELD_TYPES = {
    # Strings
    "symbol": str,                    # "EURUSD"
    "timeframe": str,                 # "M15", "H4", "D1"
    "datetime": str,                  # "2026-05-25 15:45:00"
    "m15_trend": str,                 # "UP", "DOWN", "NEUTRAL"
    "h4_trend": str,                  # "UP", "DOWN", "NEUTRAL"
    "h4_sweep_type": str,             # "HIGH", "LOW", "NONE"
    "m15_confirmation": str,          # "STRONG", "WEAK", "NONE"
    "momentum_trend": str,            # "REDUCING", "STABLE", "INCREASING"
    "regime": str,                    # "UPTREND", "DOWNTREND", "SIDEWAYS"
    
    # Booleans
    "is_aligned": bool,               # true, false
    
    # Floats (preços, indicadores, scores)
    "open": float,                    # 1.08905
    "high": float,                    # 1.08925
    "low": float,                     # 1.08895
    "close": float,                   # 1.08915
    "sma_20": float,                  # 1.08900
    "alignment_score": float,         # 0-1 (0.875)
    "flow_score": float,              # -1 a 1
    "rsi_14": float,                  # 0-100
    
    # Integers
    "volume": int,                    # 1520
}
```

## Uso em Python (recepcão)

```python
import json
from datetime import datetime

# Receber do websocket
payload = {
    "symbol": "EURUSD",
    "datetime": "2026-05-25 15:45:00",
    "m15_trend": "UP",
    "h4_trend": "UP",
    "is_aligned": True,
    "flow_score": 0.72,
    # ... todos os campos
}

# Validar
REQUIRED = {...}
if not REQUIRED.issubset(set(payload.keys())):
    raise ValueError("Missing required fields")

# Extrair features para XGBoost
features = {
    "sma_20": payload["sma_20"],
    "ema_12": payload["ema_12"],
    "atr_pct": payload["atr_pct"],
    "rsi_14": payload["rsi_14"],
    "bb_position": payload["bb_position"],
    "macd_hist": payload["macd_hist"],
    "stoch_k": payload["stoch_k"],
    "ret_1": payload["ret_1"],
    "realized_vol": payload["realized_vol"],
    "expected_move": payload["expected_move"]
}

# Processsar com XGBoost
prediction = xgb_model.predict([list(features.values())])
```

## Fluxo Completo

```
MQL5 (MT5):
  1. Calcula todos os indicadores
  2. Detecta confluência M15 vs H4
  3. Detecta sweeps
  4. Calcula flow score
  5. Monta JSON com TUDO
  6. POST para http://localhost:9999/mt5/candle

Python (Servidor):
  1. Recebe JSON
  2. Valida campos obrigatórios
  3. Extrai features
  4. Passa para XGBoost
  5. Retorna: BUY/SELL/HOLD + confiança

Python (Trading):
  1. Recebe decisão
  2. Valida gestão de risco
  3. Executa operação
  4. Log resultado
```

## Checklist MQL5

- [ ] Enviar: `symbol`, `timeframe`, `datetime`
- [ ] Enviar: `open`, `high`, `low`, `close`, `volume`
- [ ] Calcular e enviar: `sma_20`, `sma_50`, `sma_200`, `ema_12`, `ema_26`
- [ ] Calcular e enviar: `atr`, `atr_pct`, `rsi_14`
- [ ] Calcular e enviar: `bb_upper`, `bb_lower`, `bb_position`
- [ ] Calcular e enviar: `macd_line`, `macd_signal`, `macd_hist`
- [ ] Calcular e enviar: `stoch_k`, `stoch_d`
- [ ] Detectar e enviar: `m15_trend`, `h4_trend`, `is_aligned`, `alignment_score`
- [ ] Detectar e enviar: `h4_sweep_type`, `m15_confirmation`, `momentum_trend`
- [ ] Calcular e enviar: `flow_score`, `regime`
- [ ] Calcular e enviar: `ret_1`, `ret_3`, `ret_5`
- [ ] Calcular e enviar: `realized_vol`, `expected_move`

Total: **30+ campos** - Tudo calculado em MQL5!
