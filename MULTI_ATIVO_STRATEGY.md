# 📊 ESTRATÉGIA MULTI-ATIVO - QUAL AVALIAR? COMO ADICIONAR?

## 1️⃣ Quais Ativos Temos que Avaliar?

### Critério de Seleção

**Você tem 2 opções:**

### OPÇÃO A: Conservative (Recomendado para Iniciar)
```
Ativos para Começar:
├─ EURUSD (já temos backtest completo)
├─ GBPUSD (similar, alta liquidez)
└─ USDJPY (correlação baixa, diversifica)

Motivo:
  ✅ Pares maiores (high liquidity)
  ✅ Mais previsíveis (menos ruído)
  ✅ Dados históricos abundantes
  ✅ Features SMC se aplicam bem
```

### OPÇÃO B: Aggressive (Máximo Volume)
```
Ativos para Expandir:
├─ EURUSD   (já temos modelo)
├─ GBPUSD   
├─ USDJPY   
├─ AUDUSD   
├─ NZDUSD   
├─ USDCAD   
├─ GOLD     (XAU/USD - você tem dados!)
└─ Até 8-10 ativos

Motivo:
  ✅ Mais oportunidades = mais trades
  ✅ Diversificação de risco
  ✅ Descobrir qual ativo melhor
  ✅ Correlação entre pares
```

---

## 2️⃣ Como Adicionar EA no MT5 para Cada Ativo?

### Passo 1: Preparar EA Genérico

Atualmente você tem: `options.mq5` (hardcoded para EURUSD M15)

**Precisa:** Versão que funcione em qualquer símbolo

```mql5
// Antes (hardcoded):
// Só funciona em EURUSD M15

// Depois (genérico):
// Funciona em EURUSD, GBPUSD, GOLD, etc
// Funciona em M15, H1, D1, etc
```

### Passo 2: Clonar EA para Cada Ativo

No MT5:
```
MQL5/Experts/

├─ options_EURUSD_M15.mq5      ← Cópia para EUR/USD
├─ options_GBPUSD_M15.mq5      ← Cópia para GBP/USD
├─ options_GOLD_M15.mq5        ← Cópia para GOLD
├─ options_USDJPY_M15.mq5      ← Cópia para USD/JPY
└─ (etc)
```

### Passo 3: Adicionar EA no Gráfico

**No MT5 - Manual (hoje):**
1. Abra EURUSD M15
2. Clique direito na aba do gráfico
3. "Adicionar EA"
4. Selecione: options_EURUSD_M15
5. Configure: Server=127.0.0.1, Port=8765
6. Repita para GBPUSD, GOLD, etc

**Automático (próximas semanas):**
```python
# Script que: 
# 1. Compila EA para cada ativo
# 2. Adiciona aos gráficos automaticamente
# 3. Configura mesmos parâmetros
```

---

## 3️⃣ Para Backtest: Como Definir Qual Ativo?

### Arquitetura Backtest Multi-Ativo

```python
# backtest_realistic_v2.py (HOJE - só EURUSD)
python3 backtest_realistic_v2.py --symbol EURUSD

# backtest_multi_ativo.py (PRÓXIMAS SEMANAS)
python3 backtest_multi_ativo.py \
  --symbols EURUSD,GBPUSD,GOLD,USDJPY \
  --timeframe M15 \
  --start 2023-01-01 \
  --end 2026-05-24 \
  --output results/
```

### O que Seria Testado

```
Para CADA ativo:
  ├─ Win rate: triggers vs 20:00
  ├─ Profit: total pontos ganhos
  ├─ Drawdown: queda máxima
  ├─ Sharpe ratio: retorno ajustado risco
  ├─ Recomendação melhor: CALL vs PUT
  └─ Strike ótimo: qual distância melhor?

Comparação final:
  ├─ EURUSD: 99.97% win rate (melhor)
  ├─ GBPUSD: 98.5% win rate
  ├─ GOLD: 95.2% win rate
  └─ Conclusão: EURUSD é mais previsível
```

---

## 🎯 Recomendação: Por Onde Começar?

### HOJE (Próximas horas)
```
✅ 1. Ativar EURUSD M15 com EA (já pronto)
   └─ Confirmar dados chegando via HTTP POST
   └─ Confirmar sinais no Telegram

✅ 2. Deixar rodando 24h
   └─ Validar que sinais chegam em tempo real
   └─ Ver se preço concorda com recomendação
```

### ESTA SEMANA
```
☐ 1. Backtest em EURUSD apenas (confirmar sistema funciona)
     $ python3 backtest_realistic_v2.py

☐ 2. Se resultado bom (>50% win rate):
     └─ Adicionar GBPUSD + GOLD ao vivo
     └─ Deixar rodando 1 semana
     └─ Monitorar sinais

☐ 3. Comparar qual ativo é melhor:
     ├─ EURUSD: Quantos sinais? Win rate?
     ├─ GBPUSD: Quantos sinais? Win rate?
     └─ GOLD: Quantos sinais? Win rate?
```

### PRÓXIMAS 2 SEMANAS
```
☐ 1. Backtest multi-ativo (criar script novo)
     $ python3 backtest_multi_ativo.py --symbols EURUSD,GBPUSD,GOLD

☐ 2. Treinar modelos específicos por ativo
     ├─ model_EURUSD_direction.pkl
     ├─ model_GBPUSD_direction.pkl
     └─ model_GOLD_direction.pkl

☐ 3. Adicionar até 5 ativos ao vivo
     └─ Monitorar 1 semana
     └─ Validar correlação
```

---

## 🔧 Implementação Técnica (Para Desenvolvedores)

### Como Adicionar EA no MT5 Programaticamente

```mql5
// options_multi_ativo.mq5 (VERSÃO GENÉRICA)

#property strict

input string ServerIP = "127.0.0.1";        // IP do servidor Python
input int ServerPort = 8765;                // Porta
input string ConfigSymbol = "";             // Symbol (vazio = usar _Symbol atual)
input string ConfigTimeframe = "";          // Timeframe (vazio = usar _Period atual)

string symbol = ConfigSymbol != "" ? ConfigSymbol : _Symbol;
string timeframe = ConfigTimeframe != "" ? ConfigTimeframe : TimeframeLabel();

void OnTick() {
    // Calcula features
    // Envia POST para ServerIP:ServerPort/mt5/candle
    // Dados include: symbol, timeframe, OHLC, features
}
```

### Modo de Uso no MT5

```
1. Compile: Alt+F9
2. Clique direito gráfico EURUSD M15
   └─ Adicionar EA: options_multi_ativo
   └─ Inputs:
      ├─ ServerIP: 127.0.0.1
      ├─ ServerPort: 8765
      └─ ConfigSymbol: (deixar vazio = auto)

3. Clique direito gráfico GBPUSD M15
   └─ Adicionar EA: options_multi_ativo
   └─ Inputs: (mesmos parâmetros)

4. Cada EA envia para:
   ├─ /mt5/candle?symbol=EURUSD&timeframe=M15
   ├─ /mt5/candle?symbol=GBPUSD&timeframe=M15
   └─ Server diferencia automaticamente
```

---

## 📊 Estrutura de Dados Multi-Ativo

### Servidor Python (mt5_realtime_server.py)

```python
# Organiza dados por ativo
/analytics/realtime/

├─ latest_EURUSD_M15.json      # Último candle EUR
├─ stream_EURUSD_M15.ndjson    # Histórico EUR (append-only)
├─ latest_GBPUSD_M15.json      # Último candle GBP
├─ stream_GBPUSD_M15.ndjson    # Histórico GBP
├─ latest_GOLD_M15.json        # Último candle GOLD
└─ stream_GOLD_M15.ndjson      # Histórico GOLD
```

### Inference Engine

```python
# Processa cada ativo independentemente
for symbol in ["EURUSD", "GBPUSD", "GOLD"]:
    for timeframe in ["M15", "H1"]:
        json_file = f"latest_{symbol}_{timeframe}.json"
        
        if arquivo_mudou(json_file):
            signal = inference_engine.infer(
                symbol=symbol,
                timeframe=timeframe,
                features=load_json(json_file)
            )
            
            # Envia Telegram com símbolo
            telegram.send(f"📊 {symbol} M15: {signal}")
```

---

## ✅ Checklist: Começar Multi-Ativo

### HOJE
```
☐ Chat ID configurado (261535283)         ✅ FEITO
☐ .env salvo com Telegram                 ✅ FEITO
☐ EA rodando em EURUSD M15                ⏳ PRÓXIMO
☐ Sinais chegando no Telegram             ⏳ PRÓXIMO
```

### ESTA SEMANA
```
☐ Confirmar EURUSD funciona 24h
☐ Adicionar GBPUSD M15
☐ Monitorar sinais em tempo real
☐ Backtest: EURUSD vs 20:00
```

### PRÓXIMAS SEMANAS
```
☐ Adicionar GOLD + 1-2 mais ativos
☐ Backtest multi-ativo
☐ Treinar modelos específicos
☐ Validar qual ativo melhor
```

---

## 🎯 Resposta Rápida às Suas 3 Perguntas

### Q1: Quais ativos avaliar?
**A:** Comece com EURUSD (já tem). Depois GBPUSD + GOLD (dados disponíveis).

### Q2: Adicionar EA em cada ativo?
**A:** Sim, clone options.mq5 para cada ativo. Deixe genérico para funcionar em qualquer symbol.

### Q3: Para BT, como definir qual ativo?
**A:** Crie script `backtest_multi_ativo.py` que testa todos. Compare win rates por ativo.

---

## 🚀 Próximo Passo (Recomendado)

```bash
# 1. Rodar sistema em tempo real
python3 /home/ubuntu/pessoal/options/realtime_executor.py

# 2. (Em outra janela) Monitorar logs
tail -f /home/ubuntu/pessoal/options/logs/mt5_realtime_server.log

# 3. Quando sinais chegarem no Telegram:
#    ✅ Significa EURUSD está funcionando
#    ✅ Próximo passo: Adicionar GBPUSD + GOLD
```

---

**Data:** 2026-05-24  
**Chat ID:** ✅ 261535283 (Salvo)  
**Status:** Pronto para Múltiplos Ativos  
**ETA para Multi-Ativo:** 1-2 semanas
