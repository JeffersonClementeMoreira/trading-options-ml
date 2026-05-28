# 🚀 Forex ML Trading System - XGBoost + RandomForest + Decision Tree

**Status: ✅ PRODUCTION READY v1.0.0**

> Sistema de trading de divisas com ensemble ML avançado: predição de preço (XGBoost + RandomForest) + refinamento de direção (Decision Tree) com unificação de dados em single-source-of-truth.

## 📊 Quick Start (1 comando)

```bash
# Executar pipeline completo (treino + backtest + sinais + unificação)
cd /home/ubuntu/pessoal/options
python3 src/run_full_pipeline.py EURUSD
```

**Outputs**: 
- `results/UNIFIED_SIGNALS_EURUSD.csv` ← **ARQUIVO ÚNICO COM TUDO** (25 colunas)
- `results/backtest_EURUSD_DETAILED.csv` ← Todas as amostras de teste
- Análise e guias

## 📈 Performance Atual

| Ativo | Sinais | Win Rate | Total Pips | Status |
|-------|--------|----------|-----------|--------|
| **EURUSD** | 101 | 86.1% | +484.90 | ✅ Ativo |
| **GBPUSD** | 70 | 77.1% | +1,124.10 | ✅ Ativo |

## 📁 Estrutura Atual

```
📦 options/
  ├── README.md                        ← Você está aqui
  ├── SETUP_NEW_ASSET.md               📖 Guia para novos ativos (AUDUSD, NZDUSD, USDCAD)
  ├── config.json                      ⚙️  Configurações (ativos, ML params, filtros)
  │
  ├── src/                             ← CORE (ML Pipeline)
  │   ├── run_full_pipeline.py         🔥 MASTER SCRIPT (executar isto)
  │   ├── indicators.py                23 indicadores técnicos (ER, KAMA, Realized Vol)
  │   ├── decision_tree_refiner.py     Refinador de direção (+21.51% accuracy)
  │   ├── generate_detailed_csvs.py    Backtest com 40 colunas
  │   ├── generate_actionable_signals.py  Decisão ENTER/SKIP (2+ de 3 critérios)
  │   ├── generate_enhanced_signals.py  Sinais com preço real D+1
  │   ├── merge_backtest_with_signals.py  Unificador (25 colunas = tudo junto)
  │   └── ... [suporte]
  │
  ├── data/                            📊 Dados M15
  │   ├── EURUSD_M15_*.csv            59,569 candles (2024-2026)
  │   ├── GBPUSD_M15_*.csv            59,567 candles (2024-2026)
  │   └── AUDUSD_M15_*.csv            Pronto para setup
  │
  ├── results/                         📈 Outputs
  │   ├── UNIFIED_SIGNALS_EURUSD.csv  ⭐ ARQUIVO PRINCIPAL (101 sinais, 25 cols)
  │   ├── UNIFIED_SIGNALS_GBPUSD.csv  ⭐ ARQUIVO PRINCIPAL (70 sinais, 25 cols)
  │   ├── ALL_SIGNALS_*.csv            Todos os sinais com análise completa
  │   ├── ACTIONABLE_SIGNALS_*.csv     Decisões de entrada (ENTER/SKIP)
  │   ├── ENHANCED_SIGNALS_*.csv       Sinais com preço real
  │   ├── backtest_*_DETAILED.csv      17,871 amostras × 40 colunas
  │   ├── README_UNIFIED.md            📖 Guia do arquivo unificado
  │   ├── GUIDE_*.txt                  Guias de uso
  │   └── analysis_*_REPORT.txt        Análises
  │
  ├── docs/                            📚 Documentação
  │   ├── FINAL_RESULTS.md             Resultados finais
  │   └── ...
  │
  ├── .git/                            ✅ Histórico de versões
  ├── .gitignore                       🚫 Arquivos ignorados
  └── config.json                      Configuração centralizada
```

## 🎯 Features Principais

| Item | Status | Details |
|------|--------|---------|
| **Indicadores** | ✅ | 24 técnicos (RSI, SMA, MACD, Bollinger, etc) |
| **ML Models** | ✅ | XGBoost + RandomForest ensemble |
| **Backtest** | ✅ | 51.68% EURUSD / 52.50% GBPUSD |
| **Sinais** | ✅ | Com confiança automática |
| **MT5 Scripts** | ✅ | Prontos para usar |
| **WebSocket** | ⏳ | Pasta preparada em `production/websocket/` |

## 📖 Documentação

- **Começar**: [WORKSPACE_INDEX.md](WORKSPACE_INDEX.md) - Guia completo
- **Como usar**: [docs/COMO_USAR.md](docs/COMO_USAR.md)
- **ML Details**: [docs/ENSEMBLE_SUMMARY.md](docs/ENSEMBLE_SUMMARY.md)
- **Backtest**: [docs/BACKTESTING_GUIDE.md](docs/BACKTESTING_GUIDE.md)
- **Execução**: [docs/COMO_RODAR.md](docs/COMO_RODAR.md)

## 🔌 WebSocket para Produção

Quando levar para produção, implementar:

```
production/websocket/
  ├── server.py           ← Servidor WebSocket (criar)
  ├── client_mt5.mq5      ← Cliente MT5 (já existe em mql5/)
  └── README.md           ← Guia deployment
```

Fluxo:
```
MT5 EA → WebSocket → Python Server (predição) → MT5 Recebe resultado
                    (async, <100ms)
```

## 🚀 Deploy

1. **Local Testing**: `python3 src/backtest_hybrid.py` ✅
2. **MT5 Demo**: Copiar scripts de `mql5/` para MT5 ✅
3. **WebSocket**: Implementar `production/websocket/server.py` ⏳
4. **Production**: Deploy com posição pequena

## 📊 Performance

- **Win Rate**: 51-52% (50% é baseline/random)
- **Threshold Ótimo**: 0.55 (EURUSD), 0.80 (GBPUSD)
- **Coverage**: 76.9% (EURUSD), 49.1% (GBPUSD)
- **Tempo**: <100ms por predição
- **Validado**: Chronological 70/30 split (sem lookahead)

## ⚙️ Config Produção

Criar `config/production.json`:

```json
{
  "websocket": {
    "host": "0.0.0.0",
    "port": 5000,
    "timeout": 30
  },
  "trading": {
    "min_confidence_eurusd": 0.55,
    "min_confidence_gbpusd": 0.80,
    "position_size": 0.5
  }
}
```

## 🔧 Como Usar

### 1. Executar Pipeline Completo

```bash
cd /home/ubuntu/pessoal/options

# EURUSD (101 sinais)
python3 src/run_full_pipeline.py EURUSD

# GBPUSD (70 sinais)
python3 src/run_full_pipeline.py GBPUSD

# Todos os ativos habilitados
python3 src/run_full_pipeline.py --all
```

### 2. Analisar Resultados

```bash
# Arquivo unificado (recomendado - abrir em Excel/Sheets)
cd results/
libreoffice --calc UNIFIED_SIGNALS_EURUSD.csv

# Ou análise rápida em Python
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('results/UNIFIED_SIGNALS_EURUSD.csv')
print(f"Win Rate: {(df['Result']=='WIN').sum()} / {len(df)}")
print(f"Total Pips: {df['Actual Pips'].sum():+.2f}")
EOF
```

### 3. Adicionar Novo Ativo

```bash
# 1. Preparar dados M15 em data/SEUATIVO_M15_*.csv
# 2. Atualizar config.json com novo ativo
# 3. Executar pipeline
python3 src/run_full_pipeline.py SEUATIVO

# Ver guia completo
cat SETUP_NEW_ASSET.md
```

## 📊 Arquitetura ML

```
┌─────────────────────────────────────────────┐
│  DADOS (M15 Candles)                       │
│  59,569 EURUSD + 59,567 GBPUSD            │
└────────────────────┬────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    70% Treino             30% Teste
    (41,698 EUR)           (17,871 EUR)
         │                       │
    ┌────▼─────────┐       ┌─────▼──────────┐
    │ XGBoost      │       │ PREDIÇÃO       │
    │ 300 trees    │       │ Preço D+1 14:00│
    ├──────────────┤       ├────────────────┤
    │ RandomForest │       │ Confiança      │
    │ 300 trees    │       │ (XGB vs RF)    │
    └────┬─────────┘       └─────┬──────────┘
         │                       │
         │       ┌───────────────┘
         │       │
    ┌────▼───────▼────────────┐
    │ Decision Tree Refiner   │ ← +21.51% accuracy
    │ Classifica DIR (UP/DOWN)│
    │ 23 features, 7 depth    │
    └────┬─────────────────────┘
         │
    ┌────▼──────────────────────┐
    │ SINAIS ACIONÁVEIS         │
    │ 101 EURUSD (86.1% WR)     │
    │ 70 GBPUSD (77.1% WR)      │
    └────┬──────────────────────┘
         │
    ┌────▼──────────────────────┐
    │ ARQUIVO UNIFICADO         │
    │ 25 colunas, tudo junto    │
    │ Pronto p/ análise/trading │
    └───────────────────────────┘
```

## 📈 Indicadores (23 Features)

**Técnicos Clássicos (20)**
- RSI, SMA20, SMA50, MACD, ATR, Momentum
- Standard Deviation, Bollinger Bands (upper/lower/width)
- SMC Support/Resistance, Order Blocks, Fair Value Gaps
- Price positions, MACD positivity, Momentum positivity

**Novos (3)**
- **ER (Efficiency Ratio)**: Controla tendência vs ruído [0-1]
- **KAMA (Kaufman Adaptive MA)**: MA adaptativa à volatilidade
- **Realized Volatility**: Volatilidade do mercado (annual)

## 🎯 Filtros de Sinais (3 Camadas)

```
Layer 1: Confiança >= 90%
         └─ Ensemble agreement (XGB vs RF)
         
Layer 2: Confluence >= 3
         └─ Mesmo de 3+ últimos candles
         
Layer 3: 1 sinal/dia
         └─ Primeira entrada válida do dia
```

**Resultado**: Exatamente 1 sinal por dia (101/101 dias para EURUSD)

## 📂 Principais Arquivos

| Arquivo | Propósito | Status |
|---------|-----------|--------|
| `src/run_full_pipeline.py` | Pipeline maestro | ✅ Ativo |
| `src/indicators.py` | 23 indicadores | ✅ Ativo |
| `src/decision_tree_refiner.py` | Refinador de direção | ✅ Ativo |
| `config.json` | Configuração centralizada | ✅ Ativo |
| `results/UNIFIED_SIGNALS_*.csv` | **ARQUIVO PRINCIPAL** | ✅ Ativo |
| `SETUP_NEW_ASSET.md` | Guia novos ativos | ✅ Completo |
| `results/README_UNIFIED.md` | Guia unificação | ✅ Completo |

## 🚀 Próximos Passos

- [ ] Análise win rate por hora do dia
- [ ] Teste em AUDUSD, NZDUSD, USDCAD
- [ ] Exportar sinais para Google Sheets (live)
- [ ] Integrar com EA de trading em MT5
- [ ] Deploy em VPS

## 📞 Referências Rápidas

```bash
# Pipeline completo (1 comando)
python3 src/run_full_pipeline.py EURUSD

# Unificar sinais
python3 src/merge_backtest_with_signals.py EURUSD

# Ver status git
git log --oneline -5
git status

# Espaço em disco
du -sh results/ data/ models/
```

---

**Versão**: v1.0.0 (stable)  
**Data**: 28/05/2026  
**Status**: ✅ PRODUCTION READY  
**Win Rate**: EURUSD 86.1% | GBPUSD 77.1%  
**Sinais**: 101 + 70 validados e unificados 🎉
