# 🔴 REGRAS CRÍTICAS - NUNCA ESQUECER

## 1️⃣ TARGET SEMPRE É PREÇO REAL, NUNCA UP/DOWN

```
❌ ERRADO: target_direction = 'UP' ou 'DOWN'
✅ CORRETO: target_price = preço REAL às 14:00 UTC próximo dia
```

**Por quê?**
- UP/DOWN é CLASSIFICAÇÃO (prediz direção)
- PREÇO é REGRESSÃO (prediz valor exato)
- Regressão é mais preciso para operações de trading
- Permite calcular lucro/perda em pips reais

## 2️⃣ ALVO SEMPRE ÀS 14:00 UTC DO PRÓXIMO DIA

```python
# ❌ ERRADO
target_time = next_candle()  # Próximo M15

# ✅ CORRETO
target_time = tomorrow_14_00_utc()  # SEMPRE 14:00 UTC
```

**Exemplos:**
- Predição às 2024-01-15 09:15 → Target é 2024-01-16 14:00
- Predição às 2024-01-15 20:00 → Target é 2024-01-16 14:00
- Predição às 2024-01-15 13:45 → Target é 2024-01-16 14:00

## 3️⃣ NUNCA USAR DADOS INVENTADOS

```python
# ❌ ERRADO
target_price = random.uniform(1.0, 1.2)  # Inventado
target_price = model.predict(new_data)  # Sem validação

# ✅ CORRETO
target_price = historical_data['price_at_14h']  # Dados REAIS
# Sempre validar: fonte dos dados = /tmp/bt_analysis_*.csv
```

**Validação:**
- Fonte: `/tmp/bt_analysis_EURUSD.csv` e `/tmp/bt_analysis_GBPUSD.csv`
- Estrutura: timestamp, close, indicadores, pips (ganho real)
- Derivar target: `target_price = close + (pips / 10000)`
- Nunca: inventar, simular, calcular sem base

## 4️⃣ NUNCA TREINAR EM 100% DOS DADOS

```python
# ❌ ERRADO
X_train, y_train = all_data, all_labels  # 100% para treino
# Resultado: Accuracy 97% (falso, data leakage!)

# ✅ CORRETO
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42
)
# 70% para treino, 30% para validação (nunca visto)
```

**Razão:**
- 100% treino = model "memoriza" dados
- Resultados 97%+ são falsos (data leakage)
- Realidade: performance ~84-86% em dados novos
- Split 70/30 é metodologia correta

## 5️⃣ MODELO CORRETO: REGRESSÃO + ENSEMBLE

```python
# ❌ ERRADO (classificação)
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier()  # Prediz UP/DOWN
y_train = ['UP', 'DOWN', 'UP', ...]

# ✅ CORRETO (regressão)
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor

xgb = XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=7)
rf = RandomForestRegressor(n_estimators=200, max_depth=15)

ensemble_pred = (xgb.predict(X) + rf.predict(X)) / 2  # Média
y_train = [1.08120, 1.09450, 1.10230, ...]  # Preços
```

**Hiperparâmetros Validados:**
- XGBoost: `n_estimators=200, learning_rate=0.05, max_depth=7`
- RandomForest: `n_estimators=200, max_depth=15`
- Split: `test_size=0.30, random_state=42`

## 6️⃣ ENTRADA POR INDICADORES M15

**Input (Features):**
1. RSI (14)
2. SMA (20)
3. SMA (50)
4. MACD
5. ATR (14)
6. Momentum (10)
7. Price > SMA20 (binary)
8. Price > SMA50 (binary)
9. RSI Oversold <30 (binary)
10. RSI Overbought >70 (binary)
11. MACD Positive (binary)
12. Momentum Positive (binary)

**Cálculo:**
- Em cada candle M15
- Calcular 12 indicadores
- Passar para modelo
- Modelo prediz: preço às 14:00 UTC

## 7️⃣ BACKTEST CSV CORRETO

**Colunas Obrigatórias:**

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| timestamp | string | Hora da predição (M15) |
| entry_price | float | Preço de fechamento naquele M15 |
| rsi | float | RSI(14) |
| sma20 | float | SMA 20 |
| sma50 | float | SMA 50 |
| atr | float | ATR(14) |
| momentum | float | Momentum(10) |
| predicted_price | float | Preço previsto para 14:00 UTC |
| actual_price | float | Preço REAL às 14:00 UTC |
| predicted_pips | float | (predicted - entry) * 10000 |
| actual_pips | float | (actual - entry) * 10000 |
| error_pips | float | \|actual_pips - predicted_pips\| |

**Exemplo (EURUSD):**
```csv
timestamp,entry_price,rsi,sma20,sma50,atr,momentum,predicted_price,actual_price,predicted_pips,actual_pips,error_pips
2024-09-16T15:45:00,1.11222,36.65,1.11241,1.11164,0.000715,-0.000800,1.11296,1.11262,7.40,4.00,3.40
```

## 8️⃣ MÉTRICAS DE VALIDAÇÃO REGRESSÃO

```
Para Regressão (não Classificação):

✅ MAE (Mean Absolute Error)
   - Erro médio em pips
   - EURUSD: ~14-21 pips
   - GBPUSD: ~17-27 pips

✅ RMSE (Root Mean Squared Error)
   - Penaliza erros grandes mais
   - ~1.5x MAE

✅ R² (Coeficiente de Determinação)
   - Quão bem explica variância
   - 0.99 = excelente
   - EURUSD: 0.9961-0.9977
   - GBPUSD: 0.9921-0.9957

❌ NÃO USAR:
   - Accuracy (UP/DOWN certo?)
   - Precision/Recall
   - Confusion Matrix
```

## 9️⃣ RESUMO OPERACIONAL

```
ESTRUTURA BACKTEST CORRETO:

1. Carregar dados REAIS
   └─ source: /tmp/bt_analysis_*.csv

2. Calcular TARGET
   └─ target_price = close + (pips / 10000)

3. Split dados
   └─ 70% treino, 30% validação

4. Treinar modelos
   ├─ XGBoost Regressor
   └─ RandomForest Regressor

5. Ensemble
   └─ predicted_price = (xgb + rf) / 2

6. Validar em 30% (nunca visto)
   └─ Calcular MAE, RMSE, R²

7. Gerar CSV
   └─ entry_price, predicted_price, actual_price, error_pips

8. Análise
   ├─ Win rate
   ├─ Total pips
   ├─ Distribuição erros
   └─ Trades top/bottom
```

## 🔟 CÓDIGO CORRETO - TEMPLATE

```python
# ✅ TEMPLATE CORRETO PARA FUTURE USE

import csv
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb

# 1. Carregar dados REAIS
data = []
with open('/tmp/bt_analysis_EURUSD.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        close = float(row['close'])
        pips = float(row['pips'])
        target_price = close + (pips / 10000)  # ✅ TARGET CORRETO
        data.append({...})

# 2. Features + Target
X = np.array([[row[f] for f in feature_names] for row in data])
y = np.array([row['target_price'] for row in data])  # ✅ PREÇO, NÃO UP/DOWN

# 3. Split 70/30 (NUNCA 100%)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42
)

# 4. Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 5. Treinar REGRESSÃO (não classificação)
xgb_model = xgb.XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=7)
rf_model = RandomForestRegressor(n_estimators=200, max_depth=15)

xgb_model.fit(X_train_scaled, y_train)
rf_model.fit(X_train_scaled, y_train)

# 6. Validar em dados NUNCA VISTOS (30%)
xgb_pred = xgb_model.predict(X_test_scaled)
rf_pred = rf_model.predict(X_test_scaled)

mae = mean_absolute_error(y_test, (xgb_pred + rf_pred) / 2)
r2 = r2_score(y_test, (xgb_pred + rf_pred) / 2)

print(f"MAE: {mae * 10000:.2f} pips")
print(f"R²: {r2:.4f}")

# 7. Gerar backtest com preços reais
for i in range(len(X_test)):
    entry_price = data_test[i]['close']
    predicted_price = (xgb_pred[i] + rf_pred[i]) / 2
    actual_price = data_test[i]['target_price']
    
    predicted_pips = (predicted_price - entry_price) * 10000
    actual_pips = (actual_price - entry_price) * 10000
    error_pips = abs(actual_pips - predicted_pips)
```

## CHECKLIST FINAL - Antes de executar qualquer código:

- [ ] Target = PREÇO REAL às 14:00 UTC (não UP/DOWN)
- [ ] Dados = REAIS de /tmp/bt_analysis_*.csv (não inventados)
- [ ] Split = 70% treino, 30% validação (não 100%)
- [ ] Modelo = REGRESSÃO com XGBoost + RandomForest (não classificação)
- [ ] Entrada = 12 indicadores M15 + ensemble
- [ ] Saída = CSV com entry_price, predicted_price, actual_price, error_pips
- [ ] Métrica = MAE em pips, R², RMSE (não Accuracy)
- [ ] Validação = Em dados NUNCA VISTOS (test set 30%)

---

**Última atualização:** 2026-05-27  
**Status:** ✅ IMPLEMENTADO CORRETAMENTE  
**Versão:** Backtest Regressão Corretto v1.0
