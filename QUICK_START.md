# ⚡ QUICK START - COMEÇA AQUI (2 MINUTOS)

## 🎯 Objetivo
Rodar backtest, gerar CSV, abrir em Excel, ver resultados.

---

## 🚀 Passo 1: Listar Ativos
```bash
python3 backtest_complete.py --symbols
```

**Output:**
```
📊 ATIVOS DISPONÍVEIS:
   ✓ EURUSD (84433 candles)
```

---

## 📊 Passo 2: Rodar Backtest
```bash
# Opção A: Últimos 30 dias (padrão)
python3 backtest_complete.py

# Opção B: Últimos 60 dias
python3 backtest_complete.py 60

# Opção C: Período específico
python3 backtest_complete.py --start 2026-03-01 --end 2026-05-25

# Opção D: Todos os dados
python3 backtest_complete.py --full
```

**Escolha uma e execute!**

---

## 📁 Passo 3: Arquivo Gerado
```
backtest_results/backtest_20260525_HHMMSS.csv
backtest_results/backtest_20260525_HHMMSS_simplified.csv
```

---

## 📈 Passo 4: Abrir em Excel
1. Excel → File → Open
2. Selecionar: `backtest_results/backtest_*.csv`
3. Importar com delimitador: **Comma**

**Pronto!** Vê os dados em uma tabela.

---

## 🔍 Passo 5: Análise Rápida

### Filtrar por Confluência
1. Selecionar linha de cabeçalho
2. Data → AutoFilter
3. Coluna G (is_aligned):
   - ✅ = Com confluência
   - ❌ = Sem confluência

### Contar Acertos
- Coluna N (was_correct):
  - ✅ = Acertou
  - ❌ = Errou

### Calcular Taxa

**Com confluência:**
```
Acertos (✅) / Total (✅ + ❌) = X%
```

**Sem confluência:**
```
Acertos (✅) / Total (✅ + ❌) = Y%
```

**Melhoria:**
```
X% - Y% = Z%
```

---

## 💡 Exemplo Real

Período: Últimos 60 dias
Total: 40 trades

| Cenário | Trades | Acertos | Taxa |
|---------|--------|---------|------|
| Com confluência (✅) | 15 | 10 | 67% |
| Sem confluência (❌) | 25 | 10 | 40% |
| **Melhoria** | | | **+27%** ✅ |

**Decisão:** 27% de melhoria = **Integrar em produção!**

---

## 🎯 Opções de Período

```bash
# 1 semana
python3 backtest_complete.py 7

# 2 semanas
python3 backtest_complete.py 14

# 1 mês
python3 backtest_complete.py 30

# 2 meses
python3 backtest_complete.py 60

# 3 meses
python3 backtest_complete.py 90

# 1 trimestre (específico)
python3 backtest_complete.py --start 2026-01-01 --end 2026-03-31

# Tudo (3.5 anos)
python3 backtest_complete.py --full
```

---

## 📋 Colunas Principais do CSV

| Coluna | Significado | Exemplo |
|--------|-------------|---------|
| A | date | 2026-05-20 |
| B | day_of_week | Monday |
| E | m15_trend | UP |
| F | h4_trend | UP |
| G | is_aligned | ✅ (alinhado) |
| H | alignment_score | 90% |
| J | final_pred | UP |
| K | final_prob | 95% |
| L | result | UP |
| N | was_correct | ✅ |

---

## ✨ Pronto!

Você agora pode:

1. ✅ Rodar backtest de qualquer período
2. ✅ Gerar CSV com 17 colunas
3. ✅ Abrir em Excel
4. ✅ Filtrar por confluência
5. ✅ Validar acerto com vs sem
6. ✅ Decidir integração

---

## 🔗 Próximos Passos

**Se melhoria > 10%:**
```
→ Integrar em options_v3.py
→ Usar confluência como filtro
→ Testar em live/paper
```

**Se melhoria < 10%:**
```
→ Testar outro período
→ Validar manualmente alguns trades
→ Coletar mais dados
```

---

## 📞 Dúvidas?

Veja:
- `COMO_RODAR_BACKTEST.md` - Guia completo
- `RESUMO_FINAL_SOLUCAO.md` - Documentação técnica
- `README_BACKTEST.md` - Todas as opções

---

**🚀 Começar:**
```bash
python3 backtest_complete.py 30
```

**Tempo total: ~2 minutos ⏱️**
