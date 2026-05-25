# 🎯 Multi-Timeframe Confluence Daily Backtester

Sistema automático que:
1. **Analisa confluência M15 + H4** (tendências alinhadas aumentam acerto)
2. **Roda dia-a-dia** salvando sugestão de trade
3. **Compara com resultado real** do dia seguinte
4. **Gera CSV completo** para visualização e validação

---

## 📊 Como Funciona

### Fluxo de Análise

```
Para cada dia:
  ├─ M15 Data
  │  ├─ Análise técnica (SMA, momentum, etc)
  │  └─ Tendência: UP / DOWN / NEUTRAL
  │
  ├─ H4 Data (convertido de M15)
  │  ├─ Análise técnica
  │  └─ Tendência: UP / DOWN / NEUTRAL
  │
  ├─ Comparar Tendências
  │  ├─ M15 UP + H4 UP → Confluência ✅ → +50% confiança
  │  ├─ M15 UP + H4 DOWN → Divergência ❌ → -30% confiança
  │  └─ Qualquer NEUTRAL → -20% confiança
  │
  ├─ Previsão Final
  │  ├─ XGBoost prob: 70%
  │  ├─ Ajuste confluência: +50%
  │  └─ Prob final: 95%
  │
  └─ Comparar com Resultado Real
     └─ Acertou? ✅ ou ❌
```

### Exemplo de Confluência

```
Cenário 1: M15 UP + H4 UP (ALINHADO)
  ├─ M15 Análise:
  │  ├─ SMA20 > SMA50 > SMA200 ✓
  │  ├─ Momentum +2.3% ✓
  │  └─ Trend: UP (force: 85%)
  │
  ├─ H4 Análise:
  │  ├─ SMA20 > SMA50 > SMA200 ✓
  │  ├─ Momentum +1.8% ✓
  │  └─ Trend: UP (force: 80%)
  │
  ├─ Confluência: ✅ ALINHADO (90%)
  ├─ Ajuste: +50% na confiança
  └─ Recomendação: FORTE, usar estratégia agressiva

Cenário 2: M15 UP + H4 DOWN (DIVERGÊNCIA)
  ├─ M15: UP (força 75%)
  ├─ H4: DOWN (força 70%)
  ├─ Confluência: ❌ DIVERGÊNCIA (30%)
  ├─ Ajuste: -30% na confiança
  └─ Recomendação: FRACA, usar estratégia defensiva ou skip
```

---

## 🚀 Como Usar

### Instalação

```bash
cd /home/ubuntu/pessoal/options

# Verificar que os arquivos estão criados
ls -la core/multi_timeframe_confluence.py
ls -la core/daily_backtester.py
ls -la backtest_complete.py
```

### Opção 1: Rodar Backtest Completo (Recomendado)

```bash
# Últimos 30 dias (padrão)
python3 backtest_complete.py

# Últimos 60 dias
python3 backtest_complete.py 60

# Todos os dados (3.5 anos)
python3 backtest_complete.py --full

# Período específico
python3 backtest_complete.py --start 2026-03-01 --end 2026-05-25
```

**Saída esperada:**
```
================================================================================
🚀 MULTI-TIMEFRAME CONFLUENCE - DAILY BACKTEST
================================================================================

📊 Carregando dados...
✅ Dados carregados: 84352 candles
   Período: 2023-01-01 00:00:00 a 2026-05-22 20:15:00
📅 Período: Últimos 30 dias

================================================================================
FASE 1: BACKTEST DIA-A-DIA
================================================================================

🚀 Iniciando backtest: 2026-04-25 a 2026-05-25

✅ 2026-04-26 | Pred: UP (72%) | M15: UP H4: UP (90%) | Resultado: UP (+0.15%) | Acerto: ✅
✅ 2026-04-27 | Pred: DOWN (68%) | M15: DOWN H4: DOWN (85%) | Resultado: DOWN (-0.22%) | Acerto: ✅
...
(30 linhas dia-a-dia)
...

✅ Backtest finalizado com 30 dias analisados

================================================================================
FASE 2: SALVAR RESULTADOS
================================================================================

📊 Resultados salvos em: backtest_results/backtest_20260525_123456.csv

╔═══════════════════════════════════════════════════════════╗
║              📊 BACKTEST STATISTICS                      ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  TOTAL:                                                   ║
║    Trades Analisados:        30     (55.2%)              ║
║    Acertos:                  18     (60.0%)              ║
║    Erros:                    12     (40.0%)              ║
║                                                           ║
║  COM CONFLUÊNCIA (M15 = H4):                              ║
║    Trades:                   12                          ║
║    Acertos:                   9     (75.0%)              ║
║                                                           ║
║  SEM CONFLUÊNCIA (M15 ≠ H4):                              ║
║    Trades:                   18                          ║
║    Acertos:                   9     (50.0%)              ║
║                                                           ║
║  MELHORIA COM CONFLUÊNCIA:   +25.0%                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

================================================================================
FASE 3: ANÁLISE DETALHADA
================================================================================

(Padrões, estatísticas e recomendações)

================================================================================
✅ BACKTEST CONCLUÍDO COM SUCESSO!
================================================================================

📊 Arquivos gerados:
   • Principal: backtest_results/backtest_20260525_123456.csv
   • Simplificado: backtest_results/backtest_20260525_123456_simplified.csv

💡 Próximos passos:
   1. Abrir backtest_20260525_123456.csv em Excel/Google Sheets
   2. Analisar padrões por dia/confluência
   3. Validar melhoria de acerto com confluência
   4. Integrar em options_v3.py se resultados > 55%
```

### Opção 2: Rodar Componentes Individualmente

```bash
# Apenas backtest (sem análise)
python3 run_daily_backtest.py --days 30

# Apenas análise de CSV existente
python3 analyze_backtest_results.py backtest_results/backtest_20260525_123456.csv

# Usar arquivo mais recente
python3 analyze_backtest_results.py --latest
```

---

## 📋 Saída do CSV

### Colunas Disponíveis

```csv
date,day_of_week,xgb_pred,xgb_prob,m15_trend,h4_trend,is_aligned,alignment_score,confidence_adjustment,final_pred,final_prob,result,change_pct,was_correct,current_close,next_close,reasoning

2026-04-26,Saturday,UP,72%,UP,UP,✅,90%,+50%,UP,95%,UP,+0.15%,✅,1.0890,1.0892,"✅ CONFLUÊNCIA: M15 UP + H4 UP"
2026-04-27,Sunday,DOWN,68%,DOWN,DOWN,✅,85%,+50%,DOWN,95%,DOWN,-0.22%,✅,1.0892,1.0889,"✅ CONFLUÊNCIA: M15 DOWN + H4 DOWN"
2026-04-28,Monday,UP,55%,UP,NEUTRAL,❌,50%,-20%,UP,50%,UP,+0.08%,❌,"⚠️ DIVERGÊNCIA: M15 UP vs H4 NEUTRAL"
```

### Filtros Úteis no Excel

```
1. Filtrar por is_aligned:
   ✅ = Com confluência (tendência mesmo em M15 e H4)
   ❌ = Sem confluência (divergência de tendências)

2. Filtrar por m15_trend:
   UP, DOWN, NEUTRAL

3. Filtrar por day_of_week:
   Validar padrões por dia da semana

4. Ordenar por change_pct:
   Ver dias com maior movimento
   
5. Contar acertos:
   Com confluência: COUNTIF(is_aligned, "✅")
   Taxa: COUNTIF(was_correct[com confluência], "✅") / COUNTIF(is_aligned, "✅")
```

---

## 📊 Análise de Resultados

### CSV Simplificado

Arquivo `*_simplified.csv` contém apenas as colunas essenciais:
- date, day_of_week
- m15_trend, h4_trend, is_aligned, alignment_score
- final_pred, final_prob
- result, change_pct, was_correct

Perfeito para copiar direto para planilha ou Tableau.

### Métricas Principais

```
🎯 TAXA DE ACERTO GERAL
   = (Acertos) / (Total de Trades)
   Alvo: > 55%

🎯 IMPACTO DA CONFLUÊNCIA
   = (Taxa com confluência) - (Taxa sem confluência)
   Alvo: > +10%

🎯 TRADES COM CONFLUÊNCIA
   = (Trades M15=H4) / (Total)
   Típico: 30-50%

🎯 DIAS MAIS PREVISÍVEIS
   Analisar dia_of_week com melhor taxa
   (Segunda? Terça? Quinta?)

🎯 MELHORES PADRÕES
   Quais combinações M15/H4 têm melhor resultado?
   (UP/UP? DOWN/DOWN? UP/NEUTRAL?)
```

---

## 🔧 Customização

### Ajustar Limites de Confluência

Em `core/multi_timeframe_confluence.py`:

```python
# Linha ~145: Ajustar scores de confluência
if alignment_score >= 0.8:
    confidence_adjustment = 0.5  # +50%
elif alignment_score >= 0.6:
    confidence_adjustment = 0.2  # +20%
elif alignment_score >= 0.4:
    confidence_adjustment = -0.1  # -10%
else:
    confidence_adjustment = -0.3  # -30%
```

### Adicionar Mais Análises

Em `core/daily_backtester.py`:

```python
# Adicionar nova coluna no resultado:
result['nova_coluna'] = seu_valor

# Novo cálculo no analyze_day()
def seu_novo_indicador(self, df_day):
    # sua lógica aqui
    return valor
```

---

## 🎓 Interpretação dos Resultados

### Se Confluência Melhorar Acerto em +20%

```
✅ AÇÃO: Use confluência como FILTRO PRINCIPAL
└─ Modificar options_v3.py
   ├─ Filtro: Só tradear se M15 = H4
   └─ Esperado: Win rate +20% também em tempo real
```

### Se Confluência Melhorar em +5-10%

```
✓ AÇÃO: Use confluência como VALIDADOR SECUNDÁRIO
└─ Modificar options_v3.py
   ├─ Requer: M15 = H4 OU confiança XGBoost > 70%
   └─ Esperado: Win rate +5-10%
```

### Se Confluência Não Melhorar (<5%)

```
⚠️ AÇÃO: Revisar estratégia
└─ Verificar:
   ├─ Dados H4 conversão correta?
   ├─ Indicadores técnicos apropriados?
   ├─ Timeframe H4 muito longo?
   └─ Tentar M15 + M30 em vez de M15 + H4
```

---

## 📈 Exemplo de Integração em options_v3.py

```python
from core.multi_timeframe_confluence import MultiTimeframeConfluence

class OptionsV3Executor:
    def __init__(self):
        self.confluence = MultiTimeframeConfluence()
    
    def _evaluate_trigger_conditions(self, market_data_m15):
        # Previsão XGBoost
        xgb_pred, xgb_prob = self.xgboost_model.predict(market_data_m15)
        
        # Analisar confluência
        confluence = self.confluence.analyze_confluence(market_data_m15)
        
        # Ajustar probabilidade
        _, adjusted_prob, reasoning = self.confluence.adjust_prediction_with_confluence(
            xgb_pred, xgb_prob, market_data_m15
        )
        
        # Filtro: Só tradear se confluência forte OU confiança muito alta
        if confluence.is_aligned or adjusted_prob > 0.75:
            return xgb_pred, adjusted_prob
        else:
            return None, None  # Skip trade
```

---

## 📝 Exemplos de Output

### Dia com Confluência Forte (Esperado: Acertado ✅)

```
✅ 2026-04-26 | Pred: UP (72%) | M15: UP H4: UP (90%) | Resultado: UP (+0.15%) | Acerto: ✅

Análise:
  • M15: SMA20>50>200, momentum +2.3%, price > MA200 → UP forte
  • H4: SMA20>50>200, momentum +1.8%, price > MA200 → UP forte
  • Confluência: 90% alinhado
  • Ajuste: +50% confiança
  • Final: 72% → 95% confiança
  • Resultado: Próximo dia subiu +0.15% → ACERTOU ✅
```

### Dia com Divergência (Esperado: Erro ❌)

```
❌ 2026-04-28 | Pred: UP (55%) | M15: UP H4: NEUTRAL (50%) | Resultado: DOWN (-0.05%) | Acerto: ❌

Análise:
  • M15: Trend UP mas fraco
  • H4: Trend NEUTRAL (ambiguidade em 4h)
  • Confluência: 50% divergência
  • Ajuste: -20% confiança
  • Final: 55% → 50% confiança
  • Resultado: Próximo dia caiu -0.05% → ERROU ❌
```

---

## 🐛 Troubleshooting

### "Arquivo não encontrado"

```bash
# Verificar caminho dos dados
ls -la /home/ubuntu/pessoal/options/dados/EURUSD*.csv

# Se não existir, pode criar fake dados
python3 << 'EOF'
import pandas as pd
import numpy as np

# Criar dados de teste
dates = pd.date_range('2026-01-01', periods=1000, freq='15T')
closes = 1.08 + np.cumsum(np.random.randn(1000) * 0.0001)

df = pd.DataFrame({
    'time': dates,
    'open': closes - 0.00005,
    'high': closes + 0.0001,
    'low': closes - 0.0001,
    'close': closes,
    'volume': np.random.randint(1000, 10000, 1000)
})

df.to_csv('/home/ubuntu/pessoal/options/dados/EURUSD_M15_test.csv', index=False)
EOF
```

### "Erro ao converter para H4"

```
Verificar que dataframe tem índice datetime
```

### "CSV vazio"

```bash
# Verificar período solicitado vs dados disponíveis
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv')
print(f"Dados: {df.index[0]} a {df.index[-1]}")  # Qual período tem?
EOF
```

---

## 📞 Suporte

Para debug:

```bash
# Verbose mode
python3 -c "
from core.multi_timeframe_confluence import MultiTimeframeConfluence
confluence = MultiTimeframeConfluence(verbose=True)  # Ver detalhes
"

# Ver estrutura CSV
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('backtest_results/backtest_*.csv')
print(df.head(10))
print(df.info())
EOF
```

---

**Status: ✅ Pronto para usar!**

Próximo: `python3 backtest_complete.py --days 30`
