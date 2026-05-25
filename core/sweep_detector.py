"""
Detector de Sweeps em H4 + Validação em M15

Estratégia:
1. Detecta SWEEP em H4 (breakout de estrutura alta/baixa)
2. Valida confirmação em M15
3. Verifica se aceleração está reduzindo (momentum)
4. Combina com confluência para filtrar sinais
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SweepAnalysis:
    """Resultado da análise de sweep."""
    date: str
    h4_sweep_type: str  # 'HIGH', 'LOW', 'NONE'
    h4_sweep_strength: float  # 0-100
    m15_confirmation: str  # 'STRONG', 'WEAK', 'NONE'
    momentum_acceleration: float  # -1.0 a 1.0
    momentum_trend: str  # 'REDUCING', 'STABLE', 'INCREASING'
    is_tradeable: bool  # Se atende todos os critérios
    confidence: float  # 0-100
    reasoning: str


class SweepDetector:
    """Detecta sweeps e valida em M15."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
    
    def detect_h4_sweep(self, h4_df: pd.DataFrame) -> Tuple[str, float]:
        """
        Detecta sweep em H4 (breakout de estrutura).
        
        SWEEP HIGH: Price quebra acima da estrutura alta
        SWEEP LOW: Price quebra abaixo da estrutura baixa
        
        Return: (sweep_type, strength 0-100)
        """
        if len(h4_df) < 5:
            return 'NONE', 0.0
        
        # Últimas 5 barras H4
        recent = h4_df.iloc[-5:].copy()
        current = recent.iloc[-1]
        
        # Calcular estrutura (highs e lows dos últimos 5)
        highs = recent['high'].values
        lows = recent['low'].values
        
        prev_high = np.max(highs[:-1])  # High sem a barra atual
        prev_low = np.min(lows[:-1])
        
        # Verificar sweep
        sweep_type = 'NONE'
        strength = 0.0
        
        # SWEEP HIGH
        if current['low'] > prev_high:
            sweep_type = 'HIGH'
            # Força = quanto % acima da estrutura
            range_size = prev_high - prev_low
            if range_size > 0:
                strength = min(100, ((current['low'] - prev_high) / range_size) * 100)
        
        # SWEEP LOW
        elif current['high'] < prev_low:
            sweep_type = 'LOW'
            # Força = quanto % abaixo da estrutura
            range_size = prev_high - prev_low
            if range_size > 0:
                strength = min(100, ((prev_low - current['high']) / range_size) * 100)
        
        return sweep_type, strength
    
    def validate_in_m15(self, m15_df: pd.DataFrame, sweep_type: str) -> str:
        """
        Valida sweep em M15 (últimas 4 barras = 1 barra H4).
        
        STRONG: M15 também mostra movimento na mesma direção
        WEAK: Contradição ou fraco movimento em M15
        NONE: Sem validação
        """
        if len(m15_df) < 4:
            return 'NONE'
        
        # Últimas 4 barras M15 (= 1 barra H4)
        recent = m15_df.iloc[-4:].copy()
        
        if sweep_type == 'HIGH':
            # Esperamos que M15 faça lower highs ou consolidação (antes do breakout)
            # Então última barra M15 deve fechar acima das anteriores
            
            highs = recent['high'].values
            closes = recent['close'].values
            
            # Confere se foi movimento coeso pra cima
            if closes[-1] > closes[-2] and closes[-2] > closes[-3]:
                return 'STRONG'
            elif closes[-1] > np.mean(closes[:-1]):
                return 'WEAK'
            else:
                return 'NONE'
        
        elif sweep_type == 'LOW':
            # Esperamos movimento pra baixo em M15
            
            lows = recent['low'].values
            closes = recent['close'].values
            
            # Confere se foi movimento coeso pra baixo
            if closes[-1] < closes[-2] and closes[-2] < closes[-3]:
                return 'STRONG'
            elif closes[-1] < np.mean(closes[:-1]):
                return 'WEAK'
            else:
                return 'NONE'
        
        return 'NONE'
    
    def analyze_momentum_acceleration(self, m15_df: pd.DataFrame) -> Tuple[float, str]:
        """
        Analisa se aceleração/momentum está reduzindo.
        
        Momento ideal: Breakout forte mas começando a desacelerar
        (evita comprar no topo da onda)
        
        Return: (momentum_change -1.0 a 1.0, trend 'REDUCING'/'STABLE'/'INCREASING')
        """
        if len(m15_df) < 10:
            return 0.0, 'STABLE'
        
        recent = m15_df.iloc[-10:].copy()
        
        # Calcular momentum (mudança de preço)
        momentum = recent['close'].diff().dropna()
        
        # Calcular aceleração (mudança de momentum)
        acceleration = momentum.diff().dropna()
        
        if len(acceleration) < 2:
            return 0.0, 'STABLE'
        
        # Comparar aceleração recente vs anterior
        recent_accel = acceleration.iloc[-3:].mean()
        older_accel = acceleration.iloc[-6:-3].mean()
        
        # Change: -1.0 = reduzindo bastante, 0.0 = estável, 1.0 = aumentando
        if older_accel != 0:
            change = (recent_accel - older_accel) / abs(older_accel)
            change = np.clip(change, -1.0, 1.0)
        else:
            change = 0.0
        
        # Classificar
        if change < -0.2:
            trend = 'REDUCING'
        elif change > 0.2:
            trend = 'INCREASING'
        else:
            trend = 'STABLE'
        
        return change, trend
    
    def analyze_sweep_day(self, m15_df: pd.DataFrame, date_str: str) -> SweepAnalysis:
        """Análise completa de sweep para um dia."""
        
        # === Converter M15 para H4 ===
        # Último candle H4 = últimas 4 barras M15
        if len(m15_df) < 4:
            h4_data = m15_df.copy()
        else:
            # Agrupar últimas 4 barras como H4
            h4_ohlc = {
                'open': m15_df['open'].iloc[0],
                'high': m15_df['high'].max(),
                'low': m15_df['low'].min(),
                'close': m15_df['close'].iloc[-1],
                'volume': m15_df.get('volume', pd.Series([0])).sum()
            }
            h4_data = pd.DataFrame([h4_ohlc])
        
        # === DETECTAR SWEEP EM H4 ===
        sweep_type, sweep_strength = self.detect_h4_sweep(h4_data)
        
        # === VALIDAR EM M15 ===
        m15_confirmation = self.validate_in_m15(m15_df, sweep_type)
        
        # === ANALISAR MOMENTUM ===
        momentum_accel, momentum_trend = self.analyze_momentum_acceleration(m15_df)
        
        # === CALCULAR CONFIANÇA ===
        confidence = 0.0
        is_tradeable = False
        
        if sweep_type != 'NONE':
            confidence = sweep_strength * 0.4  # 40% da força do sweep
            
            if m15_confirmation == 'STRONG':
                confidence += 50  # +50% se confirmado
            elif m15_confirmation == 'WEAK':
                confidence += 20  # +20% se fraco
            
            if momentum_trend == 'REDUCING':
                confidence += 20  # +20% se desacelerando (bom!)
            elif momentum_trend == 'INCREASING':
                confidence -= 10  # -10% se acelerando (pode explodir)
            
            confidence = min(100, max(0, confidence))
            
            # É tradeable se:
            # - Sweep detectado + confirmação forte + momentum reduzindo
            is_tradeable = (
                m15_confirmation != 'NONE' and 
                momentum_trend in ['REDUCING', 'STABLE'] and
                confidence > 60
            )
        
        # === REASONING ===
        reasoning_parts = []
        
        if sweep_type == 'NONE':
            reasoning = "⚠️ Nenhum sweep detectado"
        else:
            reasoning_parts.append(f"{'🔼' if sweep_type == 'HIGH' else '🔽'} SWEEP {sweep_type}")
            reasoning_parts.append(f"Força: {sweep_strength:.0f}%")
            reasoning_parts.append(f"Confirmação M15: {m15_confirmation}")
            reasoning_parts.append(f"Momentum: {momentum_trend}")
            
            if is_tradeable:
                reasoning_parts.append("✅ TRADEABLE")
            else:
                reasoning_parts.append("❌ Não atende critérios")
            
            reasoning = " | ".join(reasoning_parts)
        
        return SweepAnalysis(
            date=date_str,
            h4_sweep_type=sweep_type,
            h4_sweep_strength=sweep_strength,
            m15_confirmation=m15_confirmation,
            momentum_acceleration=momentum_accel,
            momentum_trend=momentum_trend,
            is_tradeable=is_tradeable,
            confidence=confidence,
            reasoning=reasoning
        )
