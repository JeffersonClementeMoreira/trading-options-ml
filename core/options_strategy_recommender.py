"""
Options Strategy Recommender - Recomenda melhor estratégia de opções baseado em:
1. Previsão do XGBoost (UP/DOWN + probabilidade)
2. Volatilidade Implícita (IV)
3. Tempo até expiração (DTE)
4. Preço atual e strikes disponíveis
5. Tolerância ao risco do trader
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum


class OptionsStrategy(Enum):
    """Estratégias de opções disponíveis."""
    CALL = "CALL"
    PUT = "PUT"
    CALL_SPREAD = "CALL_SPREAD"
    PUT_SPREAD = "PUT_SPREAD"
    STRADDLE = "STRADDLE"
    STRANGLE = "STRANGLE"
    SEAGULL = "SEAGULL"
    BUTTERFLY = "BUTTERFLY"
    IRON_CONDOR = "IRON_CONDOR"


class RiskTolerance(Enum):
    """Tolerância ao risco do trader."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class StrategyRecommendation:
    """Recomendação de estratégia."""
    strategy: OptionsStrategy
    confidence: float  # 0-1
    expected_return_pct: float
    max_risk: float
    max_reward: float
    probability_itm: float
    delta: float
    gamma: float
    theta_per_day: float
    vega: float
    recommended_strikes: Dict
    reasoning: str
    score: float


class OptionsStrategyRecommender:
    """Recomenda estratégias de opções baseado em múltiplos fatores."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.last_recommendation = None
    
    def recommend(
        self,
        xgboost_prediction: int,  # 0 ou 1
        prediction_probability: float,  # 0.0-1.0
        implied_volatility: float,  # % (ex: 15.5 = 15.5%)
        current_price: float,
        available_strikes: List[float],
        time_to_expiration_days: float,
        risk_tolerance: RiskTolerance = RiskTolerance.MODERATE,
    ) -> StrategyRecommendation:
        """
        Recomenda a melhor estratégia de opções.
        
        Args:
            xgboost_prediction: 1=UP, 0=DOWN
            prediction_probability: Probabilidade da previsão (0.5-1.0)
            implied_volatility: IV em percentual
            current_price: Preço atual do ativo
            available_strikes: Lista de strikes disponíveis
            time_to_expiration_days: Dias até expiração
            risk_tolerance: Tolerância ao risco
            
        Returns:
            StrategyRecommendation com melhor estratégia
        """
        
        # Normalizar inputs
        direction = "UP" if xgboost_prediction == 1 else "DOWN"
        confidence = abs(prediction_probability - 0.5) * 2  # Escala 0-1
        iv_percentile = self._normalize_iv(implied_volatility)
        dte = max(time_to_expiration_days, 1)  # Mínimo 1 dia
        
        if self.verbose:
            print(f"\n🎯 OPTIONS STRATEGY RECOMMENDATION")
            print(f"   Direction: {direction} (prob: {prediction_probability:.1%})")
            print(f"   IV: {implied_volatility:.1f}% (percentile: {iv_percentile:.0%})")
            print(f"   DTE: {dte:.0f} dias")
            print(f"   Risk Tolerance: {risk_tolerance.value}")
        
        # Calcular scores para cada estratégia
        scores = self._calculate_strategy_scores(
            direction=direction,
            confidence=confidence,
            iv_percentile=iv_percentile,
            dte=dte,
            risk_tolerance=risk_tolerance
        )
        
        # Encontrar melhor estratégia
        best_strategy_name = max(scores, key=scores.get)
        best_strategy = OptionsStrategy[best_strategy_name]
        score = scores[best_strategy_name]
        
        # Calcular strikes ótimos
        recommended_strikes = self._calculate_optimal_strikes(
            strategy=best_strategy,
            current_price=current_price,
            available_strikes=available_strikes,
            direction=direction,
            iv_percentile=iv_percentile,
            confidence=confidence
        )
        
        # Calcular Greeks (aproximações)
        greeks = self._calculate_greeks(
            strategy=best_strategy,
            current_price=current_price,
            strike=recommended_strikes.get("long_strike", recommended_strikes.get("strike")),
            dte=dte,
            iv=implied_volatility,
            direction=direction
        )
        
        # Calcular retorno esperado
        expected_return, max_risk, max_reward = self._calculate_return_metrics(
            strategy=best_strategy,
            current_price=current_price,
            recommended_strikes=recommended_strikes,
            confidence=confidence,
            iv_percentile=iv_percentile
        )
        
        # Calcular probabilidade ITM
        probability_itm = self._calculate_probability_itm(
            strategy=best_strategy,
            current_price=current_price,
            strikes=recommended_strikes,
            direction=direction,
            iv_percentile=iv_percentile
        )
        
        # Gerar reasoning
        reasoning = self._generate_reasoning(
            strategy=best_strategy,
            direction=direction,
            confidence=confidence,
            iv_percentile=iv_percentile,
            dte=dte,
            expected_return=expected_return,
            max_risk=max_risk
        )
        
        recommendation = StrategyRecommendation(
            strategy=best_strategy,
            confidence=score / 15.0,  # Normalizar para 0-1
            expected_return_pct=expected_return,
            max_risk=max_risk,
            max_reward=max_reward,
            probability_itm=probability_itm,
            delta=greeks["delta"],
            gamma=greeks["gamma"],
            theta_per_day=greeks["theta"],
            vega=greeks["vega"],
            recommended_strikes=recommended_strikes,
            reasoning=reasoning,
            score=score
        )
        
        self.last_recommendation = recommendation
        
        if self.verbose:
            self._print_recommendation(recommendation)
        
        return recommendation
    
    def _calculate_strategy_scores(
        self,
        direction: str,
        confidence: float,
        iv_percentile: float,
        dte: float,
        risk_tolerance: RiskTolerance
    ) -> Dict[str, float]:
        """Calcula scores para cada estratégia."""
        
        scores = {
            "CALL": 0,
            "PUT": 0,
            "CALL_SPREAD": 0,
            "PUT_SPREAD": 0,
            "STRADDLE": 0,
            "STRANGLE": 0,
            "SEAGULL": 0,
            "BUTTERFLY": 0,
            "IRON_CONDOR": 0,
        }
        
        # 1. FORÇA DA PREVISÃO (componente principal)
        if direction == "UP":
            scores["CALL"] += confidence * 3
            scores["CALL_SPREAD"] += confidence * 2
            scores["SEAGULL"] += confidence * 1
        else:  # DOWN
            scores["PUT"] += confidence * 3
            scores["PUT_SPREAD"] += confidence * 2
            scores["SEAGULL"] += confidence * 1
        
        # 2. VOLATILIDADE IMPLÍCITA
        if iv_percentile > 0.75:  # IV muito alta (>75%)
            # Spread strategies beneficiam de IV alta (vender premium)
            scores["CALL_SPREAD"] += 2.5
            scores["PUT_SPREAD"] += 2.5
            scores["SEAGULL"] += 2.0
            scores["IRON_CONDOR"] += 2.0
            scores["BUTTERFLY"] += 1.5
            # Long options sofrem com IV alta
            scores["CALL"] -= 0.5
            scores["PUT"] -= 0.5
        elif iv_percentile > 0.5:  # IV média-alta (50-75%)
            scores["CALL_SPREAD"] += 1.5
            scores["PUT_SPREAD"] += 1.5
            scores["SEAGULL"] += 1.0
        else:  # IV baixa (<50%)
            # Long options beneficiam de IV baixa
            scores["CALL"] += 1.5
            scores["PUT"] += 1.5
            scores["STRADDLE"] += 2.0
            scores["STRANGLE"] += 1.5
        
        # 3. TEMPO ATÉ EXPIRAÇÃO
        if dte <= 2:  # Muito curto (<=2 dias)
            # Strategies dependentes de theta (time decay)
            scores["CALL_SPREAD"] += 1.5
            scores["PUT_SPREAD"] += 1.5
            scores["BUTTERFLY"] += 1.0
            scores["STRADDLE"] -= 0.5  # Vega/theta trade ruim
        elif 2 < dte <= 7:  # Curto (2-7 dias)
            scores["CALL_SPREAD"] += 1.0
            scores["PUT_SPREAD"] += 1.0
            scores["IRON_CONDOR"] += 1.0
        elif 7 < dte <= 21:  # Médio (1-3 semanas) - IDEAL
            scores["CALL"] += 1.5
            scores["PUT"] += 1.5
            scores["SEAGULL"] += 1.5
            scores["STRADDLE"] += 1.0
        else:  # Longo (>3 semanas)
            scores["CALL"] += 1.0
            scores["PUT"] += 1.0
            scores["STRADDLE"] += 1.5
            scores["STRANGLE"] += 1.0
        
        # 4. CONFIANÇA DO MODELO
        if confidence < 0.1:  # Modelo muito indeciso
            # Estratégias que ganham com movimento
            scores["STRADDLE"] += 2.0
            scores["STRANGLE"] += 1.5
            scores["IRON_CONDOR"] -= 0.5
        elif confidence < 0.2:  # Modelo indeciso (50-55%)
            scores["STRADDLE"] += 1.0
            scores["STRANGLE"] += 0.5
        elif confidence > 0.3:  # Modelo confiante (65%+)
            if direction == "UP":
                scores["CALL"] += 1.5
            else:
                scores["PUT"] += 1.5
        
        # 5. TOLERÂNCIA AO RISCO
        if risk_tolerance == RiskTolerance.CONSERVATIVE:
            # Preferir spreads (risco limitado)
            scores["CALL_SPREAD"] += 2.0
            scores["PUT_SPREAD"] += 2.0
            scores["SEAGULL"] += 1.0
            scores["IRON_CONDOR"] += 1.5
            # Penalizar long options
            scores["CALL"] -= 1.0
            scores["PUT"] -= 1.0
            scores["STRADDLE"] -= 1.0
        elif risk_tolerance == RiskTolerance.AGGRESSIVE:
            # Preferir directional (risco ilimitado)
            scores["CALL"] += 2.0
            scores["PUT"] += 2.0
            scores["STRADDLE"] += 1.0
            # Penalizar spreads
            scores["CALL_SPREAD"] -= 0.5
            scores["PUT_SPREAD"] -= 0.5
        # MODERATE: sem bônus/penalidades
        
        return scores
    
    def _normalize_iv(self, iv: float, min_iv: float = 5.0, max_iv: float = 50.0) -> float:
        """Normaliza IV para escala 0-1."""
        return np.clip((iv - min_iv) / (max_iv - min_iv), 0, 1)
    
    def _calculate_optimal_strikes(
        self,
        strategy: OptionsStrategy,
        current_price: float,
        available_strikes: List[float],
        direction: str,
        iv_percentile: float,
        confidence: float
    ) -> Dict[str, float]:
        """Calcula strikes ótimos baseado na estratégia."""
        
        available_strikes = sorted(set(available_strikes))
        
        # Encontrar ATM (At-The-Money)
        atm_idx = min(range(len(available_strikes)), 
                     key=lambda i: abs(available_strikes[i] - current_price))
        atm_strike = available_strikes[atm_idx]
        
        strikes_result = {"current_price": current_price, "atm_strike": atm_strike}
        
        if strategy == OptionsStrategy.CALL:
            # ITM ou ATM dependendo de confiança
            if confidence > 0.25:
                strike_idx = max(0, atm_idx - 1)  # Um strike abaixo (ITM)
            else:
                strike_idx = atm_idx  # ATM
            strikes_result["strike"] = available_strikes[strike_idx]
            strikes_result["delta"] = 0.6 if confidence > 0.25 else 0.5
        
        elif strategy == OptionsStrategy.PUT:
            # ITM ou ATM dependendo de confiança
            if confidence > 0.25:
                strike_idx = min(len(available_strikes) - 1, atm_idx + 1)  # Um strike acima (ITM)
            else:
                strike_idx = atm_idx  # ATM
            strikes_result["strike"] = available_strikes[strike_idx]
            strikes_result["delta"] = -0.6 if confidence > 0.25 else -0.5
        
        elif strategy == OptionsStrategy.CALL_SPREAD:
            # Buy ATM, Sell OTM
            long_idx = atm_idx
            short_idx = min(len(available_strikes) - 1, atm_idx + 1)
            strikes_result["long_strike"] = available_strikes[long_idx]
            strikes_result["short_strike"] = available_strikes[short_idx]
            strikes_result["delta"] = 0.3
        
        elif strategy == OptionsStrategy.PUT_SPREAD:
            # Buy ATM, Sell OTM
            long_idx = atm_idx
            short_idx = max(0, atm_idx - 1)
            strikes_result["long_strike"] = available_strikes[long_idx]
            strikes_result["short_strike"] = available_strikes[short_idx]
            strikes_result["delta"] = -0.3
        
        elif strategy == OptionsStrategy.STRADDLE:
            # Buy Call ATM + Buy Put ATM
            strikes_result["call_strike"] = atm_strike
            strikes_result["put_strike"] = atm_strike
            strikes_result["delta"] = 0.0
        
        elif strategy == OptionsStrategy.STRANGLE:
            # Buy Call OTM + Buy Put OTM (mais barato que straddle)
            call_idx = min(len(available_strikes) - 1, atm_idx + 1)
            put_idx = max(0, atm_idx - 1)
            strikes_result["call_strike"] = available_strikes[call_idx]
            strikes_result["put_strike"] = available_strikes[put_idx]
            strikes_result["delta"] = 0.0
        
        elif strategy == OptionsStrategy.SEAGULL:
            # Buy Call/Put ATM + Sell 2x OTM (coleta premium)
            if direction == "UP":
                long_idx = atm_idx
                short_idx = min(len(available_strikes) - 1, atm_idx + 2)
                strikes_result["long_strike"] = available_strikes[long_idx]
                strikes_result["short_call_1"] = available_strikes[short_idx]
                strikes_result["short_call_2"] = available_strikes[short_idx]
                strikes_result["delta"] = 0.35
            else:
                long_idx = atm_idx
                short_idx = max(0, atm_idx - 2)
                strikes_result["long_strike"] = available_strikes[long_idx]
                strikes_result["short_put_1"] = available_strikes[short_idx]
                strikes_result["short_put_2"] = available_strikes[short_idx]
                strikes_result["delta"] = -0.35
        
        elif strategy == OptionsStrategy.IRON_CONDOR:
            # Sell OTM Call Spread + Sell OTM Put Spread
            # Lucra se preço ficar no meio
            call_long = min(len(available_strikes) - 1, atm_idx + 2)
            call_short = min(len(available_strikes) - 1, atm_idx + 1)
            put_long = max(0, atm_idx - 2)
            put_short = max(0, atm_idx - 1)
            strikes_result["short_call_strike"] = available_strikes[call_short]
            strikes_result["long_call_strike"] = available_strikes[call_long]
            strikes_result["short_put_strike"] = available_strikes[put_short]
            strikes_result["long_put_strike"] = available_strikes[put_long]
            strikes_result["delta"] = 0.0
        
        return strikes_result
    
    def _calculate_greeks(
        self,
        strategy: OptionsStrategy,
        current_price: float,
        strike: float,
        dte: float,
        iv: float,
        direction: str
    ) -> Dict[str, float]:
        """Calcula Greeks aproximados (valores simplificados)."""
        
        moneyness = current_price / strike
        
        # Delta aproximado
        if strategy in [OptionsStrategy.CALL, OptionsStrategy.CALL_SPREAD]:
            delta = min(1.0, max(0.0, moneyness)) * 0.7 + 0.3
        elif strategy in [OptionsStrategy.PUT, OptionsStrategy.PUT_SPREAD]:
            delta = max(-1.0, min(0.0, -moneyness)) * 0.7 - 0.3
        else:
            delta = 0.0
        
        # Gamma (máximo perto de ATM)
        gamma = 0.1 / (1 + abs(np.log(moneyness)))
        
        # Theta (time decay, negativo para long)
        time_decay = -0.5 * (iv / 100) / np.sqrt(dte) if dte > 0 else 0
        theta = time_decay if strategy in [OptionsStrategy.CALL_SPREAD, OptionsStrategy.PUT_SPREAD] else time_decay * 2
        
        # Vega (sensibilidade a IV)
        vega = np.sqrt(dte) * (iv / 100) * 0.5
        
        return {
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
            "vega": vega
        }
    
    def _calculate_return_metrics(
        self,
        strategy: OptionsStrategy,
        current_price: float,
        recommended_strikes: Dict,
        confidence: float,
        iv_percentile: float
    ) -> Tuple[float, float, float]:
        """Calcula retorno esperado, max risk, max reward."""
        
        # Valores aproximados baseado em Greeks e premiums
        
        if strategy in [OptionsStrategy.CALL, OptionsStrategy.PUT]:
            # Long options: premium pagado
            base_premium = current_price * 0.02  # 2% do preço
            max_risk = base_premium
            max_reward = current_price * (confidence + 0.1)  # Ilimitado
            expected_return = (confidence * max_reward - (1 - confidence) * max_risk) / max_risk * 100
        
        elif strategy in [OptionsStrategy.CALL_SPREAD, OptionsStrategy.PUT_SPREAD]:
            # Spreads: debit pagado
            width = abs(recommended_strikes["long_strike"] - recommended_strikes["short_strike"])
            debit = width * 0.5
            max_risk = debit
            max_reward = width - debit
            expected_return = (confidence * max_reward - (1 - confidence) * max_risk) / max_risk * 100
        
        elif strategy == OptionsStrategy.STRADDLE:
            base_premium = current_price * 0.04
            max_risk = base_premium
            max_reward = current_price  # Ilimitado
            expected_return = (confidence * max_reward - (1 - confidence) * max_risk) / max_risk * 100
        
        elif strategy == OptionsStrategy.STRANGLE:
            base_premium = current_price * 0.03
            max_risk = base_premium
            max_reward = current_price * 0.8
            expected_return = (confidence * max_reward - (1 - confidence) * max_risk) / max_risk * 100
        
        elif strategy == OptionsStrategy.SEAGULL:
            # Menos risco que call/put, mais retorno que spread
            long_premium = current_price * 0.03
            short_credits = long_premium * 0.7
            debit = long_premium - short_credits
            max_risk = debit
            max_reward = current_price * 0.2
            expected_return = (confidence * max_reward - (1 - confidence) * max_risk) / max_risk * 100 if max_risk > 0 else 0
        
        elif strategy == OptionsStrategy.IRON_CONDOR:
            # Lucra com stagnação
            net_credit = current_price * 0.03
            max_risk = net_credit
            max_reward = net_credit  # Lucro máximo = credit
            expected_return = (confidence * 0.5 * max_reward - (1 - confidence) * max_risk) / max_risk * 100
        
        else:
            max_risk = current_price * 0.02
            max_reward = current_price * 0.05
            expected_return = 0
        
        return expected_return, max_risk, max_reward
    
    def _calculate_probability_itm(
        self,
        strategy: OptionsStrategy,
        current_price: float,
        strikes: Dict,
        direction: str,
        iv_percentile: float
    ) -> float:
        """Calcula probabilidade de ficar ITM (In The Money)."""
        
        if strategy == OptionsStrategy.CALL:
            strike = strikes.get("strike", current_price)
            return max(0, 1 - (strike - current_price) / (current_price * 0.05))
        
        elif strategy == OptionsStrategy.PUT:
            strike = strikes.get("strike", current_price)
            return max(0, 1 - (current_price - strike) / (current_price * 0.05))
        
        elif strategy in [OptionsStrategy.CALL_SPREAD, OptionsStrategy.PUT_SPREAD]:
            return max(0.1, 0.5 + iv_percentile * 0.2)
        
        elif strategy == OptionsStrategy.STRADDLE:
            return max(0.15, 0.4 + iv_percentile * 0.3)
        
        else:
            return 0.5
    
    def _generate_reasoning(
        self,
        strategy: OptionsStrategy,
        direction: str,
        confidence: float,
        iv_percentile: float,
        dte: float,
        expected_return: float,
        max_risk: float
    ) -> str:
        """Gera explicação para recomendação."""
        
        reasons = []
        
        # Razão 1: Baseada em previsão do modelo
        if confidence > 0.25:
            reasons.append(f"Modelo confiante em {direction} ({(0.5 + confidence/2):.0%} prob)")
        else:
            reasons.append(f"Modelo neutro, recomendação baseada em IV/DTE")
        
        # Razão 2: IV
        if iv_percentile > 0.75:
            reasons.append(f"IV alta ({(50 + iv_percentile * 50):.0f}th percentile) → spread preferível")
        elif iv_percentile < 0.25:
            reasons.append(f"IV baixa → long options preferível")
        
        # Razão 3: DTE
        if dte < 3:
            reasons.append(f"DTE curto ({dte:.0f} dias) → theta favorável para estratégias")
        elif dte > 21:
            reasons.append(f"DTE longo ({dte:.0f} dias) → flexibilidade para movimento")
        
        # Razão 4: Retorno esperado
        if expected_return > 100:
            reasons.append(f"Retorno esperado alto ({expected_return:.0f}%)")
        
        return " | ".join(reasons)
    
    def _print_recommendation(self, rec: StrategyRecommendation):
        """Imprime recomendação em formato legível."""
        print(f"\n✅ RECOMMENDED STRATEGY: {rec.strategy.value}")
        print(f"   Confidence: {rec.confidence:.0%}")
        print(f"   Expected Return: {rec.expected_return_pct:.1f}%")
        print(f"   Max Risk: ${rec.max_risk:.2f}")
        print(f"   Max Reward: ${rec.max_reward:.2f}")
        print(f"   Probability ITM: {rec.probability_itm:.0%}")
        print(f"\n   Greeks:")
        print(f"     Delta: {rec.delta:.2f}")
        print(f"     Gamma: {rec.gamma:.4f}")
        print(f"     Theta: {rec.theta_per_day:.4f} (por dia)")
        print(f"     Vega: {rec.vega:.4f}")
        print(f"\n   Strikes: {rec.recommended_strikes}")
        print(f"\n   Reasoning: {rec.reasoning}")
