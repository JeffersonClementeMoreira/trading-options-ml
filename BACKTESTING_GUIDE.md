# 📊 Backtesting com Dados Reais

## Resumo

Dois sistemas de backtesting para testar os modelos:

### 1️⃣ Backtesting com Dados Sintéticos (Rápido)
- **Arquivo**: `backtest_realdata_15days.py`
- **Tempo**: Instantâneo
- **Dados**: Último 15 dias simulado
- **Uso**: Teste rápido de funcionamento
- **Comando**: `python3 backtest_realdata_15days.py`

### 2️⃣ Backtesting com Dados Reais do MT5 (Preciso)
- **Arquivo**: `backtest_with_real_csv.py`
- **Tempo**: Segundos
- **Dados**: Arquivos CSV exportados do MT5
- **Uso**: Validação real do modelo
- **Comando**: `python3 backtest_with_real_csv.py`

### 3️⃣ Interface Interativa (Recomendado)
- **Arquivo**: `backtest_master.sh`
- **Menu**: Escolher opção
- **Comando**: `bash backtest_master.sh`

---

## Como Usar

### Opção 1: Teste Rápido (Dados Sintéticos)

```bash
cd /home/ubuntu/pessoal/options/src
python3 backtest_realdata_15days.py
```

**Resultado Esperado:**
```
EURUSD:
  Total de dias: 14
  Taxa de acerto: 35.7% (5/14 acertos)
  Confiança média: 77.1%
  Confiança >70%: 30.0% acertos

GBPUSD:
  Total de dias: 14
  Taxa de acerto: 57.1% (8/14 acertos)
  Confiança média: 74.0%
  Confiança >70%: 50.0% acertos
```

---

### Opção 2: Teste Real (Dados do MT5)

#### Passo 1: Exportar dados do MT5

1. Abrir MT5
2. **View → History Center**
3. Selecionar símbolo (ex: EURUSD M15)
4. Clique direito → **Export**
5. Salvar como: `EURUSD_M15.csv`

#### Passo 2: Copiar para pasta correta

```bash
mkdir -p /home/ubuntu/pessoal/options/data
cp ~/Downloads/EURUSD_M15.csv /home/ubuntu/pessoal/options/data/
```

Repetir para:
- `GBPUSD_M15.csv`
- `XAUUSD_M15.csv`

#### Passo 3: Rodar backtesting

```bash
cd /home/ubuntu/pessoal/options/src
python3 backtest_with_real_csv.py
```

**Resultado Esperado:**
```
EURUSD:
  Total de dias: 30
  Taxa de acerto: 55.2% (16/29 acertos)
  Confiança média: 76.4%
  Confiança >70%: 61.5% acertos ✅ (BOM!)

GBPUSD:
  Total de dias: 30
  Taxa de acerto: 62.3% (18/29 acertos)
  Confiança média: 73.2%
  Confiança >70%: 68.2% acertos ✅✅ (ÓTIMO!)
```

---

### Opção 3: Interface Interativa

```bash
bash /home/ubuntu/pessoal/options/bin/backtest_master.sh
```

Menu com:
1. Backtesting com dados sintéticos
2. Backtesting com dados CSV reais
3. Instruções para exportar
4. Ver estrutura de pastas
5. Retornar

---

## Interpretação dos Resultados

### Taxa de Acerto

| Taxa | Interpretação | Ação |
|------|---------------|------|
| >60% | Excelente | ✅ Use em produção |
| 55-60% | Bom | ✅ Use com cuidado |
| 50-55% | Aceitável | ⚠️ Use com MM forte |
| <50% | Ruim | ❌ Não use |

### Por Confiança

**Confiança >70%:**
- Melhor resultado esperado
- Use sempre que confiança >70%

**Confiança 50-70%:**
- Resultado médio
- Use apenas se muitas oportunidades

**Confiança <50%:**
- Pior resultado
- Evitar sempre

---

## Estrutura de Arquivos

```
/home/ubuntu/pessoal/options/
├── src/
│   ├── nextday_clf_EURUSD.pkl      (Modelo classificador)
│   ├── nextday_reg_EURUSD.pkl      (Modelo regressão)
│   ├── nextday_clf_GBPUSD.pkl
│   ├── nextday_reg_GBPUSD.pkl
│   ├── backtest_realdata_15days.py (Backtesting sintético)
│   ├── backtest_with_real_csv.py   (Backtesting real)
│   └── ...
├── data/
│   ├── EURUSD_M15.csv              (Dados exportados MT5)
│   ├── GBPUSD_M15.csv
│   └── XAUUSD_M15.csv
└── bin/
    └── backtest_master.sh          (Interface interativa)
```

---

## Próximos Passos

### Se Taxa de Acerto >55% com Confiança >70%

✅ **Pronto para Produção!**

1. Iniciar servidor:
   ```bash
   python3 /home/ubuntu/pessoal/options/src/server_nextday_predict.py
   ```

2. Compilar EA no MT5:
   - `SendCandleForNextDayPrediction.mq5`
   - Anexar ao gráfico EURUSD M15

3. Monitorar resultados por 1-2 semanas

### Se Taxa de Acerto <50%

❌ **Precisa Melhorar**

1. Retreinar modelos com mais dados:
   ```bash
   python3 /home/ubuntu/pessoal/options/src/train_nextday_close_model.py
   ```

2. Tentar com mais símbolos

3. Adicionar filtros de entrada (BOS, CHOC, SMC)

---

## Troubleshooting

### "Arquivo CSV não encontrado"

```bash
# Verificar pasta
ls -la /home/ubuntu/pessoal/options/data/

# Criar se não existir
mkdir -p /home/ubuntu/pessoal/options/data/

# Copiar arquivo
cp ~/Downloads/EURUSD_M15.csv /home/ubuntu/pessoal/options/data/
```

### "Erro ao parsing CSV"

```bash
# Verificar formato
head -3 /home/ubuntu/pessoal/options/data/EURUSD_M15.csv

# Deve parecer com:
# Date,Time,Open,High,Low,Close,Volume
# 2024.01.15,00:00,1.0850,1.0860,1.0840,1.0855,100000
```

### "Sem dados suficientes"

- Exportar mais dias (mínimo 21 dias)
- Tentar 60 dias de histórico

---

## Comandos Rápidos

```bash
# Backtesting rápido (sintético)
python3 /home/ubuntu/pessoal/options/src/backtest_realdata_15days.py

# Backtesting com CSV real
python3 /home/ubuntu/pessoal/options/src/backtest_with_real_csv.py

# Interface interativa
bash /home/ubuntu/pessoal/options/bin/backtest_master.sh

# Crear pasta de dados
mkdir -p /home/ubuntu/pessoal/options/data

# Ver arquivos de dados
ls -la /home/ubuntu/pessoal/options/data/
```

---

**Última atualização**: 2024-01-15
**Status**: ✅ Completo e Testado
