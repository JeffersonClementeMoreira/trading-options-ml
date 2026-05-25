# 🚀 GUIA RÁPIDO - COMO RODAR O BACKTEST

## Listar Ativos Disponíveis

```bash
python3 backtest_complete.py --symbols
```

**Output:**
```
📊 ATIVOS DISPONÍVEIS:

   ✓ EURUSD    (84433 candles)
```

---

## 🎯 EXEMPLOS BÁSICOS

### 1️⃣ Rodar Backtest (Padrão)
```bash
# Últimos 30 dias, EURUSD
python3 backtest_complete.py
```

### 2️⃣ Últimos N Dias
```bash
# Últimos 60 dias
python3 backtest_complete.py 60

# Últimos 90 dias
python3 backtest_complete.py 90
```

### 3️⃣ Período Específico
```bash
# De 1º de março a 25 de maio
python3 backtest_complete.py --start 2026-03-01 --end 2026-05-25
```

### 4️⃣ Todos os Dados (3.5 anos)
```bash
python3 backtest_complete.py --full
```

### 5️⃣ Especificar Ativo
```bash
# Quando houver GBPUSD (no futuro)
python3 backtest_complete.py --symbol GBPUSD 60
```

---

## 📊 RESULTADO DO BACKTEST

Cada backtest gera:

### 1. CSV Completo
```
backtest_results/backtest_20260525_HHMMSS.csv
```

**Colunas:**
```
date | day_of_week | m15_trend | h4_trend | is_aligned | alignment_score
confidence_adjustment | final_pred | final_prob | result | change_pct
was_correct | current_close | next_close | reasoning
```

### 2. CSV Simplificado
```
backtest_results/backtest_20260525_HHMMSS_simplified.csv
```

Apenas as colunas mais importantes (7 colunas).

### 3. Análises Exibidas no Terminal
```
═══════════════════════════════════════════
📊 RESULTADO GERAL
═══════════════════════════════════════════
Total Trades: 40
Acertos: 13 (32.5%)
Taxa de Acerto: 32.5%

═══════════════════════════════════════════
🎯 IMPACTO DA CONFLUÊNCIA MULTI-TF
═══════════════════════════════════════════
COM CONFLUÊNCIA (M15 = H4):
    0 trades | 0 acertos (0.0%)

SEM CONFLUÊNCIA (M15 ≠ H4):
   40 trades | 13 acertos (32.5%)

📈 MELHORIA COM CONFLUÊNCIA: -32.5%
```

---

## 📈 COMO VISUALIZAR OS RESULTADOS

### Opção 1: Excel / Google Sheets

```bash
# Abrir o CSV diretamente
cd backtest_results
# Windows: start backtest_20260525_*.csv
# Mac: open backtest_20260525_*.csv
# Linux: libreoffice backtest_20260525_*.csv
```

### Opção 2: Python (Terminal)

```python
import pandas as pd

# Carregar CSV
df = pd.read_csv('backtest_results/backtest_20260525_*.csv')

# Ver primeiras linhas
print(df.head(10))

# Estatísticas
print(f"Total: {len(df)}")
print(f"Taxa de acerto: {len(df[df['was_correct'] == '✅']) / len(df):.1%}")

# Filtrar por confluência
alinhado = df[df['is_aligned'] == '✅']
print(f"Com confluência: {len(alinhado)} trades")
```

### Opção 3: Análise Detalhada

```python
from core.daily_backtester import DailyBacktester

# Carregar backtester
bt = DailyBacktester('dados/EURUSD_M15_*_processed.csv')

# Analisar um dia específico
from datetime import datetime
result = bt.analyze_day(datetime(2026, 5, 20))

# Ver detalhes
for key, value in result.items():
    print(f"{key}: {value}")
```

---

## 🔍 FILTRANDO E ANALISANDO EM EXCEL

### Filtro 1: Apenas Confluência Alinhada
```
Coluna E (is_aligned) = ✅
Ordenar por: was_correct (✅ primeiro)
Calcular: Taxa de acerto
```

### Filtro 2: Apenas Confluência Divergente
```
Coluna E (is_aligned) = ❌
Ordenar por: was_correct (✅ primeiro)
Calcular: Taxa de acerto
Comparar com filtro 1
```

### Filtro 3: Por Dia da Semana
```
Coluna B (day_of_week) = Monday (por exemplo)
Ordenar por: was_correct
Validar padrões por dia
```

### Filtro 4: Apenas Trades Alinhados
```
Coluna E (is_aligned) = ✅
Coluna G (m15_trend) = UP (ou DOWN)
Verificar taxa de acerto
```

---

## 📊 FÓRMULAS ÚTEIS NO EXCEL

```excel
# Total de trades
=ROWS(A:A)-1

# Acertos
=COUNTIF(H:H, "✅")

# Taxa de acerto
=COUNTIF(H:H, "✅") / (ROWS(A:A)-1)

# Trades com confluência
=COUNTIF(E:E, "✅")

# Acertos com confluência
=COUNTIFS(E:E, "✅", H:H, "✅")

# Taxa com confluência
=COUNTIFS(E:E, "✅", H:H, "✅") / COUNTIF(E:E, "✅")

# Taxa sem confluência
=COUNTIFS(E:E, "❌", H:H, "✅") / COUNTIF(E:E, "❌")

# Melhoria de confluência (%)
=(Taxa com confluência) - (Taxa sem confluência)

# Groupby day_of_week
# Use: Pivot Table (Insert > Pivot Table)
```

---

## 🎯 ESTRATÉGIA SUGERIDA: SWEEPS + CONFLUENCE

### O Que é:

1. **SWEEP em H4** → Breakout de estrutura (HIGH ou LOW)
2. **Validação em M15** → Confirma movimento na mesma direção
3. **Momentum Reduzindo** → Entrada melhor posicionada (não no topo)
4. **Confluência** → M15 = H4 para confirmar

### Como Funciona:

```
H4 SWEEP HIGH + M15 CONFIRMA + Momentum REDUZINDO + M15=H4
↓
✅ SINAL FORTE → Comprar

H4 SWEEP HIGH + M15 DIVERGE (baixista) ou Momentum AUMENTANDO
↓
❌ DESCARTA → Esperar próximo
```

### Próximas Implementações:

```
[ ] Integrar SweepDetector em daily_backtester.py
[ ] Adicionar coluna "sweep_type" no CSV
[ ] Adicionar coluna "momentum_acceleration" no CSV
[ ] Testar no backtest
[ ] Medir melhoria de acerto
```

---

## 🔄 WORKFLOW COMPLETO

### Dia 1: Preparar Dados
```bash
# Preprocess (se necessário)
python3 preprocess_mt5_data.py
```

### Dia 2: Rodar Backtest
```bash
# Últimos 30 dias
python3 backtest_complete.py

# ou período específico
python3 backtest_complete.py --start 2026-03-01 --end 2026-05-25
```

### Dia 3: Analisar em Excel
```bash
# Abrir CSV gerado
open backtest_results/backtest_*.csv
```

**Filtrar:**
- ✅ Confluência alinhada vs ❌ divergente
- Taxa de acerto de cada um
- Melhoria com confluência

### Dia 4: Validar Manualmente
```
Para cada trade no CSV:
1. Abrir chart EURUSD M15 + H4 do dia
2. Ver se análise está correta
3. Confirmar se resultado foi correto
4. Anotar padrões
```

### Dia 5: Iterar
```bash
# Se > 55% de acerto:
# → Integrar em options_v3.py
# → Usar confluência como filtro

# Se < 55%:
# → Testar novos períodos
# → Validar manualmente
# → Coletar mais dados
```

---

## 📝 EXEMPLO PRÁTICO

```bash
# 1. Rodar backtest dos últimos 60 dias
python3 backtest_complete.py 60

# Output:
# ✅ backtest_20260525_150000.csv
# ✅ backtest_20260525_150000_simplified.csv

# 2. Abrir em Excel
# → Coluna E (is_aligned): filtrar ✅ e ❌
# → Coluna H (was_correct): contar acertos
# → Calcular taxa de cada um
# → Ver melhoria

# 3. Se melhoria > 10%:
# → Integrar em options_v3.py
# → Usar como filtro de entrada
```

---

## 🚨 TROUBLESHOOTING

### Erro: "Nenhum arquivo encontrado para EURUSD"
```bash
# Verificar quais arquivos existem
ls dados/*processed.csv

# Verificar que arquivo está no place correto
python3 backtest_complete.py --symbols
```

### Erro: "Sem dados para análise"
```bash
# Período muito curto (sem dados de trading)
# Use um período maior
python3 backtest_complete.py 60
```

### Modelo XGBoost não carrega
```bash
# Normal - sistema usa análise técnica como fallback
# Se tiver modelo treinado, colocar em:
# /home/ubuntu/pessoal/options/models/xgboost_model.pkl
```

---

## 💡 DICAS

1. **Para validação rápida:**
   ```bash
   python3 backtest_complete.py 30
   # Último mês = ~20 trades = análise rápida
   ```

2. **Para validação completa:**
   ```bash
   python3 backtest_complete.py --full
   # Todos os 3.5 anos = ~2000 trades = análise robusta
   ```

3. **Para período específico:**
   ```bash
   python3 backtest_complete.py --start 2026-01-01 --end 2026-03-31
   # Q1 2026 = trimestre completo
   ```

4. **Para adicionar novos ativos:**
   - Colocar arquivo `XXXXX_M15_*_processed.csv` em `dados/`
   - Usar: `python3 backtest_complete.py --symbol XXXXX`

---

**Status: ✅ Pronto para usar!**

Começar com:
```bash
python3 backtest_complete.py --start 2026-03-15 --end 2026-05-25
```
