# 📊 GUIA: Adicionar Novos Ativos (GOLD, SP500, etc)

## 🎯 Visão Geral

O `config.json` foi atualizado para suportar **qualquer tipo de ativo**:
- ✅ **Forex pairs** (EURUSD, GBPUSD, etc)
- ✅ **Commodities** (GOLD, SILVER, OIL, etc)
- ✅ **Índices** (SP500, DAX, FTSE, NASDAQ, etc)
- ✅ **Ações** (APPLE, TESLA, etc) - em breve
- ✅ **Crypto** (BTCUSD, ETHUSD, etc) - em breve

---

## 📋 Estrutura do config.json - Novos Campos

### Campo: `asset_type`
```json
"asset_type": "forex_pair" | "commodity" | "index"
```
- **forex_pair**: Pares de moedas (EURUSD, GBPUSD)
- **commodity**: Commodities (GOLD, SILVER, OIL)
- **index**: Índices (SP500, DAX, FTSE)

### Campo: `base` e `quote`
```json
"base": "EUR",      // Primeira moeda (ou nome do ativo)
"quote": "USD"      // Segunda moeda (ou null para índices/commodities)
```

**Exemplos:**
```json
// Forex
"base": "EUR", "quote": "USD"     // EURUSD
"base": "GBP", "quote": "USD"     // GBPUSD

// Commodity
"base": "GOLD", "quote": "USD"    // Ouro em dólares
"base": "OIL", "quote": "USD"     // Petróleo

// Index (sem quote!)
"base": "SPX", "quote": null      // S&P 500
"base": "DAX", "quote": null      // DAX
```

### Campo: `pip_value`
```json
"pip_value": 0.0001  // Menor movimento do ativo
```

**Referência:**
```
FOREX:
  EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCAD: 0.0001
  USDJPY, EURJPY: 0.01
  
COMMODITIES:
  GOLD, SILVER: 0.01 (ponto = $1)
  OIL: 0.01
  
ÍNDICES:
  SP500, DAX, FTSE, NASDAQ: 1.0 (ponto = 1 ponto)
```

### Campo: `spread_typical`
```json
"spread_typical": 1.2  // Spread médio em "pips" (ou pontos para índices)
```

**Referência:**
```
FOREX: 1.0-3.0 pips
GOLD: 0.30 (30 centavos)
SP500: 3.0-5.0 pontos
DAX: 2.0-3.0 pontos
FTSE: 1.5-2.0 pontos
```

### Campo: `timezone`
```json
"timezone": "UTC" | "US/Eastern" | "Europe/Berlin" | "Europe/London"
```

**Referência por ativo:**
```
Forex (24/5):     "UTC"
GOLD (COMEX):     "UTC"
SP500 (NYSE):     "US/Eastern"
DAX (EUREX):      "Europe/Berlin"
FTSE (LSE):       "Europe/London"
```

### Campo: `closing_time`
```json
"closing_time": "HH:MM"  // Horário que o preço D+1 fecha (em UTC normalmente)
```

⚠️ **CRÍTICO**: Este é o horário usado para calcular o preço-alvo D+1!

**Exemplos:**
```
Forex (você escolhe):        "14:00" (ou "16:00", "18:00", etc)
GOLD (COMEX):               "17:00"
SP500 (NYSE 4:00 PM ET):    "20:00"
DAX (EUREX 8:00 PM CET):    "22:00"
FTSE (LSE 5:00 PM GMT):     "17:00"
```

**Como descobrir para seu ativo:**
1. Abrir MetaTrader 5
2. Clicar direita no símbolo → Propriedades
3. Ver horários de negociação
4. Identificar hora de fechamento
5. Converter para UTC se necessário

### Campo: `active_hours`
```json
"active_hours": "HH:MM-HH:MM"  // Horário de negociação (informativo)
```

**Exemplos:**
```
Forex 24/5:         "00:00-23:59"
SP500 (ET):         "14:30-21:00"
DAX (CET):          "08:00-22:00"
GOLD 24/5:          "00:00-23:59"
```

---

## 🔧 Passo-a-Passo: Adicionar Novo Ativo

### Exemplo 1: Adicionar GOLD (Commodity)

**Passo 1**: Obter informações do GOLD em MT5
```
MT5 → Mercados → Procurar "GOLD"
Clicar direita → Propriedades
Ver: Spread, ponto de valor, horários
```

**Passo 2**: Preparar dados
```bash
# Exportar de MT5: M15, formato tab-separated
# Arquivo: GOLD_M15_202401012200_202605222015.csv
# Colocar em: data/GOLD_M15_*.csv
```

**Passo 3**: Atualizar config.json
```json
"GOLD": {
  "enabled": false,
  "asset_type": "commodity",
  "description": "Gold (COMEX) vs USD (M15)",
  "data_file": "data/GOLD_M15_*.csv",
  "base": "GOLD",
  "quote": "USD",
  "pip_value": 0.01,
  "spread_typical": 0.30,
  "timezone": "UTC",
  "closing_time": "17:00",
  "active_hours": "00:00-23:59",
  "notes": "COMEX closes 17:00 UTC"
}
```

**Passo 4**: Testar pipeline
```bash
# Primeiro teste individual
python3 src/run_full_pipeline.py GOLD

# Se funcionar, ativar no config
# Mudar "enabled": true
# Depois: python3 src/run_full_pipeline.py --all
```

---

### Exemplo 2: Adicionar SP500 (Index)

**Passo 1**: Obter informações do SP500
```
MT5 → Procurar "SPX" ou "US500"
Propriedades:
  - Horário: 14:30-21:00 (9:30 AM - 4:00 PM ET)
  - Spread: ~3-5 pontos
  - Ponto: 1.0
  - Fuso horário: ET (Eastern Time)
```

**Passo 2**: Preparar dados
```bash
# Exportar M15 de MT5 ou TradingView
# Arquivo: SP500_M15_202401012200_202605222015.csv
# Colocar em: data/SP500_M15_*.csv
```

**Passo 3**: Atualizar config.json
```json
"SP500": {
  "enabled": false,
  "asset_type": "index",
  "description": "S&P 500 Index (M15)",
  "data_file": "data/SP500_M15_*.csv",
  "base": "SPX",
  "quote": null,
  "pip_value": 1.0,
  "spread_typical": 3.0,
  "timezone": "US/Eastern",
  "closing_time": "20:00",
  "active_hours": "14:30-21:00",
  "notes": "NYSE 9:30 AM - 4:00 PM ET = 14:30-20:00 UTC"
}
```

⚠️ **Importante**: `closing_time: "20:00"` = 4:00 PM ET em UTC

**Conversão automática:**
```
4:00 PM ET (EDT - daylight): +4 horas do UTC
4:00 PM ET + 4 = 20:00 UTC ✓

4:00 PM ET (EST - standard): +5 horas do UTC  
4:00 PM ET + 5 = 21:00 UTC (use 21:00 em inverno)
```

**Passo 4**: Testar
```bash
python3 src/run_full_pipeline.py SP500
```

---

## ⚠️ Cuidados Importantes

### 1. Closing Time Deve Estar Correto

O pipeline busca o preço às `closing_time` para calcular target (D+1).

```
EURUSD:
  closing_time: "14:00"
  └─ Sistema busca candle de 14:00 UTC como "fechamento do dia"

SP500:
  closing_time: "20:00"
  └─ Sistema busca candle de 20:00 UTC (4:00 PM ET)
```

❌ **Errado**: Se colocar "20:00" mas NYSE fecha 16:00 ET, sistema vai buscar after-hours!

✅ **Correto**: Verificar em MT5 qual hora o candle realmente fecha.

### 2. Timezone vs Closing Time

```
Campo "timezone": Apenas para documentação/referência
Campo "closing_time": DEVE estar em UTC

Exemplo SP500:
  "timezone": "US/Eastern"  ← Documentação
  "closing_time": "20:00"   ← 20:00 UTC (4:00 PM ET)
```

### 3. pip_value Afeta Cálculos de Pips

```json
"pip_value": 0.0001  // EURUSD
└─ Se preço muda 0.0001, = 1 pip

"pip_value": 0.01    // GOLD
└─ Se preço muda 0.01, = 1 ponto ($1)

"pip_value": 1.0     // SP500
└─ Se preço muda 1.0, = 1 ponto
```

Certifique-se que está correto, afeta análise de rentabilidade!

### 4. Formato de Dados Deve Estar Correto

```
❌ Errado (Excel):
date,time,open,high,low,close
2026-01-01,14:00:00,100,101,99,100

✅ Correto (Tab-separated MT5):
date	time	open	high	low	close	tickvol	vol	spread
2026.01.01	14:00:00	100	101	99	100	100	1000	1
```

---

## 📋 Checklist: Antes de Rodar

Antes de executar `python3 src/run_full_pipeline.py SEUATIVO`:

- [ ] Arquivo CSV em `data/SEUATIVO_M15_*.csv`
- [ ] Formato: Tab-separated (verificar com `head -3 data/SEUATIVO_M15_*.csv`)
- [ ] Mínimo 1000 candles (idealmente 50k+ como EURUSD)
- [ ] Coluna headers: date, time, open, high, low, close, tickvol, vol, spread
- [ ] Configuração em config.json:
  - [ ] asset_type correto
  - [ ] base e quote preenchidos (quote=null para índices OK)
  - [ ] pip_value correto (verificar em MT5)
  - [ ] closing_time em UTC correto
  - [ ] enabled: false (primeiro teste individual)

---

## 🚀 Comandos Úteis

```bash
# 1. Testar individual (antes de ativar)
python3 src/run_full_pipeline.py GOLD

# 2. Ver status dos outputs
ls -lh results/UNIFIED_SIGNALS_GOLD.csv

# 3. Análise rápida
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('results/UNIFIED_SIGNALS_GOLD.csv')
print(f"Win Rate: {(df['Result']=='WIN').sum()}/{len(df)}")
print(f"Total Pips: {df['Actual Pips'].sum()}")
EOF

# 4. Se funcionar, ativar no config
# Editar config.json: "enabled": true
# Depois rodar:
python3 src/run_full_pipeline.py --all

# 5. Ver resultado de múltiplos ativos
for symbol in EURUSD GBPUSD GOLD SP500; do
  echo "=== $symbol ===" 
  python3 src/run_full_pipeline.py $symbol 2>&1 | grep "Win Rate\|Total Pips"
done
```

---

## 🐛 Troubleshooting

### Erro: "KeyError: 'closing_time'"
```
Problema: Campo closing_time não existe em config.json antigo
Solução: Atualizar config.json com novo formato
```

### Erro: "No data for target calculation"
```
Problema: closing_time errado, não encontra candles
Solução: Verificar em MT5 qual é a hora real de fechamento
```

### Win Rate muito baixo (< 40%)
```
Possíveis causas:
1. Ativo muito volátil (ex: SP500 vs EURUSD)
2. Spread muito alto (ajustar pip_value se necessário)
3. Poucos dados de treino
4. Horário de fechamento não é realmente representativo

Solução: Testar diferentes closing_time
```

---

## 📝 Exemplo Completo: Adicionando SILVER

```json
"SILVER": {
  "enabled": false,
  "asset_type": "commodity",
  "description": "Silver (COMEX) vs USD (M15)",
  "data_file": "data/SILVER_M15_202401012200_202605222015.csv",
  "base": "SILVER",
  "quote": "USD",
  "pip_value": 0.001,
  "spread_typical": 0.015,
  "timezone": "UTC",
  "closing_time": "17:00",
  "active_hours": "00:00-23:59",
  "notes": "COMEX closes 17:00 UTC, 1 point = $1 per ounce"
}
```

```bash
# Passo a passo
1. Exportar SILVER_M15 de MT5 → data/SILVER_M15_*.csv
2. Copiar bloco JSON acima para config.json
3. Rodar teste: python3 src/run_full_pipeline.py SILVER
4. Se OK, ativar: "enabled": true
5. Rodar todos: python3 src/run_full_pipeline.py --all
```

---

## 🎓 Referência Rápida: Closing Times por Ativo

```
FOREX (24/5):
  EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCAD: "14:00" UTC (escolher)

COMMODITIES:
  GOLD, SILVER: "17:00" UTC (COMEX)
  OIL (WTI): "21:30" UTC

ÍNDICES:
  SP500, NASDAQ: "20:00" UTC (4:00 PM ET)
  DAX: "22:00" UTC (8:00 PM CET)
  FTSE: "17:00" UTC (5:00 PM GMT)
  CAC40: "22:00" UTC (8:00 PM CET)
  IBEX: "21:00" UTC (5:00 PM CET)

AÇÕES (geralmente seguem índice local):
  NYSE (US): "20:00" UTC
  EUREX (EU): "22:00" UTC
```

---

**Data**: 28/05/2026  
**Versão**: 1.0.0  
**Status**: ✅ Production Ready
