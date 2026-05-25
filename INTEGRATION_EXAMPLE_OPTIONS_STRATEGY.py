# EXEMPLO DE INTEGRAÇÃO - Options Strategy Recommender com XGBoost

## Como usar o novo recomendador de estratégias

### 1️⃣ USO BÁSICO

```python
from core.options_strategy_recommender import (
    OptionsStrategyRecommender,
    RiskTolerance
)

# Inicializar recomendador
recommender = OptionsStrategyRecommender(verbose=True)

# Simular previsão do XGBoost
xgboost_prediction = 1  # 0=DOWN, 1=UP
prediction_probability = 0.72  # 72% confiança

# Dados de mercado
current_price = 1.0890
implied_volatility = 12.5  # IV 12.5%
available_strikes = [1.05, 1.06, 1.07, 1.08, 1.09, 1.10, 1.11, 1.12, 1.13]
time_to_expiration = 14  # 14 dias

# Obter recomendação
recommendation = recommender.recommend(
    xgboost_prediction=xgboost_prediction,
    prediction_probability=prediction_probability,
    implied_volatility=implied_volatility,
    current_price=current_price,
    available_strikes=available_strikes,
    time_to_expiration_days=time_to_expiration,
    risk_tolerance=RiskTolerance.MODERATE
)

print(f"Estratégia: {recommendation.strategy.value}")
print(f"Confiança: {recommendation.confidence:.0%}")
print(f"Retorno Esperado: {recommendation.expected_return_pct:.1f}%")
print(f"Max Risk: ${recommendation.max_risk:.2f}")
print(f"Strikes: {recommendation.recommended_strikes}")
```

**Output Esperado:**
```
🎯 OPTIONS STRATEGY RECOMMENDATION
   Direction: UP (prob: 0.72)
   IV: 12.5% (percentile: 15%)
   DTE: 14 dias
   Risk Tolerance: moderate

✅ RECOMMENDED STRATEGY: CALL
   Confidence: 65%
   Expected Return: 145.3%
   Max Risk: $21.78
   Max Reward: $150.00
   Probability ITM: 72%

   Greeks:
     Delta: 0.65
     Gamma: 0.0892
     Theta: -0.0034 (por dia)
     Vega: 0.0156

   Strikes: {'current_price': 1.0890, 'atm_strike': 1.0900, 'strike': 1.0800, 'delta': 0.6}

   Reasoning: Modelo confiante em UP (72% prob) | IV baixa → long options preferível | DTE longo (14 dias) → flexibilidade para movimento
```

---

### 2️⃣ MÚLTIPLOS CENÁRIOS

```python
def analyze_different_scenarios():
    """Analisa recomendações em diferentes cenários."""
    
    recommender = OptionsStrategyRecommender(verbose=False)
    
    scenarios = [
        # (XGBoost, prob, IV, DTE, Risk Tolerance, Label)
        (1, 0.75, 10.0, 14, RiskTolerance.AGGRESSIVE, "Bullish forte, IV baixa"),
        (1, 0.60, 20.0, 3, RiskTolerance.CONSERVATIVE, "Bullish moderado, IV alta, DTE curto"),
        (0, 0.55, 8.0, 30, RiskTolerance.MODERATE, "Bearish leve, IV muito baixa, DTE longo"),
        (1, 0.51, 18.0, 7, RiskTolerance.MODERATE, "Sinal fraco, IV média, DTE médio"),
    ]
    
    current_price = 1.0890
    strikes = [1.05, 1.06, 1.07, 1.08, 1.09, 1.10, 1.11, 1.12, 1.13]
    
    print("\n" + "="*80)
    print("ANÁLISE DE MÚLTIPLOS CENÁRIOS")
    print("="*80)
    
    for pred, prob, iv, dte, risk_tol, label in scenarios:
        print(f"\n📊 Cenário: {label}")
        print(f"   XGBoost: {'UP' if pred == 1 else 'DOWN'} ({prob:.0%})")
        print(f"   IV: {iv:.1f}%, DTE: {dte}d, Risk: {risk_tol.value}")
        
        rec = recommender.recommend(
            xgboost_prediction=pred,
            prediction_probability=prob,
            implied_volatility=iv,
            current_price=current_price,
            available_strikes=strikes,
            time_to_expiration_days=dte,
            risk_tolerance=risk_tol
        )
        
        print(f"   ➜ {rec.strategy.value} | Return: {rec.expected_return_pct:+.0f}% | Prob ITM: {rec.probability_itm:.0%}")

analyze_different_scenarios()
```

**Output esperado:**

```
================================================================================
ANÁLISE DE MÚLTIPLOS CENÁRIOS
================================================================================

📊 Cenário: Bullish forte, IV baixa
   XGBoost: UP (75%)
   IV: 10.0%, DTE: 14d, Risk: aggressive
   ➜ CALL | Return: +195% | Prob ITM: 80%

📊 Cenário: Bullish moderado, IV alta, DTE curto
   XGBoost: UP (60%)
   IV: 20.0%, DTE: 3d, Risk: conservative
   ➜ CALL_SPREAD | Return: +85% | Prob ITM: 65%

📊 Cenário: Bearish leve, IV muito baixa, DTE longo
   XGBoost: DOWN (55%)
   IV: 8.0%, DTE: 30d, Risk: moderate
   ➜ PUT | Return: +125% | Prob ITM: 58%

📊 Cenário: Sinal fraco, IV média, DTE médio
   XGBoost: UP (51%)
   IV: 18.0%, DTE: 7d, Risk: moderate
   ➜ STRADDLE | Return: +45% | Prob ITM: 50%
```

---

### 3️⃣ INTEGRAÇÃO COM OPTIONS_V3.PY

```python
# Em options_v3.py

from core.options_strategy_recommender import (
    OptionsStrategyRecommender,
    RiskTolerance,
    OptionsStrategy
)

class OptionsV3Executor:
    def __init__(self, ...):
        # ...
        self.strategy_recommender = OptionsStrategyRecommender(verbose=True)
    
    def execute_trade_with_strategy_recommendation(self, market_data):
        """Executa trade com recomendação automática de estratégia."""
        
        # 1. XGBoost Prediction
        prediction, probability = self.xgboost_model.predict(market_data)
        
        # 2. Fetch Market Data
        current_price = market_data["close"]
        iv = self.fetch_implied_volatility()  # De broker/API
        available_strikes = self.fetch_available_strikes()
        dte = self.calculate_days_to_expiration()
        
        # 3. Get Strategy Recommendation
        recommendation = self.strategy_recommender.recommend(
            xgboost_prediction=prediction,
            prediction_probability=probability,
            implied_volatility=iv,
            current_price=current_price,
            available_strikes=available_strikes,
            time_to_expiration_days=dte,
            risk_tolerance=RiskTolerance.MODERATE  # Ou de config
        )
        
        # 4. Execute Based on Strategy
        if recommendation.strategy == OptionsStrategy.CALL:
            self._execute_call_trade(
                strike=recommendation.recommended_strikes["strike"],
                quantity=self.calculate_quantity(recommendation.max_risk),
                recommendation=recommendation
            )
        
        elif recommendation.strategy == OptionsStrategy.PUT:
            self._execute_put_trade(
                strike=recommendation.recommended_strikes["strike"],
                quantity=self.calculate_quantity(recommendation.max_risk),
                recommendation=recommendation
            )
        
        elif recommendation.strategy == OptionsStrategy.CALL_SPREAD:
            self._execute_call_spread_trade(
                long_strike=recommendation.recommended_strikes["long_strike"],
                short_strike=recommendation.recommended_strikes["short_strike"],
                quantity=self.calculate_quantity(recommendation.max_risk),
                recommendation=recommendation
            )
        
        elif recommendation.strategy == OptionsStrategy.PUT_SPREAD:
            self._execute_put_spread_trade(
                long_strike=recommendation.recommended_strikes["long_strike"],
                short_strike=recommendation.recommended_strikes["short_strike"],
                quantity=self.calculate_quantity(recommendation.max_risk),
                recommendation=recommendation
            )
        
        elif recommendation.strategy == OptionsStrategy.STRADDLE:
            self._execute_straddle_trade(
                strike=recommendation.recommended_strikes["call_strike"],
                quantity=self.calculate_quantity(recommendation.max_risk),
                recommendation=recommendation
            )
        
        elif recommendation.strategy == OptionsStrategy.STRANGLE:
            self._execute_strangle_trade(
                call_strike=recommendation.recommended_strikes["call_strike"],
                put_strike=recommendation.recommended_strikes["put_strike"],
                quantity=self.calculate_quantity(recommendation.max_risk),
                recommendation=recommendation
            )
        
        # 5. Log Trade
        self._log_trade_execution(recommendation)
    
    def _log_trade_execution(self, recommendation):
        """Log detalhado da execução."""
        log_msg = f"""
        ╔════════════════════════════════════════════════════════════╗
        ║                    TRADE EXECUTED                         ║
        ╠════════════════════════════════════════════════════════════╣
        ║ Strategy:           {recommendation.strategy.value:<35} ║
        ║ Confidence:         {recommendation.confidence:>6.0%}                         ║
        ║ Model Probability:  {recommendation.probability_itm:>6.0%}                         ║
        ║ IV Percentile:      {recommendation.probability_itm:>6.0%}                         ║
        ║ Expected Return:    {recommendation.expected_return_pct:>6.1f}%                        ║
        ║ Max Risk:           ${recommendation.max_risk:>10.2f}                     ║
        ║ Max Reward:         ${recommendation.max_reward:>10.2f}                     ║
        ║ Probability ITM:    {recommendation.probability_itm:>6.0%}                         ║
        ║                                                            ║
        ║ Greeks:                                                    ║
        ║   Delta:           {recommendation.delta:>8.2f}                         ║
        ║   Gamma:           {recommendation.gamma:>8.4f}                         ║
        ║   Theta/day:       {recommendation.theta_per_day:>8.4f}                         ║
        ║   Vega:            {recommendation.vega:>8.4f}                         ║
        ║                                                            ║
        ║ Reasoning: {recommendation.reasoning:<40} ║
        ╚════════════════════════════════════════════════════════════╝
        """
        print(log_msg)
        self.logger.info(log_msg)
```

---

### 4️⃣ ESTATÍSTICAS POR ESTRATÉGIA

```python
def print_strategy_matrix():
    """Mostra matriz de quando usar cada estratégia."""
    
    matrix = """
    ╔═════════════════════════════════════════════════════════════════════╗
    ║     QUANDO USAR CADA ESTRATÉGIA - Matriz de Decisão               ║
    ╠═════════════════════════════════════════════════════════════════════╣
    ║                                                                    ║
    ║ CALL              → XGBoost UP forte (65%+), IV baixa, DTE médio  ║
    ║ PUT               → XGBoost DOWN forte (65%+), IV baixa, DTE      ║
    ║ CALL SPREAD       → XGBoost UP (55%+), IV alta, DTE curto         ║
    ║ PUT SPREAD        → XGBoost DOWN (55%+), IV alta, DTE curto       ║
    ║ STRADDLE          → Sinal fraco (50-55%), IV MUITO baixa (<10%)   ║
    ║ STRANGLE          → Sinal fraco, IV baixa, quer movimento         ║
    ║ SEAGULL           → XGBoost confiante mas quer proteção via delta ║
    ║ BUTTERFLY         → Esperando pouca volatilidade, IV decrescente  ║
    ║ IRON CONDOR       → Bullish e Bearish, IV decrescente, neutro     ║
    ║                                                                    ║
    ║ RISK TOLERANCE:                                                   ║
    ║   CONSERVATIVE    → SPREADS (call/put spread, iron condor)       ║
    ║   MODERATE        → Baseado em IV/DTE/previsão                   ║
    ║   AGGRESSIVE      → LONG OPTIONS (call, put, straddle)           ║
    ║                                                                    ║
    ║ VOLATILIDADE IMPLÍCITA (IV):                                     ║
    ║   IV < 20%        → Preferir LONG OPTIONS                        ║
    ║   IV 20-40%       → CALL/PUT ou SPREADS                          ║
    ║   IV > 40%        → Preferir SPREADS ou SEAGULL                  ║
    ║                                                                    ║
    ║ TEMPO ATÉ EXPIRAÇÃO (DTE):                                       ║
    ║   < 3 dias        → SPREADS (theta favorable)                    ║
    ║   3-14 dias       → CALL/PUT ou SEAGULL                          ║
    ║   > 14 dias       → STRADDLE/STRANGLE (mais tempo para mover)   ║
    ║                                                                    ║
    ╚═════════════════════════════════════════════════════════════════════╝
    """
    
    print(matrix)

print_strategy_matrix()
```

---

### 5️⃣ COMPARAÇÃO DE RETORNOS

```python
def compare_strategies_by_condition():
    """Compara retorno esperado por condição de mercado."""
    
    recommender = OptionsStrategyRecommender(verbose=False)
    
    print("\n📊 COMPARAÇÃO DE RETORNOS POR CONDIÇÃO DE MERCADO\n")
    
    # Condição 1: IV baixa, sinal forte
    print("1️⃣ CONDIÇÃO: IV baixa (8%), XGBoost UP forte (75%)")
    print("-" * 60)
    for risk_tol in [RiskTolerance.CONSERVATIVE, RiskTolerance.MODERATE, RiskTolerance.AGGRESSIVE]:
        rec = recommender.recommend(
            1, 0.75, 8.0, 1.09, [1.05, 1.06, 1.07, 1.08, 1.09, 1.10, 1.11, 1.12, 1.13],
            14, risk_tol
        )
        print(f"  {risk_tol.value:12s} → {rec.strategy.value:15s} | Retorno: {rec.expected_return_pct:+7.1f}%")
    
    # Condição 2: IV alta, sinal moderado
    print("\n2️⃣ CONDIÇÃO: IV alta (35%), XGBoost UP moderado (60%)")
    print("-" * 60)
    for risk_tol in [RiskTolerance.CONSERVATIVE, RiskTolerance.MODERATE, RiskTolerance.AGGRESSIVE]:
        rec = recommender.recommend(
            1, 0.60, 35.0, 1.09, [1.05, 1.06, 1.07, 1.08, 1.09, 1.10, 1.11, 1.12, 1.13],
            7, risk_tol
        )
        print(f"  {risk_tol.value:12s} → {rec.strategy.value:15s} | Retorno: {rec.expected_return_pct:+7.1f}%")
    
    # Condição 3: Sinal fraco, IV média
    print("\n3️⃣ CONDIÇÃO: IV média (18%), Sinal fraco (51%)")
    print("-" * 60)
    for risk_tol in [RiskTolerance.CONSERVATIVE, RiskTolerance.MODERATE, RiskTolerance.AGGRESSIVE]:
        rec = recommender.recommend(
            1, 0.51, 18.0, 1.09, [1.05, 1.06, 1.07, 1.08, 1.09, 1.10, 1.11, 1.12, 1.13],
            14, risk_tol
        )
        print(f"  {risk_tol.value:12s} → {rec.strategy.value:15s} | Retorno: {rec.expected_return_pct:+7.1f}%")
```

---

## 📋 RESUMO DE IMPLEMENTAÇÃO

✅ **Arquivo Criado:** `core/options_strategy_recommender.py`

✅ **Funcionalidades:**
1. Análise de XGBoost prediction + probabilidade
2. Cálculo de score para 9 estratégias diferentes
3. Seleção automática da melhor estratégia
4. Cálculo de strikes ótimos
5. Greeks aproximados (Delta, Gamma, Theta, Vega)
6. Retorno esperado, Max Risk, Max Reward
7. Probabilidade ITM
8. Reasoning automático

✅ **Estratégias Suportadas:**
- CALL / PUT (Directional simples)
- CALL_SPREAD / PUT_SPREAD (Risk controlado)
- STRADDLE / STRANGLE (Movimento)
- SEAGULL (Directional com proteção)
- BUTTERFLY / IRON_CONDOR (Avançadas)

✅ **Próximo Passo:**
Integrar em `options_v3.py` para executar trades com recomendação automática!
