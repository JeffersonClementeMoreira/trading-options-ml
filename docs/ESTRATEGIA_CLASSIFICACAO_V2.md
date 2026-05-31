# 📊 Estratégia: Classificação de Direção (v2)

## Problema do Modelo Anterior (Regressão)

### ❌ O que estava errado:
```
Modelo Antigo (Regressão):
  1. XGBoost prediz preço → 1.1050
  2. RandomForest prediz preço → 1.1048
  3. Ensemble prediz preço → 1.1049
  4. Decision Tree refina para DIREÇÃO
  ❌ Problema: modelo principal não entende o objetivo real
  ❌ Resultado: predições de preço imprecisas
```

## Novo Modelo (Classificação de Direção)

### ✅ O que muda:
```
Modelo Novo (Classificação):
  1. XGBClassifier aprende DIREÇÃO (UP/DOWN)
  2. RandomForestClassifier aprende DIREÇÃO (UP/DOWN)
  3. GradientBoostingClassifier aprende DIREÇÃO (UP/DOWN)
  4. ExtraTreesClassifier aprende DIREÇÃO (UP/DOWN)
  5. LogisticRegression aprende DIREÇÃO (UP/DOWN)
  6. SVM aprende DIREÇÃO (UP/DOWN)
  7. VotingClassifier combina todos (soft voting)
  ✅ Benefício: Ensemble entende direto o problema
  ✅ Resultado: predições de direção muito mais precisas
```

## Critério de Acerto (Direção)

```
WIN: A previsão ACERTOU a direção

  Caso 1: Previsão = UP e Preço subiu (target > close)
    ✅ ACERTOU → WIN
  
  Caso 2: Previsão = DOWN e Preço desceu (target < close)
    ✅ ACERTOU → WIN

LOSS: A previsão ERROU a direção

  Caso 3: Previsão = UP mas Preço desceu (target < close)
    ❌ ERROU → LOSS
  
  Caso 4: Previsão = DOWN mas Preço subiu (target > close)
    ❌ ERROU → LOSS
```

## Arquitetura do Ensemble v2

```
┌─────────────────────────────────────┐
│      Dados de Treinamento           │
│  (23 indicadores técnicos)          │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │  Target: UP/DOWN │
    │  (Direção real)  │
    └────────┬────────┘
             │
   ┌─────────┴─────────────────────────────────┐
   │                                           │
   │  6 Classificadores independentes          │
   │  (Soft Voting)                            │
   │                                           │
   ├─ XGBoost Classifier                       │
   ├─ Random Forest Classifier                 │
   ├─ Gradient Boosting Classifier             │
   ├─ Extra Trees Classifier                   │
   ├─ Logistic Regression                      │
   └─ SVM (RBF kernel)                         │
   │
   └─► Voting Ensemble (Média de Probabilidades)
       │
       ├─ Probabilidade de UP: avg(P1, P2, ..., P6)
       ├─ Previsão Final: P_UP > 0.5 ? UP : DOWN
       │
       └─► Decision Tree Refinement
           (Encontra os melhores indicadores)
```

## Esperado vs Resultado Anterior

### Esperado (v2):
- ✅ Acurácia Direcional: **≥ 65%** (modelo aprendeu direção)
- ✅ Win Rate: **≥ 60%** (mais sinais corretos)
- ✅ Probabilidades bem calibradas

### Resultado Anterior (v1 - Regressão):
- ❌ Acurácia Direcional: 66.77% (alto, mas modelo não otimizado para isso)
- ⚠️ Win Rate: 54-78% (muito variável entre ativos)
- ⚠️ Ensemble foca em preço, não direção

## Vantagens da Classificação

| Aspecto | Regressão (v1) | Classificação (v2) |
|---------|-----------------|-------------------|
| **Objetivo** | Prever preço exato | Prever se sobe ou desce |
| **Função Perda** | MSE (erro quadrado) | Cross-entropy (log loss) |
| **Output** | Valor contínuo | Probabilidade (0-1) |
| **Interpretação** | "Preço será 1.1050" | "87% de chance de UP" |
| **Robustez** | Afetado por outliers | Robusta a extremos |
| **Calibração** | Ruim | Ótima |
| **Trade-off** | Preço preciso, direção errada | Direção precisa |

## Métricas de Comparação

```
Comparação (Novo vs Antigo):
┌──────────────────┬──────────────┬──────────────┬──────────┐
│ Métrica          │ Regressão v1 │ Classificação│ Esperado │
├──────────────────┼──────────────┼──────────────┼──────────┤
│ Acurácia Dir.    │    66.77%    │     ?        │   ≥70%   │
│ Win Rate (ativo) │   54-78%     │     ?        │   ≥65%   │
│ Sinais/ano       │    ~1,900    │    ~1,900    │ Mesmo    │
│ Pips/sinal       │   Variable   │     ?        │  ↑ Maior │
└──────────────────┴──────────────┴──────────────┴──────────┘
```

## Plano de Testes

1. ✅ Treinar modelo v2 (classificação)
2. ⏳ Rodar backtest para EURUSD
3. ⏳ Comparar com v1 (regressão)
4. ⏳ Expandir para 6 ativos
5. ⏳ Escolher melhor versão
6. ⏳ Fazer backup e documentar

---

**Status**: Treinando 7 modelos em paralelo... 🚀
