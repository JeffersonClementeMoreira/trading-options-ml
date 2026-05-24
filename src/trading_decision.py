#!/usr/bin/env python3
"""
Estratégia de decisão de trading baseada em probabilidades do XGBoost.

Mapeia (p_down, p_flat, p_up) → (CALL, PUT, STRANGLE, NO_TRADE)
Considera confidence threshold e envios Telegram em produção.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import requests


class TradeAction(Enum):
    """Ação de trading recomendada."""
    SELL_CALL = "SELL_CALL"     # Vender CALL (espera baixa)
    SELL_PUT = "SELL_PUT"       # Vender PUT (espera alta)
    SELL_STRANGLE = "SELL_STRANGLE"  # Incerteza: venda de ambas
    NO_TRADE = "NO_TRADE"       # Confiãnça insuficiente


@dataclass
class TradingSignal:
    """Sinal de trading com metadados."""
    action: TradeAction
    symbol: str
    timeframe: str
    datetime: str
    p_up: float
    p_down: float
    p_flat: float
    confidence: float  # Máxima probabilidade
    reasoning: str


class TradingDecisionEngine:
    """Engine que converte probabilidades em decisões de trading."""
    
    def __init__(
        self,
        confidence_threshold: float = 0.55,
        strangle_threshold: float = 0.40,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
    ):
        """
        Args:
            confidence_threshold: Mínima confiança para trade (padrão 55%)
            strangle_threshold: Se p_up ou p_down < isso, considerar STRANGLE
            telegram_token: Token do bot Telegram (variável ENV: TELEGRAM_TOKEN)
            telegram_chat_id: Chat ID Telegram (variável ENV: TELEGRAM_CHAT_ID)
        """
        self.confidence_threshold = confidence_threshold
        self.strangle_threshold = strangle_threshold
        
        # Carrega credenciais do ambiente se não fornecidas
        self.telegram_token = telegram_token or os.getenv("TELEGRAM_TOKEN")
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
    def decide(
        self,
        symbol: str,
        timeframe: str,
        datetime_str: str,
        p_down: float,
        p_flat: float,
        p_up: float,
    ) -> TradingSignal:
        """Decide acao baseada em probabilidades (ESTRATEGIA DE VENDA).
        
        Logica:
        1. confidence = max(p_up, p_down, p_flat)
        2. Se confidence < threshold: NO_TRADE
        3. Se |p_up - p_down| < strangle_threshold: STRANGLE (venda de volatilidade)
        4. Se p_up > p_down: PUT_SELL (venda PUT pois espera alta)
        5. Se p_down > p_up: CALL_SELL (venda CALL pois espera baixa)
        """
        confidence = max(p_up, p_down, p_flat)
        
        # Sem confiança → não trade
        if confidence < self.confidence_threshold:
            return TradingSignal(
                action=TradeAction.NO_TRADE,
                symbol=symbol,
                timeframe=timeframe,
                datetime=datetime_str,
                p_up=p_up,
                p_down=p_down,
                p_flat=p_flat,
                confidence=confidence,
                reasoning=f"Confiança insuficiente ({confidence:.2%} < {self.confidence_threshold:.2%})"
            )
        
        # Análise de direção (apenas entre UP e DOWN)
        up_down_spread = abs(p_up - p_down)
        
        # Se a diferença é pequena → SELL_STRANGLE (incerteza alta)
        if up_down_spread < self.strangle_threshold:
            action = TradeAction.SELL_STRANGLE
            reasoning = f"Spread UP/DOWN baixo ({up_down_spread:.2%}): vender volatilidade"
        # Tendência clara para cima → VENDER PUT
        elif p_up > p_down:
            action = TradeAction.SELL_PUT
            reasoning = f"Bullish: P(UP)={p_up:.2%} > P(DOWN)={p_down:.2%} → vender PUT"
        # Tendência clara para baixo → VENDER CALL
        else:
            action = TradeAction.SELL_CALL
            reasoning = f"Bearish: P(DOWN)={p_down:.2%} > P(UP)={p_up:.2%} → vender CALL"
        
        return TradingSignal(
            action=action,
            symbol=symbol,
            timeframe=timeframe,
            datetime=datetime_str,
            p_up=p_up,
            p_down=p_down,
            p_flat=p_flat,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def send_telegram(self, signal: TradingSignal) -> bool:
        """
        Envia sinal via Telegram em produção.
        
        Returns:
            True se enviado com sucesso, False caso contrário.
        """
        if not self.telegram_token or not self.telegram_chat_id:
            return False
        
        # Formatação da mensagem
        emoji_map = {
            TradeAction.SELL_CALL: "📉",
            TradeAction.SELL_PUT: "📈",
            TradeAction.SELL_STRANGLE: "⚖️",
            TradeAction.NO_TRADE: "🚫",
        }
        
        emoji = emoji_map.get(signal.action, "❓")
        
        message = (
            f"{emoji} *{signal.action.value}*\n"
            f"Symbol: `{signal.symbol}` | TF: `{signal.timeframe}`\n"
            f"DateTime: {signal.datetime}\n"
            f"\n"
            f"📊 Probabilidades:\n"
            f"  • P(UP): {signal.p_up:.2%}\n"
            f"  • P(FLAT): {signal.p_flat:.2%}\n"
            f"  • P(DOWN): {signal.p_down:.2%}\n"
            f"\n"
            f"🎯 Confiança: {signal.confidence:.2%}\n"
            f"💡 {signal.reasoning}"
        )
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }
        
        try:
            response = requests.post(url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao enviar Telegram: {e}")
            return False


def format_signal_for_backtest(signal: TradingSignal) -> dict:
    """Formata sinal para output em backtest (CSV/HTML)."""
    return {
        "action": signal.action.value,
        "symbol": signal.symbol,
        "timeframe": signal.timeframe,
        "datetime": signal.datetime,
        "p_up": f"{signal.p_up:.4f}",
        "p_down": f"{signal.p_down:.4f}",
        "p_flat": f"{signal.p_flat:.4f}",
        "confidence": f"{signal.confidence:.4f}",
        "reasoning": signal.reasoning,
    }


# Mapa de cores para HTML colorido
ACTION_COLOR_MAP = {
    TradeAction.SELL_CALL: "#FFB6C6",  # Vermelho claro (venda CALL = bearish)
    TradeAction.SELL_PUT: "#90EE90",   # Verde claro (venda PUT = bullish)
    TradeAction.SELL_STRANGLE: "#FFD700",   # Ouro
    TradeAction.NO_TRADE: "#D3D3D3",   # Cinza
}
