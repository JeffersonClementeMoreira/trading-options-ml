# Quick Start - 5 Minutos para Começar

## ⚡ Setup Rápido

### Pré-requisitos
- Python 3.10+
- pip
- Conta Telegram
- (Opcional) MetaTrader 5

### 1️⃣ Clonar e Instalar (2 min)

```bash
git clone https://github.com/seu-usuario/trading-options-ml.git
cd trading-options-ml

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 2️⃣ Configurar Telegram (2 min)

```bash
# Copiar template
cp .env.example .env

# Editar .env
nano .env
```

Adicionar suas credenciais:
```env
TELEGRAM_TOKEN=sua_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id
```

**Como obter:**
- Token: Fale com @BotFather no Telegram → `/newbot`
- Chat ID: Ver [SETUP_TELEGRAM.md](../production/SETUP_TELEGRAM.md)

### 3️⃣ Iniciar Servidor (1 min)

```bash
# Terminal 1: Iniciar WebSocket server
cd production/websocket
python3 server.py

# Esperado:
# 🚀 WebSocket server iniciado em ws://0.0.0.0:5000
# 📁 Sinais carregados para 5 pares
# ✅ Servidor aguardando conexões MT5...
```

### 4️⃣ Testar Servidor (1 min)

```bash
# Terminal 2: Executar client de teste
cd production/websocket
python3 test_client.py

# Esperado:
# ✅ Conectado ao servidor
# 📊 Enviando dados de teste...
```

Se vir resposta com `signal: 1` e mensagem Telegram chegar → ✅ Funcionando!

### 5️⃣ Conectar MT5 (Opcional)

```
MetaTrader 5 → Novo EA → Copy mt5_client.mq5
Compilar (F5) → Attach ao gráfico EURUSD M15
```

## 🧪 Validar Tudo

### Checklist

- [ ] Servidor WebSocket rodando (`python3 server.py`)
- [ ] Test client envia dados
- [ ] Telegram recebe alertas
- [ ] Logs mostram "✅ Signal triggered"

### Ver Logs

```bash
# Em tempo real
tail -f production.log

# Com debug
LOG_LEVEL=DEBUG python3 production/websocket/server.py
```

## 📊 Arquivos de Resultado

Pré-gerados em `results/`:

- `backtest_EURUSD_CANDLE_A_CANDLE_TESTE.csv` - Histórico completo de sinais
- `PRODUCAO_1ORDEM_POR_DIA_EURUSD.csv` - Uma ordem por dia
- `backtest_resumo_TESTE_SOMENTE_30pct.csv` - Resumo por par

Usar esses arquivos para backtesting ou validação.

## 🔧 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| `Port 5000 already in use` | `lsof -i :5000` e `kill -9 <PID>` |
| Telegram não envia | Verificar `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID` em `.env` |
| `ModuleNotFoundError` | Executar `pip install -r requirements.txt` |
| Connection refused (MT5) | Aguardar 3s, servidor pode estar iniciando |

## 📖 Próximos Passos

1. **Ler arquitetura**: [ARCHITECTURE.md](../docs/ARCHITECTURE.md)
2. **Entender indicadores**: [INDICATORS.md](../docs/INDICATORS.md)
3. **Customizar thresholds**: Edit `config.json`
4. **Deploy em produção**: [DEPLOY.md](../docs/DEPLOY.md)

## 🚀 Já está pronto para usar!

Parabéns! Seu sistema ML de trading está rodando. Próxima ordem pode chegar a qualquer momento.

---

**Tempo total de setup:** ~5 minutos  
**Nível de dificuldade:** Iniciante  
**Suporte:** Ver [README.md](../README.md#suporte)
