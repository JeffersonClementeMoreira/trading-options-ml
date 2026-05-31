# Arquitetura do Sistema

## 🏗️ Visão Geral

Sistema de trading automatizado que combina:
1. **Indicadores técnicos** (23 em tempo real)
2. **Machine Learning** (Ensemble: XGBoost + RandomForest)
3. **WebSocket** (Comunicação MT5 em tempo real)
4. **Telegram** (Alertas instantâneos)

## 📊 Fluxo de Dados

```
┌─────────────┐
│  MT5 (M15)  │  ← Candles em tempo real
└──────┬──────┘
       │
       ├─ OHLCV
       │
       ▼
┌────────────────────────┐
│  WebSocket Server      │  ← Escuta em localhost:5000
│  (production/websocket)│
└──────┬─────────────────┘
       │
       ├─ Calcula 23 indicadores
       ├─ XGBoost predição
       ├─ RandomForest predição
       ├─ Ensemble voting (média)
       │
       ▼
   [Signal = 1?]  ← Há sinal válido?
       │
   ┌───┴───┐
   │       │
  SIM     NÃO
   │       │
   ▼       ▼
 ENVIA   AGUARDA
TELEGRAM  PRÓX.
         CANDLE
   │
   ▼
┌────────────┐
│  Telegram  │  ← Alerta com entrada, alvo, direção
│    Bot     │
└────────────┘
```

## 🧠 Componente ML

### Treinamento (70% dos dados)

```python
# Jan 2024 - Abril 2025 (~41,630 candles)
X_train = [23 indicadores normalizados]
y_train = [0=SELL, 1=BUY]  # Baseado em próximo dia 14:00

# Modelos em paralelo
xgb = XGBClassifier(n_estimators=300, max_depth=5)
rf = RandomForestClassifier(n_estimators=300, max_depth=8)

xgb.fit(X_train, y_train)
rf.fit(X_train, y_train)
```

### Predição (30% - Produção)

```python
# Maio 2025 - Mai 2026 (~17,840 candles)
# NUNCA visto durante treinamento

xgb_probs = xgb.predict_proba(X_test)[0, 1]  # 0-1
rf_probs = rf.predict_proba(X_test)[0, 1]    # 0-1

ensemble_prob = (xgb_probs + rf_probs) / 2    # Votação

signal = 1 if ensemble_prob >= threshold else 0
```

### Threshold Optimization

Para cada par, encontramos threshold ótimo por F1-score:

```
EURUSD:  threshold = 0.10  (98.02% WR, mas possível overfitting)
GBPUSD:  threshold = 0.10  (96.61% WR)
EURAUD:  threshold = 0.25  (96.76% WR)
NZDUSD:  threshold = 0.15  (99.29% WR)
EURJPY:  threshold = 0.10  (92.89% WR)
```

⚠️ **Nota:** Thresholds muito baixos podem indicar overfitting. Monitorar em produção.

## 📈 23 Indicadores

### Grupo 1: Trend (5)
- **SMA20**: Média móvel simples 20 períodos
- **SMA50**: Média móvel simples 50 períodos
- **EMA12**: Média móvel exponencial 12
- **EMA26**: Média móvel exponencial 26
- **KAMA**: Kaufman Adaptive Moving Average

### Grupo 2: Momentum (4)
- **RSI**: Relative Strength Index (14)
- **MACD**: Moving Average Convergence Divergence
- **Momentum**: (Close - Close[10 períodos atrás]) / Close[10]
- **ROC**: Rate of Change

### Grupo 3: Volatilidade (4)
- **ATR**: Average True Range (14)
- **BB_Width**: Largura Bollinger Bands
- **StdDev**: Desvio padrão do close
- **Realized_Vol**: Volatilidade realizada (20 períodos)

### Grupo 4: Structure (3)
- **Support/Resistance**: Últimos pivot points
- **Order_Blocks**: Blocos de ordem (consolidação)
- **Fair_Value_Gap**: Gaps não preenchidos

### Grupo 5: Eficiência (1)
- **Kaufman_ER**: Efficiency Ratio para detecção de tendência

### Grupo 6: Binários (6)
- **price_above_sma20**: 1 se close > SMA20, else 0
- **price_above_sma50**: 1 se close > SMA50, else 0
- **price_above_bb_upper**: 1 se close > BB upper
- **price_below_bb_lower**: 1 se close < BB lower
- **rsi_overbought**: 1 se RSI > 70
- **rsi_oversold**: 1 se RSI < 30

Total: 23 indicadores + 23 versões normalizadas (%) = 51 colunas no DataFrame

## 🔄 Estratégia: 1 Ordem/Dia

### Regra de Abertura

```
CADA novo candle M15:
  IF signal == 1:
    IF não há ordem aberta hoje:
      ABRIR ordem
      - Entrada: close do candle
      - Direção: BUY se target > close, SELL senão
      - Alvo: pré-calculado para 14:00 UTC amanhã
      - ENVIA TELEGRAM
    ELSE:
      IGNORAR (máximo 1/dia)
  ELSE:
    AGUARDAR próximo candle
```

### Regra de Fechamento

```
Às 14:00 UTC (24h depois):
  FECHAR ordem automaticamente
  CALCULAR resultado (pips)
  REGISTRAR em log
  PRONTO para novo sinal no dia seguinte
```

### Timing

```
Primeira ordem surge: geralmente 00:00 UTC (81.7% dos dias)
Algumas ordens: 21:00-23:00 UTC do dia anterior (16.1%)
Dias sem sinal: 0.4% (1 em 225 dias)
```

## 🌐 WebSocket Server

### Arquitetura

```
production/websocket/server.py
├── DailySignalMonitor
│   ├── Load sinais pré-calculados (PRODUCAO_1ORDEM_*.csv)
│   ├── Check trigger por pair/data
│   └── Send Telegram alerts
│
└── WebSocket Server
    ├── Porta: 5000
    ├── Max clients: 10
    ├── Conexão persistente com MT5 EA
    └── Latência: < 100ms
```

### Protocolo

**Request (MT5 → Server):**
```json
{
  "pair": "EURUSD",
  "timestamp": "2025-09-02 00:00:00",
  "ohlc": {
    "open": 1.16307,
    "high": 1.16341,
    "low": 1.16271,
    "close": 1.16314
  }
}
```

**Response (Server → MT5):**
```json
{
  "signal": 1,
  "confidence": 0.67,
  "entry_price": 1.16314,
  "target_price": 1.16433,
  "direction": "BUY"
}
```

### Lógica

```python
async def handle_websocket(websocket):
    while True:
        msg = await websocket.recv()  # Espera candle
        
        data = json.loads(msg)
        pair = data['pair']
        timestamp = parse(data['timestamp'])
        
        # Checar se há sinal do dia
        signal = monitor.check_signal_for_today(pair, timestamp)
        
        if signal:
            # Enviar Telegram
            await monitor.send_telegram_alert(signal)
            
            # Responder ao MT5
            await websocket.send(json.dumps({
                'signal': 1,
                'entry': signal['entry_price'],
                'target': signal['target_price'],
                'direction': signal['direction_label']
            }))
        else:
            # Apenas responder sem sinal
            await websocket.send(json.dumps({
                'signal': 0,
                'message': 'Aguardando sinal'
            }))
```

## 💬 Telegram Integration

### Setup

```bash
1. Criar bot: @BotFather → /newbot
2. Salvar TOKEN
3. Obter CHAT_ID via getUpdates
4. Exportar variáveis:
   export TELEGRAM_TOKEN="..."
   export TELEGRAM_CHAT_ID="..."
```

### Envio de Mensagens

```python
async def send_telegram_alert(signal):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    message = f"""
🎯 SINAL DE TRADING

📊 Par: {signal['pair']}
🔼 Direção: {signal['direction_label']}
💰 Entrada: {signal['entry_price']:.5f}
🎯 Alvo: {signal['target_price']:.5f}
📏 Pips Esperados: {signal['actual_pips']:.1f}
📊 Confiança: {signal['probability']*100:.1f}%
⏰ Horário: {signal['timestamp']}
    """
    
    response = requests.post(url, json={
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    })
```

## 📊 Monitoramento

### Métricas Rastreadas

```python
# Por dia
- Signal time
- Entry price
- Target price
- Actual result (pips)
- Win/Loss
- Confidence score

# Agregado
- Win rate (%)
- Total pips
- Profit factor
- Max drawdown
- Sharpe ratio
```

### Logs

```
2026-05-31 10:30:00 - INFO - ✅ Signal Monitor Initialized
2026-05-31 10:30:05 - INFO - 🎯 Signal triggered for EURUSD
2026-05-31 10:30:06 - INFO - 💬 Telegram sent successfully
2026-05-31 14:00:00 - INFO - ✅ EURUSD Position closed: +11.9 pips
```

## 🔒 Segurança

### Isolamento de Dados

```
├── Code: Versionado em Git (público)
├── Models: Não versionado, backup local (privado)
├── Data: Não versionado (muito grande)
├── Credentials: .env (não versionado, em .gitignore)
└── Results: Versionado (apenas PRODUCAO_*)
```

### Autenticação

- ✅ Telegram token em .env
- ✅ MT5 credentials opcionais
- ✅ WebSocket: localhost por padrão (adicionar SSL em produção)

## 📈 Escalabilidade

### Atual (Single Machine)

```
1 WebSocket server
← 1 MT5 connection (1 par de cada)
← Processamento serial
← Latência: ~50-100ms
```

### Future (Multi-machine)

```
Load balancer
├─ WebSocket server 1 (EURUSD, GBPUSD)
├─ WebSocket server 2 (EURAUD, NZDUSD)
└─ WebSocket server 3 (EURJPY, outros)

Shared:
├─ Model cache (Redis)
├─ Result database (PostgreSQL)
└─ Telegram queue (RabbitMQ)
```

---

**Última atualização:** 31/05/2026  
**Versão:** 1.0.0
