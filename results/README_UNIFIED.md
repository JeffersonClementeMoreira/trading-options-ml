# 📊 Arquivos Unificados - Guia Completo

## 🎯 O Que é Este Arquivo?

O arquivo **`UNIFIED_SIGNALS_*.csv`** é uma **versão consolidada e otimizada** que combina todos os dados de sinais, indicadores e performance em um único lugar, sem redundâncias.

---

## 📂 Antes vs Depois

### 🔴 Antes (3 arquivos separados):

```
results/
├─ ALL_SIGNALS_EURUSD_COMPLETE.csv     (101 linhas, 20 colunas)
├─ ACTIONABLE_SIGNALS_EURUSD.csv       (101 linhas, 11 colunas)
└─ ENHANCED_SIGNALS_EURUSD.csv         (101 linhas, 15 colunas)
```

**Problema:** Dados espalhados em 3 arquivos, difícil de cruzar informações.

### ✅ Depois (1 arquivo unificado):

```
results/
└─ UNIFIED_SIGNALS_EURUSD.csv          (101 linhas, 25 colunas)
```

**Solução:** Tudo em um lugar! Mais fácil analisar e negociar.

---

## 📋 Estrutura das Colunas

| Grupo | Colunas | Descrição |
|-------|---------|-----------|
| **IDENTIFICAÇÃO** | Nº, Signal Time (ENTRY) | Número do sinal e horário de entrada |
| **ENTRADA** | Entry Price, Direction, Confidence %, Refinement | Preço onde entrar, direção UP/DOWN, confiança ML, qualidade refinamento |
| **ALVO E PREÇOS** | Target Predicted, Target Price, Actual Close D+1, Price Diff, Difference (E) | Preço alvo predito, alvo do actionable, fechamento real D+1, diferenças |
| **PERFORMANCE** | Predicted Pips, Actual Pips, Pips Error, Pips Result | Quantos pips ganhou/perdeu (predito vs real) |
| **QUALIDADE** | High Conf, Good Ref, Excel Ref, Dir History, Criteria Count, Quality Scores | Checkmarks de qualidade do sinal |
| **DECISÃO** | Decision, Reasons, Result, Actual Result | ENTER/SKIP, por quê, WIN/LOSS, resultado booleano |

---

## 🎯 Como Usar

### 1️⃣ Abrir no Excel / Google Sheets
```bash
# No terminal:
libreoffice --calc results/UNIFIED_SIGNALS_EURUSD.csv
# Ou copiar para Google Sheets
```

### 2️⃣ Análise Rápida

**Quantos sinais ENTER ganham?**
```
Filter: Decision = "ENTER"
Resultado: 87/101 WIN (86.1% win rate)
Total: +484.90 pips
```

**Quantos sinais SKIP perdem menos?**
```
Filter: Decision = "SKIP"
Resultado: 0 sinais (todos são ENTER atualmente)
```

### 3️⃣ Filtros Úteis

| Filtro | Resultado |
|--------|-----------|
| `Decision = "ENTER"` | Ver apenas entradas confirmadas |
| `Result = "WIN"` | Ver apenas operações vencedoras |
| `Result = "LOSS"` | Ver apenas operações perdedoras |
| `Direction = "UP"` | Ver apenas sinais de alta |
| `Confidence % >= 99` | Ver apenas sinais com +99% confiança |
| `Quality Score >= 0.75` | Ver apenas sinais de alta qualidade |

### 4️⃣ Análise por Período

**Por mês:**
- Extrair mês de `Signal Time (ENTRY)`
- Agrupar por mês
- Calcular WIN RATE e TOTAL PIPS por mês
- Identificar meses melhores/piores

**Por hora do dia:**
- Extrair hora de `Signal Time (ENTRY)`
- Agrupar por faixa horária (ex: 00-06, 06-12, etc)
- Qual horário mais lucrativo?

**Por direção:**
- `Direction = UP` vs `Direction = DOWN`
- Qual direção tem melhor taxa de acerto?

---

## 📊 Performance Atual

### EURUSD
```
✅ Sinais: 101
✅ Win Rate: 86.1% (87/101)
✅ Total Pips: +484.90
✅ Pips Médio: +4.80
```

### GBPUSD
```
✅ Sinais: 70
✅ Win Rate: 77.1% (54/70)
✅ Total Pips: +1124.10
✅ Pips Médio: +16.06
```

---

## 🔍 Entendendo as Colunas Importantes

### Entry Price
Preço onde o sinal sugere entrar (M15 ou diário, dependendo da estratégia).

### Target Predicted vs Target Price
- **Target Predicted:** Alvo que o modelo XGB+RF previu
- **Target Price:** Alvo que o algoritmo ACTIONABLE definiu
- Geralmente similares, mas podem variar ligeiramente

### Actual Close D+1
O **PREÇO REAL** que o ativo fechou no dia seguinte às 14:00 (horário definido).

### Predicted Pips vs Actual Pips
- **Predicted Pips:** Quantos pips a predição esperava ganhar
- **Actual Pips:** Quantos pips realmente ganhou/perdeu

### Confidence % & Refinement Score
- **Confidence %:** 0-100, quanto o ensemble (XGB+RF) concorda
- **Refinement Score:** 0-1, qualidade da árvore de decisão que refinava a direção

### High Conf / Good Ref / Excel Ref / Dir History
Checkmarks (✅ ou ❌) que mostram qual critério foi atendido:
- ✅ High Conf: Confiança >= 90%
- ✅ Good Ref: Refinement >= 0.6
- ✅ Excel Ref: Refinement >= 0.75
- ✅ Dir History: Histórico de direção >= 55%

Se >= 2 critérios estão marcados → ENTER, senão → SKIP

### Decision
- **ENTER:** Sinal atende critérios, deve-se considerar entrar
- **SKIP:** Sinal não atende critérios, esperar próximo
- (Atualmente todos são ENTER, mas o campo permite futura expansão)

### Result
- **WIN:** Fechamento real ficou favorável (lucro estimado)
- **LOSS:** Fechamento real ficou desfavorável (prejuízo estimado)

---

## 🛠️ Como Regenerar

Se precisar regenerar os arquivos unificados:

```bash
cd /home/ubuntu/pessoal/options

# Opção 1: Apenas EURUSD
python3 src/merge_backtest_with_signals.py EURUSD

# Opção 2: Apenas GBPUSD
python3 src/merge_backtest_with_signals.py GBPUSD

# Opção 3: Script manual de unificação
python3 << 'EOF'
import pandas as pd

for symbol in ['EURUSD', 'GBPUSD']:
    all_sig = pd.read_csv(f'results/ALL_SIGNALS_{symbol}_COMPLETE.csv')
    act_sig = pd.read_csv(f'results/ACTIONABLE_SIGNALS_{symbol}.csv')
    enh_sig = pd.read_csv(f'results/ENHANCED_SIGNALS_{symbol}.csv')
    
    unified = all_sig.copy()
    unified['Target Price'] = act_sig['Target Price'].values
    unified['Quality Score (A)'] = act_sig['Quality Score'].values
    unified['Pips Result'] = act_sig['Pips Result'].values
    unified['Actual Result (A)'] = act_sig['Actual Result'].values
    unified['Difference (E)'] = enh_sig['Difference'].values
    
    unified.to_csv(f'results/UNIFIED_SIGNALS_{symbol}.csv', index=False)
    print(f"✅ {symbol}: {len(unified)} linhas")
EOF
```

---

## 📈 Próximos Passos

1. **Análise Profunda**
   - Qual horário do dia melhor win rate?
   - Qual faixa de Confidence % melhor resultado?
   - Qual direção (UP/DOWN) mais lucrativa?

2. **Otimização**
   - Ajustar thresholds de entrada
   - Testar novos indicadores
   - Validar com dados mais recentes

3. **Produção**
   - Exportar sinais para Excel/Sheets
   - Integrar com plataforma de trading
   - Monitorar performance em tempo real

4. **Novos Ativos**
   - Aplicar framework a AUDUSD, NZDUSD, USDCAD
   - Comparar performance entre pares

---

## 📞 Suporte

**Dúvidas sobre colunas?**
- Consultar a seção "Entendendo as Colunas Importantes"

**Quer regenerar?**
- Seguir a seção "Como Regenerar"

**Quer adicionar novo ativo?**
- Consultar `SETUP_NEW_ASSET.md` na raiz do projeto

---

## 🎓 Estrutura Técnica (Para Desenvolvedores)

O arquivo unificado é gerado por:
1. `ALL_SIGNALS_*_COMPLETE.csv` ← Base (20 colunas)
2. Merge com `ACTIONABLE_SIGNALS_*` (adiciona Quality Score, Decision, Reasons)
3. Merge com `ENHANCED_SIGNALS_*` (adiciona coluna Difference)
4. Reorganizar e limpar
5. Salvar como `UNIFIED_SIGNALS_*.csv` (25 colunas finais)

Sem redundância, sem dados faltando, pronto para análise!

---

**Última atualização:** 28/05/2026 18:20 UTC
