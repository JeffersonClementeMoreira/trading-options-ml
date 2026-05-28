# ❓ FAQ: Dúvidas sobre config.json e Novos Ativos

## Pergunta 1: "Como descrevo ativos sem pares como GOLD ou SP500?"

### Resposta:

O `config.json` foi atualizado para suportar isso! Use o campo `asset_type`:

**Antes (limitado):**
```json
"pairs": ["EUR", "USD"]  // Assumia pares de moedas
```

**Agora (flexível):**
```json
// Forex (tem par)
"base": "EUR", "quote": "USD"

// Commodity (tem contra-moeda)
"base": "GOLD", "quote": "USD"

// Índice (SEM par!)
"base": "SPX", "quote": null  // null = não tem segundo ativo
```

**Exemplos:**
```json
// GOLD (Commodity)
"GOLD": {
  "asset_type": "commodity",
  "base": "GOLD",
  "quote": "USD",
  "description": "Ouro em dólares"
}

// SP500 (Índice - sem par!)
"SP500": {
  "asset_type": "index",
  "base": "SPX",
  "quote": null,  // ← Aqui é null!
  "description": "S&P 500 Index"
}

// BTCUSD (Crypto - tem par)
"BTCUSD": {
  "asset_type": "crypto",
  "base": "BTC",
  "quote": "USD",
  "description": "Bitcoin em dólares"
}
```

---

## Pergunta 2: "O que significa 'Ready for setup'?"

### Resposta:

É apenas uma ANOTAÇÃO no campo `notes`. O que realmente importa é `enabled`:

```json
"AUDUSD": {
  "enabled": false,  // ← ISTO define se está "ready"!
  "description": "Australian Dollar vs US Dollar (M15)",
  "notes": "Ready for setup"  // ← Isto é só documentação
}
```

**Significado:**
- `"enabled": false` = Não será rodado automaticamente
- `"notes": "Ready for setup"` = Está pronto, apenas aguardando ativação

**Como ativar:**
```json
// Mudar apenas esta linha:
"enabled": true

// Depois:
python3 src/run_full_pipeline.py AUDUSD
```

**Status possíveis:**
```json
"enabled": true,   "notes": "Active"          // Ativo, roda com --all
"enabled": false,  "notes": "Ready for setup" // Pronto, aguardando teste
"enabled": false,  "notes": "Needs data"      // Falta arquivo CSV
"enabled": false,  "notes": "Experimental"    // Em fase de teste
```

---

## Pergunta 3: "Onde consigo essas informações para adicionar um novo ativo?"

### Resposta:

Existem 4 métodos principais:

### Método 1: MetaTrader 5 (RECOMENDADO ⭐)

```
1. Abrir MT5
2. Procurar o símbolo (ex: "GOLD", "SPX", "DAX")
3. Clicar direita no símbolo
4. Selecionar "Propriedades" ou "Informações"
5. Ver na aba "Geral" ou "Negociação":
   ├─ Spread (para "spread_typical")
   ├─ Ponto (para "pip_value")
   ├─ Horários de negociação (para "closing_time" e "active_hours")
   └─ Fuso horário (para "timezone")
```

**Exemplo prático MT5:**
```
Símbolo: GOLD
Propriedades:
  Spread: 0.3
  Ponto: 0.01
  Horários: 00:00-23:59
  Fuso horário: UTC
  Fecha em: 17:00 UTC

Resultado config.json:
  "pip_value": 0.01
  "spread_typical": 0.3
  "closing_time": "17:00"
  "timezone": "UTC"
```

### Método 2: TradingView

```
1. Abrir gráfico do ativo (ex: "GOLD", "SPX")
2. Clicar no nome do símbolo no topo
3. "More info" ou seta → mostra:
   ├─ Exchange
   ├─ Horários de negociação
   ├─ Spread typical
   └─ Tipo de ativo
```

### Método 3: Sites Oficiais

**Para Commodities e Índices:**
- CME Group: cmegroup.com (commodities)
  - GOLD, SILVER, OIL, etc
  - Horários e especificações
  
- EUREX: eurex.com (índices europeus)
  - DAX, EuroStoxx, etc
  - Horários de trading
  
- NYSE: nyse.com (índices US)
  - SP500, NASDAQ
  - Horários de trading

**Para Forex:**
- OANDA: oanda.com
- IG Markets: ig.com
- XM: xm.com

### Método 4: Documentação do Broker

```
1. Abrir site do seu broker (IG, OANDA, etc)
2. Procurar "Especificações do instrumento"
3. Buscar seu ativo
4. Encontrar:
   ├─ Pip value / Point size
   ├─ Spread típico
   ├─ Horários de negociação
   └─ Fuso horário
```

---

## Pergunta 4: "SP500 vence às 20:00, não 14:00. Como mudo isso facilmente?"

### Resposta:

Basta mudar o campo `closing_time` em `config.json`!

```json
// EURUSD (fecha 14:00 UTC)
"EURUSD": {
  "closing_time": "14:00"  // ← Aqui!
}

// SP500 (fecha 20:00 UTC = 4:00 PM ET)
"SP500": {
  "closing_time": "20:00"  // ← Mudou!
}

// GOLD (fecha 17:00 UTC)
"GOLD": {
  "closing_time": "17:00"  // ← Aqui!
}

// DAX (fecha 22:00 UTC = 8:00 PM CET)
"DAX": {
  "closing_time": "22:00"  // ← Mudou!
}
```

### ⚠️ IMPORTANTE: Conversão de Fusos Horários

O `closing_time` **SEMPRE** deve estar em **UTC**!

**Exemplo SP500:**
```
NYSE fecha: 16:00 ET (4:00 PM Eastern Time)

Conversão:
  • EDT (Daylight, verão): 16:00 ET = 20:00 UTC
  • EST (Standard, inverno): 16:00 ET = 21:00 UTC

Resultado:
  "closing_time": "20:00"  // Use durante EDT (maioria do ano)
  // Ou mude para "21:00" se quiser cobrir EST também
```

**Tabela de Conversão Rápida:**
```
Horário Local → UTC (atenção a horário de verão!)

4:00 PM ET (EDT) → 20:00 UTC
4:00 PM ET (EST) → 21:00 UTC

8:00 PM CET (CEST) → 18:00 UTC  (verão)
8:00 PM CET (CET) → 19:00 UTC   (inverno)

5:00 PM GMT (BST) → 16:00 UTC   (verão)
5:00 PM GMT (GMT) → 17:00 UTC   (inverno)
```

### Mudança Prática:

```json
// Antes (EURUSD)
"EURUSD": {
  "closing_time": "14:00",
  "timezone": "UTC"
}

// Depois (SP500)
"SP500": {
  "closing_time": "20:00",      // ← Mudou para 20:00
  "timezone": "US/Eastern"      // ← Referência do fuso
}
```

### Teste Rápido:

Depois de mudar `closing_time`, rodar:

```bash
python3 src/run_full_pipeline.py SP500

# Ver se os preços D+1 fazem sentido
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('results/UNIFIED_SIGNALS_SP500.csv')
print(df[['Signal Time (ENTRY)', 'Actual Close D+1']].head(10))
EOF
```

Se os preços parecem aleatórios ou muito diferentes, `closing_time` estava errado!

---

## Pergunta 5: "E se quiser mudar o horário para todos os forex?"

### Resposta:

Basta mudar em TODOS os forex em config.json:

```json
"EURUSD": {
  "closing_time": "16:00"  // Mudou de 14:00
},
"GBPUSD": {
  "closing_time": "16:00"  // Mudou de 14:00
},
"AUDUSD": {
  "closing_time": "16:00"  // Mudou de 14:00
},
// ... e assim por diante
```

**Ou use um script Python:**

```python
import json

# Carregar config
with open('config.json', 'r') as f:
    config = json.load(f)

# Mudar closing_time de todos os forex
for symbol, data in config['assets'].items():
    if data.get('asset_type') == 'forex_pair':
        data['closing_time'] = '16:00'  # Novo horário

# Salvar
with open('config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Atualizado!")
```

---

## Pergunta 6: "Qual é o impacto de mudar closing_time?"

### Resposta:

**CRÍTICO!** Muda COMPLETAMENTE o treinamento:

```
closing_time = "14:00" vs "16:00"
  ├─ Preço-alvo muda (busca candle diferente)
  ├─ Indicadores técnicos mudam
  ├─ Win rate pode aumentar ou cair significativamente
  └─ Pode ser mais rentável OU menos!

Exemplo EURUSD:
  closing_time: "14:00"
    └─ 87/101 WIN (86.1%), +484.90 pips
  
  closing_time: "16:00"  
    └─ Possivelmente: 75/101 WIN (74.3%), -200 pips
    (números ilustrativos, vai depender dos dados)
```

**Recomendação:**
1. Treinar com closing_time original
2. Ver performance
3. Se quiser testar outro horário, treinar TUDO de novo
4. Comparar resultados
5. Escolher o melhor

---

## Pergunta 7: "Posso ter diferentes closing_time para diferentes operações?"

### Resposta:

NÃO no config.json atual, mas pode criar configs separadas:

```bash
# config-14h.json
# closing_time: 14:00

# config-16h.json
# closing_time: 16:00

# config-18h.json
# closing_time: 18:00

# Testar cada uma:
python3 src/run_full_pipeline.py EURUSD --config config-14h.json
python3 src/run_full_pipeline.py EURUSD --config config-16h.json
python3 src/run_full_pipeline.py EURUSD --config config-18h.json

# Comparar outputs:
python3 << 'EOF'
import pandas as pd
for hour in ['14h', '16h', '18h']:
    df = pd.read_csv(f'results/UNIFIED_SIGNALS_EURUSD_config-{hour}.csv')
    wr = (df['Result']=='WIN').sum() / len(df) * 100
    pips = df['Actual Pips'].sum()
    print(f"{hour}: {wr:.1f}% WR, {pips:+.0f} pips")
EOF
```

---

## Pergunta 8: "Onde vejo o closing_time em tempo real?"

### Resposta:

Depois de rodar o pipeline:

```bash
# Ver CSV unificado
head -2 results/UNIFIED_SIGNALS_EURUSD.csv | cut -d',' -f1-8

# Saída:
Nº,Signal Time (ENTRY),Entry Price,Direction,Confidence %,Refinement,Target Predicted,Target Price
1,2025-09-04 00:15:00,1.16595,DOWN,99.33...,0.6071...,1.16606...,1.16606...
```

A coluna `Signal Time (ENTRY)` mostra o horário real que o sistema usou como "fechamento do dia".

```python
import pandas as pd
df = pd.read_csv('results/UNIFIED_SIGNALS_EURUSD.csv')

# Ver horário de entrada
print(df['Signal Time (ENTRY)'].unique()[:10])

# Saída possível:
# 2025-09-04 00:15:00
# 2025-09-10 04:45:00
# 2025-09-11 02:00:00
# ... (muitos horários diferentes, normal!)

# Para ver em qual horário mais sinais aparecem:
print(df['Signal Time (ENTRY)'].dt.hour.value_counts().sort_index())
```

---

## Pergunta 9: "Como garantir que closing_time está correto?"

### Resposta:

**Checklist de Validação:**

```python
import pandas as pd

df = pd.read_csv('results/UNIFIED_SIGNALS_EURUSD.csv')

# 1. Ver distribuição de horários
print("Horários que aparecem:")
print(df['Signal Time (ENTRY)'].dt.hour.value_counts().sort_index())

# 2. Ver preço actual D+1 (deve fazer sentido)
print("\nPreços reais D+1:")
print(df[['Signal Time (ENTRY)', 'Actual Close D+1']].head(20))

# 3. Comparar com preço predito
print("\nErro de predição:")
df['pred_error'] = abs(df['Target Predicted'] - df['Actual Close D+1'])
print(df[['Target Predicted', 'Actual Close D+1', 'pred_error']].head(10))

# Se pred_error está muito alto (ex: > 50 pips para EURUSD),
# closing_time pode estar errado!
```

---

## Pergunta 10: "Posso usar isso com ativos que não tenho em MT5?"

### Resposta:

SIM! Desde que tenha dados M15:

```
Fontes de dados M15:
  ✅ MetaTrader 5 (melhor, mais aceito)
  ✅ TradingView (exportar candles)
  ✅ Yahoo Finance (alguns ativos)
  ✅ Alpha Vantage (API)
  ✅ Quandl (dados de qualidade)
  ✅ Seu broker (muitos permitem download)

Requisitos:
  ├─ Formato: CSV tab-separated
  ├─ Colunas: date, time, open, high, low, close, tickvol, vol, spread
  ├─ Data: Pelo menos 50,000 candles (idealmente)
  └─ Período: Contínuo (sem gaps grandes)
```

**Exemplo com TradingView:**
```
1. Abrir gráfico em TradingView (ex: "BTCUSD")
2. 3 pontos "..." → "Export chart data"
3. Selecionar período desejado
4. Download como CSV
5. Converter para formato MT5 (se necessário)
6. Adicionar em config.json
7. Rodar: python3 src/run_full_pipeline.py BTCUSD
```

---

## Resumo Executivo

| Pergunta | Resposta Rápida |
|----------|-----------------|
| **GOLD ou SP500?** | Use `base` e `quote`, com `asset_type` |
| **"Ready for setup"?** | Significa `enabled: false`, pronto pra testar |
| **Onde achar info?** | MT5 (propriedades), TradingView, CME, broker docs |
| **Mudar closing_time?** | Editar campo em config.json, é tudo! |
| **SP500 20:00?** | Mudar `closing_time: "20:00"` (em UTC!) |
| **Impacto?** | CRÍTICO - treinar tudo de novo, testar |
| **Múltiplos horários?** | Criar configs separados e comparar |
| **Validar?** | Ver distribuição de horários e preços |
| **Sem MT5?** | Usar TradingView, Yahoo Finance, ou broker |

---

**Documentação completa:** `docs/CONFIG_JSON_GUIDE.md`  
**Config template:** `config.json` (leia comentários)  
**Version:** 1.0.0+ support  
**Status:** ✅ Production Ready
