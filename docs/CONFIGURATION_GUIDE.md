# 📊 GUIA COMPLETO - CONFIGURAÇÃO E MONITORAMENTO

## 🎯 Parte 1: Escolher Quais Pares Usar

### Localização: `production/websocket/server.py`

**3 lugares para editar (SEMPRE MUDAR JUNTO):**

#### 1️⃣ Linha ~68 - Track de alertas enviados
```python
self.sent_today = {
    'EURUSD': False,   # ← Mudar aqui
    'GBPUSD': False,
    # 'NZDUSD': False,  # ← Descomentar para adicionar
    # 'EURJPY': False,
}
```

#### 2️⃣ Linha ~78 - Carregar sinais do CSV
```python
for pair in ['EURUSD', 'GBPUSD']:  # ← Mudar aqui
    csv_file = self.signals_dir / f'daily_signals_{pair}.csv'
```

#### 3️⃣ Linha ~311 - Log de confirmação
```python
logger.info(f"⏰ Signals configured: EURUSD + GBPUSD")  # ← Mudar aqui
```

### Exemplos de Configuração

**Opção A: Começar simples (EURUSD apenas)**
```python
# Linha 68
self.sent_today = {
    'EURUSD': False,
}

# Linha 78
for pair in ['EURUSD']:

# Linha 311
logger.info(f"⏰ Signals configured: EURUSD ONLY")
```

**Opção B: Recomendado (EURUSD + GBPUSD)**
```python
# Já vem assim por padrão
# Mantém como está se quiser
```

**Opção C: Agressivo (Todos os 4 pares)**
```python
# Linha 68
self.sent_today = {
    'EURUSD': False,
    'GBPUSD': False,
    'NZDUSD': False,
    'EURJPY': False,
}

# Linha 78
for pair in ['EURUSD', 'GBPUSD', 'NZDUSD', 'EURJPY']:

# Linha 311
logger.info(f"⏰ Signals configured: EURUSD + GBPUSD + NZDUSD + EURJPY")
```

---

## 🌐 Parte 2: Configuração MetaTrader 5

### Com Expert Advisor (Recomendado)

**Passo 1: Copiar código do EA**
```
Arquivo: production/websocket/mt5_client.mq5
```

**Passo 2: Compilar no MT5**
- Abrir: MetaTrader 5 → File → New → Expert Advisor
- Copiar/colar todo conteúdo de `mt5_client.mq5`
- F5 ou F7 para compilar
- Salvar como: `TradingOptionsML`

**Passo 3: Attach ao chart**
- Abrir gráfico: **EURUSD M15** (ou qual par estiver usando)
- Drag & drop o EA no chart
- Popup aparecerá:
  - ✅ Allow automated trading
  - ✅ Allow WebSocket
  - Click OK

**Passo 4: Verificar funcionamento**
- Ir à aba: **Experts** (ou Logs)
- Deve aparecer: 
  ```
  WebSocket connecting...
  Connected to ws://localhost:5000
  Ready for signals
  ```

### Sem MetaTrader (Apenas servidor Python)

Se não quiser usar EA, pode apenas rodar o servidor e testar com `test_client.py`:

```bash
# Terminal 1
cd production/websocket
python3 server.py

# Terminal 2
cd production/websocket
python3 test_client.py
```

---

## 📡 Parte 3: Confirmar Recebimento de Sinais

### Método 1: Ver Logs em Tempo Real

**Terminal:**
```bash
tail -f production.log
```

**Saída esperada:**
```
2026-05-31 10:00:00 - INFO - 🚀 WebSocket server iniciado em ws://0.0.0.0:5000
2026-05-31 10:00:00 - INFO - 📁 Sinais carregados para 2 pares
2026-05-31 10:00:00 - INFO - ✅ Loaded 224 signals for EURUSD
2026-05-31 10:00:00 - INFO - ✅ Loaded 224 signals for GBPUSD
2026-05-31 10:00:00 - INFO - ⏰ Signals configured: EURUSD + GBPUSD
2026-05-31 10:00:00 - INFO - ✅ Server aguardando conexões...
2026-05-31 10:15:00 - INFO - 🔌 Cliente conectado
2026-05-31 10:15:15 - INFO - 📊 Recebido candle M15: EURUSD
2026-05-31 10:15:15 - INFO - 🎯 Signal=0 (nenhum sinal programado)
2026-05-31 10:30:00 - INFO - 📊 Recebido candle M15: GBPUSD
2026-05-31 10:30:00 - INFO - 🎯 Signal=1 (SINAL ENCONTRADO!)
2026-05-31 10:30:00 - INFO - 💬 Telegram enviado com sucesso
```

### Método 2: Debug Verboso (Informações detalhadas)

**Terminal:**
```bash
LOG_LEVEL=DEBUG python3 production/websocket/server.py
```

**Saída (muito mais detalhe):**
```
DEBUG: Conectando ao arquivo signals...
DEBUG: Verificando linha 2026-05-31 em GBPUSD...
DEBUG: Encontrada signal em linha 45
DEBUG: Entry: 1.12345
DEBUG: Target: 1.12500
DEBUG: Confidence: 0.67
DEBUG: Enviando para Telegram...
DEBUG: Response Telegram: 200 OK
```

### Método 3: Testar com Client

**Terminal 1 (servidor):**
```bash
cd production/websocket
python3 server.py
```

**Terminal 2 (teste):**
```bash
cd production/websocket
python3 test_client.py
```

**Saída esperada:**
```
✅ Conectado ao servidor WebSocket
📊 Enviando EURUSD...
🎯 Response: signal=0
📊 Enviando GBPUSD...
🎯 Response: signal=1, entry=1.12345, target=1.12500
💬 Telegram enviado!
✅ Teste concluído
```

---

## 🧠 Parte 4: Como o Modelo Avalia os Sinais

### Fluxo Técnico

```
MT5 EA (ou test_client.py)
    │
    ├─ Envia JSON com OHLC M15
    │  {
    │    "pair": "GBPUSD",
    │    "timestamp": "2026-05-31 10:30:00",
    │    "ohlc": {"open": 1.12300, "high": 1.12400, ...}
    │  }
    │
    ▼
WebSocket Server recebe
    │
    ├─ Parse timestamp e par
    │
    ├─ Log: "📊 Recebido candle M15: GBPUSD"
    │
    ├─ check_signal_for_today("GBPUSD", timestamp)
    │   │
    │   ├─ Abre arquivo: production/PRODUCAO_1ORDEM_POR_DIA_GBPUSD.csv
    │   │
    │   ├─ Procura linha com Data = "2026-05-31"
    │   │
    │   ├─ SE ENCONTRA:
    │   │   ├─ Log: "🎯 Signal=1 ENCONTRADO"
    │   │   ├─ Busca: entry_price, target_price, confidence
    │   │   ├─ Chama send_telegram_alert()
    │   │   └─ Return {signal: 1, entry: ..., target: ...}
    │   │
    │   └─ SE NÃO ENCONTRA:
    │       ├─ Log: "🎯 Signal=0 (já teve sinal ou nenhum)"
    │       └─ Return {signal: 0}
    │
    └─ Envia response de volta ao MT5
       {
         "signal": 1 ou 0,
         "entry_price": 1.12345,
         "target_price": 1.12500,
         "direction": "BUY",
         "confidence": 0.67
       }
```

### Arquivo de Sinais (CSV)

**Exemplo: production/PRODUCAO_1ORDEM_POR_DIA_GBPUSD.csv**

```
Data_Operacao,Timestamp_Completo,Horario_Abertura,...,Preco_Entrada,Preco_Alvo,Confianca_%,Pips_Esperado
2026-05-31,2026-05-31 00:00:00,00:00:00,...,1.12300,1.12500,67,20.0
2026-06-01,2026-06-01 00:15:00,00:15:00,...,1.12400,1.12600,71,20.0
```

Quando servidor recebe candle GBPUSD em 31/05/2026:
- Procura por Data = "2026-05-31" ✅ ENCONTRA
- Envia signal=1
- Telegram recebe alert

Quando recebe candle GBPUSD em 01/06/2026:
- Se já enviou alert hoje → Ignora (1 por dia)
- Se ainda não enviou → Envia novo alert

---

## ✅ Checklist de Operação

### Antes de Iniciar

- [ ] Editar `production/websocket/server.py` com os pares desejados
- [ ] Verificar `production/PRODUCAO_1ORDEM_POR_DIA_*.csv` existem
- [ ] Editar `.env` com TELEGRAM_TOKEN e TELEGRAM_CHAT_ID
- [ ] Testar Telegram com `test_client.py`

### Durante Operação

- [ ] Servidor rodando: `python3 production/websocket/server.py`
- [ ] Logs mostram "✅ Loaded X signals for PAIR"
- [ ] Logs mostram "⏰ Signals configured: PAIR1 + PAIR2"
- [ ] MT5 EA compilado e attachado ao chart (ou test_client rodando)
- [ ] A cada 15min deve aparecer "📊 Recebido candle" nos logs

### Se Houver Sinal

- [ ] Logs mostram "🎯 Signal=1 ENCONTRADO"
- [ ] Logs mostram "💬 Telegram enviado"
- [ ] Telegram recebe mensagem com detalhes do sinal
- [ ] MT5 EA recebe response com signal=1
- [ ] (Opcional) MT5 EA abre ordem ou apenas log

### Troubleshooting

| Problema | Solução |
|----------|---------|
| Port 5000 em uso | `lsof -i :5000 \| grep LISTEN \| awk '{print $2}' \| xargs kill -9` |
| Não recebe candles | Verificar MT5 EA compilado e attachado corretamente |
| Signal sempre 0 | Verificar data do candle bate com CSV (timezone UTC!) |
| Telegram não envia | Verificar TELEGRAM_TOKEN e TELEGRAM_CHAT_ID em .env |
| Erro "ModuleNotFoundError" | `pip install -r requirements.txt` |

---

## 🎯 Resumo Final

1. **Escolher pares**: Editar 3 linhas em `server.py`
2. **Rodar servidor**: `python3 production/websocket/server.py`
3. **Attach MT5 ou testar**: EA no chart ou `test_client.py`
4. **Monitorar**: `tail -f production.log`
5. **Confirmar sinais**: Ver "Signal=1" e "Telegram enviado"

Tudo pronto! 🚀
