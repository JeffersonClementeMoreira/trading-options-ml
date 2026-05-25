# 📊 Trading Options - Estrutura do Projeto

## 📁 Organização de Pastas

```
options/
├── docs/                      📚 Documentação
│   ├── README.md              (Visão geral do projeto)
│   ├── DECISION_ENGINE.md     (Explicação do engine de decisão)
│   ├── PRODUCTION_GUIDE.md    (Guia de produção)
│   ├── QUICK_REFERENCE.md     (Referência rápida)
│   └── ... (mais documentação)
│
├── src/                       💻 Código Principal
│   ├── trading_decision.py    (Engine de decisão: p_up/p_down → PUT_SELL/CALL_SELL)
│   ├── realtime_analysis.py   (Análise em tempo real com features históricas)
│   ├── explain_decision_logic.py (Demonstração da lógica)
│   ├── example_backtest_integration.py (Exemplo de backtest)
│   ├── calculate_hit_rate.py  (Calcula acurácia dos sinais)
│   ├── validate_example.py    (Validador de outputs)
│   ├── xgb_entry_optimizer.py (Otimizador de entrada XGBoost)
│   ├── mt5_realtime_server.py (Servidor em tempo real)
│   ├── realtime_inference.py  (Inferência em tempo real)
│   ├── telegram_notifier.py   (Notificações Telegram)
│   └── hour_scan.py           (Scanner por hora)
│
├── analysis/                  🔬 Análises
│   └── CRITICAL_ANALYSIS_DATA_LEAKAGE.py (Análise dos problemas corrigidos)
│
├── dados/                     📊 Dados MT5
│   ├── EURUSD_M15_*.csv       (Dados de preços M15)
│   └── XAUUSD_M15_*.csv       (Dados de preços M15)
│
├── predictions/               📈 Outputs de Análise
│   ├── realtime_analysis.csv  (Sinais em tempo real)
│   ├── example_backtest.csv   (Exemplo de backtest)
│   └── example_backtest.html  (Backtest colorido)
│
├── logs/                      📋 Logs
│   └── ... (logs de execução)
│
├── analytics/                 📊 Análises (legado)
│   └── ... (análises antigas)
│
├── backtests/                 ⏮️ Backtests
│   └── ... (resultados de backtests)
│
├── config/                    ⚙️ Configurações
│   └── ... (arquivos de config)
│
├── core/                      🔧 Core (legado)
│   └── ... (funções core)
│
├── venv/                      🐍 Ambiente Virtual
│   └── ... (Python venv)
│
└── .git, .gitignore, INDEX.md (Git e índice)
```

---

## 🎯 Fluxo Principais de Uso

### 1️⃣ **Entender a Lógica**
```bash
cd src/
python3 explain_decision_logic.py
```
→ Vê exemplos de PUT_SELL (bullish) e CALL_SELL (bearish)

### 2️⃣ **Rodar Exemplo de Backtest**
```bash
cd src/
python3 example_backtest_integration.py
```
→ Gera `predictions/example_backtest.csv` + `.html`

### 3️⃣ **Analisar Dados Reais**
```bash
cd src/
python3 realtime_analysis.py
```
→ Gera sinais de EUR/USD com features históricas

### 4️⃣ **Validar Acurácia**
```bash
cd src/
python3 calculate_hit_rate.py
```
→ Calcula % de acerto dos sinais

---

## 🔑 Correções Críticas Aplicadas

### ✅ Problema 1: Data Leakage
- **Antes**: Usava `next_day['close']` → 88.80% artificial
- **Depois**: Usa features históricas (RSI, Volatilidade, Momentum) → 55-65% realista

### ✅ Problema 2: Lógica Invertida
- **Antes**: CALL (compra) quando p_up, PUT (compra) quando p_down
- **Depois**: PUT_SELL (venda) quando p_up, CALL_SELL (venda) quando p_down

---

## 📚 Documentação Importante

| Arquivo | Conteúdo |
|---------|----------|
| `docs/README.md` | Visão geral do projeto |
| `docs/QUICK_REFERENCE.md` | Comandos rápidos |
| `docs/DECISION_ENGINE.md` | Explicação do engine |
| `docs/PRODUCTION_GUIDE.md` | Guia para produção |
| `analysis/CRITICAL_ANALYSIS_DATA_LEAKAGE.py` | Análise dos problemas corrigidos |

---

## 🚀 Próximos Passos

1. ✅ Estrutura reorganizada
2. 📊 Validar acurácia com `calculate_hit_rate.py`
3. 🔗 Integrar com MT5 EA
4. 📱 Configurar notificações Telegram
5. 🎯 Teste em paper trading
6. 💰 Deploy em produção

---

## 📞 Dúvidas?

Consulte a documentação em `docs/` ou execute:
```bash
python3 src/explain_decision_logic.py
```
