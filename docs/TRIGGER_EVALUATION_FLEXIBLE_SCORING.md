# 📊 SISTEMA DE TRIGGERS FLEXÍVEL (Score-Based)

## Mudança de Paradigma

### ❌ ANTES (Imposição Rígida)
```
if (distância_SD ≤ 0.5%) AND (candle em FVG):
    Entry = SIM ✅
else:
    Entry = NÃO ❌
```

**Problema:** Muito rigoroso. Perdia oportunidades em 0.6% ou boas entradas com score 85%.

---

### ✅ DEPOIS (Score Flexível)

```
overall_entry_quality = (sd_score × 0.5) + (confluence_score × 0.3) + (regime_factor × 0.2)

Recomendação:
  - 75-100%: FORTE (entre com confiança)
  - 50-74%:  MÉDIA (entre mas com cuidado)
  - 25-49%:  FRACA (considere esperar)
  - 0-24%:   EVITAR (não é um bom setup)
```

**Vantagem:** Você VÊ os scores e DECIDE você mesmo!

---

## Componentes do Score

### 1️⃣ SD_QUALITY_SCORE (50% do peso)
Mede proximidade da Supply/Demand:

```
100 → Candle DENTRO da SD zone
 75 → ≤0.5% de distância (muito próximo)
 50 → ≤1.0% de distância (aceitável)
 25 → ≤2.0% de distância (longe)
  0 → >2.0% de distância (muito longe)
```

**Exemplo:**
```
Spot: 1.0850
SD zone: 1.0848 - 1.0852
Distância: 0.2%
Score: 75 (≤0.5%)
```

### 2️⃣ CONFLUENCE_SCORE (30% do peso)
Múltiplas confirmações aumentam o score:

```
0 confluências = 0%
1 confluência  = 20%
2 confluências = 40%
3+ confluências = 60%+
```

**Exemplo:**
- SD zone ✅
- Trend aligned ✅
- Mean reversion signal ✅
- **Score: 60%**

### 3️⃣ REGIME_FACTOR (20% do peso)
Estado do mercado:

```
TREND    = 50% (baixo risco, movimento previsível)
RANGE    = 40% (médio risco)
MANIPULATION = 30% (alto risco, caótico)
```

**Exemplo:**
```
Regime: TREND_BULL
Factor: 50%
```

---

## Cálculo Final (Exemplo Real)

```
Spot:      1.0850
SD zone:   1.0848 - 1.0852  (width: 0.0004)
Distância: 0.2%

sd_score       = 75  (≤0.5%)
confluence     = 2   → score = 40%
regime_factor  = 50% (TREND)

overall_quality = (75 × 0.5) + (40 × 0.3) + (50 × 0.2)
                = 37.5 + 12 + 10
                = 59.5% → "MÉDIA"

═════════════════════════════
│ QUALIDADE: 59% (█████░░░░░)
│ Recomendação: MÉDIA
│ Ação: Entre mas reduza risco
═════════════════════════════
```

---

## Casos de Uso

### Caso 1: Setup Perfeito (100%)
```
✅ Candle dentro da SD
✅ 3 confluências alinhadas
✅ Regime em TREND
✅ ATR em compressão

overall_quality = 100%
recommendation  = FORTE

👉 AÇÃO: ENTRY MÁXIMA CONFIANÇA
```

### Caso 2: Setup Bom (75%)
```
✅ 0.3% de distância da SD
✅ 2 confluências
✅ RANGE regime
⚠️ ATR normal

overall_quality = 75%
recommendation  = FORTE

👉 AÇÃO: ENTRY NORMAL
```

### Caso 3: Setup Médio (55%)
```
⚠️ 0.8% de distância da SD
✅ 2 confluências
✅ TREND regime
❌ Sem FVG alinhado

overall_quality = 55%
recommendation  = MÉDIA

👉 AÇÃO: ENTRY REDUZIDA OU ESPERAR
```

### Caso 4: Setup Fraco (30%)
```
❌ 1.5% de distância da SD
✅ 1 confluência
⚠️ MANIPULATION regime
❌ Sem confirmações técnicas

overall_quality = 30%
recommendation  = FRACA

👉 AÇÃO: SKIP ESTE SETUP
```

---

## Interpretação de Scores

### ≥75% (FORTE) 🟢
- **Quando usar:** Sempre que possível
- **Tamanho posição:** 100% do permitido
- **SL:** Standard
- **TP:** Agressivo

### 50-74% (MÉDIA) 🟡
- **Quando usar:** Quando outras confirmações validam
- **Tamanho posição:** 70% do permitido
- **SL:** Apertado (tight)
- **TP:** Conservador

### 25-49% (FRACA) 🟠
- **Quando usar:** Apenas em setups extremos
- **Tamanho posição:** 30-50% do permitido
- **SL:** Muito apertado
- **TP:** Muito conservador

### <25% (EVITAR) 🔴
- **Quando usar:** NUNCA (espere outro setup)
- **Ação:** SKIP

---

## Output no Terminal

```
════════════════════════════════════════════════
AVALIAÇÃO DE TRIGGERS (FLEXÍVEL - Não é imposição)
════════════════════════════════════════════════

📊 QUALIDADE GERAL DA ENTRADA: █████░░░░░ 59%
   Recomendação: MÉDIA

   • Supply/Demand Score: 75% (Distância: 0.2000%)
   • Confluências Score: 40% (2 confluência(s))

   Summary: 🟢 BOM: Apenas 0.2% de distância da SD (muito próximo) | 2 confluências extras

════════════════════════════════════════════════
```

---

## Uso Prático

### No seu código Python:
```python
result = run_pipeline(
    csv_file="dados.csv",
    iv=0.25,
    days=5,
)

context = result["context"]
trigger_eval = context.get("trigger_evaluation", {})

# Acessar scores
overall_quality = trigger_eval.get("overall_entry_quality")
recommendation = trigger_eval.get("recommendation")
distance_pct = trigger_eval.get("distance_to_sd_pct")

# Usar na lógica
if overall_quality >= 75:
    # ENTRY FORTE
    position_size = 1.0  # 100%
elif overall_quality >= 50:
    # ENTRY MÉDIA
    position_size = 0.7  # 70%
else:
    # SKIP
    position_size = 0.0
```

---

## Vantagens do Sistema Flexível

✅ **Adapta-se a diferentes mercados**
- Mercado muito volátil? Score mais baixo = cuidado
- Mercado stável? Score alto = confiança

✅ **Decisão do trader, não do algoritmo**
- Você VÊ os percentuais
- Você DECIDE se quer entrar mesmo com 45%
- Sistema sugere, você comanda

✅ **Útil para backtesting**
- Testar apenas entries com score ≥70%
- Testar strategy risk/reward em diferentes scores
- Validar que score ≥75% realmente tem better hit rate

✅ **Sem pontos duros**
- 0.5% era arbitrário
- Agora é contínuo: 0.2%, 0.6%, 1.3%, etc
- Cada setup tem seu próprio score

---

## Próximos Passos

1. **Rodar novamente** `python3 options_v3.py`
   - Veja os scores na saída

2. **Analisar backtest**
   - Qual score gera melhor hit rate?
   - Há diferença entre 70% e 80%?

3. **Otimizar pesos**
   - Se SD é mais importante: aumentar 0.5 para 0.6
   - Se confluências importam menos: reduzir 0.3 para 0.2

4. **Validar em dados reais**
   - Confirme que scores altos = trades melhores
   - Ajuste SL/TP baseado em score

