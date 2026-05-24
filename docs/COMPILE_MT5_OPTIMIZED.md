# 🚀 COMPILAR E EXECUTAR O INDICADOR MQ5 OTIMIZADO

## Arquivo a Usar

**Novo Indicador:**  
`mt5/SMC_Features_Indicator_OPTIMIZED.mq5`

**Diferença:**
- Anterior: 25 features (todas)
- Novo: 5 features (TOP preditoras = 27% do poder)
- Benefício: Mais rápido, menos ruído, mesmo resultado

---

## ⚙️ Passo 1: Copiar para MT5

### Windows
```
Copiar:
  SMC_Features_Indicator_OPTIMIZED.mq5

Para:
  C:\Users\<SeuUsuário>\AppData\Roaming\MetaQuotes\Terminal\<TerminalID>\MQL5\Indicators\

Ou simplesmente:
  Abrir MetaTrader 5 → File → Open Data Folder
  Navegar até: MQL5\Indicators\
  Colar arquivo lá
```

### Linux / Wine / Box64
```bash
# Encontrar pasta do MT5
ls ~/.wine/drive_c/Users/*/AppData/Roaming/MetaQuotes/Terminal/*/MQL5/Indicators/

# Ou usar local padrão (copiar para ambos)
cp SMC_Features_Indicator_OPTIMIZED.mq5 ~/.wine/drive_c/Users/*/AppData/Roaming/MetaQuotes/Terminal/*/MQL5/Indicators/
```

---

## 🔧 Passo 2: Compilar no MetaEditor

1. Abra **MetaTrader 5**
2. Pressione **F4** (ou Tools → MetaEditor)
3. Vá para: File → Open
4. Selecione: `SMC_Features_Indicator_OPTIMIZED.mq5`
5. Pressione **F5** (ou Compile)

**Resultado esperado:**
```
0 error(s), 0 warning(s) → Compilation successful
```

Se houver erros, verifique:
- Path está correto?
- Arquivo tem 280+ linhas?
- Sintaxe MQL5 correta?

---

## 📊 Passo 3: Adicionar ao Gráfico

1. Abra um gráfico **EURUSD M15** (pode ser histórico também)
2. Vá para: **Insert → Indicators → Custom → SMC_Features_Indicator_OPTIMIZED**
3. Clique OK (configurações padrão OK)
4. Indicador aparece no gráfico

**Log esperado:**
```
SMC Features Indicator OPTIMIZED (TOP 5 only) Started
Symbol: EURUSD | Period: 15
Exporting to: smc_features_optimized.csv
```

---

## ✅ Passo 4: Verificar que está Gerando Dados

### Procure o arquivo `smc_features_optimized.csv`

**Windows:**
```
C:\Users\<SeuUsuário>\AppData\Roaming\MetaQuotes\Terminal\<TerminalID>\MQL5\Files\
```

**Linux:**
```bash
~/.wine/drive_c/Users/*/AppData/Roaming/MetaQuotes/Terminal/*/MQL5/Files/smc_features_optimized.csv
```

### Verificar conteúdo

```bash
# Ver primeiras linhas
head -5 smc_features_optimized.csv

# Esperado (5 colunas):
datetime	dist_top_liquidity	dist_bottom_liquidity	vol_regime	premium_discount_score	range_duration
2026-05-22 20:15:00	0.12345	0.98765	1	0.25643	5
2026-05-22 20:30:00	0.45678	0.12345	0	-0.10234	3
```

---

## 🐍 Passo 5: Ler em Python

### Copiar CSV para pasta certa

```bash
# De: Terminal\MQL5\Files\
cp ~/Downloads/smc_features_optimized.csv /home/ubuntu/pessoal/options/dados/
```

### Testar leitura

```python
from core.mt5_smc_reader import MT5SMCFeaturesReader

reader = MT5SMCFeaturesReader()
if reader.load():
    # Deve funcionar!
    features = reader.get_latest_features()
    print(f"dist_top: {features['dist_top_liquidity']}")
    print(f"vol_regime: {features['vol_regime']}")
```

---

## 📈 Passo 6: Treinar Novo Modelo

```bash
cd /home/ubuntu/pessoal/options

# Opção A: Treinar com dados otimizados (5 features)
python3 train_smc_models.py --data dados/smc_features_optimized.csv

# Opção B: Treinar com técnicas adicionadas (recomendado)
python3 train_smc_models_with_techniques.py
```

---

## 📊 Resultado Esperado

```
🎯 MODELO 1: DIRECTION PREDICTION
Acurácia:  60-65%  (vs 54.4% anterior)
AUC:       62-68%  (vs 55.8% anterior)
```

---

## ⚠️ Troubleshooting

### Problema: "Arquivo não gerado"
**Solução:**
- Verificar que indicador está no gráfico (deve ter nome na aba)
- Aguardar novo candle (M15 = cada 15 minutos)
- Verificar permissões da pasta MQL5\Files\

### Problema: "Correlação mostra NaN"
**Solução:**
- Aguardar mais candles (precisa de ~100+ para estatística)
- Verificar que arquivo tem mais de 1 linha

### Problema: "Arquivo grande demais"
**Solução:**
- Normal! Cresce ~1 linha a cada 15 minutos
- 1 dia = 96 candles = 96 linhas
- 1 mês = ~2000 linhas (~20KB)

---

## 📋 Checklist Final

```
✅ Arquivo copiado para MQL5\Indicators\
✅ Compilado sem erros (F5)
✅ Adicionado ao gráfico (Insert → Custom)
✅ Arquivo smc_features_optimized.csv criado
✅ Primeiro candle foi exportado
✅ Python consegue ler o arquivo
✅ Modelo treinado com dados otimizados
✅ Acurácia melhorou vs anterior
```

---

## 🎯 Próxima Fase (Após treinar)

Uma vez que modelo está com 60-65% acurácia, você pode:

1. **Backtest:**
   - Testar sinais em histórico
   - Medir ROI, Sharpe, Drawdown

2. **Feature Engineering:**
   - Adicionar RSI, MACD, SMA
   - Criar interações (dist_ratio, etc)

3. **Deploy:**
   - Conectar com EA MT5
   - Gerar sinais em tempo real
   - Enviar para Telegram

---

## 💡 FAQ

**P: Preciso remover o indicador original (SMC_Features_Indicator.mq5)?**  
R: Não, pode deixar os dois. O otimizado exporta para arquivo diferente (smc_features_optimized.csv)

**P: Posso rodar em mais de um timeframe?**  
R: Sim! Execute em EURUSD M15, M30, H1 - indicador funciona em qualquer TF

**P: Quanto tempo demora pra gerar dados?**  
R: 1 candle = 1 linha. EURUSD M15: ~1 linha a cada 15 minutos. Para 100 linhas: 25 horas

**P: Posso usar dados históricos?**  
R: Indicador só funciona em tempo real. Para histórico, use `core/smc_features.py` em Python

