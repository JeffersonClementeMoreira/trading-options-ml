# ✅ BACKTEST CHRONOLOGICAL - ORDEM MANTIDA + INDICADORES + PREDIÇÕES

## Problema Identificado
Versão anterior embaralhava dados com `train_test_split()` aleatório, causando preços em ordem não-cronológica:
```
2024 → 2025 → 2024 → 2025 (ERRADO!)
```

## Solução Implementada

### 1️⃣ Split Temporal (Não Aleatório)
```python
# ANTES (ERRADO):
X_train, X_test = train_test_split(X, test_size=0.30, random_state=42)  # Embaralha!

# DEPOIS (CORRETO):
split_idx = int(len(data) * 0.70)
X_train = X[:split_idx]      # Primeiros 70% = dados históricos
X_test = X[split_idx:]       # Últimos 30% = dados recentes
```

### 2️⃣ Ordem Cronológica Mantida
```
ENTRADA:  59.569 linhas (2024-01-01 → 2026-05-22) ✅ Cronológicas
   ↓
SAÍDA:    59.569 linhas (mesma ordem!) ✅ Chronological
   ├─ 41.698 linhas (70%) - Sem predição (usadas para treino)
   └─ 17.871 linhas (30%) - Com predição (teste/validação)
```

### 3️⃣ Indicadores Calculados

Todos os 12 indicadores foram calculados para **TODAS** as linhas:

| Indicador | Cálculo | Valores | Status |
|-----------|---------|---------|--------|
| RSI | 14-período | 59.556 valores | ✅ Completo |
| SMA20 | Média 20 candles | 59.550 valores | ✅ Completo |
| SMA50 | Média 50 candles | 59.520 valores | ✅ Completo |
| MACD | EMA12 - EMA26 | 59.569 valores | ✅ Completo |
| ATR | True Range 14 | 59.555 valores | ✅ Completo |
| Momentum | Diferença 14 | 59.555 valores | ✅ Completo |
| Price > SMA20 | Binário | 59.569 valores | ✅ Binário |
| Price > SMA50 | Binário | 59.569 valores | ✅ Binário |
| RSI Oversold | RSI < 30 | 59.569 valores | ✅ Binário |
| RSI Overbought | RSI > 70 | 59.569 valores | ✅ Binário |
| MACD Positive | MACD > 0 | 59.569 valores | ✅ Binário |
| Momentum Positive | Mom > 0 | 59.569 valores | ✅ Binário |

## Estrutura da Saída

### Arquivos Gerados
```
/results/
├── backtest_EURUSD_chronological.csv    (59.569 linhas × 23 colunas)
└── backtest_GBPUSD_chronological.csv    (59.567 linhas × 23 colunas)
```

### Colunas (23 total)

#### 1-2: Timestamp + Entry Price
1. `timestamp` - Data/hora M15
2. `close` - Preço de entrada

#### 3-14: Indicadores Técnicos
3. `rsi` - RSI (0-100)
4. `sma20` - Média móvel 20 candles
5. `sma50` - Média móvel 50 candles
6. `macd` - MACD
7. `atr` - Average True Range
8. `momentum` - Momentum 14-períodos
9. `price_above_sma20` - Binário
10. `price_above_sma50` - Binário
11. `rsi_oversold` - Binário (RSI < 30)
12. `rsi_overbought` - Binário (RSI > 70)
13. `macd_positive` - Binário
14. `momentum_positive` - Binário

#### 15-17: Predições (3 modelos)
15. `predicted_price_xgb` - Predição XGBoost
16. `predicted_price_rf` - Predição RandomForest
17. `predicted_price_ensemble` - Predição média (XGB + RF) / 2

#### 18-23: Análise de Performance
18. `confidence` - Confiança 0-1 (baseada em concordância XGB vs RF)
19. `confidence_pct` - Confiança em percentual (0-100%)
20. `actual_price` - Preço real (target)
21. `predicted_pips_ensemble` - Pips previsto
22. `actual_pips` - Pips real (ganho/perda)
23. `error_pips` - |Pips real - Pips previsto|

## Dados de Treino vs Predição

### EURUSD
```
Entrada:        59.569 candles (2024-01-01 22:15 → 2026-05-22 20:15)
Treino:         41.698 candles (70%) - Histórico
Predição:       17.871 candles (30%) - Recente

Período Treino: 2024-01-01 → 2025-09-03
Período Teste:  2025-09-03 → 2026-05-22
```

### GBPUSD
```
Entrada:        59.567 candles
Treino:         41.696 candles (70%)
Predição:       17.871 candles (30%)

Período Treino: 2024-01-01 → 2025-09-03
Período Teste:  2025-09-03 → 2026-05-22
```

## Performance

### EURUSD (30% - Teste)
```
Total Pips:        -19.50
Win Rate:          49.31% (8.813 / 17.871)
Confiança Média:   92.82%
MAE Modelo:        12.11 pips
R²:                0.9182
```

### GBPUSD (30% - Teste)
```
Total Pips:        +76.50
Win Rate:          49.36% (8.822 / 17.871)
Confiança Média:   93.55%
MAE Modelo:        6.60 pips
R²:                0.9951
```

## Validação ✅

### Ordem Cronológica
- ✅ Primeira linha: 2024-01-01 22:15:00
- ✅ Última linha: 2026-05-22 20:15:00
- ✅ Timestamps em ordem ascendente contínua
- ✅ **NÃO embaralhado**

### Linhas
- ✅ EURUSD: 59.569 linhas entrada → 59.569 linhas saída
- ✅ GBPUSD: 59.567 linhas entrada → 59.567 linhas saída

### Indicadores
- ✅ 12 indicadores calculados para TODAS as linhas
- ✅ Primeiras ~50 linhas com NaN (aquecimento SMA/RSI)
- ✅ Resto completamente preenchido

### Predições
- ✅ 70% primeiras linhas: NaN (não treinado)
- ✅ 30% últimas linhas: Valores numéricos (predições)
- ✅ Confiança varia 0.70 até 0.99 (baseada em concordância XGB vs RF)

## Como Usar

### Python - Carregar e Analisar
```python
import pandas as pd

df = pd.read_csv('backtest_EURUSD_chronological.csv')

# Dados de treino (sem predições)
df_train = df[df['predicted_price_ensemble'].isna()]

# Dados de teste (com predições)
df_test = df[df['predicted_price_ensemble'].notna()]

# Filtrar por confiança alta
df_high_conf = df_test[df_test['confidence'] > 0.95]

# Análise
wins = (df_test['actual_pips'] > 0).sum()
losses = (df_test['actual_pips'] < 0).sum()
win_rate = wins / len(df_test) * 100

print(f"Win Rate: {win_rate:.2f}%")
```

### Verificar Ordem
```python
import pandas as pd

df = pd.read_csv('backtest_EURUSD_chronological.csv')
timestamps = pd.to_datetime(df['timestamp'])
is_ordered = (timestamps.diff().dropna() >= pd.Timedelta(0)).all()

print(f"Ordem cronológica: {'✅ SIM' if is_ordered else '❌ NÃO'}")
```

### Comparar Modelos
```python
# Ver concordância entre XGBoost e RandomForest
df['diff_xgb_rf'] = abs(df['predicted_price_xgb'] - df['predicted_price_rf'])
df['mean_diff'] = df['diff_xgb_rf'].mean()

# Linhas onde modelos discordam muito
df_low_conf = df[df['confidence'] < 0.80]
```

## 📊 Diferenças vs Versão Anterior

| Aspecto | Anterior | Chronological |
|---------|----------|---------------|
| **Ordem** | ❌ Embaralhada | ✅ Mantida |
| **Linhas** | 30% (apenas teste) | ✅ 100% (tudo) |
| **Indicadores** | Somente teste | ✅ Todos calculados |
| **Modelos** | Ensemble só | ✅ XGB, RF, Ensemble |
| **Confiança** | Média global | ✅ Por predição |
| **NaN** | Nenhum | ✅ Nos 70% treino |

## ⚠️ Notas Importantes

1. **Primeiras ~50 linhas**: NaN em indicadores (aquecimento SMA/RSI)
2. **Primeiros 41.698 linhas**: NaN em predições (dados de treino)
3. **Últimas 17.871 linhas**: Predições completas (dados de teste)
4. **Confiança**: Calculada como `1 - (|xgb - rf| / max_diff)`
   - Valor alto = modelos concordam (mais confiável)
   - Valor baixo = modelos discordam (menos confiável)

## 📁 Arquivos

```
/home/ubuntu/pessoal/options/results/
├── backtest_EURUSD_chronological.csv
└── backtest_GBPUSD_chronological.csv
```

Ambos prontos para análise com ordem cronológica mantida!

---
**Gerado em:** 2026-05-27
**Script:** `/home/ubuntu/pessoal/options/src/backtest_chronological.py`
**Status:** ✅ PRODUÇÃO
