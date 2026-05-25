# 🔗 Integração MQL5 ↔ Python XGBoost

## Arquitetura Completa

```
┌─ MQL5 (MT5) ──────────────────────────────────────────────┐
│                                                             │
│  1. Calcula indicadores (SMA, RSI, ATR, etc)              │
│  2. Detecta confluência (M15 vs H4)                       │
│  3. Detecta sweeps (breakouts)                            │
│  4. Calcula flow score                                    │
│  5. Monta JSON com 30+ campos                             │
│  6. POST para http://localhost:9998/ml5/predict          │
│                                                             │
└────────────────────────────────┬──────────────────────────┘
                                 │ HTTP POST (JSON)
                                 ↓
┌─ Python Inference Server ──────────────────────────────────┐
│                                                             │
│  1. Recebe JSON                                            │
│  2. Valida campos obrigatórios                            │
│  3. Extrai features                                        │
│  4. XGBoost faz predição                                  │
│  5. Retorna: BUY/SELL/HOLD + confiança                   │
│                                                             │
└────────────────────────────────┬──────────────────────────┘
                                 │ JSON Response
                                 ↓
┌─ MQL5 Trading (MT5) ───────────────────────────────────────┐
│                                                             │
│  1. Recebe decisão (BUY/SELL/HOLD)                        │
│  2. Recebe confiança (0-1)                                │
│  3. Valida gestão de risco                                │
│  4. Executa ordem (se confiança > threshold)             │
│  5. Log resultado                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Setup Passo a Passo

### 1️⃣ Iniciar Servidor Python

```bash
# Terminal 1: Iniciar servidor de inferência
python3 src/ml5_inference_server.py

# Output esperado:
# ================================================================================
# 🚀 SERVIDOR DE INFERÊNCIA ML5 COM XGBOOST
# ================================================================================
# ✅ Modelo XGBoost carregado: /home/ubuntu/pessoal/options/models/xgboost_model.pkl
# 📡 Escutando em: http://0.0.0.0:9998
# 📍 Endpoint: POST /ml5/predict
# 🏥 Health: GET /health
```

### 2️⃣ Configurar EA no MT5

**Criar Expert Advisor que:**

```mql5
// 1. Calcula indicadores
double sma_20 = iMA(_Symbol, PERIOD_M15, 20, 0, MODE_SMA, PRICE_CLOSE);
double rsi_14 = iRSI(_Symbol, PERIOD_M15, 14, PRICE_CLOSE);
// ... mais indicadores

// 2. Calcula confluência
string m15_trend = "UP";  // Resultado de sua análise
string h4_trend = "UP";   // Resultado de sua análise
bool is_aligned = (m15_trend == h4_trend);
double alignment_score = 0.90;

// 3. Detecta sweeps
string h4_sweep_type = "HIGH";  // HIGH, LOW, NONE
string m15_confirmation = "STRONG";  // STRONG, WEAK, NONE
string momentum_trend = "REDUCING";  // REDUCING, STABLE, INCREASING

// 4. Monta JSON
string json = StringFormat(
    "{"
    "\"symbol\":\"%s\","
    "\"timeframe\":\"M15\","
    "\"datetime\":\"%s\","
    "\"open\":%.5f,"
    "\"high\":%.5f,"
    "\"low\":%.5f,"
    "\"close\":%.5f,"
    "\"volume\":%d,"
    "\"sma_20\":%.5f,"
    "\"sma_50\":%.5f,"
    "\"rsi_14\":%.1f,"
    "\"m15_trend\":\"%s\","
    "\"h4_trend\":\"%s\","
    "\"is_aligned\":%s,"
    "\"alignment_score\":%.2f,"
    "\"h4_sweep_type\":\"%s\","
    "\"m15_confirmation\":\"%s\","
    "\"momentum_trend\":\"%s\","
    "\"flow_score\":%.2f,"
    "\"regime\":\"%s\","
    "\"atr_pct\":%.4f,"
    "\"bb_position\":%.2f,"
    "\"macd_hist\":%.6f,"
    "\"stoch_k\":%.1f,"
    "\"ret_1\":%.6f,"
    "\"ret_3\":%.6f,"
    "\"ret_5\":%.6f,"
    "\"realized_vol\":%.4f,"
    "\"expected_move\":%.5f,"
    "\"ema_12\":%.5f,"
    "\"ema_26\":%.5f,"
    "\"bb_upper\":%.5f,"
    "\"bb_lower\":%.5f,"
    "\"macd_line\":%.6f,"
    "\"macd_signal\":%.6f,"
    "\"stoch_d\":%.1f"
    "}",
    _Symbol, TimestampToStr(TimeCurrent()),
    open_price, high_price, low_price, close_price, volume,
    sma_20, sma_50, rsi_14,
    m15_trend, h4_trend, (is_aligned ? "true" : "false"), alignment_score,
    h4_sweep_type, m15_confirmation, momentum_trend,
    flow_score, regime, atr_pct, bb_position, macd_hist, stoch_k,
    ret_1, ret_3, ret_5, realized_vol, expected_move,
    ema_12, ema_26, bb_upper, bb_lower, macd_line, macd_signal, stoch_d
);

// 5. Envia para Python
string url = "http://localhost:9998/ml5/predict";
char result[];
WebRequest("POST", url, NULL, NULL, json, result);
```

### 3️⃣ Processar Resposta

```mql5
// Resposta esperada:
// {
//   "decision": "BUY",
//   "confidence": 0.85,
//   "reasoning": "✅ CONFLUÊNCIA: M15 UP = H4 UP | ...",
//   "timestamp": "2026-05-25T15:45:00.123456"
// }

// Parse resposta
void ProcessPrediction(string response) {
    
    // Parse JSON
    string decision = ParseJsonString(response, "decision");  // "BUY", "SELL", "HOLD"
    double confidence = ParseJsonDouble(response, "confidence");  // 0-1
    string reasoning = ParseJsonString(response, "reasoning");
    
    // Validar confiança
    if (confidence < 0.65) {
        Print("Confiança baixa, esperar próximo sinal");
        return;
    }
    
    // Executar trade
    if (decision == "BUY") {
        OpenBuyOrder();
    } else if (decision == "SELL") {
        OpenSellOrder();
    } else {
        Print("HOLD - Sem ação");
    }
    
    // Log
    Print("Decisão: " + decision + " | Confiança: " + DoubleToString(confidence, 2));
}
```

---

## ✅ Teste de Conexão

### Terminal 2: Testar conexão

```bash
# Verificar se servidor está respondendo
curl -X GET http://localhost:9998/health

# Esperado:
# {
#   "status": "ok",
#   "timestamp": "2026-05-25T15:45:00.123456"
# }
```

### Terminal 3: Testar predição

```bash
# Fazer POST com dados teste
curl -X POST http://localhost:9998/ml5/predict \
  -H "Content-Type: application/json" \
  -d '{
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
    "is_aligned": true,
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
    "expected_move": 0.00150
  }'

# Esperado:
# {
#   "decision": "BUY",
#   "confidence": 0.85,
#   "reasoning": "✅ CONFLUÊNCIA: M15 UP = H4 UP | 🔄 SWEEP HIGH + M15 STRONG | ...",
#   "features": {...},
#   "xgb_score": 0.92,
#   "timestamp": "2026-05-25T15:45:00.123456"
# }
```

---

## 🔄 Fluxo Completo de Execução

### 1. MT5 Envia Dados (a cada novo candle)

```
POST http://localhost:9998/ml5/predict
{...dados completos do MQL5...}
```

### 2. Python Processa

```
✅ Valida campos
✅ Extrai features
✅ XGBoost predição
✅ Retorna decisão
```

### 3. MT5 Recebe Resposta

```
{
  "decision": "BUY",
  "confidence": 0.87,
  ...
}
```

### 4. EA Executa Trade

```
if confidence > 0.65 and decision == "BUY":
    OpenBuyOrder()
```

---

## 📊 Exemplo Esperado

**Entrada (MQL5 → Python):**
```json
{
  "symbol": "EURUSD",
  "m15_trend": "UP",
  "h4_trend": "UP",
  "is_aligned": true,
  "alignment_score": 0.90,
  "h4_sweep_type": "HIGH",
  "m15_confirmation": "STRONG",
  "momentum_trend": "REDUCING",
  "flow_score": 0.72,
  "regime": "UPTREND",
  "sma_20": 1.08900,
  "rsi_14": 65.0,
  ...
}
```

**Saída (Python → MQL5):**
```json
{
  "decision": "BUY",
  "confidence": 0.87,
  "reasoning": "✅ CONFLUÊNCIA: M15 UP = H4 UP | 🔄 SWEEP HIGH + M15 STRONG | 📈 UPTREND | 💰 Flow FORTE | Confiança: 87%",
  "xgb_score": 0.92,
  "timestamp": "2026-05-25T15:45:00.123456"
}
```

---

## 🛠️ Checklist de Setup

- [ ] Servidor Python rodando: `python3 src/ml5_inference_server.py`
- [ ] Porta 9998 acessível: `curl http://localhost:9998/health`
- [ ] EA no MT5 com cálculos de indicadores
- [ ] EA no MT5 montando JSON completo
- [ ] EA no MT5 enviando POST para Python
- [ ] EA no MT5 processando resposta
- [ ] EA no MT5 executando trades baseado em confiança
- [ ] Logs salvando resultados

---

## 🚀 Começar

```bash
# Terminal 1: Servidor Python
python3 src/ml5_inference_server.py

# Terminal 2: Monitorar (opcional)
tail -f logs/ml5_inference.log

# Terminal 3: Testes
curl http://localhost:9998/health
```

---

**Fluxo:** MQL5 (calcula) → Python (XGBoost) → MQL5 (executa)
