# 📁 Estrutura do Projeto Options

```
/home/ubuntu/pessoal/options/
├── 📄 REGRAS_CRITICAS.md (docs/)    ← Salvo em docs/
├── 📁 data/                         ← Dados de entrada
│   ├── EURUSD_M15_...csv           (dados brutos históricos)
│   ├── GBPUSD_M15_...csv           (dados brutos históricos)
│   ├── bt_analysis_EURUSD.csv      (dados processados com indicadores)
│   └── bt_analysis_GBPUSD.csv      (dados processados com indicadores)
│
├── 📁 src/                          ← Scripts Python
│   ├── backtest_regressor_correct.py     (🔮 PRINCIPAL - backtest regressão)
│   ├── analyze_backtest_regressor.py     (📊 análise detalhada)
│   ├── train_*.py                       (treinamento modelos)
│   ├── *.py                             (outros scripts)
│   └── __init__.py
│
├── 📁 models/                       ← Modelos treinados (.pkl)
│   ├── ml_ensemble_eurusd.pkl      (Ensemble final EURUSD)
│   ├── ml_ensemble_gbpusd.pkl      (Ensemble final GBPUSD)
│   ├── ml_scaler_eurusd.pkl        (StandardScaler EURUSD)
│   ├── ml_scaler_gbpusd.pkl        (StandardScaler GBPUSD)
│   ├── xgboost_EURUSD.pkl
│   ├── xgboost_GBPUSD.pkl
│   ├── nextday_*.pkl               (modelos dia seguinte)
│   └── ... (outros modelos)
│
├── 📁 results/                      ← 🎯 RESULTADOS BACKTEST
│   ├── backtest_EURUSD_regressor_correct.csv      (6.731 predições)
│   └── backtest_GBPUSD_regressor_correct.csv      (6.731 predições)
│
├── 📁 docs/                         ← Documentação
│   └── REGRAS_CRITICAS.md           (NUNCA ESQUECER!)
│
├── 📁 bin/                          ← Scripts shell executáveis
│   ├── start_system.sh
│   ├── train_models_menu.sh
│   ├── backtest_master.sh
│   └── ...
│
└── 📄 README.md                     ← Documentação principal
```

---

## 🎯 Arquivos Principais

### 📊 Backtest Results
```
results/
├── backtest_EURUSD_regressor_correct.csv  (681 KB, 6.731 linhas)
│   └─ Colunas: timestamp, entry_price, rsi, sma20, sma50, atr, momentum, 
│              predicted_price, actual_price, predicted_pips, actual_pips, error_pips
│
└── backtest_GBPUSD_regressor_correct.csv  (682 KB, 6.731 linhas)
   └─ Idem EURUSD
```

**Como usar:**
```bash
# Abrir backtest
cd /home/ubuntu/pessoal/options
cat results/backtest_EURUSD_regressor_correct.csv | head -20

# Analisar em Python
python3 src/analyze_backtest_regressor.py

# Copiar para análise
cp results/backtest_*.csv ~/Desktop/
```

---

### 🤖 Modelos Treinados
```
models/
├── ml_ensemble_eurusd.pkl         ← Ensemble (XGBoost + RF) EURUSD
├── ml_ensemble_gbpusd.pkl         ← Ensemble (XGBoost + RF) GBPUSD
├── ml_scaler_eurusd.pkl           ← StandardScaler EURUSD
├── ml_scaler_gbpusd.pkl           ← StandardScaler GBPUSD
└── ... (outros modelos)
```

**Como carregar:**
```python
import pickle

# Carregar modelo
with open('models/ml_ensemble_eurusd.pkl', 'rb') as f:
    model = pickle.load(f)

# Usar
predictions = model.predict(X)
```

---

### 📁 Dados
```
data/
├── EURUSD_M15_...csv              ← Dados brutos (22.435 candles)
├── GBPUSD_M15_...csv              ← Dados brutos (22.434 candles)
├── bt_analysis_EURUSD.csv         ← Com indicadores (22.435 candles)
└── bt_analysis_GBPUSD.csv         ← Com indicadores (22.434 candles)
```

---

### 🐍 Scripts Python
```
src/

✨ PRINCIPAIS:
├── backtest_regressor_correct.py       (🔮 EXECUTAR: rodar backtest regressão)
└── analyze_backtest_regressor.py       (📊 EXECUTAR: analisar resultados)

🔧 SUPORTE:
├── train_ensemble_final.py             (treinar modelos ensemble)
├── train_xgboost_model.py              (treinar XGBoost)
└── ... (outros scripts)
```

---

## 🚀 Como Usar

### 1. Rodar Backtest
```bash
cd /home/ubuntu/pessoal/options
python3 src/backtest_regressor_correct.py
```

**Output:**
- `results/backtest_EURUSD_regressor_correct.csv`
- `results/backtest_GBPUSD_regressor_correct.csv`

### 2. Analisar Resultados
```bash
python3 src/analyze_backtest_regressor.py
```

**Output:** Estatísticas, melhores/piores trades, distribuição de ganhos

### 3. Exportar para Análise
```bash
# Copiar para home
cp results/backtest_*.csv ~

# Copiar para Excel/Power BI
cp results/backtest_*.csv ~/Desktop/
```

---

## 📊 Estrutura do CSV (12 Colunas)

| # | Coluna | Tipo | Descrição |
|---|--------|------|-----------|
| 1 | `timestamp` | string | Hora da predição M15 |
| 2 | `entry_price` | float | Preço de entrada |
| 3 | `rsi` | float | RSI(14) |
| 4 | `sma20` | float | SMA 20 |
| 5 | `sma50` | float | SMA 50 |
| 6 | `atr` | float | ATR(14) |
| 7 | `momentum` | float | Momentum(10) |
| 8 | `predicted_price` | float | 🔮 Preço previsto para 14:00 UTC |
| 9 | `actual_price` | float | ✅ Preço REAL às 14:00 UTC |
| 10 | `predicted_pips` | float | Pips baseado em predição |
| 11 | `actual_pips` | float | **Pips REAIS (ganho/perda)** |
| 12 | `error_pips` | float | Erro da predição |

---

## ✅ Checklist - Regras Críticas

- ✅ TARGET = PREÇO REAL (não UP/DOWN)
- ✅ SEMPRE 14:00 UTC próximo dia
- ✅ DADOS REAIS de `/data/bt_analysis_*.csv`
- ✅ SPLIT 70/30 (sem data leakage)
- ✅ MODELO: Ensemble Regressão
- ✅ MÉTRICA: MAE, RMSE, R² (não Accuracy)
- ✅ 6.731 predições em dados NUNCA VISTOS

👉 Documentação completa: `docs/REGRAS_CRITICAS.md`

---

## 📈 Resultados Atuais

| Métrica | EURUSD | GBPUSD |
|---------|--------|--------|
| Predições | 6.731 | 6.731 |
| Total Pips | +7.343,50 | +654,90 |
| Win Rate | 48,03% | 49,95% |
| Erro Médio | 17,43 pips | 21,80 pips |
| R² Modelo | 0,9977 ⭐ | 0,9957 ⭐ |

---

## 🔧 Referência Rápida

```bash
# Localização dos CSVs de backtest
ls -lh /home/ubuntu/pessoal/options/results/

# Contar linhas
wc -l /home/ubuntu/pessoal/options/results/backtest_*.csv

# Ver primeiras linhas
head -5 /home/ubuntu/pessoal/options/results/backtest_EURUSD_regressor_correct.csv

# Análise rápida em Python
python3 -c "
import pandas as pd
df = pd.read_csv('/home/ubuntu/pessoal/options/results/backtest_EURUSD_regressor_correct.csv')
print(f'Total pips: {df[\"actual_pips\"].sum():.2f}')
print(f'Win rate: {(df[\"actual_pips\"] > 0).sum() / len(df) * 100:.2f}%')
"
```

---

**Última atualização:** 2026-05-27  
**Status:** ✅ Organizado e Pronto
