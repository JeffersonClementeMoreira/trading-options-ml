# 🚀 WebSocket + Telegram Alert System

Sistema em tempo real que:
1. ✅ Recebe candles M15 do MT5
2. ✅ Monitora sinais pré-calculados (daily_signals_*.csv)
3. ✅ **Envia alerta Telegram** quando sinal é acionado
4. ✅ Pronto para entrada manual com **opções**

## 📊 Estrutura

```
websocket/
├── server.py           ← WebSocket server (Python) - recebe candles
├── mt5_client.mq5      ← EA para MT5 - envia candles
├── test_client.py      ← Script de teste
└── README.md           ← Este arquivo
```

## ⚙️ Setup

### 1️⃣ Instalar dependências

```bash
pip install websockets requests pandas
```

### 2️⃣ Configurar Telegram

#### A. Criar bot no Telegram

1. Abrir Telegram e procurar por **@BotFather**
2. Enviar: `/newbot`
3. Seguir passos e copiar o **token** (exemplo: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

#### B. Obter Chat ID

1. Procurar por **@userinfobot** no Telegram
2. Enviar qualquer mensagem
3. O bot retorna seu **Chat ID** (número grande)

#### C. Configurar variáveis de ambiente

```bash
# Linux/Mac - adicionar ao ~/.bashrc ou ~/.zshrc
export TELEGRAM_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="987654321"

# Ou Windows (PowerShell)
$env:TELEGRAM_TOKEN="seu_token_aqui"
$env:TELEGRAM_CHAT_ID="seu_chat_id_aqui"
```

### 3️⃣ Verificar sinais carregados

```bash
python3 production/websocket/test_client.py
```

Output esperado:
```
✅ EURUSD:
   Total signals: 218
   First signal: 2025-09-03 06:00:00
   Last signal: 2026-05-22 06:45:00

✅ GBPUSD:
   Total signals: 217
   First signal: 2025-09-03 10:15:00
   Last signal: 2026-05-22 01:00:00
```

## 🏃 Como Usar

### Passo 1: Iniciar WebSocket Server

```bash
# Terminal 1 - Servidor Python
python3 production/websocket/server.py
```

Esperado:
```
INFO:root:✅ Signal Monitor Initialized
INFO:root:🚀 WebSocket Server started on ws://0.0.0.0:8765
INFO:root:📊 Monitoring 2 pairs
INFO:root:⏰ Signals configured: EURUSD + GBPUSD
```

### Passo 2: Rodar Cliente de Teste (opcional)

```bash
# Terminal 2 - Teste com candles simulados
python3 production/websocket/test_client.py
```

Esperado:
```
📤 Test 1: Sending EURUSD candle...
📩 Response: Status: ok, Signal Found: True
   ✅ SIGNAL TRIGGERED!
   📲 Telegram alert sent!
```

### Passo 3: Conectar MT5 (quando pronto)

1. Copiar `mt5_client.mq5` para MT5
2. Compilar e rodar no gráfico
3. Cada candle M15 será enviado para o servidor

## 📱 Alerta Telegram

Quando sinal é acionado, recebe no Telegram:

```
🚀 TRADING SIGNAL ALERT

📊 EURUSD
⏰ 2025-09-03 06:00:00

📈 Direction: UP
📍 Confidence: 100%

💰 Entry Price: 1.16733
🎯 Target Price: 1.17101
📌 Pips to Target: 368 pips

⚠️ Action: Prepare options entry
✅ Ready to enter with UP binary option
```

## 🔧 Configuração Avançada

### Alterar tolerância de tempo

No arquivo `production/websocket/server.py`, linha ~180:

```python
if time_diff <= 30:  # Mudar 30 para seu valor (minutos)
```

### Alterar porta do servidor

No arquivo `production/websocket/server.py`, linha ~280:

```python
server = WebSocketServer(host='0.0.0.0', port=8765)  # Mudar 8765
```

### Desabilitar alertas Telegram (teste sem bot)

No teste, remova as variáveis de ambiente:

```bash
unset TELEGRAM_TOKEN
unset TELEGRAM_CHAT_ID
# Ou simplesmente não defina
```

## 📊 Fluxo de Dados

```
MT5 (M15 Candle)
    ↓
    │ WebSocket
    ↓
Python Server
    ├─ Verifica data/hora do sinal
    ├─ Calcula direção (UP/DOWN)
    └─ Envia para Telegram
         ↓
    Trader recebe alerta
         ↓
    Abre posição manual (opções)
         ↓
    MT5 continua monitorando até target
```

## ⚠️ Importante

### 1. Um sinal por dia

O sistema garante **máximo 1 alerta por dia por par**:
- Se houver múltiplos candles no horário do sinal, apenas o primeiro dispara o alerta
- Próximo alerta só será enviado no próximo dia

### 2. Tolerância de tempo

- ✅ Alerta dispara: ±30 minutos do horário programado
- ❌ Fora desse intervalo: sem alerta

### 3. Timezone

- Todos os horários em **UTC**
- MT5 usa UTC por padrão
- Verificar se seu Telegram está na mesma zona horária para referência

## 🐛 Troubleshooting

### "Connection refused"

```
❌ ERROR: Could not connect to WebSocket server
```

**Solução:**
1. Verificar se servidor está rodando
2. Verificar porta (padrão 8765)
3. Testar: `netstat -an | grep 8765`

### "Telegram not configured"

```
⚠️ Telegram not configured
```

**Solução:**
1. Obter token em @BotFather
2. Obter chat ID em @userinfobot
3. Exportar variáveis de ambiente:
   ```bash
   export TELEGRAM_TOKEN="seu_token"
   export TELEGRAM_CHAT_ID="seu_id"
   ```

### Não recebe candle do MT5

**Solução:**
1. Verificar se EA está compilado (sem erros)
2. Verificar server address em MT5_CLIENT (localhost vs 127.0.0.1)
3. Testar com test_client.py primeiro

## 📝 Exemplos de Uso

### Exemplo 1: Teste Local

```bash
# Terminal 1
python3 production/websocket/server.py

# Terminal 2 (outro terminal)
python3 production/websocket/test_client.py
```

### Exemplo 2: Com MT5 Real

1. Colocar `mt5_client.mq5` em `MQL5/Experts/`
2. Compilar em MetaEditor (F7)
3. Rodar no gráfico (agregar com Enter)
4. Servidor receberá candles automaticamente cada 15 min

### Exemplo 3: Monitorar Logs

```bash
# Ver logs em tempo real
tail -f production.log

# Ou mais detalhado
python3 production/websocket/server.py 2>&1 | tee server.log
```

## 🎯 Próximos Passos

- [ ] Configurar Telegram
- [ ] Testar WebSocket com test_client.py
- [ ] Compilar EA do MT5
- [ ] Começar a receber alertas
- [ ] Monitorar por 1 semana
- [ ] Otimizar confiança/cobertura se necessário

## 📞 Suporte

Dúvidas? Verificar:
1. Sinais carregados: `test_client.py`
2. Logs do servidor: stdout
3. Configuração Telegram: @BotFather + @userinfobot
4. Conexão MT5: netstat/telnet

---

**Status:** ✅ Pronto para Produção  
**Última atualização:** Maio 2026  
**Versão:** 1.0
