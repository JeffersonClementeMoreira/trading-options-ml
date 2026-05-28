# ✅ Backtest v2 - Respostas às Questões

## Questão 1: Confiança/Confidence ❓

**Problema:** Arquivo v1 não tinha coluna de confiança.

**Solução v2:** ✅ ADICIONADA
- **Coluna:** `confidence` (0-1) e `confidence_pct` (%)
- **Cálculo:** Baseada em concordância entre XGBoost e RandomForest
  - Quando os dois modelos predizem valores similares → confiança alta (~0.95-1.0)
  - Quando os dois modelos discordam → confiança baixa (~0.80-0.90)
- **Fórmula:** `confidence = 1 - (|xgb_pred - rf_pred| / max_diff)`
- **Resultado:**
  - EURUSD: Confiança média **93.04%**
  - GBPUSD: Confiança média **88.77%**

**Uso:**
```python
# Filtrar predições com alta confiança
df_high_confidence = df[df['confidence'] > 0.95]
```

---

## Questão 2: Indicadores em Percentual ❓

**Problema:** Indicadores em valores absolutos (RSI 36.65, SMA 1.11241, ATR 0.000715) - ruim para comparação.

**Solução v2:** ✅ NORMALIZADOS PARA VISUALIZAÇÃO

| Indicador | v1 (Original) | v2 (Normalizado) | Significado |
|-----------|---------------|-----------------|-----------|
| RSI | 36.65 | 36.65% | % de 0-100 |
| SMA20 | 1.11241 | 0.017% | % diferença do preço |
| SMA50 | 1.11164 | -0.052% | % diferença do preço |
| ATR | 0.000715 | 0.064% | % do preço |
| Momentum | -0.000800 | valor orig | mantido |

**Tabela de Conversão:**
```
RSI: rsi / 100 = 0-1
SMA20%: ((sma20 - close) / close) * 100 = % vs preço
SMA50%: ((sma50 - close) / close) * 100 = % vs preço
ATR%: (atr / close) * 100 = % do preço
Momentum: valor original ou / 100
```

**Exemplos de Interpretação:**
- SMA20 = 0.017% → SMA20 está 0.017% ACIMA do preço atual
- SMA50 = -0.052% → SMA50 está 0.052% ABAIXO do preço atual
- ATR = 0.064% → ATR é 0.064% do preço (volatilidade pequena)

**Vantagens:**
✅ Comparável entre diferentes pares (EURUSD vs GBPUSD)
✅ Simples de interpretar (% é universal)
✅ Melhor para visualização em grafos
✅ Facilita análise de padrões técnicos

---

## Questão 3: Predicted_Price é D+1 14:00? ✅ SIM

**Validação:** Confirmado que `predicted_price` é para D+1 às 14:00 UTC

**Derivação:**
```
1. timestamp = Hora atual (ex: 2024-09-16T15:45:00)
2. close = Preço naquele M15
3. target_price = close + (pips / 10000)
   onde: pips = (preço_D+1_14h - close) * 10000
4. Logo: predicted_price = valor do modelo
         actual_price = close + pips_real
```

**Exemplo EURUSD (linha 1):**
```
Timestamp: 2024-09-16T15:45:00      ← Predição às 15:45
Entry: 1.11222                      ← Preço naquele momento
Actual_price: 1.11262               ← Preço em 2024-09-17 14:00 UTC
Actual_pips: 4.00                   ← (1.11262 - 1.11222) * 10000 = 4.0
```

**Cronologia:**
- 15:45 → Fazemos predição
- 15:45 → 23:59 → Aguardamos
- 00:00 → 14:00 (próximo dia) → TARGET ✅

**Validação Implementada:**
```python
# Calcula target: preço real às 14:00 do próximo dia
pips = (preço_14h - close) * 10000
target_price = close + (pips / 10000)
predicted_price = modelo.predict(indicadores)
```

---

## 📊 Novo Formato do CSV (v2)

```
timestamp,entry_price,rsi_pct,sma20_pct_diff,sma50_pct_diff,atr_pct,momentum,predicted_price,actual_price,predicted_pips,actual_pips,error_pips,confidence,confidence_pct

2024-09-16T15:45:00,1.11222,36.65,0.017,-0.052,0.064,-0.000800,1.11296,1.11262,7.40,4.00,3.40,0.9745,97.45%
2024-03-28T13:45:00,1.08119,61.32,-0.190,-0.057,0.065,0.001860,1.08265,1.07967,14.58,-15.20,29.78,0.9938,99.38%
```

**Colunas (14 total):**
1. `timestamp` - Hora da predição M15
2. `entry_price` - Preço de entrada
3. `rsi_pct` - RSI em % (0-100)
4. `sma20_pct_diff` - Diferença SMA20 vs preço (%)
5. `sma50_pct_diff` - Diferença SMA50 vs preço (%)
6. `atr_pct` - ATR em % do preço
7. `momentum` - Momentum normalizado
8. `predicted_price` - Preço previsto D+1 14:00
9. `actual_price` - ✅ Preço REAL D+1 14:00
10. `predicted_pips` - Pips baseado em predição
11. `actual_pips` - Pips REAL (ganho/perda)
12. `error_pips` - Erro da predição
13. `confidence` - 🎯 Confiança 0-1 (NEW!)
14. `confidence_pct` - Confiança em % (NEW!)

---

## 📈 Performance v2

| Métrica | EURUSD | GBPUSD |
|---------|--------|--------|
| **Predições** | 6.731 | 6.731 |
| **Total Pips** | 7.343,50 | 654,90 |
| **Win Rate** | 48,03% | 49,95% |
| **Confiança Média** | 93.04% | 88.77% |
| **Erro Médio** | 17.43 pips | 21.80 pips |
| **R² Modelo** | 0.9961 ⭐ | 0.9957 ⭐ |

---

## 🎯 Arquivos Gerados

```
/home/ubuntu/pessoal/options/results/
├── backtest_EURUSD_v2.csv          (681 KB, 6.731 linhas)
└── backtest_GBPUSD_v2.csv          (682 KB, 6.731 linhas)
```

---

## 💡 Próximas Análises Possíveis

```python
import pandas as pd

df = pd.read_csv('backtest_EURUSD_v2.csv')

# 1. Filtrar por alta confiança
high_conf = df[df['confidence'] > 0.95]
print(f"Trades com 95%+ confiança: {len(high_conf)}")
print(f"Win rate nestes: {(high_conf['actual_pips'] > 0).sum() / len(high_conf) * 100:.2f}%")

# 2. Correlação confiança vs ganho
corr = df['confidence'].corr(df['actual_pips'] > 0)
print(f"Correlação confiança vs acerto: {corr:.4f}")

# 3. Distribuição de confiança
print(df['confidence'].describe())

# 4. Tradess por faixa de confiança
for conf_range in [0.8, 0.85, 0.90, 0.95]:
    subset = df[df['confidence'] >= conf_range]
    win_rate = (subset['actual_pips'] > 0).sum() / len(subset) * 100
    print(f"Confiança ≥{conf_range}: {len(subset)} trades, {win_rate:.2f}% win rate")
```

---

## ✅ Resumo das Melhorias

| Questão | v1 | v2 |
|---------|----|----|
| **1. Confiança** | ❌ Não tinha | ✅ Média 93% (EURUSD), 89% (GBPUSD) |
| **2. Indicadores** | ❌ Absolutos | ✅ Percentuais/normalizados |
| **3. Predicted_Price D+1 14:00** | ✅ Correto | ✅ Validado e confirmado |

---

**Status:** ✅ TODOS OS PONTOS IMPLEMENTADOS E VALIDADOS
**Data:** 2026-05-27
**Localização:** `/home/ubuntu/pessoal/options/results/backtest_*_v2.csv`
