#!/usr/bin/env python3
"""
Integração Telegram para notificações em produção.
Envia sinais de trading via bot do Telegram.
"""

import os
from typing import Optional

import requests


class TelegramNotifier:
    """Notificador de sinais de trading via Telegram."""
    
    def __init__(
        self,
        token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        """
        Inicializa notificador.
        
        Args:
            token: Token do bot Telegram (env: TELEGRAM_TOKEN)
            chat_id: Chat ID (env: TELEGRAM_CHAT_ID)
        """
        self.token = token or os.getenv("TELEGRAM_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token and self.chat_id)
    
    def send_signal(
        self,
        action: str,  # "CALL", "PUT", "STRANGLE", "NO_TRADE"
        symbol: str,
        timeframe: str,
        p_up: float,
        p_down: float,
        p_flat: float,
        confidence: float,
    ) -> bool:
        """
        Envia sinal de trading via Telegram.
        
        Returns:
            True se enviado, False se desabilitado ou erro.
        """
        if not self.enabled:
            return False
        
        emoji_map = {
            "CALL": "📈",
            "PUT": "📉",
            "STRANGLE": "⚖️",
            "NO_TRADE": "🚫",
        }
        emoji = emoji_map.get(action, "❓")
        
        message = (
            f"{emoji} *{action}*\n"
            f"`{symbol}` | `{timeframe}`\n"
            f"\n"
            f"P(↑) = {p_up:.2%}\n"
            f"P(→) = {p_flat:.2%}\n"
            f"P(↓) = {p_down:.2%}\n"
            f"\n"
            f"🎯 Conf: {confidence:.2%}"
        )
        
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            response = requests.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                },
                timeout=5,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[TG] Erro: {e}")
            return False
    
    def send_alert(self, title: str, message: str) -> bool:
        """Envia alerta genérico."""
        if not self.enabled:
            return False
        
        text = f"⚠️ *{title}*\n\n{message}"
        
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            response = requests.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                },
                timeout=5,
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[TG Alert] Erro: {e}")
            return False
