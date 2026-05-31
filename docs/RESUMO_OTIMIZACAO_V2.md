# 📊 RESUMO: Otimização com Classificação (v2)

## O que fizemos:

### 1. **Problema do v1 (Regressão)**
- ❌ Modelo prediz **PREÇO** (1.1050, 1.1048)
- ❌ Decision Tree refina DEPOIS para direção
- ❌ Não otimizado para o objetivo real
- ⚠️ Win Rate variável: 54-78%

### 2. **Solução v2 (Classificação)**
- ✅ Modelo prediz diretamente **DIREÇÃO** (UP/DOWN)
- ✅ 7 algoritmos treinados como **classificadores**:
  - XGBoost Classifier
  - Random Forest Classifier
  - Gradient Boosting Classifier
  - Extra Trees Classifier
  - Logistic Regression
  - SVM (RBF kernel)
  - Voting Ensemble (soft voting)
- ✅ Ensemble robusto que entende direção
- 🎯 Esperado: Win Rate **≥ 65%** mais consistente

### 3. **Otimização com Grid Search**
- 🔍 **Hyperparameter Optimizer**: Testa 8 configurações diferentes
  - Agressivo (500 árvores, depth 4)
  - Conservador (200 árvores, depth 15)
  - Balanceado v1 e v2
  - Shallow (evita overfitting)
  - Deep (máxima capacidade)
  - HighLR / LowLR (learning rates diferentes)

- ⚡ **Turbo Optimizer**: Versão rápida com 6 configs
  - Light (100 estimadores)
  - Medium (200)
  - Heavy (300)
  - Shallow (depth 3)
  - Deep (depth 20)
  - Balanced

### 4. **Métricas de Avaliação**
Cada configuração é medida por:
- **Acurácia Direcional**: % de direções corretas
- **Win Rate**: % de sinais com pips > 0
- **Score Composto**: accuracy × 0.4 + win_rate × 0.6
  (Peso maior no Win Rate - métrica mais importante)

## Execução Atual:

### Fase 1: Treino Completo (v2)
```
🤖 Pipeline v2 para EURUSD
├─ Load dados (59.570 candles)
├─ Calculate direction target (47% UP, 53% DOWN)
├─ Split 70/30 (41.699 treino, 17.871 teste)
├─ Train 7 modelos com 23 features
├─ Predict + Voting Ensemble
├─ Apply Decision Tree refinement
└─ Salvar: backtest_EURUSD_DIRECTION_CLASSIFICATION.csv
```

### Fase 2: Otimização (Paralela)
```
⚡ Turbo Optimizer
├─ Testa 6 configs
├─ Light → Avg: 52.5% ✓ (primeira rodada)
├─ Medium → Testing...
└─ Salvar resultados em optimization_logs/
```

### Fase 3: Pipeline Paralelo (Aguardando)
```
Quando EURUSD terminar:
📊 Roda GBPUSD, EURAUD, EURJPY, NZDUSD, GOLD
├─ Em paralelo (máximo 6 processos simultâneos)
├─ Cada um com 70/30 split seu próprio
└─ Gera 6 CSVs de backtest
```

### Fase 4: Comparação e Análise
```
📈 Compara Regressão v1 vs Classificação v2
├─ Acurácia direcional
├─ Win Rate
├─ Total de pips
├─ Pips por sinal
└─ Salva em comparison_regression_vs_classification.json
```

## Arquivos Gerados:

### Resultados de Classificação (v2):
```
results/backtest_EURUSD_DIRECTION_CLASSIFICATION.csv
results/backtest_GBPUSD_DIRECTION_CLASSIFICATION.csv
results/backtest_EURAUD_DIRECTION_CLASSIFICATION.csv
results/backtest_EURJPY_DIRECTION_CLASSIFICATION.csv
results/backtest_NZDUSD_DIRECTION_CLASSIFICATION.csv
results/backtest_GOLD_DIRECTION_CLASSIFICATION.csv
```

Colunas:
- timestamp, close, target_price
- xgb_direction, rf_direction, gb_direction, et_direction, lr_direction, svm_direction
- ensemble_direction (Voting), actual_direction
- direction_correct, direction_accuracy
- actual_pips, result (WIN/LOSS)
- ensemble_proba, refinement_score, refined_direction

### Logs de Otimização:
```
optimization_logs/turbo_EURUSD_HHMMSS.csv
optimization_logs/turbo_GBPUSD_HHMMSS.csv
... (6 arquivos)

Colunas:
- config (nome da configuração)
- xgb_acc, rf_acc, gb_acc, ensemble_acc
- avg_acc (score final)
```

### Comparação Final:
```
results/comparison_regression_vs_classification.json

JSON com:
{
  "EURUSD": {
    "regression": {
      "signals": 7231,
      "accuracy": 66.77,
      "win_rate": 54.6,
      "total_pips": ...,
      "pips_per_signal": ...
    },
    "classification": {
      "signals": ...,
      "accuracy": ...,
      "win_rate": ...,
      ...
    }
  },
  ... (5 outros ativos)
}
```

## Análise Esperada:

### Cenário 1: Classificação MELHOR ✅
```
EURUSD:
  Regressão:       66.77% acc | 54.6% WR
  Classificação:   69.5% acc  | 62.3% WR ⬆️

Conclusão: Use v2! Ganho de ~7-8pp no Win Rate
```

### Cenário 2: Regressão Melhor ❌
```
EURUSD:
  Regressão:       66.77% acc | 54.6% WR
  Classificação:   65.2% acc  | 52.1% WR ⬇️

Conclusão: Manter v1 para esse ativo
```

### Cenário 3: Trade-off ⚠️
```
EURUSD:
  Regressão:       66.77% acc | 54.6% WR
  Classificação:   70.1% acc  | 54.2% WR

Conclusão: v2 melhor em acurácia, similar em WR
           Escolher baseado em risco/retorno
```

## Timeline Esperado:

```
⏳ EURUSD Pipeline v2:  ~10-15 minutos (em execução)
📊 Paralelo (5 ativos):  ~40-50 minutos (após EURUSD)
📈 Comparação:           ~2-3 minutos (rápida)
---
Total: ~1 hora para resultados completos
```

## Próximas Ações (após resultados):

1. **Se v2 VENCER**:
   - ✅ Atualizar configs baseado em otimização
   - ✅ Aplicar daily signal filter (1 ENTER/dia)
   - ✅ Gerar ANALYSIS_*_ENHANCED_v2.csv
   - ✅ Commit e backup para GitHub

2. **Se v1 VENCER**:
   - ✅ Manter v1 como padrão
   - ✅ Documentar por que regressão funcionou melhor
   - ✅ Investigar possíveis melhorias para v2

3. **Se EMPATE**:
   - ✅ Usar v2 (mais interpretável)
   - ✅ Fine-tune hiperparâmetros específicos
   - ✅ Considerar ensemble misto (v1 + v2)

---

**Status**: Aguardando EURUSD... 🚀
