"""
Multi-Timeframe Confluence Analysis (M15 + H4)

Melhora confiança do sinal se os timeframes estão alinhados:
- M15 tendência UP + H4 tendência UP → Aumenta confiança
- M15 tendência UP + H4 tendência DOWN → Diminui confiança (divergência)
- Sem confluência → Percentual de acerto reduzido
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TimeframeAnalysis:
    """Resultado da análise em um timeframe."""
    timeframe: str
    trend: str  # 'UP', 'DOWN', 'NEUTRAL'
    trend_strength: float  # 0-1 (0 = fraco, 1 = forte)
    momentum: float  # 0-1
    confluence_count: int  # Quantos sinais confirmam a tendência


@dataclass
class ConfluenceResult:
    """Resultado da análise de confluência."""
    m15_trend: str
    h4_trend: str
    is_aligned: bool
    alignment_score: float  # 0-1 (0 = divergente, 1 = alinhado)
    confidence_adjustment: float  # -0.3 a +0.5 (multiplicador)
    reasoning: str


class MultiTimeframeConfluence:
    """Analisa confluência de tendências entre M15 e H4."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def analyze_timeframe_trend(self, df: pd.DataFrame, timeframe: str) -> TimeframeAnalysis:
        """
        Analisa tendência em um timeframe específico.
        
        Fatores considerados:
        1. SMA20 vs SMA50 alignment
        2. Momentum (últimas 10 velas)
        3. Price vs MA200
        4. Close posição relativa
        """
        
        if len(df) < 200:
            return TimeframeAnalysis(
                timeframe=timeframe,
                trend='NEUTRAL',
                trend_strength=0.0,
                momentum=0.0,
                confluence_count=0
            )
        
        # Calcular indicadores
        sma20 = df['close'].rolling(20).mean().iloc[-1]
        sma50 = df['close'].rolling(50).mean().iloc[-1]
        sma200 = df['close'].rolling(200).mean().iloc[-1]
        
        current_price = df['close'].iloc[-1]
        last_10_momentum = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
        
        # Contar sinais de confluência
        confluence_count = 0
        
        # 1. SMA alignment (SMA20 > SMA50 > SMA200)
        if sma20 > sma50 > sma200:
            confluence_count += 1
            trend_signal = 'UP'
        elif sma20 < sma50 < sma200:
            confluence_count += 1
            trend_signal = 'DOWN'
        else:
            trend_signal = 'NEUTRAL'
        
        # 2. Price vs MA200
        if current_price > sma200:
            confluence_count += 1
        elif current_price < sma200:
            confluence_count -= 1
        
        # 3. Momentum
        momentum = max(-1, min(1, last_10_momentum * 10))  # Normalizar
        if (trend_signal == 'UP' and momentum > 0) or (trend_signal == 'DOWN' and momentum < 0):
            confluence_count += 1
        
        # Determinar força da tendência
        trend_strength = min(1.0, abs(last_10_momentum) * 5)
        
        # Determinar trend final
        if confluence_count >= 2:
            final_trend = trend_signal if trend_signal != 'NEUTRAL' else 'NEUTRAL'
        else:
            final_trend = 'NEUTRAL'
        
        if self.verbose:
            print(f"\n📊 {timeframe} Analysis:")
            print(f"   SMA20: {sma20:.4f} | SMA50: {sma50:.4f} | SMA200: {sma200:.4f}")
            print(f"   Price: {current_price:.4f}")
            print(f"   Momentum (10 candles): {last_10_momentum:.2%}")
            print(f"   Confluence Count: {confluence_count}/4")
            print(f"   Trend: {final_trend} (strength: {trend_strength:.2%})")
        
        return TimeframeAnalysis(
            timeframe=timeframe,
            trend=final_trend,
            trend_strength=trend_strength,
            momentum=momentum,
            confluence_count=confluence_count
        )
    
    def convert_to_h4(self, df_m15: pd.DataFrame) -> pd.DataFrame:
        """Converte dados M15 para H4 (4 horas = 16 candles M15)."""
        
        if len(df_m15) < 16:
            return None
        
        # Resample: cada 16 candles M15 = 1 candle H4
        # Usar OHLC
        ohlc_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        # Agrupar por 4 horas (usar '4h' não '4H')
        df_h4 = df_m15.resample('4h').agg(ohlc_dict)
        df_h4 = df_h4.dropna()
        
        return df_h4
    
    def analyze_confluence(self, df_m15: pd.DataFrame) -> ConfluenceResult:
        """
        Analisa confluência entre M15 e H4.
        
        Returns:
            ConfluenceResult com scores e ajustes de confiança
        """
        
        # Análise M15
        m15_analysis = self.analyze_timeframe_trend(df_m15, 'M15')
        
        # Converter para H4 e analisar
        df_h4 = self.convert_to_h4(df_m15)
        if df_h4 is None or len(df_h4) < 50:
            h4_analysis = TimeframeAnalysis(
                timeframe='H4',
                trend='NEUTRAL',
                trend_strength=0.0,
                momentum=0.0,
                confluence_count=0
            )
        else:
            h4_analysis = self.analyze_timeframe_trend(df_h4, 'H4')
        
        # Verificar alinhamento
        is_aligned = (m15_analysis.trend == h4_analysis.trend) and (m15_analysis.trend != 'NEUTRAL')
        
        # Calcular score de alinhamento
        if m15_analysis.trend == 'NEUTRAL' or h4_analysis.trend == 'NEUTRAL':
            alignment_score = 0.5  # Neutro
            reasoning = "Um dos timeframes está neutro"
        elif m15_analysis.trend == h4_analysis.trend:
            # Alinhados - aumentar confiança
            alignment_score = 0.9
            base_strength = (m15_analysis.trend_strength + h4_analysis.trend_strength) / 2
            alignment_score = 0.8 + (base_strength * 0.2)  # 0.8 a 1.0
            reasoning = f"✅ CONFLUÊNCIA: M15 {m15_analysis.trend} + H4 {h4_analysis.trend}"
        else:
            # Divergência - diminuir confiança
            alignment_score = 0.3
            reasoning = f"⚠️ DIVERGÊNCIA: M15 {m15_analysis.trend} vs H4 {h4_analysis.trend}"
        
        # Calcular ajuste de confiança
        # Base: score de 50%
        # +50%: se alinhados com força
        # -30%: se divergentes
        # -20%: se neutro
        if alignment_score >= 0.8:
            confidence_adjustment = 0.5  # +50% na confiança
        elif alignment_score >= 0.6:
            confidence_adjustment = 0.2  # +20% na confiança
        elif alignment_score >= 0.4:
            confidence_adjustment = -0.1  # -10% na confiança
        else:
            confidence_adjustment = -0.3  # -30% na confiança
        
        result = ConfluenceResult(
            m15_trend=m15_analysis.trend,
            h4_trend=h4_analysis.trend,
            is_aligned=is_aligned,
            alignment_score=alignment_score,
            confidence_adjustment=confidence_adjustment,
            reasoning=reasoning
        )
        
        if self.verbose:
            print(f"\n🎯 CONFLUÊNCIA RESULT:")
            print(f"   M15: {m15_analysis.trend} | H4: {h4_analysis.trend}")
            print(f"   Alinhado: {is_aligned}")
            print(f"   Score: {alignment_score:.0%}")
            print(f"   Ajuste Confiança: {confidence_adjustment:+.0%}")
            print(f"   {result.reasoning}")
        
        return result
    
    def adjust_prediction_with_confluence(
        self,
        xgboost_pred: int,
        xgboost_prob: float,
        df_m15: pd.DataFrame
    ) -> Tuple[int, float, str]:
        """
        Ajusta probabilidade do XGBoost baseado em confluência.
        
        Args:
            xgboost_pred: 0 (DOWN) ou 1 (UP)
            xgboost_prob: Probabilidade original
            df_m15: DataFrame com dados M15
        
        Returns:
            (pred_ajustado, prob_ajustada, reasoning)
        """
        
        confluence = self.analyze_confluence(df_m15)
        
        # Se modelo prediz UP
        if xgboost_pred == 1:
            if confluence.m15_trend == 'UP':
                # Alinhado com tendência - aumentar confiança
                adjusted_prob = min(0.99, xgboost_prob + confluence.confidence_adjustment)
                reasoning = f"XGBoost UP + M15 {confluence.reasoning}"
            elif confluence.m15_trend == 'DOWN':
                # Divergente - diminuir confiança
                adjusted_prob = max(0.51, xgboost_prob + confluence.confidence_adjustment)
                reasoning = f"XGBoost UP mas {confluence.reasoning}"
            else:
                # Neutro - manter
                adjusted_prob = xgboost_prob
                reasoning = f"XGBoost UP mas tendência neutra"
        
        # Se modelo prediz DOWN
        else:
            if confluence.m15_trend == 'DOWN':
                # Alinhado com tendência - aumentar confiança
                adjusted_prob = min(0.99, xgboost_prob + confluence.confidence_adjustment)
                reasoning = f"XGBoost DOWN + M15 {confluence.reasoning}"
            elif confluence.m15_trend == 'UP':
                # Divergente - diminuir confiança
                adjusted_prob = max(0.51, xgboost_prob + confluence.confidence_adjustment)
                reasoning = f"XGBoost DOWN mas {confluence.reasoning}"
            else:
                # Neutro - manter
                adjusted_prob = xgboost_prob
                reasoning = f"XGBoost DOWN mas tendência neutra"
        
        return xgboost_pred, adjusted_prob, reasoning
    
    def print_summary(self, confluence: ConfluenceResult):
        """Imprime sumário visual."""
        print(f"""
╔════════════════════════════════════════════════════════════╗
║        MULTI-TIMEFRAME CONFLUENCE ANALYSIS                ║
╠════════════════════════════════════════════════════════════╣
║ M15 Trend:          {confluence.m15_trend:<8} │ H4 Trend:   {confluence.h4_trend:<8} ║
║ Aligned:            {'✅ YES' if confluence.is_aligned else '❌ NO':<32}       ║
║ Alignment Score:    {confluence.alignment_score:.0%}                             ║
║ Confidence Adjust:  {confluence.confidence_adjustment:+.0%}                            ║
║ Reasoning:          {confluence.reasoning:<41} ║
╚════════════════════════════════════════════════════════════╝
        """)
