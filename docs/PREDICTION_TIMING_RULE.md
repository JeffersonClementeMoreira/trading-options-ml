# 🎯 Regra de Timing das Previsões

## Entendimento Correto

A previsão **NÃO é para o próximo candle** (ex: M15).  
A previsão **É para o próximo dia às 14:00** (fechamento do dia).

## A Regra Fundamental

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│ ⏰ REGRA IMUTÁVEL:                                         │
│                                                            │
│ Horário de previsão = SEMPRE 14:00                        │
│ O que pode variar = O DIA (D+1, D+2, D+3...)             │
│                                                            │
│ Exemplos:                                                  │
│  • Previsão feita em 2026-05-24 10:30 → Para 2026-05-25  │
│  • Previsão feita em 2026-05-24 13:00 → Para 2026-05-25  │
│  • Previsão feita em 2026-05-25 10:15 → Para 2026-05-26  │
│  • Previsão feita em 2026-05-25 15:00 → Para 2026-05-26  │
│                                                            │
│ Todos os casos: validação acontece às 14:00 do dia alvo  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Estrutura do CSV

```
datetime          | prediction_date | prediction_time | symbol | timeframe | ... | action
2026-05-24 10:30 | 2026-05-25      | 14:00          | EURUSD | D1        | ... | CALL
2026-05-24 11:45 | 2026-05-25      | 14:00          | EURUSD | D1        | ... | STRANGLE
2026-05-25 10:15 | 2026-05-26      | 14:00          | EURUSD | D1        | ... | CALL
```

**Colunas importantes:**
- `datetime`: Quando a previsão foi feita (pode ser qualquer horário)
- `prediction_date`: Data para a qual a previsão se aplica
- `prediction_time`: Horário da previsão (sempre 14:00)
- `prediction_datetime`: Combinação de `prediction_date` + `prediction_time`

## Validação da Previsão

Uma vez que a previsão é feita para D+1 14:00:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│ Previsão feita em: 2026-05-24 10:30                   │
│ Alvo da previsão: 2026-05-25 14:00                    │
│ Timeframe: D1 (dia inteiro)                           │
│                                                         │
│ Validação ocorre em 2026-05-25 14:00 (fechamento):    │
│ ✓ O preço subiu? → CALL foi correto ✅              │
│ ✓ O preço desceu? → PUT seria correto ✅            │
│ ✓ O preço ficou flat? → STRANGLE seria correto ✅   │
│ ✓ Nada funciona? → NO_TRADE era correto ✅          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Por Que Sempre 14:00?

Motivos operacionais:
- **Fechamento consistente**: Todos os dias fecham no mesmo horário (14:00)
- **Sem ambiguidade**: Não importa quando a previsão foi feita
- **Fácil de validar**: Basta saber o preço de fechamento de um dia específico
- **Sem overfit**: Prevê movimento de um dia inteiro, não um candle de minutos

## Lógica no Code

```python
# Exemplo: previsão feita às 10:30 do dia 24 de maio
for row in test_data:
    # Extrai a data e hora da previsão
    prediction_datetime = f"{row['prediction_date']} {row['prediction_time']}"
    # 2026-05-25 14:00 ← Sempre será assim!
    
    signal = engine.decide(
        symbol=row["symbol"],
        timeframe="D1",  # Sempre D1 (dia inteiro)
        datetime_str=prediction_datetime,  # 2026-05-25 14:00
        p_down=float(row["p_down"]),
        p_flat=float(row["p_flat"]),
        p_up=float(row["p_up"]),
    )
```

## Implicações para o Backtest

```
┌─────────────────────────────────────────────────────────┐
│ BACKTEST LOGIC                                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Cada linha do histórico de dados = 1 previsão         │
│                                                         │
│ Exemplo com 100 dias de histórico:                     │
│ • Dia 1 → Previsão para Dia 2 14:00                   │
│ • Dia 2 → Previsão para Dia 3 14:00                   │
│ • Dia 3 → Previsão para Dia 4 14:00                   │
│ ...                                                     │
│ • Dia 100 → Previsão para Dia 101 14:00               │
│                                                         │
│ Total de previsões = 100 (uma por dia)                │
│ Resultado será conhecido = 99 previsões (faltam 1)    │
│ Pois o dia 101 ainda não fechou                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Mudanças Futuras Possíveis

A regra **não muda** o horário, mas pode ser estendida:

```
Configuração atual:
  ✅ Sempre 14:00 (fechamento do dia)
  ✅ Sempre D+1 (próximo dia)

Possibilidades futuras:
  • Mudar para D+2 (daqui a 2 dias)?
  • Mudar para D+3 (daqui a 3 dias)?
  • Mas o horário CONTINUA 14:00
  
  ❌ NÃO pode:
  • Mudar o horário (sempre 14:00)
  • Fazer previsão para candle M15 específico
  • Fazer previsão para horário variável
```

## Resumo

| Aspecto | Valor | Pode Mudar? |
|---------|-------|-------------|
| Horário | 14:00 | ❌ NÃO |
| Dia | D+1 | ✅ SIM (para D+2, D+3, etc) |
| Timeframe | D1 | ❌ NÃO |
| Validação | Fechamento | ❌ NÃO |

---

**Tl;dr:** Sempre 14:00, sempre fechamento do dia, o que muda é quantos dias à frente a previsão se refere.
