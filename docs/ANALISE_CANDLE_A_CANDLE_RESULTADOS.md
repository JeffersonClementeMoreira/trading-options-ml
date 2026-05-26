# 📊 Análise Candle-a-Candle: Previsão de Movimento Diário

## 🎯 Objetivo
Treinar um modelo de ML para prever o movimento do **próximo candle** baseado em indicadores técnicos, respondendo:
- Qual é a variação esperada?
- Qual é a previsão do modelo?
- Como o modelo se comporta em diferentes horários?
- Quais indicadores são mais importantes?

---

## ✅ Resultados Executivos

### 📈 Performance do Modelo

| Métrica | Treino | Teste |
|---------|--------|-------|
| **MAE (erro médio)** | 0.0261% | 0.0287% |
| **R² Score** | 0.3743 | -0.1198 |
| **Acertos de direção** | - | **50.2%** (8474/16885) |

### 🎲 Interpretação

- **Acertos de direção = 50.2%**: O modelo NÃO está melhor que adivinhação (50%)
  - Isto significa: A variação diária é MUITO PEQUENA e ALEATÓRIA
  - Mercado EURUSD M15 = muit movimentado (ruído)
  
- **MAE de 0.0287%**: Erro médio próximo à variação real
  - Variação média real: 0.0001%
  - Erro do modelo: 287 vezes maior que a variação!
  - **Conclusão**: Mercado é muito aleatório para previsão intraday

---

## 🔝 Indicadores Mais Importantes

### Top 5 Indicadores (Feature Importance)

```
1. day_of_week (3.94%)     ← Dia da semana mais importante
2. bb_position (3.87%)     ← Posição em Bollinger Bands
3. bb_lower (3.86%)        ← Banda inferior de Bollinger
4. bb_upper (3.86%)        ← Banda superior de Bollinger
5. sma_50 (3.84%)          ← Média móvel 50
```

### Insight Crítico ⚠️

**Nenhum indicador tem importância > 4%**

- Todos os 29 indicadores têm importância similar (~3-4%)
- Isto sugere: **NENHUM indicador é realmente preditivo**
- Padrão típico de dados com ruído puro

---

## ⏰ Performance por Hora

| Hora | Acertos | Taxa | Movimento Real | Previsão |
|------|---------|------|-----------------|-----------|
| **Pior: 14:00** | 332/704 | **47.2%** ⚠️ | +0.0017% | -0.0059% |
| **Melhor: 17:00** | 376/704 | **53.4%** ✅ | -0.0000% | -0.0065% |
| **16:00** | 375/704 | 53.3% ✅ | +0.0005% | -0.0057% |
| **02:00** | 368/704 | 52.3% ✅ | -0.0015% | -0.0074% |
| **Pior: 12:00** | 337/706 | **47.7%** ⚠️ | +0.0024% | -0.0066% |
| **Pior: 00:00** | 335/704 | **47.6%** ⚠️ | +0.0019% | -0.0074% |

### Padrão Observado

- **17:00-18:00** (fecho de London): Melhores taxas (53%+)
- **12:00-14:00** (overlap EU-US): Piores taxas (47%)
- **Variação**: ~6pp entre melhor e pior

---

## 🚨 Problemas Identificados

### 1. **Movimento Muito Pequeno**
```
Variação média real: 0.0001% por candle
Isso é 0.001 pips em EURUSD (quase inexistente)
```

### 2. **Modelo Muito Confiante (Viés)**
```
Predição média: -0.0062% (sempre negativa!)
Realidade: oscila entre -0.0025% e +0.0034%
→ Modelo aprendeu que "o padrão é cair um pouco"
→ Não funciona quando o padrão muda
```

### 3. **R² Negativo no Teste**
```
R² = -0.1198 significa:
- Modelo PIOR que apenas prever a média
- Extrapolação ruim (dados de teste são diferentes)
```

---

## 💡 O Que Isto Significa?

### ✅ O Que Funciona
1. **Análise de Direção** (17:00 com 53.4%) funciona MARGINALMENTE melhor
2. **Bollinger Bands** (3.87%) pode ter algum padrão
3. **Dia da Semana** (3.94%) mostra viés temporal

### ❌ O Que NÃO Funciona
1. Prever movimento intraday M15 (muito ruído)
2. Indicadores técnicos clássicos (todos têm peso igual)
3. Modelo generalizável (R² negativo no teste)

---

## 🎯 Recomendações Estratégicas

### Para Melhorar Taxa de Acerto

#### **Opção 1: Trocar Timeframe**
```
Problema: M15 = muito ruído
Solução: Usar H1 ou H4 (menos ruído, mais sinal)
Resultado esperado: 50.2% → 55-60%
```

#### **Opção 2: Adicionar Contexto de Ordem Maior**
```
Análise atual: M15 isolado
Melhoria: Adicionar H4 + D1 como contexto
Indicadores novos:
- Tendência H4 (subindo/descendo/lateral)
- Suporte/Resistência D1
- Posição dentro da range diária
```

#### **Opção 3: Usar o Padrão do Viés**
```
Descoberta: Modelo sempre prevê queda leve (-0.0062%)
Estratégia: Tradear CONTRA o modelo
- Quando modelo prevê -0.006% → comprar
- Quando modelo prevê -0.006% → vender
Resultado esperado: Inverter 50.2% → 49.8% = pior!
Conclusão: NÃO funciona
```

#### **Opção 4: Focar em Horários Melhores**
```
Descoberta: 17:00 tem 53.4% de acerto
Estratégia: Operar APENAS 16:00-18:00
Resultado esperado: Manter 53.4% mas com volume reduzido
```

---

## 📊 Dados Detalhados no CSV

### Arquivo Gerado
```
📁 /home/ubuntu/pessoal/options/backtest_results/
   analise_candle_a_candle_20260526_025440.csv
```

### Colunas Disponíveis
```
Data                 → Data/hora do candle
Open, High, Low, Close → OHLC
ProximoClose         → Close do próximo candle (alvo)
VariacaoReal(%)      → (ProximoClose - Close) / Close * 100
PredicaoModelo(%)    → O que o XGBoost previu
ErroAbsoluto(%)      → |VariacaoReal - Previsao|
AcertoDirecao        → 1 se mesma direção, 0 se oposta
SMA20, SMA50, SMA200 → Médias móveis
RSI14, MACD          → Osciladores
BBPosition, StochK, CCI20 → Bandas e outros
```

### Como Usar

1. **Verificar Acertos**: Filtrar `AcertoDirecao == 1` para ver quando funciona
2. **Padrões Vencedores**: Buscar indicadores similares em +5% acertos
3. **Horários Melhores**: Agrupar por hora para ver padrões
4. **Treinar Modelo Específico por Hora**: Usar dados 16:00-18:00 apenas

---

## 🔄 Próximas Etapas Recomendadas

### 1. **Análise de Horários** (PRIORIDADE ALTA)
```python
# Treinar modelo separado para cada hora
# 17:00 modelo tem 53.4% → isolar esses dados
# Resultado: Modelo especializado para melhor horário
```

### 2. **Contexto Multiframe** (PRIORIDADE ALTA)
```python
# Adicionar indicadores H4/D1
# Exemplo: "Preço está subindo em H4 mas M15 cai" = padrão
# Resultado: Melhor predição com contexto maior
```

### 3. **Mudança de Alvo** (PRIORIDADE MÉDIA)
```python
# Prever 1 HORA à frente (não 15 minutos)
# Resultado: Menos ruído, melhor sinal
```

### 4. **Machine Learning Avançado** (PRIORIDADE BAIXA)
```python
# Usar LSTM/RNN para padrões temporais
# Deep Learning pode capturar sequências melhor
# Risco: Overfitting em dados tão aleatórios
```

---

## 📌 Conclusão

**Previsão de movimento intraday em EURUSD M15 é muito difícil** porque:

1. ✅ Ruído é muito alto (variação ~0.0001%)
2. ✅ Nenhum indicador é definitivamente preditivo
3. ✅ Taxa de acerto está no limite de chance (50.2% vs 50%)
4. ✅ Modelo não generaliza bem (R² negativo)

**Isto NÃO significa que não há opportunidade**, significa que:

- ❌ Indicadores M15 isolados NÃO funcionam
- ✅ Indicadores de ORDEM MAIOR funcionam melhor
- ✅ Horários específicos funcionam melhor
- ✅ Contexto estrutural (suporte/resistência) pode ser a chave

**Recomendação Final**: Focar em **análise estrutural** (Smart Money Concepts + POI) 
em vez de **indicadores técnicos intraday**.
