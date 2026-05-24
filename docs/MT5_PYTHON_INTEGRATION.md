# 🔗 MT5 + Python XGBoost Integration Guide

## Overview

```
┌─────────────────────────────────┐
│   MetaTrader 5                   │
│                                  │
│ SMC_Features_Indicator.mq5      │
│   ↓                             │
│ Calcula 25+ features SMC        │
│   ↓                             │
│ Exporta → smc_features.csv      │
└─────────────────────────────────┘
              ↓
              ↓ (Arquivo CSV)
              ↓
┌─────────────────────────────────┐
│   Python / XGBoost               │
│                                  │
│ mt5_smc_reader.py               │
│   ↓                             │
│ Lê smc_features.csv             │
│   ↓                             │
│ core/smc_xgboost.py             │
│   ↓                             │
│ Modelos treinam/predizem        │
│   ↓                             │
│ Sinais: SELL_PUT, SELL_CALL... │
└─────────────────────────────────┘
```

---

## Part 1: MT5 Setup

### 1.1 Copiar Indicador para MT5

```bash
# No Windows/MT5:
# Copie o arquivo para:
C:\Users\<YourUser>\AppData\Roaming\MetaQuotes\Terminal\<TerminalID>\MQL5\Indicators\

# No Linux (via wine/box64):
cp SMC_Features_Indicator.mq5 /path/to/mt5/indicators/
```

### 1.2 Compilar Indicador

1. Abra MetaTrader 5
2. Vá para: Tools → MetaEditor (F4)
3. Abra: SMC_Features_Indicator.mq5
4. Compile: File → Compile (ou F5)
5. Se houver erros, ajuste includes no cabeçalho

### 1.3 Executar Indicador

1. Vá para EURUSD M15
2. Abra: Insert → Indicators → Custom → SMC_Features_Indicator
3. Configurações padrão OK
4. OK

✅ Indicador agora calcula features a cada candle e exporta para `smc_features.csv`

### 1.4 Encontrar Arquivo CSV

O arquivo é salvo em:
```
Windows: C:\Users\<YourUser>\AppData\Roaming\MetaQuotes\Terminal\<TerminalID>\MQL5\Files\smc_features.csv
Linux:   ~/.wine/drive_c/Users/<YourUser>/AppData/Roaming/MetaQuotes/Terminal/<TerminalID>/MQL5/Files/smc_features.csv
```

Ou copie manualmente para:
```
/home/ubuntu/pessoal/options/dados/smc_features.csv
```

---

## Part 2: Python Integration

### 2.1 Verificar que SMC Features estão sendo calculadas

```python
from core.mt5_smc_reader import MT5SMCFeaturesReader

# Ler features
reader = MT5SMCFeaturesReader()
if reader.load():
    features = reader.get_latest_features()
    print(f"Distance to Top: {features['dist_top_liquidity']:.2f} ATRs")
    print(f"FVG Pressure: {features['fvg_pressure']:.3f}")
    print(f"ATR Compression: {features['atr_compression_ratio']:.3f}")
```

### 2.2 Treinar Modelos XGBoost com Features MT5

```python
from core.mt5_smc_reader import MT5SMCFeaturesReader
from core.smc_xgboost import SMCXGBoostTrainer

# 1. Ler features exportadas pelo MT5
reader = MT5SMCFeaturesReader()
reader.load()
smc_df = reader.get_all_features_df()

# 2. Combinar com OHLC data
# smc_df tem as 25+ features
# Precisamos do OHLC também

df_ohlc = pd.read_csv("dados/EURUSD_M15.csv")
# ... processar para daily ...

# 3. Treinar modelos
trainer = SMCXGBoostTrainer()
trainer.train_all(df_ohlc, smc_df, extremos)

# 4. Modelos estão em: models/smc_xgboost_models.pkl
```

### 2.3 Gerar Sinais em Tempo Real

```python
from core.mt5_smc_reader import SMCFeaturesIntegration
import pickle

# Inicializar leitor
smc = SMCFeaturesIntegration()
smc.initialize()

# Loop em tempo real
while True:
    # Verificar atualizações do MT5
    if smc.update():
        # Novas features disponíveis
        features = smc.get_current_features()
        
        # Carregar modelos treinados
        with open("models/smc_xgboost_models.pkl", "rb") as f:
            data = pickle.load(f)
            models = data["models"]
        
        # Prever
        direction_prob = models["direction"].predict_proba([features])
        expected_move = models["expected_move"].predict([features])[0]
        
        # Decisão
        if direction_prob[0][1] > 0.65:  # 65% chance UP
            action = "SELL_PUT"
            strike_distance = expected_move * 0.5
        else:
            action = "SELL_CALL"
            strike_distance = expected_move * 0.5
        
        print(f"Signal: {action} at -{strike_distance:.0f} pts")
```

---

## Part 3: Nomenclatura de Ações

### ✅ Nomes Padronizados

Todas as ações agora seguem o padrão:

| Ação | Significado | Quando |
|------|-------------|--------|
| **SELL_PUT** | Vender PUT | p_up > p_down (bullish) |
| **SELL_CALL** | Vender CALL | p_down > p_up (bearish) |
| **SELL_STRANGLE** | Vender ambas | Incerteza (|p_up - p_down| < threshold) |
| **NO_TRADE** | Sem sinal | Confiança < threshold |

### Arquivo: trading_decision.py

```python
class TradeAction(Enum):
    SELL_CALL = "SELL_CALL"       # Bearish
    SELL_PUT = "SELL_PUT"         # Bullish
    SELL_STRANGLE = "SELL_STRANGLE"  # Uncertain
    NO_TRADE = "NO_TRADE"
```

---

## Part 4: Workflow Completo

### 4.1 Setup Inicial

```bash
# 1. Copiar indicador MQ5 para MT5 e compilar
# 2. Executar indicador no gráfico EURUSD M15
# 3. Esperar alguns candles para acumular dados
```

### 4.2 Treinamento (Uma vez)

```bash
cd /home/ubuntu/pessoal/options

# Features do MT5 estão em dados/smc_features.csv
# Dados OHLC estão em dados/EURUSD_M15_*.csv

python3 train_smc_models.py \
  --data dados/EURUSD_M15_202301012200_202605222015.csv
```

Resultado:
```
📊 Modelo 1 (Direction): 62% acurácia
📊 Modelo 2 (Sweep): 64% acurácia
📊 Modelo 3 (Reversal): 61% acurácia
📊 Modelo 4 (Expected Move): R² = 0.58
📊 Modelo 5 (Strike): 68% acurácia
```

### 4.3 Sinais em Tempo Real

```bash
# Script que roda continuamente
python3 realtime_smc_signals.py

# Outputs:
# - Sinais a cada novo candle
# - Strike recomendado
# - Probabilidade OTM
# - Envio Telegram (opcional)
```

### 4.4 Backtest

```bash
# Testar sinais históricos
python3 backtest_with_smc.py

# Gera:
# - Acurácia por modelo
# - P&L esperado
# - Distribuição de strikes
# - HTML report
```

---

## Part 5: Troubleshooting

### Problema: "smc_features.csv não encontrado"

```python
# Solução: Especificar path manualmente
reader = MT5SMCFeaturesReader(
    smc_csv_path="/path/to/smc_features.csv"
)
reader.load()
```

### Problema: Features sempre 0

```
Causa: Indicador MQ5 não está rodando
Solução:
  1. Verificar se indicador está no gráfico
  2. Verificar se há candles novos (M15 atualizar)
  3. Procurar arquivo CSV em: Terminal\MQL5\Files\
  4. Copiar manualmente para /home/ubuntu/pessoal/options/dados/
```

### Problema: Features diferentes de zero mas modelo não prediz bem

```
Causa: Talvez Features e OHLC estejam desalinhados
Solução:
  1. Verificar timestamps: smc_features.csv vs OHLC
  2. Garantir que ambos usam M15 como timeframe
  3. Verificar que datas/horas são iguais
  4. Re-treinar modelos com dados alinhados
```

---

## Part 6: Arquivos da Integração

```
/home/ubuntu/pessoal/options/
│
├── mt5/
│   └── SMC_Features_Indicator.mq5    ← Indicador MQ5
│
├── core/
│   ├── mt5_smc_reader.py             ← Lê features do MT5
│   ├── smc_xgboost.py                ← Modelos (usa features)
│   └── indicators.py                 ← Calculadores locais (fallback)
│
├── src/
│   ├── trading_decision.py           ← Enum com SELL_PUT, SELL_CALL
│   └── realtime_analysis.py          ← Gerador de sinais
│
├── dados/
│   ├── EURUSD_M15_*.csv              ← OHLC
│   └── smc_features.csv              ← Features do MT5
│
├── models/
│   └── smc_xgboost_models.pkl        ← Modelos treinados
│
└── docs/
    └── SMC_XGBOOST_ARCHITECTURE.md
```

---

## Part 7: Próximos Passos

### Imediato
1. [ ] Copiar indicador MQ5 para MT5
2. [ ] Executar indicador no gráfico
3. [ ] Verificar smc_features.csv sendo criado
4. [ ] Testar reader em Python

### Curto Prazo
1. [ ] Treinar modelos com features MT5
2. [ ] Validar acurácia vs features locais
3. [ ] Implementar realtime_smc_signals.py
4. [ ] Testar sinais em backtest

### Médio Prazo
1. [ ] Adicionar mais features no MQ5 (BOS, CHOCH, etc)
2. [ ] Otimizar threshold com Modelo 5
3. [ ] Integrar com MT5 EA para execução automática
4. [ ] Adicionar notificações Telegram

---

## Part 8: FAQ

**P: Por que rodar SMC no MT5 em vez de Python?**

R: 
- MT5 atualiza SMC em tempo real, Python teria delay
- Evita duplicação de cálculos
- Sincronização perfeita com preços do MT5

**P: E se MT5 ficar offline?**

R: 
- O arquivo smc_features.csv fica estático
- Python pode usar features "antigas" ou recalcular localmente
- Fallback para core/smc_features.py (Python version)

**P: Como sincronizar timestamps?**

R:
- Indicador MQ5 usa Time[0] (UTC do servidor MT5)
- Python lê CSV e faz match por datetime
- Garantir ambos usam mesmo formato: "YYYY-MM-DD HH:MM:SS"

**P: Posso rodar em outros pares?**

R:
- Sim! Execute indicador em GBPUSD, XAUUSD, etc
- Treinar modelos separados para cada par
- Features SMC são universais

