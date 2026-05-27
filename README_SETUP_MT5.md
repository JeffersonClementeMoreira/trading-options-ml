# 🚀 Integração MT5 Real com Sistema de Sinais

## Fluxo de Dados

```
MT5 (Wine Linux)
  ↓
Script MQL5 SendCandlesToServer.mq5
  ↓ (HTTP POST)
Servidor Python: server_mt5_http.py (HTTP port 8765)
  ↓ (Calcula indicadores + rastreia datetime)
WebSocket broadcast (ws://localhost:9001)
  ↓ (Novo candle detectado)
Monitor: monitor_mt5_real.py
  ↓ (XGBoost + Telegram)
📱 Telegram (seus sinais!)
```

---

## 📋 Setup

### 1️⃣ **Copiar script MQL5 para MT5**

```bash
# Arquivo está em:
/home/ubuntu/pessoal/options/SendCandlesToServer.mq5

# Copiar para diretório MT5:
cp SendCandlesToServer.mq5 ~/mt5/drive_c/Program\ Files/MetaTrader\ 5/MQL5/Scripts/

# OU manualmente:
# - Abrir MetaEditor (F11 no MT5)
# - Copiar código de SendCandlesToServer.mq5
# - Novo arquivo > Scripts
# - Colar código
# - Salvar como "SendCandlesToServer.mq5"
# - Compilar (F5)
```

### 2️⃣ **Configurar MT5 para aceitar WebRequest**

No MT5:
- **Tools → Options → Expert Advisors**
- ✅ Ativar "Allow WebRequest for listed URLs"
- ✅ Adicionar: `http://127.0.0.1:8765`

### 3️⃣ **Executar Script no MT5**

No MT5:
- Navview → Scripts
- Clicar com direito em "SendCandlesToServer"
- Clique em "Attach to chart"
- Escolher qualquer par/timeframe
- ✅ Script começa a enviar dados

**Verificar se está enviando:**
```bash
# No Linux, você verá:
# ✅ GBPUSD enviado: 2026-05-26T19:15:00 Close: 1.27580
# ✅ EURUSD enviado: 2026-05-26T19:15:00 Close: 1.08520
# ✅ XAUUSD enviado: 2026-05-26T19:15:00 Close: 2400.50
```

---

## 🔧 Rodar Sistema

### Terminal 1: Servidor HTTP (recebe dados MT5)
```bash
cd /home/ubuntu/pessoal/options/src
python3 server_mt5_http.py
```

Esperado:
```
🌐 HTTP servidor em http://localhost:8765/mt5/candle
🚀 WebSocket servidor em ws://localhost:9001
✅ NOVO CANDLE! GBPUSD | 2026-05-26T19:15:00
   Close: 1.27580
```

### Terminal 2: Monitor (envia Telegram)
```bash
cd /home/ubuntu/pessoal/options/src
python3 monitor_mt5_real.py
```

Esperado:
```
🔗 Conectando a ws://localhost:9001...
✅ Conectado!
⏳ Aguardando novos candles...

🔔 NOVO CANDLE DETECTADO! GBPUSD | 2026-05-26T19:15:00
   Tipo: Alta | Close: 1.25870
✅ Mensagem #1 ENVIADA
```

---

## ✅ Validação

### Verificar que está funcionando:

```bash
# Terminal 3: Ver logs do servidor HTTP
tail -f /tmp/server_mt5_http.log

# Ver processos rodando
ps aux | grep -E 'server_mt5_http|monitor_mt5_real'

# Ver último candle recebido
curl -s http://localhost:8765/mt5/candle | jq . 2>/dev/null || echo "Sem dados"
```

### Telegram
- Verificar chat: `-1001735082183`
- Mensagens devem chegar com:
  - ✅ DateTime correto (19:15, 19:30, 19:45...)
  - ✅ OHLC do candle
  - ✅ Indicadores
  - ✅ Score XGBoost
  - ✅ Ação (POSICIONAR/OBSERVAR/AGUARDAR)

---

## 🐛 Troubleshooting

### "HTTP 400" no MT5
- Verificar JSON do script MQL5
- Confirmar porta 8765 aberta
- Verificar WebRequest habilitado no MT5

### "Sem dados" na API
- MT5 não está enviando?
- Verificar que script está attachado ao chart
- Confirmar que tem histórico de candles (50+ M15)

### Telegram não recebe
- Verificar token: `6024515460:AAFGPwqNStgL0mv3VfxCQ_ZyQS3CtdzOeF0`
- Verificar chat ID: `-1001735082183`
- Verificar conexão de internet

### Monitor desconectando
- Checar se servidor HTTP está rodando
- Checar porta 9001 disponível: `lsof -i :9001`

---

## 📊 Logs

```bash
# Ver logs em tempo real
tail -f ~/pessoal/options/logs/server.log
tail -f ~/pessoal/options/logs/monitor.log

# Ver últimas mensagens enviadas
tail -50 ~/pessoal/options/logs/telegram.log
```

---

## 🎯 Próximos Passos

1. ✅ Copiar script MQL5
2. ✅ Rodar servidor HTTP
3. ✅ Rodar monitor
4. ✅ Verificar Telegram
5. 🔄 Deixar rodando 1-2 semanas para testes
6. 📊 Validar sinais com MT5 real

---

## 📝 Dúvidas

**P: Quanto de histórico precisa?**
A: 100 candles M15 (25 horas) mínimo. Script envia apenas o últimocandle.

**P: Pode enviar múltiplos pares?**
A: Sim! Configurar em `SendCandlesToServer.mq5` linha: `input string Symbols = "GBPUSD,EURUSD,XAUUSD";`

**P: O que se break?**
A: Monitor reconecta automaticamente a cada 5 segundos.

**P: Usar em produção?**
A: Sim, mas testar 1-2 semanas primeiro para validar sinais.
