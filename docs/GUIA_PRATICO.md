# 📖 Guia Prático: Como Ler e Usar o Backtest

## 1. Abrindo o CSV

```bash
# Opção 1: Ver em Excel/Sheets
open backtest_results/backtest_corrigido_20260526_022521.csv

# Opção 2: Terminal com Python
python3 -c "
import pandas as pd
df = pd.read_csv('backtest_results/backtest_corrigido_20260526_022521.csv')
print(df.to_string())
"

# Opção 3: Terminal simples
head -20 backtest_results/backtest_corrigido_20260526_022521.csv
```

---

## 2. Entendendo as Colunas

### Estrutura do CSV (35 Colunas)

#### 📅 Identificação (Colunas 1-4)
```
date           : 2026-01-02
day_of_week    : Friday
analysis_time  : 21:45:00  (quando a análise foi feita)
result_date    : 2026-01-04 (próximo dia com dados)
```

#### 💹 OHLC - Dados do Dia da Análise (Colunas 5-11)
```
open           : 1.17506   (abertura do dia)
high           : 1.17646   (máximo do dia)
low            : 1.17129   (mínimo do dia)
close          : 1.17192   (fechamento/análise)
close_14h      : 1.172     (fechamento às 14:00 UTC) ← NOVO
volume         : 49993
range_pct      : 0.441%    (%)
```

#### 📊 Indicadores - No Momento da Análise (Colunas 12-18)
```
sma20          : 1.1722    (média 20 candles)
sma50          : 1.1724    (média 50 candles)
sma200         : 1.1738    (média 200 candles) ← AGORA FUNCIONA
rsi14          : 54.3      (0-100, 30-70 é seguro)
macd           : -0.00022  (momentum, neg=baixa)
volatility     : 0.0496    (%)
momentum10     : 0.0204    (mudança últimos 10)
```

#### 📏 Supply/Demand - Distância ao Extremo (Colunas 19-22)
```
dist_alto_pct      : 0.155%  (quão longe do HIGH em %)
dist_baixo_pct     : 0.044%  (quão longe do LOW em %)
sd_trend_type      : BETWEEN_EXTREMES (posição vs extremos)
sma_position       : BELOW_SMA50 (preço vs SMA)
```

#### 🔄 Sweep/BOS Detection (Colunas 23-25)
```
em_sweep_h4        : False   (está em sweep? ⚠️)
sweep_type         : (BULLISH/BEARISH/empty)
pct_proximo_bos    : 0.0358% (distância até BOS)
```

#### 🤖 Predição XGBoost (Colunas 26-27)
```
xgb_pred           : SELL    (BUY ou SELL)
xgb_confidence     : 0.7711  (77.11% confiança)
```

#### 🔗 Confluência M15 vs H4 (Colunas 28-31)
```
m15_trend          : NEUTRAL (trend no M15)
h4_trend           : NEUTRAL (trend no H4)
is_aligned         : ❌      (✅ se alinhados)
alignment_score    : 0.5     (0-1)
```

#### 💰 Resultado (Colunas 32-35)
```
next_close         : 1.1705  (fechamento do próximo dia)
change_pct         : -0.121% (mudança %)
result             : DOWN    (UP/DOWN)
acertou            : ✅      (✅ se XGBoost acertou)
```

---

## 3. Exemplos Práticos de Leitura

### Exemplo 1: Trade Acertado

```
date           2026-01-16
analysis_time  21:45:00
sma20          1.1727
sma50          1.1716
sma200         1.1715
rsi14          45.2       ← Seguro (30-70)
em_sweep_h4    False      ← Sem sweep ✅
xgb_pred       BUY
xgb_confidence 0.87
dist_alto_pct  0.18%      ← Longe do extremo
sd_trend_type  BETWEEN_EXTREMES

next_close     1.1731
change_pct     +0.22%     ← Subiu
result         UP
acertou        ✅         ← Modelo ACERTOU

👉 CONCLUSÃO: Operação segura, bem posicionada, modelo acertou.
```

### Exemplo 2: Trade com Sweep (Arriscado)

```
date           2026-01-27
analysis_time  23:45:00
sma20          1.1751
sma50          1.1751
sma200         1.1750
rsi14          48.5
em_sweep_h4    True       ← ⚠️ SWEEP ATIVO!
sweep_type     BULLISH_SWEEP
pct_proximo_bos 0.18%     ← Perto de BOS
xgb_pred       BUY        ← Modelo diz BUY
xgb_confidence 0.96       ← Muito confiante (suspeito)

next_close     1.17463
change_pct     -0.35%     ← Caiu apesar de BUY
result         DOWN
acertou        ❌         ← Modelo ERROU

👉 CONCLUSÃO: Sweep causou retorno (CHOC), modelo foi "liquidado"
Lição: Ignorar sinais quando em sweep ou esperar confirmação.
```

### Exemplo 3: Monitorar com close_14h

```
date           2026-01-19
analysis_time  23:45:00
close          1.1824     (fechamento final do dia)
close_14h      1.1813     (como estava às 14:00)
change_pct     +0.75%

Comparação:
  - Às 14:00: 1.1813
  - Ao final: 1.1824
  - Movimento tarde: +0.11 (continuou subindo após 14:00)
  
👉 USE: Se houver reversão pós-14:00, desconfie do movimento.
```

---

## 4. Interpretando Indicadores

### RSI (0-100)
```
RSI < 30     : Sobrevenda (limite para BUY)
30 < RSI < 70 : Zona segura ✅
RSI > 70     : Sobrecompra (limite para SELL)
```

### SMA200 (Tendência Principal)
```
Preço > SMA200 : Tendência ALTA (favore BUY)
Preço < SMA200 : Tendência BAIXA (favore SELL)
Preço ≈ SMA200 : Neutro ou transição
```

### Distância ao Extremo (%)
```
< 0.1%  : MUITO PERTO (zona crítica, pode fazer liquidity grab)
0.1-0.3% : PRÓXIMO (monitore)
> 0.3%  : LONGE (seguro)
```

### Sweep/BOS Status
```
em_sweep_h4 = True  : ⚠️ Evitar entrada OR esperar CHOC
pct_proximo_bos < 0.1% : Risco muito alto
```

---

## 5. Checklist Antes de Operar

```
✅ Checklist de Entrada

□ Sem Sweep H4? (em_sweep_h4 = False)
  → SIM: Pode continuar
  → NÃO: Aguardar CHOC ou pular

□ RSI na zona segura? (30 < RSI < 70)
  → SIM: Bom sinal
  → NÃO: Risco aumentado

□ Distância ao extremo confortável? (dist > 0.1%)
  → SIM: Seguro
  → NÃO: Muito arriscado

□ Close 14h alinhado? (verificar padrão)
  → SIM: Continuação provável
  → NÃO: Reversão possível

□ Confluência XGBoost (confiança > 70%)
  → SIM: Confiável
  → NÃO: Possível falso sinal

RESULTADO:
  3-5 checkmarks ✅ : ENTRAR
  1-2 checkmarks ⚠️ : CONSIDERAR COM CUIDADO
  0 checkmarks ❌ : PULAR
```

---

## 6. Interpretando Score de Entrada (Backtest com Filtros)

```
Score = Sem_Sweep (0-2) + RSI_OK (0-1) + SMA_OK (0-1)

ENTRADA_SEGURA (Score 3-4):
  → Todos os filtros passaram
  → Win Rate: 56.2%
  → EXECUTAR com confiança

ENTRADA_OK (Score 2):
  → Algum filtro falhou mas não crítico
  → Win Rate: 72.7%
  → USAR com vigilância

EVITAR_ENTRADA (Score 0-1):
  → Múltiplos problemas
  → Win Rate: 35.7%
  → PULAR esta operação
```

---

## 7. Exemplo de Análise Completa (Linha por Linha)

```
LINHA DO CSV: 2026-01-02 21:45:00

ANÁLISE PASSO-A-PASSO:

1️⃣ IDENTIFICAÇÃO
   Data: 2026-01-02 (Sexta-feira)
   Horário: 21:45:00 (Último candle do dia)
   Resultado visto em: 2026-01-04

2️⃣ MOVIMENTO DO DIA
   Abertura: 1.17506
   Máximo: 1.17646 (+0.119%)
   Mínimo: 1.17129 (-0.321%)
   Fechamento: 1.17192 (-0.267%)
   Range: 0.44% (moderado)

3️⃣ INDICADORES NO MOMENTO
   SMA20: 1.1722 (preço acima = SELL signal)
   SMA50: 1.1724 (preço acima = SELL signal)
   SMA200: 1.1738 (preço abaixo = DOWNTREND confirmado)
   RSI: 54.3 (zona segura, neutro)
   MACD: -0.00022 (negativo = momentum baixa)
   Conclusão: Ambiente BEARISH

4️⃣ SEGURANÇA
   Sweep: NÃO (em_sweep_h4 = False) ✅ SEGURO
   Distância ao alto: 0.155% (confortável)
   Distância ao baixo: 0.044% (muito próximo)
   Posição: BETWEEN_EXTREMES (normal)

5️⃣ SINAL XGBoost
   Predição: SELL (venda)
   Confiança: 77.11% (bom)
   Lógica: Preço abaixo de SMAs, MACD negativo

6️⃣ O QUE ACONTECEU
   Fechamento seguinte: 1.1705 (-0.12%)
   Resultado: DOWN ✅
   Modelo acertou? SIM ✅

7️⃣ DECISÃO
   ✅ OPERARIA? SIM
      - Sem sweep
      - RSI seguro
      - Sinal claro de venda
      - Resultado confirmou
```

---

## 8. Debugging: Por que o modelo errou?

Quando `acertou = ❌`, procure:

```
❌ Exemplo: 2026-01-13 (ERROU)

Checklist de erros:
□ Sweep estava ativo? (SIM - em_sweep_h4 = True)
  → Este era o problema!
□ RSI estava no extremo? (SIM - RSI = 0.34)
  → Muito baixo (sobrevendido)
□ Volatility estava alta? (SIM - 0.0157)
  → Market estava instável
□ Confiança do modelo era alta? (SIM - 71%)
  → Falso sinal (confiante mas errado)

CONCLUSÃO:
  O modelo tinha TUDO contra:
  - Sweep ativo (liquidity grab likely)
  - RSI em extremo (reversão provável)
  - Volatility alta (incerteza)
  
  Mesmo assim modelo deu SELL 71% confiança e ERROU.
  
  LIÇÃO: Ignorar sinais quando muitos filtros estão vermelhos.
```

---

## 9. CSV Rápido (Apenas Colunas Essenciais)

Se quiser visualizar apenas o essencial:

```python
import pandas as pd

df = pd.read_csv('backtest_results/backtest_corrigido_20260526_022521.csv')

# Apenas essencial
df_essencial = df[[
    'date', 'analysis_time', 
    'close', 'close_14h',
    'sma20', 'sma50', 'sma200', 'rsi14',
    'em_sweep_h4', 'xgb_pred', 'xgb_confidence',
    'change_pct', 'result', 'acertou'
]]

print(df_essencial.to_string())
```

---

## 10. Próximos Passos

1. **Abrir o CSV no Excel**
   - Aplicar formatação condicional em `acertou` (✅ verde, ❌ vermelho)
   - Filtrar por `em_sweep_h4` = FALSE
   - Analisar padrões de erro

2. **Criar filtro no Excel**
   - Show only: `Score = 3` e `RSI entre 30-70`
   - Contar win rate nesse subset

3. **Comparar com sua análise manual**
   - Você teria entrado nessas mesmas operações?
   - Concorda com o score de entrada?
   - Acha que RSI foi o melhor filtro?

---

**Status**: Pronto para análise manual 🎯  
**Versão**: Backtest Corrigido 2.0 (com SMA200 e close_14h)  
**Próxima Etapa**: Aplicar em tempo real com Telegram
