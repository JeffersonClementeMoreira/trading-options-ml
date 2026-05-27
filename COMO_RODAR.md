╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                  🚀 COMO RODAR O SISTEMA - GUIA PRÁTICO                  ║
║                                                                            ║
║              Receber dados reais do MT5 e enviar alertas                  ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝


## ⚡ INICIAR RÁPIDO

```bash
bash /home/ubuntu/pessoal/options/bin/start_system.sh
```

Pronto! Sistema está rodando e aguardando dados do MT5.


## 📊 O QUE O SISTEMA FAZ

1. **server_mt5_http.py** (porta 8765)
   - Recebe HTTP POST do MT5 via SendCandlesToServer.mq5
   - Calcula 25+ indicadores técnicos
   - Broadcast via WebSocket para monitor

2. **monitor_mt5_real.py** (porta 9001)
   - Conecta ao WebSocket do servidor
   - Carrega modelos XGBoost
   - Faz predições (score 0-100%)
   - Envia alertas Telegram com dados reais


## 🔄 DEIXAR RODANDO 24/7

### Opção 1: Screen (recomendado)

```bash
# Iniciar em um screen
screen -S mt5system bash /home/ubuntu/pessoal/options/bin/start_system.sh

# Para sair (deixa rodando):
# Ctrl+A depois D

# Para voltar:
screen -r mt5system

# Para matar:
screen -X -S mt5system quit
```

### Opção 2: Nohup (simples)

```bash
# Rodar em background e desconectar sem matar
nohup bash /home/ubuntu/pessoal/options/bin/start_system.sh > /tmp/mt5_startup.log 2>&1 &

# Ver PID
ps aux | grep start_system

# Matar depois se necessário
kill -9 <PID>
```

### Opção 3: Systemd (profissional)

Criar arquivo `/etc/systemd/system/mt5-realtime.service`:

```ini
[Unit]
Description=MT5 Real-time Trading System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/pessoal/options
ExecStart=/bin/bash /home/ubuntu/pessoal/options/bin/start_system.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Depois:
```bash
sudo systemctl daemon-reload
sudo systemctl start mt5-realtime
sudo systemctl enable mt5-realtime  # Inicia no boot

# Ver status
sudo systemctl status mt5-realtime

# Ver logs
sudo journalctl -u mt5-realtime -f
```


## 📝 MONITORAR SISTEMA

### Ver candles chegando em tempo real

```bash
tail -f /tmp/server_real.log | grep "NOVO CANDLE"
```

Esperado:
```
✅ NOVO CANDLE! XAUUSD | 2026-05-27T02:15:00
   Close: 4511.25
   RSI: 52.3
   SMA_20: 4508.75
✅ NOVO CANDLE! EURUSD | 2026-05-27T02:15:00
   Close: 1.0851
```

### Ver logs completos do servidor

```bash
tail -f /tmp/server_real.log
```

### Ver logs do monitor (Telegram)

```bash
tail -f /tmp/monitor_real.log
```

### Ver status dos processos

```bash
ps aux | grep -E "server_mt5_http|monitor_mt5_real" | grep -v grep
```


## 🆕 ADICIONAR NOVOS PARES

### 1. Modificar SendCandlesToServer.mq5

Abra o arquivo `/home/ubuntu/pessoal/options/SendCandlesToServer.mq5`

Procure por esta seção (linhas ~90-95):

```mql5
// ═════════════════════════════════════════════════════════════════════════════
// PARES MONITORADOS
// ═════════════════════════════════════════════════════════════════════════════

string symbols_mt5[] = {"XAUUSD", "EURUSD", "GBPUSD"};      // ← EDITAR AQUI
string symbols_api[] = {"XAUUSD", "EURUSD", "GBPUSD"};
```

**Para adicionar novo par (ex: USDJPY):**

```mql5
string symbols_mt5[] = {"XAUUSD", "EURUSD", "GBPUSD", "USDJPY"};
string symbols_api[] = {"XAUUSD", "EURUSD", "GBPUSD", "USDJPY"};
```

Depois compilar e reanexar no MT5.

### 2. Criar modelo XGBoost para novo par

Você precisa treinar um modelo XGBoost para o novo par.

O servidor espera por:
```
/home/ubuntu/pessoal/options/src/xgboost_USDJPY.pkl
```

**Se o arquivo não existir:**
- Monitor vai exibir erro: `❌ ERRO CRÍTICO: Modelo XGBoost para USDJPY não disponível!`
- Telegram NÃO vai receber alertas para esse par
- Sistema continua com os outros pares normalmente

**Para usar o novo par sem modelo:**

Modifique `/home/ubuntu/pessoal/options/src/monitor_mt5_real.py`:

Procure por (linhas ~70-80):

```python
# Pares monitorados
self.models = {
    'GBPUSD': None,
    'EURUSD': None,
    'XAUUSD': None,
}
```

Adicione:
```python
self.models = {
    'GBPUSD': None,
    'EURUSD': None,
    'XAUUSD': None,
    'USDJPY': None,
}

self.last_datetime = {
    'GBPUSD': None,
    'EURUSD': None,
    'XAUUSD': None,
    'USDJPY': None,
}
```

Depois reinicie o sistema:
```bash
bash /home/ubuntu/pessoal/options/bin/start_system.sh
```


## 📊 ESTRUTURA FINAL

```
/home/ubuntu/pessoal/options/
│
├── 🚀 RODAR
│   └── bin/start_system.sh          ← Este arquivo!
│
├── 💾 MQL5
│   └── SendCandlesToServer.mq5      ← Editar para novos pares
│
├── 🐍 SISTEMA
│   └── src/
│       ├── server_mt5_http.py        (porta 8765)
│       ├── monitor_mt5_real.py       (porta 9001) ← Editar para novos pares
│       ├── analyze_deep_real.py
│       └── dashboard_real.py
│
└── 📚 DOCUMENTAÇÃO
    ├── README.md
    ├── COMO_RODAR.md                 ← Este arquivo
    ├── PROXIMOS_PASSOS.md
    └── ...
```


## 🧪 TESTAR ANTES DE DEIXAR RODANDO

### 1. Compilar MQL5

No MetaEditor (MT5):
- File → Open SendCandlesToServer.mq5
- Compile (F7)
- Esperado: 0 errors, 0 warnings

### 2. Anexar no MT5

No MT5:
- Gráfico XAUUSD M15
- Expert Advisors (Ctrl+E)
- Drag SendCandlesToServer.mq5

### 3. Iniciar sistema

```bash
bash /home/ubuntu/pessoal/options/bin/start_system.sh
```

### 4. Aguardar primeiro candle

```bash
tail -f /tmp/server_real.log | grep "NOVO CANDLE"
```

Quando chegar um candle M15 novo:
```
✅ NOVO CANDLE! XAUUSD | 2026-05-27T02:15:00
   Close: 4511.25
```

### 5. Verificar Telegram

Você deve receber uma mensagem no grupo "MT5 Real-time Alerts":
```
🚨 XAUUSD | M15 | 02:15:00
Close: 4511.25
XGBoost Score: 78%
✅ POSICIONAR
```


## ⚠️ TROUBLESHOOTING

### Sem dados chegando

```bash
# 1. Verificar se MQL5 está anexado
#    → Veja em MT5: Expert Advisors (Ctrl+E)
#    → Deve ter ícone 🤖 na barra de ferramentas

# 2. Verificar se servidor está rodando
ps aux | grep -E "server_mt5_http|monitor_mt5_real" | grep -v grep

# 3. Reiniciar
bash /home/ubuntu/pessoal/options/bin/start_system.sh

# 4. Ver erros no MT5
#    → Veja aba "Experts" em MT5 para mensagens de erro
#    → Confirme que WebRequests está habilitado (Tools → Options → Expert Advisors)
```

### Telegram não recebe

```bash
# 1. Ver logs do monitor
tail -f /tmp/monitor_real.log

# 2. Verificar token e chat_id em monitor_mt5_real.py
#    Procure por TELEGRAM_TOKEN e TELEGRAM_CHAT

# 3. Reiniciar
bash /home/ubuntu/pessoal/options/bin/start_system.sh
```

### Porta já está em uso

```bash
# Ver o que está usando porta 8765 ou 9001
lsof -i :8765
lsof -i :9001

# Matar processos antigos
pkill -9 -f "server_mt5_http"
pkill -9 -f "monitor_mt5_real"

# Reiniciar
bash /home/ubuntu/pessoal/options/bin/start_system.sh
```


## 🎯 RESUMO RÁPIDO

| Ação | Comando |
|------|---------|
| **Iniciar** | `bash /home/ubuntu/pessoal/options/bin/start_system.sh` |
| **Deixar rodando** | `screen -S mt5 bash /home/ubuntu/pessoal/options/bin/start_system.sh` |
| **Monitorar** | `tail -f /tmp/server_real.log` |
| **Ver novos pares** | Editar `/home/ubuntu/pessoal/options/SendCandlesToServer.mq5` |
| **Parar** | `pkill -9 -f "server_mt5_http\|monitor_mt5_real"` |


## 📌 PONTOS IMPORTANTES

✅ **Após compilar MQL5, reanexar no MT5** (não é automático)

✅ **Sistema aguarda por 15 minutos** (próximo candle M15)

✅ **Se adicionar par novo, criar modelo XGBoost** (ou vai mostrar erro)

✅ **Manter Linux rodando 24/7** (ou sistema para quando reboot)

✅ **Backup de modelos XGBoost** em `/home/ubuntu/pessoal/options/src/xgboost_*.pkl`


## 🚀 PRÓXIMO PASSO

```bash
bash /home/ubuntu/pessoal/options/bin/start_system.sh
```

Sistema está pronto! 🎉
