# 📊 CONFIGURAÇÃO DE TREINO E RECOMENDAÇÃO DE ESTRATÉGIAS DE OPÇÕES

## 1️⃣ CONFIGURAÇÃO ATUAL DE TREINO

### 🎯 Ativo e Dados

**Arquivo de Dados:**
```
/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv
```

**Especificações:**
```
Ativo:           EURUSD (Euro vs Dólar)
Timeframe:       M15 (15 minutos)
Data Início:     2023-01-01 22:00
Data Fim:        2026-05-22 20:15
Total Candles:   84,352 candles
Período:         ~3 anos e 5 meses
Volume de Dados: ~17 MB
```

### 📈 Split dos Dados

**Treino/Test Split:**
```
Total:    84,352 candles (100%)
├─ Treino: 67,481 candles (80%)
└─ Teste:  16,871 candles (20%)

Split Type: Temporal (sem shuffle)
Razão: Preservar sequência temporal para séries financeiras
```

**Distribuição da Target:**
```
UP moves (class 1):   ~50.5% (média histórica)
DOWN moves (class 0): ~49.5% (média histórica)
Balance: Bem balanceado (não precisa de balancing)
```

### 🔧 Hiperparâmetros XGBoost

```python
XGBClassifier(
    n_estimators=150,        # 150 árvores (vs 100 baseline)
    max_depth=7,             # Profundidade 7 (captura interações)
    learning_rate=0.08,      # Taxa de aprendizado moderada
    subsample=0.8,           # 80% das amostras por árvore
    colsample_bytree=0.9,    # 90% das features por árvore
    min_child_weight=1,      # Mínimo de amostras por folha
    gamma=0.5,               # Regularização L1/L2
    random_state=42,         # Reprodutibilidade
    eval_metric="logloss",
    verbosity=0
)
```

### 📊 Features Utilizadas

**Total: 60 Features** (aumentado de 27)

```
Technical Indicators:       5 features
  • SMA20, SMA50
  • EMA12, EMA26
  • ATR%

Trend Features:             5 features
  • price_above_sma20
  • price_above_sma50
  • sma_alignment
  • momentum_score
  • trend_confirmation

Volatility Features:        3 features
  • vol_normalized
  • vol_spike
  • vol_trend

Price Action:               3 features
  • candle_body_percent
  • close_position
  • range_expansion

SMC Top5:                   5 features
  • dist_top_liquidity
  • dist_bottom_liquidity
  • vol_regime
  • premium_discount_score
  • range_duration

SMC Context:                7 features
  • bull_fvg_count
  • bear_fvg_count
  • fvg_pressure
  • bos_bull_count
  • bos_bear_count
  • candles_since_choch
  • choch_type

Advanced Indicators:       22 features ⭐ NEW
  • sweep_strength, is_strong_sweep
  • displacement, directional_displacement
  • momentum_burst, exhaustion
  • break_high, break_low, break_strength
  • flow, flow_acceleration, flow_volatility
  • pos_range, dist_mean, zscore
  • atr_pct, vol_regime, vol_expansion
  • reversal_score

Composite Features:         7 features ⭐ NEW
  • sweep_displacement
  • break_momentum
  • position_quality
  • vol_context
  • ema_alignment
  • entry_score (0-100) ⭐ MAIN GATE
  • setup_readiness

Derivative Features:        3 features
  • liquidity_pressure
  • smc_confluence
  • trend_clarity
```

### 🎯 Target Definition

**OLD (Incorreto):**
```python
next_close = df["close"].shift(-96)
# Problemas:
# - 96 é um número fixo
# - 96 candles ≠ sempre 24h (ex: 16:00 entry = 22h, não 24h)
# - Bias sistemático na target
```

**NEW (Correto - Dynamic):**
```python
# Para cada candle, calcula quantos candles até D+1 às 14:00
# Resultado: 60-150 candles (média 126.1)
# Sem bias sistemático

for i in range(len(df)):
    current_ts = df.index[i]
    target_ts = pd.Timestamp(current_day) + pd.Timedelta(days=1, hours=14)
    
    # Skip weekends
    while target_ts.weekday() >= 5:
        target_ts += pd.Timedelta(days=1)
    
    # Encontra o close no target_ts ou após
    candidates = df[df.index >= target_ts]
    if candidates.empty:
        continue
    
    next_close = candidates.iloc[0]["close"]
    
    # Target: 1 se UP, 0 se DOWN
    y = 1 if next_close > current_close else 0
```

### 📝 Como Executar

```bash
cd /home/ubuntu/pessoal/options

# Treino com config padrão
python3 train_enhanced_model.py

# Treino com arquivo customizado
python3 train_enhanced_model.py --data /caminho/novo.csv

# Mudar tamanho de teste (default 0.2)
python3 train_enhanced_model.py --test-size 0.3

# Especificar diretório de saída
python3 train_enhanced_model.py --output /novo/caminho/models
```

---

## 2️⃣ NOVO SISTEMA: RECOMENDAÇÃO DE ESTRATÉGIA DE OPÇÕES

### 🎯 Conceito

Após XGBoost prever UP ou DOWN, analisar:
1. **Força da previsão** (probabilidade do modelo)
2. **Volatilidade implícita** (IV)
3. **Moneyness** (distância do strike vs spot)
4. **Tempo até expiração** (DTE)
5. **Risk/Reward esperado**

E recomendar a melhor estratégia dentre as disponíveis.

### 📊 Estratégias de Opções Disponíveis

```
┌─ DIRECTIONAL STRATEGIES (Aposta clara em direção)
│
├─ 🟢 CALL (Bullish, Risco Limitado)
│  Quando: Previsão UP forte (prob >= 0.65)
│  Ideal para: IV baixo, DTE médio
│  Max Loss: Prêmio pago
│  Max Gain: Ilimitado
│
├─ 🔴 PUT (Bearish, Risco Limitado)
│  Quando: Previsão DOWN forte (prob >= 0.65)
│  Ideal para: IV baixo, DTE médio
│  Max Loss: Prêmio pago
│  Max Gain: Ilimitado
│
├─ 🟡 CALL SPREAD (Bullish, Risco/Reward controlado)
│  Quando: Previsão UP moderada (prob 0.55-0.65)
│  Ideal para: IV alto, DTE curto
│  Max Loss: Debit pago
│  Max Gain: Width - Debit
│
├─ 🟠 PUT SPREAD (Bearish, Risco/Reward controlado)
│  Quando: Previsão DOWN moderada (prob 0.55-0.65)
│  Ideal para: IV alto, DTE curto
│  Max Loss: Debit pago
│  Max Gain: Width - Debit
│
├─ 🔵 SEAGULL (Directional com proteção)
│  Quando: Previsão UP/DOWN com hedge
│  Ideal para: IV muito alto, DTE médio
│  Estrutura: Buy Call/Put + Sell 2x Out-of-Money
│  Max Loss: Premium pago - credit recebido
│
└─ VOLATILITY STRATEGIES (Aposta em movimento)
   
   ├─ 📊 STRADDLE (Aposta em movimento grande)
   │  Quando: Previsão é NEUTRAL mas IV baixa
   │  Ideal para: Antes de news, IV muito baixa
   │  Max Loss: Premium pago
   │  Max Gain: Ilimitado (ambos lados)
   │
   └─ 📊 STRANGLE (Straddle mais barato)
      Quando: NEUTRAL, IV baixa, margem pequena
      Ideal para: DTE longo, IV baixa
```

### 🤖 Algoritmo de Recomendação

```python
def recommend_options_strategy(
    xgboost_prediction,        # 0 ou 1
    prediction_probability,    # 0.0-1.0
    implied_volatility,        # IV percentual
    current_price,
    strike_prices,
    time_to_expiration_days,   # DTE
    risk_tolerance             # "conservative", "moderate", "aggressive"
) -> dict:
    """
    Retorna: {
        "strategy": "CALL" | "PUT" | "CALL_SPREAD" | etc,
        "confidence": 0.0-1.0,
        "expected_return": float,
        "max_risk": float,
        "max_reward": float,
        "recommendation": string descritiva,
        "strikes": [strike prices recomendadas],
        "Greeks": {"delta": float, "theta": float, "vega": float}
    }
    """
    
    # Normalizar inputs
    direction = "UP" if xgboost_prediction == 1 else "DOWN"
    confidence = abs(prediction_probability - 0.5) * 2  # 0-1 scale
    iv_percentile = normalize_iv(implied_volatility)    # 0-1 scale
    
    # Scoring matriz
    score_call = 0
    score_put = 0
    score_call_spread = 0
    score_put_spread = 0
    score_straddle = 0
    score_strangle = 0
    score_seagull = 0
    
    # 1. FORÇA DA PREVISÃO
    if direction == "UP":
        score_call += confidence * 3
        score_call_spread += confidence * 2
    else:
        score_put += confidence * 3
        score_put_spread += confidence * 2
    
    # 2. VOLATILIDADE IMPLÍCITA
    if iv_percentile > 0.75:  # IV muito alta
        score_call_spread += 2
        score_put_spread += 2
        score_seagull += 2
    elif iv_percentile > 0.5:  # IV média-alta
        score_call_spread += 1
        score_put_spread += 1
    else:  # IV baixa
        score_call += 1
        score_put += 1
        score_straddle += 1
        score_strangle += 1
    
    # 3. TEMPO ATÉ EXPIRAÇÃO
    if time_to_expiration_days <= 3:  # Muito curto
        score_call_spread += 1
        score_put_spread += 1
    elif time_to_expiration_days >= 30:  # Longo
        score_call += 1
        score_put += 1
        score_straddle += 1
    else:  # Médio (ideal)
        score_call += 1
        score_put += 1
        score_seagull += 1
    
    # 4. CONFIANÇA DO MODELO
    if confidence < 0.1:  # Modelo indeciso
        score_straddle += 2
        score_strangle += 2
    elif confidence > 0.3:  # Modelo confiante
        score_call += 2 if direction == "UP" else 0
        score_put += 2 if direction == "DOWN" else 0
    
    # 5. TOLERÂNCIA AO RISCO
    if risk_tolerance == "conservative":
        score_call_spread += 2
        score_put_spread += 2
        score_seagull += 1
    elif risk_tolerance == "aggressive":
        score_call += 2
        score_put += 2
    # "moderate" = neutro, sem bônus
    
    # Encontrar melhor estratégia
    scores = {
        "CALL": score_call,
        "PUT": score_put,
        "CALL_SPREAD": score_call_spread,
        "PUT_SPREAD": score_put_spread,
        "STRADDLE": score_straddle,
        "STRANGLE": score_strangle,
        "SEAGULL": score_seagull,
    }
    
    best_strategy = max(scores, key=scores.get)
    confidence_score = scores[best_strategy] / 15  # Normalizar 0-1
    
    return {
        "strategy": best_strategy,
        "confidence": confidence_score,
        "model_probability": prediction_probability,
        "iv_percentile": iv_percentile,
        "direction": direction,
        "recommended_strikes": calculate_optimal_strikes(best_strategy, current_price),
        "expected_return": calculate_expected_return(best_strategy, ...),
        "max_risk": calculate_max_risk(best_strategy, ...),
    }
```

---

## 3️⃣ INTEGRAÇÃO COM OPTIONS_V3.PY

### Novo Fluxo

```
XGBoost Prediction (UP/DOWN, prob)
        ↓
Fetch Market Data:
  • Current Price
  • Available Strikes
  • IV (Implied Volatility)
  • DTE (Days to Expiration)
        ↓
Call: recommend_options_strategy()
        ↓
Compare Strategies:
  • Return/Risk ratio
  • Greeks exposure
  • Market conditions
        ↓
Select Best Strategy
        ↓
Calculate Optimal Strikes:
  • Moneyness
  • Probability ITM
  • Delta target
        ↓
Execute Trade:
  • Place order
  • Set SL/TP
  • Log trade details
```

### Exemplo de Código

```python
# Em options_v3.py, após ter previsão do XGBoost

class OptionsV3Executor:
    def __init__(self, ...):
        # ...
        self.strategy_recommender = OptionsStrategyRecommender()
    
    def execute_trade_with_strategy(self, market_data):
        """Executar trade recomendando melhor estratégia."""
        
        # 1. Get XGBoost prediction
        prediction, probability = self.xgboost_model.predict(market_data)
        
        # 2. Get market data
        current_price = market_data["close"]
        iv = self.fetch_implied_volatility()  # De broker
        available_strikes = self.fetch_strikes()
        dte = self.calculate_dte()
        
        # 3. Recommend strategy
        recommendation = self.strategy_recommender.recommend(
            prediction=prediction,
            probability=probability,
            iv=iv,
            current_price=current_price,
            strikes=available_strikes,
            dte=dte,
            risk_tolerance="moderate"
        )
        
        # 4. Execute based on recommendation
        if recommendation["strategy"] == "CALL":
            self.place_call_order(recommendation["strikes"], recommendation["qty"])
        elif recommendation["strategy"] == "PUT":
            self.place_put_order(recommendation["strikes"], recommendation["qty"])
        elif recommendation["strategy"] == "CALL_SPREAD":
            self.place_call_spread_order(
                long_strike=recommendation["strikes"]["long"],
                short_strike=recommendation["strikes"]["short"],
                qty=recommendation["qty"]
            )
        # ... etc para outras estratégias
        
        # 5. Log
        self.logger.info(f"""
            Strategy: {recommendation['strategy']}
            Model Prediction: {['DOWN', 'UP'][prediction]}
            Probability: {probability:.2%}
            IV Percentile: {recommendation['iv_percentile']:.0%}
            Expected Return: {recommendation['expected_return']:.2%}
            Max Risk: ${recommendation['max_risk']:.2f}
        """)
```

---

## 4️⃣ MATÉRIA DE IMPLEMENTAÇÃO

### Arquivos a Criar/Modificar

```
📁 core/
  └─ options_strategy_recommender.py ⭐ NEW
     • recommend_options_strategy()
     • calculate_optimal_strikes()
     • calculate_expected_return()
     • calculate_greeks()

📁 
  └─ options_v3.py (MODIFICAR)
     • Integrar recomendador
     • Adicionar market data fetching
     • Implementar trade execution por tipo
```

### Recomendações Esperadas

```
Cenário 1: XGBoost UP forte (prob 0.75), IV baixa
Resultado: CALL (simples)
Razão: Confiança alta, IV favorável para long options

Cenário 2: XGBoost UP moderado (prob 0.60), IV alta
Resultado: CALL SPREAD
Razão: Proteger contra queda de IV

Cenário 3: XGBoost neutro (prob 0.50), IV muito baixa
Resultado: STRADDLE ou STRANGLE
Razão: Apostar em movimento, não em direção

Cenário 4: XGBoost DOWN forte, DTE muito curto (1 dia)
Resultado: PUT SPREAD
Razão: Theta favorável, IV high decay

Cenário 5: XGBoost DOWN, IV muito alta, risk_tolerance baixa
Resultado: SEAGULL
Razão: Proteção via credit, hedge natural
```

---

## 5️⃣ PRÓXIMOS PASSOS

### Imediato
```bash
# 1. Treinar modelo com 60 features (já pronto)
python3 train_enhanced_model.py

# 2. Validar feature importance
cat models/enhanced_model_results.json
```

### Curto Prazo
```python
# 1. Criar core/options_strategy_recommender.py
# 2. Implementar recommend_options_strategy()
# 3. Integrar em options_v3.py
# 4. Testar com dados simulados
```

### Validação
```bash
# Backtest com recomendações de estratégia
python3 backtest_with_strategy_recommendation.py

# Esperado: Win rate 60-65%, melhor Sharpe ratio
```

---

## 📊 RESUMO

| Aspecto | Configuração |
|---------|--------------|
| **Ativo** | EURUSD (EUR/USD) |
| **Timeframe** | M15 (15 minutos) |
| **Dados** | 84,352 candles (3.5 anos) |
| **Split** | 80% treino, 20% teste |
| **Features** | 60 (27 → 60, +33 novas) |
| **Target** | Dinâmico D+1 @ 14:00 (não fixo) |
| **XGBoost** | 150 árvores, depth=7, lr=0.08 |
| **Próximo Passo** | Recomendação de Estratégias de Opções |

---

*Última atualização: 2026-05-25 05:00 UTC*
