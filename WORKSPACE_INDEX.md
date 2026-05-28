# 📊 Workspace - Índice de Estrutura

## 📁 Organização Principal

```
📦 options/
│
├── 📄 backtest_EURUSD_final.csv      ← Resultado final corrigido (18M)
├── 📄 backtest_GBPUSD_final.csv      ← Resultado final corrigido (18M)
│
├── 📁 src/                            ← Core do sistema (9 arquivos essenciais)
│   ├── indicators.py                  ✅ 24 indicadores técnicos
│   ├── backtest_hybrid.py             ✅ Backtest PRINCIPAL (multi-output + 70/30)
│   ├── backtest_chronological.py      ✅ Referência de validação
│   ├── backtest_multioutput.py        ✅ Demonstração de conceito
│   ├── signal_generator.py            ✅ Geração de sinais
│   ├── confidence_analysis.py         ✅ Análise de confiança
│   ├── train_ml_models_final.py       ✅ Treino dos modelos
│   ├── test_models.py                 ✅ Testes unitários
│   └── __init__.py                    ✅ Package init
│
├── 📁 models/                         ← Modelos treinados (135M)
│   ├── ml_ensemble_eurusd.pkl         ✅ Ensemble XGB+RF EURUSD
│   ├── ml_ensemble_gbpusd.pkl         ✅ Ensemble XGB+RF GBPUSD
│   ├── ml_scaler_eurusd.pkl           ✅ StandardScaler EURUSD
│   ├── ml_scaler_gbpusd.pkl           ✅ StandardScaler GBPUSD
│   └── ... [8 modelos adicionais]
│
├── 📁 data/                           ← Dados de entrada (7M)
│   ├── EURUSD_M15_202401012200_202605222015.csv
│   └── GBPUSD_M15_202401012200_202605222015.csv
│
├── 📁 results/                        ← Resultados de backtest (126M)
│   ├── backtest_EURUSD_hybrid.csv     ✅ Backtest final
│   ├── backtest_GBPUSD_hybrid.csv     ✅ Backtest final
│   ├── signals_EURUSD.csv             ✅ Sinais gerados
│   ├── signals_GBPUSD.csv             ✅ Sinais gerados
│   └── ... [análises, logs, etc]
│
├── 📁 docs/                           ← Documentação (170K)
│   ├── COMO_USAR.md                   ← Comece aqui!
│   ├── COMO_RODAR.md                  ← Como executar
│   ├── TREINAR_MODELOS_DO_MT5.md      ← Integração MT5
│   ├── RESUMO_EXECUTIVO.txt           ← Overview executivo
│   ├── ENSEMBLE_SUMMARY.md            ← Detalhes do ensemble
│   ├── BACKTESTING_GUIDE.md           ← Como usar backtest
│   └── ... [mais 15+ documentos]
│
├── 📁 mql5/                           ← Scripts MetaTrader 5 (produção)
│   ├── SendCandleForNextDayPrediction.mq5  ← Enviar candles ao servidor
│   ├── SendCandlesToServer.mq5        ← Versão alternativa
│   └── GetCandleData.mq5              ← Coletar histórico
│
├── 📁 bin/                            ← Scripts executáveis
│   ├── backtest_master.sh             ← Executar backtest
│   ├── train_and_view.sh              ← Treinar e visualizar
│   ├── nextday_strategy.sh            ← Estratégia next-day
│   └── ... [8 scripts adicionais]
│
├── 📁 scripts/                        ← Utilitários e análises
│   ├── analysis_multioutput_vs_chronological.py
│   ├── CHECKLIST_15MIN.sh
│   └── LISTA_ARQUIVOS_CRIADOS.sh
│
├── 📁 production/                     ← PRONTO PARA PRODUÇÃO ⭐
│   ├── websocket/                     ← WebSocket para MT5 (futura)
│   ├── servers/                       ← HTTP/gRPC (futura)
│   └── README.md                      ← Guia de deploy
│
├── 📁 config/                         ← Configurações (criada para futuro)
│
├── 📁 tests/                          ← Logs de testes (28K)
│   ├── backtest_hybrid_corrected_log.txt
│   ├── backtest_hybrid_log.txt
│   ├── backtest_log.txt
│   └── backtest_multioutput_log.txt
│
└── 📁 .git/                           ← Controle de versão
```

## 🚀 Quick Start

### 1️⃣ Executar backtest (VERIFICAR TUDO FUNCIONA)
```bash
cd /home/ubuntu/pessoal/options
python3 src/backtest_hybrid.py
```

### 2️⃣ Gerar sinais de trading
```bash
python3 src/signal_generator.py
# Outputs: results/signals_EURUSD.csv, signals_GBPUSD.csv
```

### 3️⃣ Analisar confiança
```bash
python3 src/confidence_analysis.py
```

### 4️⃣ Treinar novos modelos
```bash
python3 src/train_ml_models_final.py
```

## 📊 Status Atual

| Componente | Status | Nota |
|-----------|--------|------|
| **Indicadores** | ✅ PRONTO | 24 indicadores calculados |
| **Modelos ML** | ✅ PRONTO | XGB + RF ensemble treinado |
| **Backtest** | ✅ PRONTO | 51-52% win rate validado |
| **Sinais** | ✅ PRONTO | Gerados com confiança |
| **WebSocket** | ⏳ FUTURE | Aguardando deploy |
| **HTTP Server** | ⏳ FUTURE | Roadmap futuro |

## 🎯 Performance Esperada

- **EURUSD**: 51.68% win rate (threshold: 0.55, coverage: 76.9%)
- **GBPUSD**: 52.50% win rate (threshold: 0.80, coverage: 49.1%)
- **Tempo de predição**: <100ms por candle
- **Acurácia**: Validada em 30% dos dados (test set)

## 📝 Documentação

- 📖 Começar: [COMO_USAR.md](docs/COMO_USAR.md)
- 🏃 Rodar: [COMO_RODAR.md](docs/COMO_RODAR.md)
- 🤖 ML Details: [ENSEMBLE_SUMMARY.md](docs/ENSEMBLE_SUMMARY.md)
- 🧪 Backtesting: [BACKTESTING_GUIDE.md](docs/BACKTESTING_GUIDE.md)
- 📊 Executivo: [RESUMO_EXECUTIVO.txt](docs/RESUMO_EXECUTIVO.txt)

## ⚙️ Arquivos Sensíveis

Não editar:
- `src/indicators.py` - Cálculos validados
- `src/backtest_hybrid.py` - Lógica de teste validada
- `models/` - Modelos treinados

Seguros para modificar:
- `src/signal_generator.py` - Pode adicionar filtros
- `src/confidence_analysis.py` - Pode customizar análises
- `production/` - Adicione seus servidores aqui

## 🔧 Manutenção

### Limpar cache
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
```

### Espaço em disco
```bash
du -sh . && du -sh models/ results/ data/
# Total: ~571M
```

### Fazer backup
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz \
  backtest_*.csv models/ src/ results/
```

## 💡 Next Steps

1. ✅ **Validar tudo funciona**: `python3 src/backtest_hybrid.py`
2. ✅ **Analisar sinais**: `python3 src/signal_generator.py`
3. ✅ **Preparar MT5**: Copiar scripts de `mql5/` para MT5
4. ⏳ **Implementar WebSocket**: Quando levar para produção
5. ⏳ **Deploy**: Rodar servidor em ambiente de produção

## 📞 Referências

- Git history: `git log --oneline`
- Commits recentes: `git log -5`
- Últimas alterações: `git status`
