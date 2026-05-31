# 📚 SETUP DE NOVOS ATIVOS - Guia Completo

## 📋 Status Atual

### ✅ Ativos Configurados e Testados
- **EURUSD**: Totalmente funcional
- **GBPUSD**: Totalmente funcional

### ⏳ Ativos Prontos para Setup
- **AUDUSD**: Dados em `data/AUDUSD_M15_202401012200_202605222015.csv`
- **NZDUSD**: Aguardando dados
- **USDCAD**: Aguardando dados

---

## 🚀 Como Adicionar Um Novo Ativo

### Passo 1: Preparar os Dados

**Requisitos:**
- Arquivo CSV com dados M15 (15 minutos)
- Formato: `TAB-SEPARATED`
- Colunas (nesta ordem):
  ```
  date       time       open    high    low     close   tickvol  vol      spread
  2024.01.01 22:15:00   1.0956  1.0957  1.0954  1.0955  100      1000     1.2
  2024.01.01 22:30:00   1.0955  1.0958  1.0954  1.0957  150      1500     1.2
  ```

**Exemplo de comando MT5 para exportar:**
```
1. MT5 → Gráfico M15 do ativo
2. Clique direito → Exportar dados históricos
3. Formato: Data, Tempo, Abertura, Máxima, Mínima, Fechamento, Volume
4. Separador: Tab
```

---

### Passo 2: Atualizar config.json

Edite `/home/ubuntu/pessoal/options/config.json`:

```json
{
  "assets": {
    "SEUATIVO": {
      "enabled": true,
      "description": "Descrição do ativo",
      "data_file": "data/SEUATIVO_M15_YYYYMMDD_YYYYMMDD.csv",
      "pairs": ["MOEDA1", "MOEDA2"],
      "pip_value": 0.0001,
      "spread_typical": 1.5,
      "active_hours": "00:00-23:59",
      "notes": "Observações"
    }
  }
}
```

**Exemplo para AUDUSD:**
```json
{
  "AUDUSD": {
    "enabled": true,
    "description": "Australian Dollar vs US Dollar (M15)",
    "data_file": "data/AUDUSD_M15_202401012200_202605222015.csv",
    "pairs": ["AUD", "USD"],
    "pip_value": 0.0001,
    "spread_typical": 1.8,
    "active_hours": "00:00-23:59",
    "notes": "Ready for setup"
  }
}
```

---

### Passo 3: Executar Pipeline

#### Opção A: Um ativo específico
```bash
cd /home/ubuntu/pessoal/options
python3 src/run_full_pipeline.py AUDUSD
```

#### Opção B: Todos os ativos habilitados
```bash
python3 src/run_full_pipeline.py --all
```

#### Opção C: Com arquivo customizado
```bash
python3 src/run_full_pipeline.py AUDUSD --datafile data/AUDUSD_M15_custom.csv
```

---

## 📊 O Que o Pipeline Executa

```
1. ✅ LOAD DATA
   └─ Carrega arquivo CSV
   └─ Valida formato
   └─ Cria timestamp

2. ✅ CALCULATE INDICATORS (23 features)
   ├─ RSI, SMA20, SMA50, MACD
   ├─ ATR, Momentum, Bollinger Bands
   ├─ SMC Zones (Support/Resistance)
   ├─ ER (Efficiency Ratio)
   ├─ KAMA (Kaufman Adaptive MA)
   └─ Realized Volatility

3. ✅ SPLIT DATA (70% treino / 30% teste)
   └─ Cronológico (sem shuffle = sem lookahead bias)

4. ✅ TRAIN MODELS
   ├─ XGBoost (300 estimadores)
   ├─ RandomForest (300 árvores)
   └─ Decision Tree (refinador de direção)

5. ✅ PREDICT & REFINE
   ├─ Predição de preço (XGB + RF ensemble)
   ├─ Cálculo de confiança
   └─ Refinamento com Decision Tree

6. ✅ GENERATE OUTPUTS
   ├─ backtest_{ATIVO}_DETAILED.csv (todas as amostras + análise)
   ├─ signals_{ATIVO}_QUALITY.csv (sinais filtrados)
   ├─ ACTIONABLE_SIGNALS_{ATIVO}.csv (ENTER/SKIP)
   └─ ENHANCED_SIGNALS_{ATIVO}.csv (predição vs real)
```

---

## 📈 Saídas Esperadas

### Após executar `python3 src/run_full_pipeline.py AUDUSD`:

```
results/
├─ backtest_AUDUSD_DETAILED.csv        (~ 17k linhas, 40 colunas)
├─ signals_AUDUSD_QUALITY.csv          (1 sinal/dia, filtrado)
├─ ACTIONABLE_SIGNALS_AUDUSD.csv       (ENTER/SKIP decision)
├─ ENHANCED_SIGNALS_AUDUSD.csv         (predição vs real)
├─ analysis_AUDUSD_REPORT.txt          (análise detalhada)
├─ GUIDE_AUDUSD.txt                    (guia de uso)
└─ GUIDE_ENHANCED_AUDUSD.txt           (guia completo)
```

---

## 🔍 Estrutura do CSV Detalhado

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| timestamp | datetime | Horário do candle |
| open, high, low, close | float | Preço OHLC |
| target_price | float | Preço esperado D+1 14:00 |
| **Indicadores (23)** | float | RSI, SMA, MACD, ATR, etc |
| predicted_price_xgb | float | Predição XGBoost |
| predicted_price_rf | float | Predição RandomForest |
| predicted_price_ensemble | float | Predição Ensemble (média) |
| confidence_pct | float | Confiança 0-100% |
| ensemble_direction | string | UP / DOWN |
| refined_direction | string | UP / DOWN (após Decision Tree) |
| refinement_score | float | Qualidade do refinamento |
| predicted_pips | float | Pips preditos |
| actual_pips | float | Pips reais |
| error_pips | float | Diferença |

---

## 🎯 Verificação Pós-Setup

### 1. Verificar carregamento de dados
```bash
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data/AUDUSD_M15_202401012200_202605222015.csv', sep='\t', skiprows=1)
print(f"Linhas: {len(df)}")
print(f"Colunas: {df.columns.tolist()}")
print(df.head())
EOF
```

### 2. Verificar indicadores
```bash
python3 << 'EOF'
from indicators import calculate_all_indicators, get_model_features
features = get_model_features()
print(f"Features: {len(features)}")
print(features)
EOF
```

### 3. Verificar outputs
```bash
ls -lh results/
wc -l results/backtest_AUDUSD_DETAILED.csv
head -5 results/ACTIONABLE_SIGNALS_AUDUSD.csv
```

---

## 📊 Comparação de Performance Entre Ativos

### Template de Análise

```bash
python3 << 'EOF'
import pandas as pd

ativos = ['EURUSD', 'GBPUSD', 'AUDUSD']

for symbol in ativos:
    try:
        df = pd.read_csv(f'results/backtest_{symbol}_DETAILED.csv')
        
        wins = (df['actual_pips'] > 0).sum()
        win_rate = wins / len(df) * 100
        total_pips = df['actual_pips'].sum()
        
        print(f"\n{symbol}:")
        print(f"  Win Rate: {win_rate:.2f}%")
        print(f"  Total Pips: {total_pips:+.2f}")
        print(f"  Avg Pips: {df['actual_pips'].mean():+.2f}")
    except:
        print(f"\n{symbol}: ❌ Não encontrado")
EOF
```

---

## 🔧 Troubleshooting

### Erro: "Arquivo não encontrado"
```bash
# Verificar arquivo existe
ls -la data/SEUATIVO_M15_*.csv

# Se não existe, exportar do MT5 novamente
```

### Erro: "Colunas não encontradas"
```bash
# Verificar formato do arquivo
head -3 data/SEUATIVO_M15_*.csv

# Deve ser TAB-SEPARATED, skiprows=1
```

### Erro: "Não há dados suficientes"
```bash
# Precisam de pelo menos ~1000 candles (mínimo 70% treino)
# Idealmente 59k+ candles como EURUSD/GBPUSD
```

### Predições muito ruins
```bash
# Pode ser:
# 1. Muito pouco histórico
# 2. Ativo muito volátil
# 3. Horários de abertura/fechamento impactando
# 4. Spread muito alto
```

---

## ⚙️ Customização de Parâmetros

Editar `config.json`:

### Alterar hyperparâmetros do XGBoost
```json
{
  "ml_params": {
    "xgboost": {
      "n_estimators": 300,
      "learning_rate": 0.03,
      "max_depth": 6,
      "subsample": 0.85,
      "colsample_bytree": 0.85
    }
  }
}
```

### Alterar split treino/teste
```json
{
  "backtest_params": {
    "train_ratio": 0.70,
    "test_ratio": 0.30
  }
}
```

### Alterar filtros de sinais
```json
{
  "signal_filters": {
    "confidence_threshold": 0.90,
    "confluence_min_score": 3,
    "refinement_threshold": 0.60
  }
}
```

---

## 📌 Checklist de Setup

- [ ] Dados em `data/SEUATIVO_M15_*.csv`
- [ ] `config.json` atualizado com novo ativo
- [ ] `"enabled": true` em config.json
- [ ] Arquivo é TAB-SEPARATED
- [ ] Arquivo tem >10k linhas
- [ ] Coluna header válida (date, time, open, high, low, close, tickvol, vol, spread)
- [ ] Executar `python3 src/run_full_pipeline.py SEUATIVO`
- [ ] Verificar outputs em `results/`
- [ ] Analisar CSV detalhado

---

## 🎓 Próximos Passos

1. **Setup AUDUSD** → Testar com dados disponíveis
2. **Otimizar hyperparâmetros** → Ajustar para cada ativo
3. **Análise de regime de mercado** → Qual funciona melhor em TREND vs RANGE
4. **Portfólio** → Combinar múltiplos ativos
5. **Live trading** → Gerar sinais em tempo real

---

## 📞 Suporte

**Problemas:**
- Verificar logs em terminal
- Consultar `GUIDE_ENHANCED_{ATIVO}.txt` após geração
- Revisar estrutura de dados em `config.json`

**Dúvidas:**
- Indicadores: Ver `src/indicators.py`
- Modelos: Ver `src/decision_tree_refiner.py`
- Pipeline: Ver `src/run_full_pipeline.py`

