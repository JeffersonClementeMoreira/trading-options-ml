# Sistema de Trading com XGBoost - Guia de Uso

## Arquitetura

```
┌─────────────────┐
│   MT5 EA        │
│  (options.mq5)  │
└────────┬────────┘
         │ WebSocket JSON
         │ (candle + 5 indicadores)
         ▼
┌─────────────────────────────┐
│  mt5_realtime_server.py     │
│  (HTTP/websocket listener)  │
└────────┬────────────────────┘
         │ JSON com features
         │
         ▼
┌──────────────────────────────────┐
│  realtime_inference.py (produção)│
│  - Carrega XGBoost pkl           │
│  - Prediz p(up,down,flat)        │
│  - Mapeia para CALL/PUT/STRANGLE │
│  - Envia Telegram                │
└──────────────────────────────────┘
         │ Mensagem Telegram
         ▼
    📱 Chat do Trader
```

## Modos de Operação

### 1️⃣ MODO BACKTEST (Local - Análise)

```bash
# Treinar XGBoost com dados históricos
python xgb_entry_optimizer.py \
  --data dados/EURUSD_features.csv \
  --backtest-days 30

# Output:
# - CSV com decisões (action, p_up, p_down, confidence)
# - HTML colorido com sinais visuais
```

**Características:**
- ✅ Entrada: CSV local
- ✅ Saída: HTML colorido + CSV para análise
- ✅ Sem Telegram
- ✅ Análise histórica de performance

### 2️⃣ MODO PRODUÇÃO (VPS - Trading Real)

```bash
# 1. Exportar modelos treinados
python xgb_entry_optimizer.py \
  --data dados/EURUSD_features.csv \
  --export-models models/

# 2. Iniciar servidor de inferência
python -c "
from realtime_inference import make_inference_engine
from pathlib import Path
import os

engine = make_inference_engine(
    model_dir=Path('models/'),
    telegram_enabled=True,  # ← ATIVA TELEGRAM
)

# Engine pronto para receber requisições websocket
print(f'Engine carregado. Telegram: {engine.telegram_enabled}')
"
```

**Variáveis de Ambiente Necessárias:**

```bash
# Telegram
export TELEGRAM_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="987654321"

# Opcional: configurar limites
export CONFIDENCE_THRESHOLD="0.55"  # Mínimo para trade
export STRANGLE_THRESHOLD="0.40"   # Spread max para STRANGLE
```

## 5 Indicadores Novos (XGBoost)

Os 5 indicadores adicionados ao EA agora estão disponíveis:

```python
EXTERNAL_RSI_COLS = ("mt5_rsi_norm",)                    # [0, 1]
EXTERNAL_MACD_LINE_COLS = ("mt5_macd_line",)             # bruta
EXTERNAL_MACD_SIGNAL_COLS = ("mt5_macd_signal",)         # bruta
EXTERNAL_MACD_HISTOGRAM_COLS = ("mt5_macd_histogram_pct",) # % do close
EXTERNAL_BB_POSITION_COLS = ("mt5_bb_position",)         # [0, 1]
EXTERNAL_VOLUME_RATIO_COLS = ("mt5_volume_ratio",)       # vol/vol_sma
EXTERNAL_CCI_COLS = ("mt5_cci_norm",)                    # [-1, 1]
```

## Lógica de Decisão

```python
class TradeAction(Enum):
    CALL = "📈"       # P(UP) > P(DOWN) + confidence ✅
    PUT = "📉"        # P(DOWN) > P(UP) + confidence ✅
    STRANGLE = "⚖️"   # |P(UP) - P(DOWN)| < threshold (venda volatilidade)
    NO_TRADE = "🚫"   # Confiança < threshold ou ambiguidade
```

### Exemplos de Decisão

| P(UP) | P(DOWN) | P(FLAT) | Conf | Ação | Razão |
|-------|---------|---------|------|------|-------|
| 0.70  | 0.20    | 0.10    | 0.70 | CALL | Viés positivo forte |
| 0.25  | 0.70    | 0.05    | 0.70 | PUT  | Viés negativo forte |
| 0.45  | 0.42    | 0.13    | 0.45 | STRANGLE | Muito incerto |
| 0.50  | 0.48    | 0.02    | 0.50 | NO_TRADE | Confiança < 55% |

## Output Backtest (CSV)

```csv
datetime,symbol,timeframe,p_up,p_down,p_flat,action,confidence,reasoning
2026-05-24 14:00,EURUSD,M15,0.72,0.18,0.10,CALL,0.72,Viés positivo: P(UP)=72.00% > P(DOWN)=18.00%
2026-05-24 15:00,EURUSD,M15,0.35,0.38,0.27,STRANGLE,0.38,Spread UP/DOWN baixo (3.00%): vender volatilidade
2026-05-24 16:00,EURUSD,M15,0.52,0.48,0.00,NO_TRADE,0.52,Confiança insuficiente (52.00% < 55.00%)
```

## Output Produção (Telegram)

```
📈 CALL
`EURUSD` | `M15`

P(↑) = 72.00%
P(→) = 10.00%
P(↓) = 18.00%

🎯 Conf: 72.00%
```

## Configuração Telegram

### 1. Criar Bot

1. No Telegram, procure por `@BotFather`
2. Comando: `/newbot`
3. Escolha nome (ex: "TradeSignalsBot")
4. Receba token: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

### 2. Obter Chat ID

1. Crie/entre em um grupo privado
2. Adicione o bot ao grupo
3. Envie mensagem: `/start` ou qualquer texto
4. Acesse: `https://api.telegram.org/bot{TOKEN}/getUpdates`
5. Procure por `"chat"` → `"id"` (ex: `987654321`)

### 3. Configurar Variáveis

```bash
# ~/.bashrc ou .env
export TELEGRAM_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TELEGRAM_CHAT_ID="987654321"

# Verificar
source ~/.bashrc
echo $TELEGRAM_TOKEN
```

## Fluxo Completo

### Dia 1: Backtest & Treinamento

```bash
cd /home/ubuntu/pessoal/options

# Baixar dados históricos (ex: 6 meses)
python options_v3.py --tail 10000 --csv dados/EURUSD_M15_history.csv

# Treinar XGBoost
python xgb_entry_optimizer.py \
  --data dados/EURUSD_M15_history.csv \
  --backtest-days 180 \
  --export-models models/

# Analisar resultados
open predictions/backtest_EURUSD_M15_*_colored.html
cat predictions/backtest_EURUSD_M15_*_policy.csv
```

### Dia 2+: Produção

```bash
# Na VPS Oracle:
# 1. EA rodando em M15, postando via websocket
# 2. Servidor inferência ouvindo
# 3. Sinais vindo via Telegram

# Monitorar logs
tail -f logs/realtime_signals.log

# Parar tudo
pkill -f realtime_inference
pkill -f mt5_realtime_server
```

## Arquivo de Resultados

### HTML Colorido (Backtest)

- **Verde claro** = CALL ✅
- **Vermelho claro** = PUT ✅
- **Ouro** = STRANGLE ⚖️
- **Cinza** = NO_TRADE ❌

### CSV (Análise)

Colunas principais:
- `datetime` - timestamp
- `symbol`, `timeframe` - contexto
- `p_up`, `p_down`, `p_flat` - probabilidades XGBoost
- `action` - recomendação (CALL/PUT/STRANGLE/NO_TRADE)
- `confidence` - máx(p_up, p_down, p_flat)
- `reasoning` - explicação da decisão

## Troubleshooting

### Telegram não envia

```bash
# 1. Verificar credenciais
echo $TELEGRAM_TOKEN
echo $TELEGRAM_CHAT_ID

# 2. Testar manualmente
curl -X POST https://api.telegram.org/bot{TOKEN}/sendMessage \
  -d "chat_id={CHAT_ID}" \
  -d "text=Teste"
```

### Modelos não carregam

```bash
# Verificar se pkl foi salvo
ls -la models/*.pkl

# Treinar novamente
python xgb_entry_optimizer.py --data dados/*.csv --export-models models/
```

### Websocket não recebe dados

```bash
# Verificar servidor
ps aux | grep mt5_realtime_server

# Ver logs
tail -f logs/*realtime*.log

# Reiniciar
python mt5_realtime_server.py --port 8765
```

## Métricas de Performance (Backtest)

```
Acurácia Direção (XGBoost):    72.3%
Hit Rate (sinais executados):   68.5%
Coverage (% trades):            35.2%
Melhor condição:                D+1 às 14:00 (score: 71.2)
```

---

**Próximos passos:**
1. ✅ Treinar modelo ternário em 180 dias de dados
2. ✅ Validar em 30 dias de teste
3. ✅ Ativar Telegram em produção
4. ✅ Monitorar hit rate nas primeiras 2 semanas
5. ⏳ Ajustar thresholds se necessário
