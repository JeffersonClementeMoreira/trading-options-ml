# 🎯 Sistema Automático de Treinamento - Resumo Executivo

## ✨ O Que Mudou

**ANTES:**
```
❌ Arquivo CSV externo → train_xgboost_model.py → Modelos
❌ Depende de arquivo salvo em disco
❌ Precisa exportar manualmente do MT5
```

**DEPOIS:**
```
✅ MT5 → ExportHistoricalDataForTraining.mq5 → HTTP POST → train_models_from_mt5.py → Modelos
✅ Automático e independente de arquivos
✅ Dados sempre frescos do MT5
```

---

## 🔄 Fluxo Completo

```
PASSO 1: Iniciar Servidor Python
─────────────────────────────────────
$ bash /home/ubuntu/pessoal/options/bin/train_from_mt5.sh
        ↓
    Servidor aguardando em 0.0.0.0:9999


PASSO 2: Executar Script no MT5
─────────────────────────────────────
MT5 → Tools → Scripts → ExportHistoricalDataForTraining
        ↓
    Coleta 500 candles M15 de:
    ├─ EURUSD
    ├─ GBPUSD
    └─ GOLD


PASSO 3: Envio de Dados
─────────────────────────────────────
POST http://0.0.0.0:9999/train
{
  "symbol": "EURUSD",
  "timeframe": "M15",
  "data": [
    {"datetime": "2026-05-27 10:15:00", "open": 1.0851, ...},
    ...500 candles total...
  ]
}
        ↓


PASSO 4: Treinamento Automático
─────────────────────────────────────
Python train_models_from_mt5.py recebe dados
        ↓
    Extrai 8 features:
    ├─ RSI_14
    ├─ SMA_20
    ├─ SMA_50
    ├─ ATR (%)
    ├─ Momentum
    ├─ Confluence
    ├─ Close
    └─ Volume MA
        ↓
    Treina XGBoost (100 árvores, max_depth=5)
        ↓
    Salva modelo .pkl


RESULTADO: Modelos prontos!
─────────────────────────────────────
✅ /home/ubuntu/pessoal/options/src/xgboost_EURUSD.pkl
✅ /home/ubuntu/pessoal/options/src/xgboost_GBPUSD.pkl
✅ /home/ubuntu/pessoal/options/src/xgboost_XAUUSD.pkl
```

---

## 🚀 Uso Rápido

### Teste Simulado (Validação)
```bash
bash /home/ubuntu/pessoal/options/bin/train_models_menu.sh
# Escolher opção 1
```

### Treinamento Real (Dados do MT5)
```bash
bash /home/ubuntu/pessoal/options/bin/train_from_mt5.sh
# Depois executar script no MT5
```

### Menu Interativo
```bash
bash /home/ubuntu/pessoal/options/bin/train_models_menu.sh
# Oferece 3 opções (teste, real ou docs)
```

---

## 📂 Arquivos Criados

| Arquivo | Tipo | Função |
|---------|------|--------|
| `ExportHistoricalDataForTraining.mq5` | MQL5 Script | Coleta dados do MT5 e envia para Python |
| `train_models_from_mt5.py` | Python Server | Recebe dados, treina modelos, salva .pkl |
| `train_from_mt5.sh` | Bash Script | Inicia servidor e aguarda treinamento |
| `train_models_menu.sh` | Bash Menu | Interface interativa com 3 opções |
| `test_training_simulation.py` | Python Test | Simula dados para teste |
| `TREINAR_MODELOS_DO_MT5.md` | Documentação | Guia completo com troubleshooting |

---

## 🎓 Como Usar (Passo a Passo)

### 1️⃣ Abra um terminal e execute:
```bash
bash /home/ubuntu/pessoal/options/bin/train_from_mt5.sh
```

Saída:
```
╔════════════════════════════════════════════════════════════════╗
║  TREINAR MODELOS XGBOOST A PARTIR DO MT5                      ║
╚════════════════════════════════════════════════════════════════╝

1️⃣  Iniciando servidor de treinamento (porta 9999)...

2️⃣  PRÓXIMOS PASSOS NO MT5:
   ├─ Abra o MT5
   ├─ Menu: Tools → Scripts → ExportHistoricalDataForTraining
   └─ OU: Clique duplo em ExportHistoricalDataForTraining na aba Scripts

⏳ Aguardando dados do MT5...
```

### 2️⃣ Abra o MT5 e execute o script:
```
MT5 → Tools → Scripts → ExportHistoricalDataForTraining (duplo-clique)
```

### 3️⃣ Aguarde o terminal exibir:
```
✅ TODOS OS MODELOS TREINADOS COM SUCESSO!

-rw-r--r-- xgboost_EURUSD.pkl
-rw-r--r-- xgboost_GBPUSD.pkl
-rw-r--r-- xgboost_XAUUSD.pkl
```

### 4️⃣ Reinicie o sistema:
```bash
pkill -f "server_mt5_http|monitor_mt5" || true
bash /home/ubuntu/pessoal/options/bin/start_system.sh
```

### 5️⃣ Reanexe o EA no MT5:
```
MT5 → Gráfico EURUSD M15 → Tools → Expert Advisors → SendCandlesToServer
```

---

## ✅ Benefícios

- ✨ **Automático**: Um comando, tudo é feito
- 🔄 **Atualizado**: Sempre treina com dados frescos
- 📊 **Sem arquivo externo**: Dados vêm direto do MT5
- 🚀 **Rápido**: Treina em segundos
- 🔧 **Configurável**: Altere símbolos e períodos facilmente
- 📈 **Melhor**: Usa últimos 500 candles reais

---

## 🐛 Se Algo Não Funcionar

### Erro: "Connection refused"
```bash
# Verificar se servidor está rodando:
ps aux | grep train_models_from_mt5
```

### Erro: "Timeout"
1. Verificar se MT5 está aberto
2. Verificar se gráficos M15 estão carregados
3. Ver logs do MT5 (View → Logs)

### Erro: "ModuleNotFoundError"
```bash
# Instalar dependências:
pip3 install xgboost scikit-learn numpy requests
```

---

## 📞 Próximos Passos

Após treinar com sucesso:

1. ✅ **Modelos criados** (`xgboost_*.pkl`)
2. ✅ **Reiniciar sistema** (`start_system.sh`)
3. ✅ **Reanexar EA** (SendCandlesToServer no MT5)
4. ✅ **Monitorar alertas** (Telegram a cada 15 min)
5. ✅ **7 dias de teste** antes de produção

---

## 📚 Documentação Completa

Para mais detalhes:
```bash
less /home/ubuntu/pessoal/options/TREINAR_MODELOS_DO_MT5.md
```

Ou use o menu interativo:
```bash
bash /home/ubuntu/pessoal/options/bin/train_models_menu.sh
# Opção 3 para documentação
```
