# 📁 Estrutura do Workspace - Organizado

## 🎯 Pastas Principais

### 📊 `/results/` - **RESULTADOS DOS BACKTESTS**
- `backtest_results_23_indicators_final.csv` ← **PRINCIPAL** (23 indicadores, 5 pares)
- `backtest_per_pair_detailed.csv` ← Detalhado por par
- `backtest_EURUSD_detailed.csv` ← Específico EURUSD
- `RECOMENDACOES_AACAO.csv` ← Recomendações de ação
- `comparison_23_vs_26_indicators.csv` ← Comparação modelos
- `validation_chronological.csv` ← Hold-out validation (70/30)
- `validation_holdout.csv` ← Hold-out validation (por ano)
- **Outros CSVs:** resultados históricos

### 🤖 `/backtest/` - **SCRIPTS DE BACKTEST**
- `backtest_classification_optimized.py` ← Backtest 23 indicadores (PRODUÇÃO)
- `holdout_validation.py` ← Validação com hold-out
- `compare_models_regression_vs_classification.py` ← Comparação modelos

### 📈 `/analysis/` - **SCRIPTS DE ANÁLISE**
- `ANALYSIS_23_vs_26_INDICATORS.py` ← Análise comparativa
- `COMPARISON_FULL_vs_SIMPLIFIED.py` ← Full vs simplified
- `DEBUG_REPORT_FINAL.py` ← Relatório de debug
- `FINAL_REPORT_*.py` ← Relatórios finais (várias versões)
- `analyze_*.py` ← Análises específicas

### 📝 `/docs/` - **DOCUMENTAÇÃO E GUIAS**
- `COMECE_AQUI.md` ← Guia de início
- `GUIDE_NANO_EDITING.py` ← Como editar com nano
- `FINAL_SUMMARY.txt` ← Resumo executivo
- `README_PRODUCAO.txt` ← Guia de produção
- **Outros:** Análises, decisões, explicações

### 📦 `/archive/` - **SCRIPTS ANTIGOS/DESCARTADOS**
- Versões antigas de backtest
- Scripts experimentais
- Pode deletar se necessário

### 🔍 `/src/` - **CÓDIGO-FONTE PRINCIPAL**
- `backtest_classification_optimized.py` ← Backtest (link simbólico)
- `indicators.py` ← 23 indicadores técnicos (CORE)

### 🧪 `/tests/` - **TESTES E VALIDAÇÕES**
- Scripts de testes unitários

---

## ⚡ Arquivos Mais Importantes

### 1. **Para Avaliar Resultados:**
```bash
cat results/backtest_results_23_indicators_final.csv
cat results/backtest_EURUSD_detailed.csv
cat results/RECOMENDACOES_AACAO.csv
```

### 2. **Para Rodar Backtest:**
```bash
python3 backtest/backtest_classification_optimized.py
```

### 3. **Para Editar (nano):**
```bash
nano src/backtest_classification_optimized.py
nano src/indicators.py
```

### 4. **Para Validar:**
```bash
python3 backtest/holdout_validation.py
```

---

## 🚀 Próximas Ações

- [ ] Revisar `results/backtest_EURUSD_detailed.csv`
- [ ] Calcular ER e Aceleração (melhorias)
- [ ] Desabilitar EURJPY no backtest
- [ ] Implementar risk management
- [ ] Deploy em produção

---

**Última atualização:** 30/05/2026
**Modelo aprovado:** 23 indicadores
**Status:** ✅ Pronto para produção
