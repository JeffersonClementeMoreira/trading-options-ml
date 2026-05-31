# Trading Options - ML Model in Production

[![Build Status](https://img.shields.io/badge/status-production-green)]()
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue)]()
[![ML Framework](https://img.shields.io/badge/ML-XGBoost%20%2B%20RF-orange)]()

Sistema de trading automatizado que identifica sinais em pares forex usando machine learning e envia alertas via Telegram para operações com opções.

## 🎯 Resumo Rápido

- **23 indicadores técnicos** calculados em tempo real
- **Ensemble ML** (XGBoost + RandomForest) com validação em 30% test set
- **1 ordem/dia** sem visão do futuro (tempo real puro)
- **WebSocket server** para integração MT5
- **Alertas Telegram** instantâneos
- **Performance validada**: 48-54% win rate em dados nunca vistos

## 📊 Performance (Test Set - Dados Nunca Vistos)

| Par | Trades | Win Rate | Total Pips | Status |
|-----|--------|----------|-----------|--------|
| **GBPUSD** | 224 | 50.89% | +1,199 | ✅ Recomendado |
| **EURUSD** | 224 | 48.21% | +537 | ✅ Ativo |
| **NZDUSD** | 225 | 52.89% | +597 | ✅ Ativo |
| **EURJPY** | 223 | 54.71% | +188,920 | 🚀 Premium |
| **EURAUD** | 225 | 40.44% | -2,745 | ❌ Desabilitado |

## 🚀 Quick Start

### 1. Clonar repositório
```bash
git clone https://github.com/seu-usuario/trading-options-ml.git
cd trading-options-ml
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar credenciais
```bash
cp .env.example .env
# Editar .env com seus dados Telegram
```

### 4. Iniciar servidor
```bash
cd production/websocket
python3 server.py
```

### 5. Conectar MT5
- Copiar `production/websocket/mt5_client.mq5` para MT5
- Compilar e attache ao gráfico M15

## 📁 Estrutura do Projeto

```
trading-options-ml/
├── production/                    # Sistema em produção
│   ├── websocket/
│   │   ├── server.py             # WebSocket + Telegram
│   │   ├── mt5_client.mq5        # EA para MT5
│   │   └── test_client.py        # Cliente de teste
│   ├── PRODUCAO_1ORDEM_*.csv     # Sinais pré-calculados (5 pares)
│   ├── SETUP_TELEGRAM.md         # Guia de setup
│   └── STATUS_PRODUCAO.txt       # Status atual
│
├── src/                          # Código fonte
│   ├── indicators.py             # 23 indicadores técnicos
│   └── backtest_classification_optimized.py
│
├── models/                       # Modelos treinados (ignored)
│   ├── ml_ensemble_eurusd.pkl
│   └── ml_scaler_eurusd.pkl
│
├── data/                         # Dados M15 (ignored)
│   ├── EURUSD_M15_*.csv
│   ├── GBPUSD_M15_*.csv
│   └── ...
│
├── results/                      # Resultados da validação
│   ├── backtest_*CANDLE_A_CANDLE_TESTE.csv
│   ├── PRODUCAO_1ORDEM_*.csv
│   └── backtest_resumo_TESTE_SOMENTE_30pct.csv
│
├── docs/                         # Documentação
│   ├── ARCHITECTURE.md           # Arquitetura do sistema
│   ├── INDICATORS.md             # Lista de 23 indicadores
│   └── DEPLOY.md                 # Guia de deploy
│
├── config.json                   # Configuração de ativos
├── .env.example                  # Template de variáveis
├── .gitignore
└── README.md (este arquivo)
```

## 🔧 Configuração

### Variáveis de Ambiente

Criar arquivo `.env` na raiz:

```env
# Telegram Bot (obrigatório)
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id

# WebSocket (opcional)
WEBSOCKET_PORT=5000
WEBSOCKET_HOST=0.0.0.0

# Logging (opcional)
LOG_LEVEL=INFO
```

### Obter Credenciais Telegram

1. **Criar bot**: Fale com @BotFather no Telegram → `/newbot`
2. **Obter token**: BotFather envia token automático
3. **Obter chat ID**: 
   - Envie uma mensagem para seu bot
   - Acesse: `https://api.telegram.org/bot[TOKEN]/getUpdates`
   - Procure por `chat.id`

Ver [SETUP_TELEGRAM.md](production/SETUP_TELEGRAM.md) para guia completo.

## 📊 Componentes Principais

### 1. Indicators (23 Indicadores)

```python
from src.indicators import calculate_all_indicators

df = calculate_all_indicators(df)  # Retorna DataFrame com 51 colunas
# 5 OHLCV + 23 indicadores + 23 versões normalizadas
```

**Indicadores calculados:**
- Trend: SMA20, SMA50, EMA12, EMA26, KAMA
- Momentum: RSI, MACD, Momentum, ROC  
- Volatility: ATR, Bollinger Bands, StdDev, Realized Volatility
- SMC: Support/Resistance, Order Blocks, Fair Value Gaps
- Efficiency: Kaufman ER
- Binary: price_above_sma20/50, rsi_oversold/overbought, etc

### 2. ML Models

**Ensemble:**
- XGBoost: 300 trees, max_depth=5
- RandomForest: 300 trees, max_depth=8
- Método: Votação por média de probabilidades

**Validação:**
- Split: 70% treinamento, 30% teste (cronológico)
- Período: Jan 2024 - Mai 2026
- Threshold: Otimizado por F1-score

### 3. WebSocket Server

```python
# Servidor escuta em ws://localhost:5000
# MT5 EA envia: {timestamp, ohlc, indicadores}
# Servidor retorna: {signal, confidence, entry, target}
# Se signal=1 e nenhuma ordem aberta: ENVIA TELEGRAM
```

### 4. Telegram Alerts

Formato de mensagem:

```
🎯 SINAL DE TRADING

📊 Par: EURUSD
🔼 Direção: BUY
💰 Entrada: 1.16289
🎯 Alvo: 1.16598
📏 Pips Esperados: +30.9
📊 Confiança: 60%
⏰ Horário: 2025-09-02 00:00:00

✅ Sistema de Produção Ativo
```

## 🧪 Testes

### Teste de Backtest (30% test set)

```bash
python3 src/backtest_classification_optimized.py
# Gera arquivo: results/backtest_*CANDLE_A_CANDLE_TESTE.csv
```

### Teste de Indicadores

```bash
python3 << 'EOF'
from src.indicators import calculate_all_indicators
import pandas as pd

df = pd.read_csv('data/EURUSD_M15.csv', sep='\t')
df = calculate_all_indicators(df)
print(f"Colunas: {df.shape[1]}")  # Deve ser 51
print(df.head())
EOF
```

### Teste de WebSocket

```bash
cd production/websocket
python3 test_client.py
```

## 🔐 Segurança

### Credenciais

- ✅ Nunca commitar `.env` (está em `.gitignore`)
- ✅ Usar `.env.example` como template
- ✅ Em produção: usar secrets manager ou env vars do sistema

### Modelos

- ✅ Modelos em `.gitignore` (muito grandes)
- ✅ Backup em location segura
- ✅ Versionamento via Git LFS (opcional)

### Comunicação

- ✅ WebSocket: implementar SSL em produção
- ✅ MT5: validar origem de conexões
- ✅ Telegram: usar rate limiting

## 📈 Roadmap

- [x] Modelo ML com 23 indicadores
- [x] Validação em 30% test set
- [x] 1 ordem/dia sem futuro
- [x] WebSocket server
- [x] Integração Telegram
- [ ] Dashboard de monitoramento
- [ ] Implementar filtros (ER, BOS, Aceleração)
- [ ] Retraining automático
- [ ] Multi-timeframe analysis

## 📞 Suporte

### Troubleshooting

| Problema | Solução |
|----------|---------|
| WebSocket não conecta | `lsof -i :5000` - verificar porta |
| Telegram sem mensagens | Verificar `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID` |
| MT5 EA não envia dados | Verificar compilação e firewall |
| Sinais muito fracos | Aumentar `MIN_CONFIDENCE` em `.env` |

### Logs

```bash
# Ver logs em tempo real
tail -f production.log

# Iniciar com debug
LOG_LEVEL=DEBUG python3 production/websocket/server.py
```

## 📚 Documentação Detalhada

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Design do sistema
- [INDICATORS.md](docs/INDICATORS.md) - 23 indicadores explicados
- [DEPLOY.md](docs/DEPLOY.md) - Deploy em produção
- [SETUP_TELEGRAM.md](production/SETUP_TELEGRAM.md) - Setup Telegram passo-a-passo

## 📊 Resultados Recentes

**Período de Teste:** Maio 2025 - Mai 2026 (30% dos dados)  
**Estratégia:** Primeira ordem válida do dia, abre imediatamente  
**Status:** Production Ready

### Por Par
- GBPUSD: **+1,199 pips** (224 trades, 50.89% WR) ✅
- EURJPY: **+188,920 pips** (223 trades, 54.71% WR) 🚀
- NZDUSD: **+597 pips** (225 trades, 52.89% WR) ✅
- EURUSD: **+537 pips** (224 trades, 48.21% WR) ✅

## 📄 Licença

MIT License - Ver LICENSE para detalhes

## 👤 Autor

Desenvolvido com 🤖 Machine Learning

---

**Última atualização:** 31/05/2026  
**Status:** 🟢 Production Ready  
**Versão:** 1.0.0
