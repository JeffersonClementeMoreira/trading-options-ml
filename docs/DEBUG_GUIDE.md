# 🔍 GUIA DE DEBUG - Monitor WebSocket

## ✅ Sistema Iniciado

Seu sistema está **100% operacional** em modo **DEBUG**.

### Status Atual
- ✅ Servidor Bridge (DEMO): **ATIVO** (PID 512930)
- ✅ Monitor WebSocket (Debug): **ATIVO** (PID 573732)
- ✅ Telegram Bot: **PRONTO**
- ✅ WebSocket Porta 9001: **ABERTA**

---

## 📊 O Que Está Acontecendo

### Fluxo de Dados
```
Servidor Bridge (a cada 10 seg)
   ├─ Lê novos candles M15
   ├─ Calcula 25+ indicadores
   ├─ Avalia XGBoost (score 0-1)
   └─ Envia JSON via WebSocket

Monitor Debug (a cada novo candle)
   ├─ Recebe JSON com todos os dados
   ├─ Formata mensagem simples
   └─ ENVIA AO TELEGRAM (TODOS os candles)
```

### Que Mensagens São Enviadas

**Formato:**
```
📡 MONITOR WEBSOCKET EM ANDAMENTO

📡 Conectado ao Bridge MT5
├─ URL: ws://localhost:9001
├─ Par: GBPUSD
├─ Timeframe: M15
├─ DateTime: 2026/05/26 17:00
├─ Close: 1.31568
└─ Status: 🟢 ONLINE

📊 Indicadores Resultado:
├─ RSI(14): 65.2
├─ MACD: +0.0042
├─ EMA-12: 1.2498
├─ SMA-20: 1.2500
├─ ATR%: 0.25
├─ Stoch-K: 78.5
├─ Confluence: 2/4
└─ XGBoost Score + Signal = 🟢 HIGH (>70%)

🎯 Ação:
└─ POSICIONAR ORDEM

🔔 Aguardando próximo candle...
```

---

## 🔧 Comandos para Monitorar

### 1️⃣ Ver Status Completo
```bash
# Comando principal de diagnóstico
cd /home/ubuntu/pessoal/options/src && ./diagnostic.sh

# OU manualmente:
ps aux | grep -E 'mt5_websocket|live_websocket_monitor_debug' | grep -v grep
```

**O que procurar:**
- ✅ 2 processos Python rodando (Servidor + Monitor)
- ✅ CPU baixo (< 5%)
- ✅ RAM baixo (< 1%)

### 2️⃣ Ver Atividade em Tempo Real

Se quiser ver mensagens sendo enviadas:
```bash
# Ver saída do monitor enquanto roda
ps aux | grep -E 'mt5_websocket|live_websocket' | grep -v grep
```

**Cada 10 segundos você verá algo como:**
```
📨 [GBPUSD] Novo candle detectado
   Hora: 2026-05-26 17:15:00
✅ 17:15:02 - Mensagem enviada ao Telegram
```

### 3️⃣ Verificar Telegram

**Abra seu Telegram** → Canal `-1001735082183`

Você deve ver:
1. Mensagem inicial: "🚀 MONITOR DEBUG INICIADO"
2. Depois a cada novo candle M15: mensagem com OHLC + indicadores + XGBoost score

---

## 🎯 Validação - Como Saber que Está Funcionando

### ✅ Checklist de Funcionamento

- [ ] **Processos rodando?**
  ```bash
  ps aux | grep -E 'mt5_websocket|live_websocket' | grep -v grep
  ```
  Deve mostrar 2 processos Python

- [ ] **Porta aberta?**
  ```bash
  netstat -ln | grep 9001
  ```
  Deve mostrar: `127.0.0.1:9001 LISTEN`

- [ ] **Servidor respondendo?**
  ```bash
  cd /home/ubuntu/pessoal/options/src && ./diagnostic.sh
  ```
  Deve mostrar: `✅ Servidor respondendo`

- [ ] **Telegram recebendo?**
  - Abra seu Telegram
  - Vá para canal `-1001735082183`
  - Procure por mensagens recentes
  - Devem estar chegando a cada M15

---

## 🐛 Troubleshooting

### Problema: Não Recebendo Mensagens no Telegram

**Solução 1: Verificar se os processos estão rodando**
```bash
ps aux | grep -E 'mt5_websocket|live_websocket_monitor_debug' | grep -v grep
```

Se não aparecer, reiniciar:
```bash
cd /home/ubuntu/pessoal/options/src
python3 mt5_websocket_server_demo.py &
sleep 2
python3 live_websocket_monitor_debug.py &
```

**Solução 2: Verificar conectividade**
```bash
cd /home/ubuntu/pessoal/options/src && ./diagnostic.sh
```

Procure por:
- ✅ Servidor Bridge: ATIVO
- ✅ Monitor Debug: ATIVO
- ✅ Porta WebSocket 9001: ABERTA
- ✅ Servidor respondendo

**Solução 3: Verificar Token do Telegram**

Se as mensagens não chegam, pode ser token errado:
```bash
grep "BOT_TOKEN\|CHAT_ID" /home/ubuntu/pessoal/options/src/live_websocket_monitor_debug.py
```

### Problema: Servidor Usando Porta

```bash
# Forçar limpeza
pkill -9 -f "mt5_websocket_server_demo"
lsof -i :9001 | grep -v COMMAND | awk '{print $2}' | xargs kill -9

# Reiniciar
cd /home/ubuntu/pessoal/options/src
python3 mt5_websocket_server_demo.py &
```

---

## 📈 Estatísticas do Sistema

### Modo DEMO vs Produção

**Atualmente (DEMO):**
- ✅ Dados: Históricos (do backtesting)
- ✅ Candles simulados a cada 10 segundos
- ✅ 100% funcional
- ✅ Perfeito para teste

**Quando MT5 Real:**
- 🔄 Dados: Tempo real da corretora
- 🔄 Candles: Reais (M15 = 15 minutos)
- 🔄 Mesmo sistema, apenas fonte diferente

---

## 🚀 Duração do Teste

- **Modo:** DEBUG (enviando todos os candles)
- **Duração:** 1-2 semanas
- **Objetivo:** Validar funcionamento antes de ligar auto-operações

---

## 📋 Resumo de Arquivos

| Arquivo | Função |
|---------|--------|
| `mt5_websocket_server_demo.py` | Servidor Bridge (calcula indicadores) |
| `live_websocket_monitor_debug.py` | Monitor em DEBUG (envia todos os candles) |
| `diagnostic.sh` | Comando de diagnóstico rápido |
| `live_websocket_monitor.py` | Monitor normal (só sinais > 70%) |

---

## 🎮 Controle Rápido

```bash
# Ver status
./diagnostic.sh

# Parar sistema
pkill -9 -f 'mt5_websocket_server_demo|live_websocket_monitor_debug'

# Reiniciar
cd /home/ubuntu/pessoal/options/src
python3 mt5_websocket_server_demo.py & && sleep 2 && python3 live_websocket_monitor_debug.py &

# Ver processos
ps aux | grep -E 'mt5_websocket|live_websocket' | grep -v grep
```

---

## 📞 Para Voltar ao Modo Normal

Quando quiser parar de enviar todos os candles e voltar a enviar apenas sinais FORTES (score > 70%):

```bash
# 1. Parar o monitor debug
pkill -9 -f "live_websocket_monitor_debug"

# 2. Iniciar o monitor normal
cd /home/ubuntu/pessoal/options/src
python3 live_websocket_monitor.py &
```

---

**Status:** 🟢 ATIVO E TESTANDO  
**Última Atualização:** 2026-05-26 17:09:00  
**Modo:** 🔍 DEBUG (Todos os candles)
