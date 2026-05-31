# 📊 Arquivos CSV para Análise de SEND

## 🎯 Resumo dos Arquivos Disponíveis

### 📄 1. **SEND_ANALYSIS_EURUSD.csv** (1.8 MB)
**Melhor para: Análise detalhada de cada sinal**

```
11.479 linhas (224 SEND + 11.255 FILTERED)
11 colunas: timestamp, close, confidence_pct, confidence_with_bonus_pct, 
            confluence_score, refinement_scores, predicted_price_ensemble, 
            predicted_pips_ensemble, actual_price, actual_pips, signal_status
```

**Use quando:**
- ✅ Quer ver cada SEND e FILTERED individualmente
- ✅ Quer analisar métricas específicas
- ✅ Quer filtrar/classificar por critério (ex: maior pips, menor confiança)
- ✅ Quer validar timing de entrada

**Exemplo de análise:**
```sql
-- Quais SEND tiveram os piores resultados?
SELECT timestamp, confidence_pct, actual_pips 
FROM SEND_ANALYSIS_EURUSD.csv 
WHERE signal_status = 'SEND' 
ORDER BY actual_pips ASC 
LIMIT 10
```

---

### 📄 2. **SEND_DAILY_SUMMARY_EURUSD.csv** (21 KB)
**Melhor para: Comparar SEND vs Oportunidades Perdidas**

```
224 linhas (1 por dia com SEND)
8 colunas:
  • date, send_time, send_confidence, send_confluence, send_pips
  • filtered_count, best_filtered_confidence, best_filtered_confluence
```

**Use quando:**
- ✅ Quer saber quantos sinais foram bloqueados cada dia
- ✅ Quer comparar: "SEND tinha confiança X, mas melhor FILTERED tinha Y"
- ✅ Quer validar: "Enviava sempre o melhor ou nem sempre?"
- ✅ Quer ver: Qual era a qualidade dos sinais perdidos

**Exemplo de análise:**
```
Linha 1:
  date: 2025-09-03
  send_time: 2025-09-03 04:15:00 (primeiro do dia)
  send_confidence: 110.49%
  filtered_count: 50 (outros 50 sinais bloqueados)
  best_filtered_confidence: 114.60% ← Era 4.11% melhor!
  
Conclusão: Primeiro sinal não era o melhor daquele dia.
```

---

### 📄 3. **results/backtest_EURUSD_chronological.csv** (38 MB)
**Melhor para: Análise completa com contexto**

```
59.569 linhas (TODOS os candles do backtest)
40 colunas (todas as métricas e indicadores)
```

**Use quando:**
- ✅ Quer ver contexto completo (NO_PREDICTION também)
- ✅ Quer análise técnica (RSI, MACD, Bollinger, etc)
- ✅ Quer traçar gráficos
- ✅ Quer validar a lógica dos filtros

---

### 📄 4. **results/backtest_GBPUSD_chronological.csv** (36 MB)
**Melhor para: Comparar com outro ativo**

```
59.567 linhas (EURUSD, mesmo período)
210 SEND | 7.010 FILTERED | 52.347 NO_PREDICTION

Mesmo conteúdo, ativo diferente
```

---

## 📊 Estatísticas Rápidas (EURUSD)

| Métrica | SEND (224) | FILTERED (11.255) | Diferença |
|---------|-----------|------------------|-----------|
| **Confidence (%)** | 94.96% | 95.83% | FILTERED +0.87% |
| **Confidence + Bonus (%)** | 109.21% | 110.20% | FILTERED +0.99% |
| **Confluence Score** | 4.68 | 4.86 | FILTERED +3.9% |
| **Pips Médios** | -18.33 | -22.90 | SEND melhor por -4.57 |

---

## 🎯 Guia Rápido de Uso

### Scenario 1: "Como estão os sinais SEND que enviamos?"
```
Arquivo: SEND_ANALYSIS_EURUSD.csv
Filtro: signal_status = 'SEND'
Análise: confidence_pct, actual_pips, actual_price
```

### Scenario 2: "Quantos sinais foram bloqueados cada dia?"
```
Arquivo: SEND_DAILY_SUMMARY_EURUSD.csv
Coluna: filtered_count
Análise: Soma/Média/Max por período
```

### Scenario 3: "Comparar SEND vs melhor oportunidade bloqueada"
```
Arquivo: SEND_DAILY_SUMMARY_EURUSD.csv
Compare: send_confidence vs best_filtered_confidence
Análise: Quantas vezes o FILTERED era melhor?
```

### Scenario 4: "Validar timing (early vs late sinal)"
```
Arquivo: SEND_ANALYSIS_EURUSD.csv ou SEND_DAILY_SUMMARY_EURUSD.csv
Coluna: send_time
Análise: Em que hora do dia chegam os SEND?
```

### Scenario 5: "Qual era a qualidade média dos SEND?"
```
Arquivo: SEND_ANALYSIS_EURUSD.csv
Filtro: signal_status = 'SEND'
Agregação: AVG(confidence_pct), AVG(confluence_score)
```

---

## 📈 Exemplos Práticos com Excel/Sheets

### Exemplo 1: Histograma de SEND por Hora do Dia
```
Arquivo: SEND_DAILY_SUMMARY_EURUSD.csv
Coluna: send_time (extrair HOUR)
Gráfico: Bar chart das horas
Conclusão: Sinais mais cedo? Mais tarde? Distribuição?
```

### Exemplo 2: Scatter Plot - Confidence vs Pips
```
Arquivo: SEND_ANALYSIS_EURUSD.csv (apenas SEND)
X: confidence_pct
Y: actual_pips
Conclusão: Maior confiança = mais pips? Linear?
```

### Exemplo 3: Tabela Dinâmica - Por Dia
```
Arquivo: SEND_DAILY_SUMMARY_EURUSD.csv
Pivot: date → sum(filtered_count), avg(send_confidence)
Conclusão: Dias com mais sinais bloqueados eram melhores/piores?
```

---

## 🔍 Colunas Explicadas

### SEND_ANALYSIS_EURUSD.csv

| Coluna | Significado |
|--------|-----------|
| timestamp | Data/hora do sinal |
| close | Preço de fechamento |
| confidence_pct | Confiança do ensemble (%) |
| confidence_with_bonus_pct | Confiança + bonus confluence (%) |
| confluence_score | Quantos indicadores alinhados (0-5) |
| refinement_scores | Confiança do Decision Tree (0-1) |
| predicted_price_ensemble | Preço predito pelo ensemble |
| predicted_pips_ensemble | Pips preditos |
| actual_price | Preço real que aconteceu |
| actual_pips | Pips reais |
| signal_status | SEND ou FILTERED |

### SEND_DAILY_SUMMARY_EURUSD.csv

| Coluna | Significado |
|--------|-----------|
| date | Data |
| send_time | Timestamp do SEND daquele dia |
| send_confidence | Confidence do SEND |
| send_confluence | Confluence do SEND |
| send_pips | Pips do SEND |
| filtered_count | Quantos FILTERED houve naquele dia |
| best_filtered_confidence | Confidence do melhor FILTERED |
| best_filtered_confluence | Confluence do melhor FILTERED |

---

## ✅ Recomendação para Começar

**Ordem de leitura:**
1. ✅ **SEND_DAILY_SUMMARY_EURUSD.csv** (30 minutos)
   - Entender visão geral
   - Ver distribuição de SEND/FILTERED
   - Identificar padrões

2. ✅ **SEND_ANALYSIS_EURUSD.csv** (análise detalhada)
   - Filtrar SEND apenas
   - Analisar outliers
   - Validar qualidade

3. ✅ **results/backtest_EURUSD_chronological.csv** (contexto)
   - Entender indicadores
   - Traçar gráficos
   - Análise técnica

---

## 📞 Próximas Ações

Com esses arquivos, você pode:
- [ ] Validar se os SEND foram realmente os melhores do dia
- [ ] Identificar padrões de quando SEND é bom/ruim
- [ ] Quantificar oportunidades perdidas (FILTERED)
- [ ] Decidir se precisa mudar os filtros
- [ ] Exportar para BI/análise mais profunda
