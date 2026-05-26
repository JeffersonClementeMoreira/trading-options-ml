# 📊 CHECKLIST DE ENTRADA - Estratégia POI+CONFIRMAÇÃO (S3_RANGE)

## ✅ CONDIÇÕES DE ENTRADA (TODAS OBRIGATÓRIAS)

Antes de abrir QUALQUER posição, TODOS os 4 pontos abaixo devem estar em VERDE:

```
┌─────────────────────────────────────────────────────────────┐
│ ✅ CHECKPOINT 1: FAR BELOW DO SUPORTE                        │
├─────────────────────────────────────────────────────────────┤
│ Métrica: dist_sup_pct > 0.1%                                │
│                                                              │
│ EM PORTUGUÊS:                                               │
│ "Preço está LONGE do fundo do dia?"                         │
│                                                              │
│ NO TRADINGVIEW:                                             │
│ Veja o LOW do dia (linha azul no gráfico)                   │
│ Preço está > 0.1% ACIMA do LOW                              │
│                                                              │
│ VISUAL:                                                     │
│ ████ [LOW DO DIA]                                            │
│ ░░░░░░░░░░░░░░░░░ < gap de 0.1%+                           │
│ ████ [PREÇO ATUAL] ← Você está aqui                         │
│                                                              │
│ CONFIRMAÇÃO: Preço em VERDE neste checkpoint                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✅ CHECKPOINT 2: CONFIRMAÇÃO DE TENDÊNCIA (SMA)              │
├─────────────────────────────────────────────────────────────┤
│ Critério 2A: Close > SMA200                                 │
│ Critério 2B: SMA50 > SMA200                                 │
│                                                              │
│ EM PORTUGUÊS:                                               │
│ "Preço está acima da linha de tendência longa?"             │
│ "Tendência está apontando para cima?"                       │
│                                                              │
│ NO TRADINGVIEW (adicionar 3 SMAs):                          │
│ - SMA (20): linha cinza                                     │
│ - SMA (50): linha AZUL (média-prazo)                        │
│ - SMA (200): linha VERMELHA (longo-prazo)                   │
│                                                              │
│ ORDEM CORRETA:                                              │
│ └─ Preço (BRANCO)  <-- deve estar aqui                      │
│    └─ SMA20 (CINZA)                                         │
│       └─ SMA50 (AZUL)                                       │
│          └─ SMA200 (VERMELHO)                               │
│                                                              │
│ SE ESTIVER DIFERENTE: ❌ NÃO ENTRE                          │
│ CONFIRMAÇÃO: Preço > SMA200 e SMA50 > SMA200                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✅ CHECKPOINT 3: POSIÇÃO SEGURA NA RANGE                     │
├─────────────────────────────────────────────────────────────┤
│ Métrica: pos_in_range entre 0.3 e 0.7                       │
│                                                              │
│ EM PORTUGUÊS:                                               │
│ "Preço está no meio do caminho?"                            │
│ (não muito no fundo, não muito no topo)                     │
│                                                              │
│ CÁLCULO:                                                    │
│ pos_in_range = (Preço - LOW dia) / (HIGH dia - LOW dia)    │
│                                                              │
│ EXEMPLO:                                                    │
│ HIGH do dia:    1.10000                                     │
│ LOW do dia:     1.09000                                     │
│ RANGE:          0.01000 (1000 pips)                         │
│ Preço agora:    1.09500                                     │
│ pos = (1.09500 - 1.09000) / 0.01000 = 0.5 ✅ OK             │
│                                                              │
│ VISUAL (pos_in_range):                                      │
│ 1.10000 ─────────── HIGH                                    │
│ 1.10000 ░░░░░░░░░░░ Zona FRACA (0.7-1.0) ❌                 │
│ 1.09700 ██████████ Zona FORTE (0.3-0.7) ✅                  │
│ 1.09500 ██████████ ← Você está aqui (0.5) ✅                │
│ 1.09300 ██████████ Zona FORTE (0.3-0.7) ✅                  │
│ 1.09000 ░░░░░░░░░░░ Zona FRACA (0.0-0.3) ❌                 │
│ 1.09000 ─────────── LOW                                     │
│                                                              │
│ CONFIRMAÇÃO: pos_in_range entre 0.3 e 0.7                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✅ CHECKPOINT 4: HORÁRIO (OPCIONAL - MAS RECOMENDADO)       │
├─────────────────────────────────────────────────────────────┤
│ Melhor: 16:00-18:00 UTC (fecho London/abertura NY)         │
│ Aceitável: Qualquer hora (mas preferir best times)         │
│                                                              │
│ HORÁRIOS RUINS (evitar se possível):                        │
│ - 12:00-14:00 UTC (overlap EU - piores dados)              │
│                                                              │
│ CONFIRMAÇÃO: Se for 16:00-18:00 UTC, +0.3% WR ✅            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔴 CHECKLIST DE NÃO-ENTRADA (SINAIS CONTRA)

Se QUALQUER UM desses estiver verdadeiro, **PULE O TRADE:**

```
❌ SINAL CONTRA 1: Preço MUITO PERTO do LOW
   Se dist_sup_pct < 0.05% → evitar (muito arriscado)

❌ SINAL CONTRA 2: Tendência está DOWN
   Se SMA50 < SMA200 → evitar (contra-tendência)
   Se Close < SMA200 → evitar (contra-tendência)

❌ SINAL CONTRA 3: Preço nos extremos
   Se pos_in_range < 0.2 → muito perto do fundo (armadilha!)
   Se pos_in_range > 0.8 → muito perto do topo (reversão!)

❌ SINAL CONTRA 4: Dia muito volátil (opcional)
   Se range_pct > 1.5% → dia atípico (maior risco)

❌ SINAL CONTRA 5: Notícia importante
   Fed meeting, NFP, BCB decision, etc → evitar
   (manualmente, sem automação)
```

---

## 📝 TEMPLATE DE VERIFICAÇÃO (USE ANTES DE CADA TRADE)

```
╔═══════════════════════════════════════════════════════════╗
║          VERIFICAÇÃO PRÉ-ENTRADA POI+CONFIRMAÇÃO         ║
╚═══════════════════════════════════════════════════════════╝

Data/Hora: _____________  Par: EURUSD  Timeframe: M15

┌─ CHECKPOINTS ────────────────────────────────────────────┐

[_] CP1: FAR BELOW
    dist_sup_pct = _______ %
    [ ] ✅ > 0.1% ? 
    [ ] ❌ Valores:
        
[_] CP2: TENDÊNCIA SMA
    [ ] Close > SMA200? (Sim/Não)
    [ ] SMA50 > SMA200? (Sim/Não)
    [ ] ✅ Ambos SIM?
    [ ] ❌ Se NÃO:
        
[_] CP3: POSIÇÃO RANGE
    pos_in_range = _______
    [ ] Entre 0.3 e 0.7? (Sim/Não)
    [ ] ✅ Confirmado?
    [ ] ❌ Se NÃO (valor):
        
[_] CP4: HORÁRIO
    Hora UTC: _______ 
    [ ] Ideal (16-18h)? Melhor
    [ ] Aceitável (outra)? OK
    [ ] Ruim (<3h UTC)? EVITAR

┌─ SINAIS CONTRA ──────────────────────────────────────────┐

[_] ❌ Preço muito perto LOW? (< 0.05%) → SKIP
[_] ❌ Tendência DOWN? → SKIP
[_] ❌ Extremo (pos < 0.2 ou > 0.8)? → SKIP
[_] ❌ Dia muito volátil (> 1.5%)? → SKIP
[_] ❌ Notícia importante? → SKIP

┌─ DECISÃO FINAL ───────────────────────────────────────────┐

Todos os 4 checkpoints ✅?
Nenhum sinal contra?

[ ] ✅ VERDE - ENTRAR
[ ] ❌ VERMELHO - AGUARDAR

Entrada se ✅: _____ pips stop
            _____ pips target (1.5x)
            _____ lote

┌─ PÓS-ENTRADA ─────────────────────────────────────────────┐

Stop Loss: _____ (rígido, sem exceção!)
Take Profit: _____ (1.5x do stop)
Risk/Reward: 1:_____

Tempo de entrada: _____
Resultado: [ ] Win [ ] Loss [ ] Breakeven

Notas: _______________________________________________
       _______________________________________________

```

---

## 💡 EXEMPLOS PRÁTICOS

### EXEMPLO 1: TRADE VÁLIDO ✅

```
Hora: 17:00 UTC (perfeito!)
Par: EURUSD
Close: 1.09500
LOW do dia: 1.09000
HIGH do dia: 1.10000

VERIFICAÇÃO:
[✅] dist_sup_pct = (1.09500 - 1.09000) / 1.09500 * 100 = 0.457%
     → 0.457% > 0.1% ✅ FAR BELOW OK

[✅] Close (1.09500) > SMA200 (1.08900) ✅
     SMA50 (1.09200) > SMA200 (1.08900) ✅

[✅] pos_in_range = (1.09500 - 1.09000) / 0.01000 = 0.5
     → 0.3 < 0.5 < 0.7 ✅ MID RANGE OK

[✅] Horário: 17:00 UTC ✅ IDEAL

[✅] Nenhum sinal contra

RESULTADO: 🚀 ENTRAR
Stop: -0.1% (rígido)
Target: +0.15% (1.5x)
Position: 0.1 lote
```

### EXEMPLO 2: TRADE INVÁLIDO ❌

```
Hora: 14:00 UTC
Par: EURUSD  
Close: 1.09050
LOW do dia: 1.09000
HIGH do dia: 1.10000

VERIFICAÇÃO:
[❌] dist_sup_pct = (1.09050 - 1.09000) / 1.09050 * 100 = 0.046%
     → 0.046% < 0.1% ❌ MUITO PERTO DO LOW

[❌] Hora: 14:00 UTC ❌ PIOR HORA DO DIA

[❌] pos_in_range = 0.05 ❌ < 0.3 EXTREMO BAIXO

RESULTADO: ❌ PULAR ESTE TRADE
(Esperar melhor entrada ou próxima vela)
```

---

## 🎯 RESUMO RÁPIDO (30 SEGUNDOS)

```
Para ENTRAR em POI+CONFIRMAÇÃO:

1. ✅ Preço LONGE do LOW (> 0.1%)
2. ✅ Acima da SMA200 + tendência UP
3. ✅ No MEIO da range (0.3-0.7)
4. ✅ Preferencialmente 16-18h UTC

Se tudo ✅: ENTRA
Se algo ❌: AGUARDA

Stop: -0.1% (rígido)
Target: +0.15% (1.5x)
```

---

**Use este checklist TODA VEZ que considerar uma entrada.**
**Disciplina = Lucro. Impulsividade = Perda.**
