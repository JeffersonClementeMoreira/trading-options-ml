"""
🎯 CONFLUENCE FILTER
Usa os top indicadores para validar entrada de sinal
Aumenta acurácia filtrando false signals
"""

import pandas as pd
import numpy as np


def calculate_confluence_score(row):
    """
    Calcula score de confluência baseado nos TOP 5 indicadores
    com MAIOR importância no modelo D+1
    
    Top Indicators:
    1. SMA 20 - 6.41%
    2. SMA 50 - 6.40%
    3. Confluence Score - 6.11%
    4. MACD Signal - 4.83%
    5. Range Duration - 4.82%
    
    Returns: score 0-100 (100 = máxima confluência)
    """
    
    score = 0.0
    weight = 0.0
    
    # 1. SMA ALIGNMENT (20% weight)
    # Quando preço alinha com SMA = força de tendência
    if 'price_above_sma20' in row.index:
        price_above_20 = row.get('price_above_sma20', 0)
        price_above_50 = row.get('price_above_sma50', 0)
        
        if price_above_20 == price_above_50:  # Aligned
            score += 20
        weight += 20
    
    # 2. SMA MOMENTUM (15% weight)
    # SMA20 > SMA50 = uptrend, SMA20 < SMA50 = downtrend
    if 'sma_alignment' in row.index:
        alignment = row.get('sma_alignment', 0)
        if alignment != 0:  # Strong trend
            score += 15 * abs(alignment)
        weight += 15
    
    # 3. CONFLUENCE SCORE (15% weight)
    # Already calculated in features
    if 'confluence_score' in row.index:
        conf = row.get('confluence_score', 0.5)
        score += 15 * min(max(conf, 0), 1)
        weight += 15
    
    # 4. MACD CONFIRMATION (20% weight)
    # MACD histogram shows momentum
    if 'macd_histogram' in row.index:
        histogram = row.get('macd_histogram', 0)
        macd_signal = row.get('macd_signal', 0)
        
        # MACD crossover or strong histogram = confirmation
        if (histogram > 0 and macd_signal > 0) or (histogram < 0 and macd_signal < 0):
            score += 20  # Strong confirmation
        elif histogram != 0:
            score += 10  # Weak confirmation
        weight += 20
    
    # 5. VOLATILITY REGIME (15% weight)
    # Low vol spike during confluence = better entry
    if 'vol_spike' in row.index:
        vol_spike = row.get('vol_spike', 0)
        if vol_spike < 1.2:  # Not spiking too much
            score += 15 * (1 - vol_spike / 2)
        weight += 15
    
    # 6. TREND CONFIRMATION (10% weight)
    if 'trend_confirmation' in row.index:
        trend_conf = row.get('trend_confirmation', 0)
        if trend_conf > 0.5:
            score += 10
        weight += 10
    
    # Normalize to 0-100
    if weight > 0:
        confluence_pct = (score / weight) * 100
    else:
        confluence_pct = 0.0
    
    return confluence_pct


def should_open_trade(model_prob, confluence_score, confidence_threshold=60):
    """
    Decide se deve abrir trade baseado em confluência
    
    Args:
        model_prob: probabilidade do modelo (0-1)
        confluence_score: score de confluência (0-100)
        confidence_threshold: threshold mínimo (default 60%)
    
    Returns:
        {
            'should_open': bool,
            'confidence': float,
            'direction': 'UP' or 'DOWN' or None,
            'reason': str
        }
    """
    
    # Converte probabilidade para 0-100
    model_prob_pct = model_prob * 100
    
    # Combina modelo com confluência (50% peso cada)
    combined_confidence = (model_prob_pct * 0.5) + (confluence_score * 0.5)
    
    # Determina direção
    if model_prob_pct > 50:
        direction = 'UP'
    elif model_prob_pct < 50:
        direction = 'DOWN'
    else:
        direction = None
    
    # Decision logic
    should_open = False
    reason = ""
    
    if combined_confidence >= confidence_threshold:
        # Strong signal + Good confluence
        if confluence_score >= 70:
            should_open = True
            reason = f"🎯 STRONG SIGNAL: Model {model_prob_pct:.1f}% + Confluence {confluence_score:.1f}%"
        # Good signal with decent confluence
        elif combined_confidence >= 65 and confluence_score >= 55:
            should_open = True
            reason = f"✅ VALID SIGNAL: Combined confidence {combined_confidence:.1f}%"
    
    # Weak signal, even with good confluence - skip
    if model_prob_pct < 52 and model_prob_pct > 48:
        should_open = False
        reason = "⏭️ SKIP: Indecisive signal (50/50)"
    
    return {
        'should_open': should_open,
        'confidence': combined_confidence,
        'direction': direction,
        'reason': reason,
        'model_prob': model_prob_pct,
        'confluence': confluence_score
    }


def get_strike_selection(direction, entry_price, probability, max_distance=500):
    """
    Seleciona strike com base na probabilidade
    
    Strategy selection:
    - Probability > 65% → Narrow strategies (Call/Put, Call/Put Spread)
    - Probability 55-65% → Medium strategies (Spreads, Strangle)
    - Probability 45-55% → Wide strategies (Straddle, Iron Condor)
    
    Args:
        direction: 'UP' or 'DOWN'
        entry_price: preço de entrada
        probability: probabilidade do modelo (0-1)
        max_distance: distância máxima do strike do entry
    
    Returns:
        {
            'strategy': str,
            'strike_call': float,
            'strike_put': float,
            'width': float,
            'max_loss': float
        }
    """
    
    prob_pct = probability * 100
    distance = max_distance / 2  # Default ~250 pontos
    
    if prob_pct > 65:
        # High confidence: Use narrow strategies
        if direction == 'UP':
            strategy = 'CALL'
            strike_call = entry_price + (distance * 0.3)
            strike_put = entry_price - (distance * 0.2)
        else:
            strategy = 'PUT'
            strike_call = entry_price + (distance * 0.2)
            strike_put = entry_price - (distance * 0.3)
        width = distance * 0.5
    
    elif prob_pct > 55:
        # Medium confidence: Use spreads
        if direction == 'UP':
            strategy = 'CALL_SPREAD'
            strike_call = entry_price + (distance * 0.2)
            strike_put = entry_price  # Short leg
        else:
            strategy = 'PUT_SPREAD'
            strike_call = entry_price  # Short leg
            strike_put = entry_price - (distance * 0.2)
        width = distance
    
    else:
        # Low confidence: Use wide strategies
        strategy = 'STRANGLE' if direction == 'UP' else 'STRANGLE'
        strike_call = entry_price + (distance * 0.4)
        strike_put = entry_price - (distance * 0.4)
        width = distance * 0.8
    
    max_loss = max_distance
    
    return {
        'strategy': strategy,
        'strike_call': round(strike_call, 2),
        'strike_put': round(strike_put, 2),
        'width': round(width, 2),
        'max_loss': max_loss,
        'probability': prob_pct
    }


def format_trade_signal(confluence_result, strike_result, entry_price):
    """
    Formata sinal de trade para log/debug
    """
    
    if not confluence_result['should_open']:
        return f"❌ SKIP: {confluence_result['reason']}"
    
    msg = f"""
    ✅ TRADE SIGNAL
    Direction: {confluence_result['direction']}
    Entry: {entry_price:.2f}
    Model Probability: {confluence_result['model_prob']:.1f}%
    Confluence Score: {confluence_result['confluence']:.1f}%
    Combined Confidence: {confluence_result['confidence']:.1f}%
    
    Strategy: {strike_result['strategy']}
    Call Strike: {strike_result['strike_call']:.2f}
    Put Strike: {strike_result['strike_put']:.2f}
    Max Loss: {strike_result['max_loss']} points
    
    Reason: {confluence_result['reason']}
    """
    
    return msg
