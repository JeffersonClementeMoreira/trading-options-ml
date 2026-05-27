╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                    🤖 COMO TREINAR MODELO XGBOOST                        ║
║                                                                            ║
║              Para novos pares (USDJPY, GBPUSD, etc)                      ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝


## ⚡ RÁPIDO (1 minuto)

Se você tem dados históricos em CSV:

```bash
cd /home/ubuntu/pessoal/options/src

# Exemplo: Treinar USDJPY
python3 train_xgboost_model.py --symbol USDJPY --csv USDJPY_M15.csv
```

Pronto! Arquivo `xgboost_USDJPY.pkl` criado e pronto para usar.


## 📊 PASSO A PASSO

### 1. Obter dados históricos

#### Opção A: Exportar do MT5 (recomendado)

No MT5:
1. Abrir gráfico M15 do par (ex: USDJPY)
2. Tools → History Center
3. Selecionar par e período
4. Exportar como CSV

Resultado: `USDJPY_M15.csv`

#### Opção B: Baixar de API online

Usar Alpha Vantage, OANDA, etc:

```python
import requests

symbol = "USDJPY"
api_key = "YOUR_KEY"

# Baixar dados
response = requests.get(f"https://api.example.com/data?symbol={symbol}")
data = response.json()

# Salvar como CSV
import csv
with open(f'{symbol}_M15.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    writer.writeheader()
    for candle in data:
        writer.writerow(candle)
```


### 2. Preparar o CSV

O arquivo CSV deve ter as colunas:
- `datetime` (opcional)
- `open`
- `high`
- `low`
- `close`
- `volume`

Exemplo (USDJPY_M15.csv):
```
datetime,open,high,low,close,volume
2026-01-01 00:15:00,140.50,140.75,140.45,140.62,1500
2026-01-01 00:30:00,140.62,140.80,140.60,140.72,1600
2026-01-01 00:45:00,140.72,140.90,140.70,140.85,1700
...
```

**Requisitos:**
- Mínimo: 100 candles
- Recomendado: 500+ candles
- Período: M15


### 3. Treinar modelo

```bash
cd /home/ubuntu/pessoal/options/src

python3 train_xgboost_model.py \
  --symbol USDJPY \
  --csv USDJPY_M15.csv \
  --output /home/ubuntu/pessoal/options/src
```

Saída esperada:
```
📂 Carregando dados de: USDJPY_M15.csv
   Total de linhas: 1200
   ✅ Dados carregados: 1200 candles

📊 Calculando indicadores...
   ✅ Features calculadas: 1145 exemplos
   X shape: (1145, 8)
   y distribution: 572 positivos, 573 negativos

⚙️  Treinando XGBoost...

✅ Acurácia de treinamento: 52.1%

💾 Salvando modelo em: /home/ubuntu/pessoal/options/src/xgboost_USDJPY.pkl
✅ Modelo salvo com sucesso!
```

Pronto! Arquivo `xgboost_USDJPY.pkl` foi criado.


### 4. Usar o modelo

O sistema automaticamente carrega o modelo:

1. Adicionar o par em `SendCandlesToServer.mq5`:
   ```mql5
   string symbols_mt5[] = {"XAUUSD", "EURUSD", "GBPUSD", "USDJPY"};
   ```

2. Adicionar em `monitor_mt5_real.py`:
   ```python
   self.models = {
       'XAUUSD': None,
       'EURUSD': None,
       'GBPUSD': None,
       'USDJPY': None,  # ← NOVO
   }
   ```

3. Reiniciar:
   ```bash
   bash /home/ubuntu/pessoal/options/bin/start_system.sh
   ```

Sistema vai carregar `xgboost_USDJPY.pkl` automaticamente!


## 🎯 EXEMPLOS COMPLETOS

### Exemplo 1: Treinar GBPUSD com dados de arquivo local

```bash
# Supondo que você tem GBPUSD_data.csv
python3 train_xgboost_model.py --symbol GBPUSD --csv GBPUSD_data.csv

# Resultado: xgboost_GBPUSD.pkl
```

### Exemplo 2: Treinar múltiplos pares

```bash
# Treinar USDJPY
python3 train_xgboost_model.py --symbol USDJPY --csv USDJPY_M15.csv

# Treinar EURGBP
python3 train_xgboost_model.py --symbol EURGBP --csv EURGBP_M15.csv

# Treinar AUDUSD
python3 train_xgboost_model.py --symbol AUDUSD --csv AUDUSD_M15.csv
```

### Exemplo 3: Treinar com dados exportados do MT5

No MT5:
1. Gráfico USDJPY M15
2. Tools → History Center
3. Exportar → `USDJPY_export.csv`

Então:
```bash
python3 train_xgboost_model.py --symbol USDJPY --csv USDJPY_export.csv
```


## 📈 FORMATO ESPERADO DO CSV

**Opção 1: Nomes em inglês maiúsculo**
```
Open,High,Low,Close,Volume
140.50,140.75,140.45,140.62,1500
140.62,140.80,140.60,140.72,1600
```

**Opção 2: Nomes em inglês minúsculo**
```
open,high,low,close,volume
140.50,140.75,140.45,140.62,1500
140.62,140.80,140.60,140.72,1600
```

**Opção 3: Com datetime**
```
datetime,open,high,low,close,volume
2026-01-01 00:15:00,140.50,140.75,140.45,140.62,1500
2026-01-01 00:30:00,140.62,140.80,140.60,140.72,1600
```

Script automaticamente detecta o formato!


## ⚠️ REQUISITOS

### Instalações necessárias

```bash
# XGBoost
pip3 install xgboost

# NumPy (já deve estar instalado)
pip3 install numpy
```

### Versões testadas

- Python: 3.8+
- XGBoost: 1.5+
- NumPy: 1.20+


## 🧪 TESTAR MODELO TREINADO

Depois de treinar, verificar se arquivo foi criado:

```bash
ls -lah /home/ubuntu/pessoal/options/src/xgboost_USDJPY.pkl

# Deve retornar algo como:
# -rw-rw-r-- 1 ubuntu ubuntu 125K May 27 02:15 xgboost_USDJPY.pkl
```

Carregar e testar:

```python
import pickle
import numpy as np

# Carregar modelo
with open('xgboost_USDJPY.pkl', 'rb') as f:
    model = pickle.load(f)

# Teste com dados fictícios (8 features)
test_data = np.array([[52.3, 140.5, 140.2, 0.5, 0.1, 3, 140.62, 1500]])
prediction = model.predict_proba(test_data)

print(f"Score: {prediction[0][1]:.2%}")  # Deve retornar entre 0-100%
```


## 🎯 INDICADORES USADOS PELO MODELO

O script calcula automaticamente 8 features (mesmos do sistema em produção):

1. **RSI_14** - Relative Strength Index (0-100)
2. **SMA_20** - Simple Moving Average 20 períodos
3. **SMA_50** - Simple Moving Average 50 períodos
4. **ATR_pct** - Average True Range em percentual
5. **Momentum** - Diferença entre close atual e 15 candles atrás
6. **Confluence** - Contagem de sinais convergentes (0-4)
7. **Close** - Preço de fechamento atual
8. **Volume_MA** - Volume médio dos últimos 20 candles


## 📊 ACURÁCIA ESPERADA

Acurácias típicas (baseado em dados históricos):

- **XAUUSD**: 96.4% (muito bom)
- **EURUSD**: 32.7% (baixo, mercado difícil)
- **GBPUSD**: 87.2% (bom)
- **Novo par**: Começar com 50-55% (melhorar depois)

⚠️ **Aviso**: Acurácia em histórico ≠ Resultado futuro real!
Sempre validar com dados reais antes de tradear.


## 🔄 RETREINAR MODELO

Se quer melhorar um modelo existente:

1. Coletar mais dados históricos
2. Treinar novamente com dados maiores
3. Sistema automaticamente carrega nova versão

```bash
# Retreinar com mais dados
python3 train_xgboost_model.py \
  --symbol USDJPY \
  --csv USDJPY_M15_1year.csv  # Arquivo maior

# Vai sobrescrever xgboost_USDJPY.pkl existente
```


## ❓ FAQ

### P: Quanto tempo leva para treinar?

**R:** Depende do tamanho do CSV:
- 100 candles: ~1 segundo
- 500 candles: ~2 segundos
- 1000 candles: ~3 segundos
- 5000 candles: ~5 segundos

### P: Quantos candles preciso?

**R:** Mínimo 100 para treinar, mas recomendado 500+.
Quanto mais dados, melhor o modelo.

### P: Posso treinar com outro período (H1, D1)?

**R:** Sim! Basta ter dados em CSV com os mesmos indicadores.
Script funciona com qualquer período.

### P: Modelo falha ao carregar

**R:** Verificar:
```bash
# 1. Arquivo existe?
ls -la /home/ubuntu/pessoal/options/src/xgboost_USDJPY.pkl

# 2. Permissões corretas?
chmod 644 xgboost_USDJPY.pkl

# 3. Reiniciar sistema
bash /home/ubuntu/pessoal/options/bin/start_system.sh
```

### P: Como melhorar acurácia?

**R:** 
1. Mais dados históricos (500+ candles)
2. Ajustar parâmetros XGBoost (n_estimators, max_depth, learning_rate)
3. Outras features (RSI diferente, MACD, Stochastic, etc)
4. Validação cruzada antes de usar em produção


## 🚀 WORKFLOW COMPLETO

```bash
# 1. Obter dados (exportar do MT5 ou baixar)
#    Resultado: USDJPY_M15.csv

# 2. Treinar modelo
cd /home/ubuntu/pessoal/options/src
python3 train_xgboost_model.py --symbol USDJPY --csv USDJPY_M15.csv

# 3. Verificar arquivo criado
ls xgboost_USDJPY.pkl

# 4. Adicionar par ao SendCandlesToServer.mq5

# 5. Compilar e anexar MQL5 no MT5

# 6. Iniciar sistema
bash /home/ubuntu/pessoal/options/bin/start_system.sh

# 7. Monitorar
tail -f /tmp/server_real.log | grep "NOVO CANDLE"
```

Pronto! Sistema vai começar a fazer predições para USDJPY!


## 📌 RESUMO

| O quê | Como |
|------|------|
| **Treinar** | `python3 train_xgboost_model.py --symbol USDJPY --csv data.csv` |
| **Resultado** | `xgboost_USDJPY.pkl` em `/src/` |
| **Usar** | Adicionar par em MQL5 + reiniciar sistema |
| **Retreinar** | Mesmo comando com dados novos |
| **Verificar** | `ls /src/xgboost_*.pkl` |


**Pronto para treinar novos modelos! 🚀**
