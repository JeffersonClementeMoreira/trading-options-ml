# MT5 HTTP Server - Sistema de Sinais em Tempo Real

## 🎯 Visão Geral

Sistema que recebe dados M15 em tempo real do MT5 via HTTP, processa com modelo de machine learning e gera sinais de trading.

```
MT5 (Linux/Wine)
  ↓ (HTTP POST /candle)
server_mt5_http.py
  ↓ (processa indicadores + ML)
Modelo XGBoost + RandomForest
  ↓ (thresholds otimizados)
Telegram Alert
```

## 📋 Arquitetura

### Componentes

1. **MT5 Terminal** (`~/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe`)
   - Roda via Wine em background
   - EA `SendCandlesToServer.ex5` envia candles M15

2. **HTTP Server** (`production/server_mt5_http.py`)
   - Flask app na porta 8765
   - Recebe POST requests com OHLCV
   - Calcula 23 indicadores técnicos
   - Usa modelo ML para predict
   - Aplica thresholds otimizados por par
   - Envia alertas Telegram

3. **Modelo ML** (integrado no server)
   - XGBoost (300 trees, max_depth=5)
   - RandomForest (300 trees, max_depth=8)
   - Ensemble: média das probabilidades
   - Thresholds otimizados por par

### Fluxo de Dados

```json
MT5 POST:
{
  "symbol": "EURUSD",
  "datetime": "2026-05-31T14:30:00",
  "open": 1.0850,
  "high": 1.0851,
  "low": 1.0849,
  "close": 1.0850,
  "volume": 1000
}

↓ (server_mt5_http.py processa)

Response:
{
  "status": "ok",
  "signal": 1,
  "confidence": 0.87,
  "entry_price": 1.0850,
  "timestamp": "2026-05-31T14:31:00Z"
}

↓ (se signal=1)

Telegram Alert:
🟢 BUY EURUSD
Entry: $1.08500
Confidence: 87%
```

## 🚀 Como Rodar

### 1️⃣ Instalação

```bash
cd /home/ubuntu/pessoal/options

# Instalar dependências (Flask, etc)
pip install -r requirements.txt

# Configurar Telegram (opcional)
cp .env.example .env
vi .env  # editar TELEGRAM_TOKEN e TELEGRAM_CHAT_ID
```

### 2️⃣ Iniciar Sistema

#### Opção A: Usar script de startup

```bash
bash bin/start_mt5_production.sh
```

Este script:
- Verifica dependências
- Limpa processos antigos
- Carrega modelos ML (1-2 minutos)
- Inicia servidor HTTP
- Monitora com auto-restart

#### Opção B: Manual

```bash
# Terminal 1: Servidor HTTP
cd /home/ubuntu/pessoal/options/production
python3 server_mt5_http.py

# Terminal 2: Ver logs
tail -f /tmp/mt5_server.log
```

### 3️⃣ Iniciar MT5 (em outro terminal)

```bash
# Parar MT5 antigo (se existir)
pkill -9 -f "terminal64.exe"

# Iniciar novo
DISPLAY=:99 wine ~/.wine/drive_c/Program\ Files/MetaTrader\ 5/terminal64.exe &
```

## 🧪 Testando

### Sem MT5 (teste rápido)

```bash
# Terminal 1: Servidor
cd /home/ubuntu/pessoal/options/production
python3 server_mt5_http.py

# Terminal 2: Cliente de teste
python3 test_client_http.py

# Esperado:
# ✅ test_client_http.py simula 21 candles históricos
# ✅ Depois 3 candles "reais"
# 🎯 Se confidence > threshold, Signal=1 e Telegram é enviado
```

### Com MT5 Real

1. MT5 rodando com EA `SendCandlesToServer.ex5`
2. Servidor HTTP ouve na porta 8765
3. A cada novo candle M15, EA envia para http://127.0.0.1:8765/mt5/candle
4. Servidor processa e retorna sinal
5. Se Signal=1, Telegram é enviado

## 📊 Monitorar em Tempo Real

```bash
# Ver todos os logs
tail -f /tmp/mt5_server.log

# Ver apenas sinais gerados
grep 'SINAL GERADO' /tmp/mt5_server.log | tail -20

# Ver alertas Telegram
grep 'Telegram enviado' /tmp/mt5_server.log | tail -10

# Ver candles recebidos
grep 'Recebido:' /tmp/mt5_server.log | tail -20

# Status do servidor (JSON)
curl http://localhost:8765/mt5/status | jq .

# Teste de conexão
curl -X POST http://localhost:8765/mt5/candle \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "datetime": "2026-05-31T14:30:00",
    "open": 1.0850,
    "high": 1.0851,
    "low": 1.0849,
    "close": 1.0850,
    "volume": 1000
  }'
```

## 🎯 Configuração

### Mudar Pares Ativos

Editar `production/server_mt5_http.py`:

```python
OPTIMAL_THRESHOLDS = {
    'EURUSD': 0.85,   # ← Win Rate: 55.04%
    'GBPUSD': 0.70,   # ← Win Rate: 53.16%
    'EURAUD': 0.90,   # ← desativado
    'EURJPY': 0.50,   # ← desativado
}
```

### Mudar Thresholds

Cada par tem um threshold otimizado. Quanto maior o threshold, menos sinais:

- `threshold=0.50`: Mais sinais (risco maior)
- `threshold=0.85`: Menos sinais (conservador)

## 📈 Performance

Resultados no test set (30% dados não vistos):

| Par | Win Rate | Total Pips | Profit Factor |
|-----|----------|-----------|--------------|
| EURUSD | 55.04% | +537 | 1.21x |
| GBPUSD | 53.16% | +1,199 | 2.45x |
| EURAUD | 53.82% | -2,745 | - |
| EURJPY | 54.71% | +188,920 | - |
| NZDUSD | 52.89% | +597 | - |

## 🛑 Parar Sistema

```bash
# Parar servidor HTTP
pkill -9 -f server_mt5_http

# Parar MT5
pkill -9 -f "terminal64.exe"

# Ver processos rodando
ps aux | grep -E "server_mt5_http|terminal64.exe" | grep -v grep
```

## 🐛 Troubleshooting

### "Cannot connect to server"

```bash
# Verificar se servidor está rodando
ps aux | grep server_mt5_http | grep -v grep

# Ver erros
tail -50 /tmp/mt5_server.log

# Reiniciar
pkill -9 -f server_mt5_http
sleep 1
python3 production/server_mt5_http.py
```

### "Modelos não carregados"

```bash
# Verificar arquivo de dados
ls -lh /home/ubuntu/pessoal/options/data/EURUSD_M15*.txt

# Rebuild dos modelos
python3 src/backtest_classification_optimized.py
```

### MT5 não envia dados

1. Verificar que MT5 está rodando:
   ```bash
   pgrep -f "terminal64.exe"
   ```

2. Verificar EA está anexado ao gráfico EURUSD M15

3. Ver logs MT5:
   ```bash
   tail -f ~/.wine/drive_c/Program\ Files/MetaTrader\ 5/logs/*
   ```

### Telegram não funciona

1. Verificar credenciais em `.env`:
   ```bash
   grep TELEGRAM /home/ubuntu/pessoal/options/.env
   ```

2. Testar manualmente:
   ```bash
   curl -X POST https://api.telegram.org/botTOKEN/sendMessage \
     -d "chat_id=CHAT_ID&text=test"
   ```

## 📚 Referências

- **Server Source**: `production/server_mt5_http.py`
- **Model**: `src/backtest_classification_optimized.py`
- **Indicators**: `src/indicators.py`
- **EA Source**: `production/websocket/mt5_client.mq5`
- **Startup Script**: `bin/start_mt5_production.sh`
- **Test Client**: `production/test_client_http.py`

## 🎓 Fluxo Completo

1. **Setup** (primeira vez)
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   vi .env  # configurar Telegram
   ```

2. **Treinar modelo**
   ```bash
   python3 src/backtest_classification_optimized.py
   ```

3. **Iniciar sistema**
   ```bash
   bash bin/start_mt5_production.sh
   ```

4. **Iniciar MT5**
   ```bash
   DISPLAY=:99 wine ~/.wine/drive_c/Program\ Files/MetaTrader\ 5/terminal64.exe &
   ```

5. **Monitorar**
   ```bash
   tail -f /tmp/mt5_server.log
   ```

6. **Testar (sem MT5)**
   ```bash
   python3 production/test_client_http.py
   ```

---

**Status**: ✅ Production Ready  
**Last Update**: 2026-05-31  
**Maintainer**: Trading System
