# CHANGELOG

Todas as mudanças notáveis neste projeto estão documentadas neste arquivo.

## [1.0.0] - 2026-05-28

### 🎉 RELEASE ESTÁVEL - UNIFICAÇÃO COMPLETA

#### ✅ Adicionado
- **Arquivo Unificado**: `UNIFIED_SIGNALS_*.csv` (25 colunas consolidadas)
  - Combina ALL_SIGNALS + ACTIONABLE_SIGNALS + ENHANCED_SIGNALS
  - Source único de verdade para sinais
  - Fácil de analisar em Excel/Sheets

- **Decision Tree Refiner** (+21.51% melhoria EURUSD)
  - Classifica direção UP/DOWN baseado em 23 features
  - Importante Feature: SMC zones (support/resistance) 71.5%
  - Melhora 40-43% das predições do ensemble

- **3 Novos Indicadores**
  - ER (Efficiency Ratio): Tendência vs ruído [0-1]
  - KAMA (Kaufman Adaptive MA): MA adaptativa
  - Realized Volatility: Volatilidade realizada

- **Pipeline Parametrizável** (`run_full_pipeline.py`)
  - Suporte a múltiplos ativos via `config.json`
  - Comandos: `--all`, `--datafile`, `--config`
  - Ready para AUDUSD, NZDUSD, USDCAD

- **Documentação Completa**
  - `SETUP_NEW_ASSET.md`: Guia passo-a-passo novos ativos
  - `results/README_UNIFIED.md`: Guia do arquivo unificado
  - Updated `README.md` com nova arquitetura

- **Script de Merge** (`merge_backtest_with_signals.py`)
  - Une dados de backtest com decisões de sinais
  - Regenerável a qualquer tempo
  - Sem redundância

#### 📈 Performance
- **EURUSD**: 86.1% WR (87/101), +484.90 pips
- **GBPUSD**: 77.1% WR (54/70), +1,124.10 pips
- **Combined**: 82.6% WR (141/171), +1,609.00 pips

#### ✨ Features Consolidados
- 23 indicadores técnicos (tested & validated)
- XGBoost (300 trees) + RandomForest (300 trees)
- Ensemble confidence 0-100%
- Decision Tree refinement scores
- 3-layer signal filtering (confidence, confluence, 1/day)
- Quality scoring system (4 criteria)

#### 🔒 Data Integrity
- ✅ Validação: 101 sinais EURUSD = 101 dias (1/dia)
- ✅ Validação: Horários, preços, direções idênticas across files
- ✅ Validação: No data loss na unificação
- ✅ Validação: Preço real (Actual Close D+1) explícito em outputs

#### 🧹 Limpeza
- Consolidação de 6 arquivos de sinais em 2 unificados
- Remoção de redundâncias
- Estrutura otimizada para análise

#### 📚 Documentation
- README.md: Reescrito com arquitetura nova
- SETUP_NEW_ASSET.md: Criado (completo)
- README_UNIFIED.md: Criado (25 colunas + uso)
- Comentários inline em todos os scripts

---

## [0.9.0] - 2026-05-27

### 🔧 Anterior
- XGBoost + RandomForest ensemble baseline (50-52% WR)
- Geração de sinais com confiança manual
- Separação de dados em múltiplos CSVs
- Setup específico para EURUSD/GBPUSD

### ⬆️ Improvements
- Adicionado Decision Tree refiner
- Implementado 3 novos indicadores
- Parametrização para novos ativos
- Unificação de outputs

---

## Histórico de Commits Principais

```
v1.0.0      Unificação completa, Decision Tree, 3 indicators
v0.9.0      XGBoost+RF ensemble com sinais
v0.8.0      Estrutura base do projeto
```

---

## 🚀 Roadmap v1.1.0+ (TODO)

- [ ] Teste em AUDUSD, NZDUSD, USDCAD
- [ ] Análise win rate por hora/dia
- [ ] Google Sheets integration (live signals)
- [ ] MT5 EA com WebSocket
- [ ] Market regime analysis (TREND vs RANGE)
- [ ] Portfolio combining multiple assets
- [ ] Performance dashboard
- [ ] Alternative architectures (LightGBM, NN)

---

**Última atualização**: 28/05/2026  
**Versão estável**: v1.0.0 🎉
