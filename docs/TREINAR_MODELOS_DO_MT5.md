# 🚀 Treinar Modelos XGBoost Diretamente do MT5

## O Problema Antigo
Antes, era necessário:
1. Exportar dados manualmente para CSV
2. Passar o CSV para `train_xgboost_model.py`
3. Depender de arquivo externo

## A Solução Nova
Agora é automático:
1. **MT5 coleta dados** automaticamente dos últimos 500 candles M15
2. **Envia para Python** via HTTP
3. **Python treina e salva** os modelos `.pkl` 
4. **Nenhuma dependência** de arquivo externo!

---

## 📋 Passo a Passo

### 1️⃣ Iniciar Servidor de Treinamento

```bash
bash /home/ubuntu/pessoal/options/bin/train_from_mt5.sh
```

Saída esperada:
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

### 2️⃣ Executar Script no MT5

No **MT5**, execute o script:

**Opção A - Menu:**
```
Tools → Scripts → ExportHistoricalDataForTraining (duplo-clique)
```

**Opção B - Aba Scripts:**
```
1. Abra a aba Scripts à esquerda
2. Procure por "ExportHistoricalDataForTraining"
3. Duplo-clique para executar
```

### 3️⃣ Aguardar Treinamento

O terminal mostrará quando cada modelo foi treinado:

```
════════════════════════════════════════════════════════
📊 TREINANDO MODELO: EURUSD
════════════════════════════════════════════════════════
   Candles: 500
   Features: (499, 8)
   Labels: (499,)
   Classes: [238 261]
   Acurácia: 54.31%
✅ Modelo salvo: /home/ubuntu/pessoal/options/src/xgboost_EURUSD.pkl

📊 TREINANDO MODELO: GBPUSD
...
```

Quando todos os 3 modelos forem treinados:

```
✅ TODOS OS MODELOS TREINADOS COM SUCESSO!

-rw-r--r-- 1 ubuntu ubuntu 32K May 27 10:50 /home/ubuntu/pessoal/options/src/xgboost_EURUSD.pkl
-rw-r--r-- 1 ubuntu ubuntu 31K May 27 10:51 /home/ubuntu/pessoal/options/src/xgboost_GBPUSD.pkl
-rw-r--r-- 1 ubuntu ubuntu 33K May 27 10:52 /home/ubuntu/pessoal/options/src/xgboost_XAUUSD.pkl
```

---

## 🔧 Como Funciona

### Script MQL5 (`ExportHistoricalDataForTraining.mq5`)

```mql5
// 1. Coleta últimos 500 candles M15 de:
//    - EURUSD
//    - GBPUSD  
//    - GOLD (mapeado para XAUUSD)

// 2. Prepara JSON com:
//    {
//      "symbol": "EURUSD",
//      "timeframe": "M15",
//      "data": [
//        { "datetime": "2026-05-27 10:15:00", "open": 1.0851, ... },
//        ...
//      ]
//    }

// 3. Envia via HTTP POST para Python:
//    POST http://0.0.0.0:9999/train
```

### Server Python (`train_models_from_mt5.py`)

```python
# 1. Recebe dados JSON do MT5
# 2. Extrai features:
#    - RSI_14
#    - SMA_20
#    - SMA_50
#    - ATR (%)
#    - Momentum
#    - Confluence
#    - Close
#    - Volume MA

# 3. Treina XGBoost com:
#    - 100 árvores
#    - Max depth 5
#    - Learning rate 0.1
#    - 80% subsample

# 4. Salva modelo em .pkl
```

---

## ⚙️ Configuração

### Mudar quantidade de candles

Editar em `ExportHistoricalDataForTraining.mq5`:

```mql5
input int PERIODS = 500;  // ← Mudar aqui (ex: 1000)
```

Depois recompilar em MetaEditor.

### Mudar símbolos

Editar:

```mql5
input string SYMBOLS = "EURUSD,GBPUSD,GOLD";  // ← Mudar aqui
```

### Mudar porta Python

Editar:

```mql5
input int SERVER_PORT = 9999;  // ← Mudar aqui
```

E também em `train_models_from_mt5.py`:

```python
server = HTTPServer(('0.0.0.0', 9999), TrainingHandler)  # ← Mudar aqui
```

---

## 🐛 Troubleshooting

### Erro: "Script não encontrado no MT5"

Solução:
```bash
# Compilar novamente em MetaEditor:
DISPLAY=:1 wine ~/.wine/drive_c/Program\ Files/MetaTrader\ 5/MetaEditor64.exe \
  ~/.wine/drive_c/Program\ Files/MetaTrader\ 5/MQL5/Scripts/ExportHistoricalDataForTraining.mq5 \
  /compile
```

### Erro: "Connection refused"

Possíveis causas:
1. Servidor Python não foi iniciado
   - Solução: `bash /home/ubuntu/pessoal/options/bin/train_from_mt5.sh`

2. Firewall bloqueando porta 9999
   - Solução: Desabilitar firewall ou liberar porta

3. MT5 rodando em ambiente diferente
   - Solução: Mudar `SERVER_IP` no script MQL5

### Timeout: "Não foi possível treinar em 3 minutos"

Possíveis causas:
1. Gráficos M15 não estão abertos
   - Solução: Abrir gráficos para EURUSD, GBPUSD, GOLD em M15

2. Script não executou
   - Solução: Verificar Logs do MT5 (View → Logs → Experts)

3. Dados insuficientes
   - Solução: Aumentar `PERIODS` de 500 para 1000

---

## 📊 Features Extracted

O modelo usa 8 features calculadas de cada candle:

| Feature | Descrição |
|---------|-----------|
| RSI_14 | Relative Strength Index (14 períodos) |
| SMA_20 | Média Móvel Simples (20 períodos) |
| SMA_50 | Média Móvel Simples (50 períodos) |
| ATR_pct | Average True Range em % do preço |
| Momentum | Close - SMA_20 |
| Confluence | Quantos indicadores apontam para alta (0-3) |
| Close | Preço de fechamento |
| Volume_MA | Média Móvel do Volume (20 períodos) |

**Label**: 1 se próximo candle fecha acima, 0 senão

---

## ✅ Próximos Passos

Após treinar com sucesso:

1. **Reiniciar sistema**:
   ```bash
   pkill -f "server_mt5_http|monitor_mt5" || true
   bash /home/ubuntu/pessoal/options/bin/start_system.sh
   ```

2. **Reanexar EA** (SendCandlesToServer):
   - Abra MT5
   - Clique em um gráfico EURUSD M15
   - Tools → Expert Advisors → SendCandlesToServer

3. **Monitorar alertas**:
   ```bash
   tail -f /tmp/monitor_real.log
   ```

4. **Validar**:
   - Deve receber 1 alerta a cada 15 minutos
   - Com XGBoost score incluído
   - Alertas enviados para Telegram

---

## 📝 Exemplo de Saída Completa

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

════════════════════════════════════════════════════════
📊 TREINANDO MODELO: EURUSD
════════════════════════════════════════════════════════
   Candles: 500
   Features: (499, 8)
   Labels: (499,)
   Classes: [238 261]
   Acurácia: 54.31%
✅ Modelo salvo: /home/ubuntu/pessoal/options/src/xgboost_EURUSD.pkl

════════════════════════════════════════════════════════
📊 TREINANDO MODELO: GBPUSD
════════════════════════════════════════════════════════
   Candles: 500
   Features: (499, 8)
   Labels: (499,)
   Classes: [239 260]
   Acurácia: 52.91%
✅ Modelo salvo: /home/ubuntu/pessoal/options/src/xgboost_GBPUSD.pkl

════════════════════════════════════════════════════════
📊 TREINANDO MODELO: XAUUSD
════════════════════════════════════════════════════════
   Candles: 500
   Features: (499, 8)
   Labels: (499,)
   Classes: [237 262]
   Acurácia: 55.71%
✅ Modelo salvo: /home/ubuntu/pessoal/options/src/xgboost_XAUUSD.pkl

✅ TODOS OS MODELOS TREINADOS COM SUCESSO!

-rw-r--r-- 1 ubuntu ubuntu 32K May 27 10:50 /home/ubuntu/pessoal/options/src/xgboost_EURUSD.pkl
-rw-r--r-- 1 ubuntu ubuntu 31K May 27 10:51 /home/ubuntu/pessoal/options/src/xgboost_GBPUSD.pkl
-rw-r--r-- 1 ubuntu ubuntu 33K May 27 10:52 /home/ubuntu/pessoal/options/src/xgboost_XAUUSD.pkl
```

---

## 🎯 Benefícios

✅ **Sem dependência de arquivo externo** - Dados vêm do MT5  
✅ **Automático** - Um comando e pronto  
✅ **Sempre atualizado** - Treina com últimos dados disponíveis  
✅ **Flexível** - Pode mudar quantidade de candles a qualquer hora  
✅ **Rápido** - Treina em segundos com dados históricos  

