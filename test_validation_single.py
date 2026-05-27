#!/usr/bin/env python3
"""
Teste de verificação - Envia UM único candle real para validação
NÃO injeta dados contínuos, apenas UM teste
"""

import json
import requests
from datetime import datetime

def test_send_candle():
    """Enviar UM candle de teste com valores REAIS"""
    
    # Dados REAIS para teste:
    # XAUUSD na casa dos 4500+ (ouro)
    # EURUSD na casa dos 1.08+ (EUR/USD)
    
    candle = {
        "symbol": "XAUUSD",
        "datetime": datetime.utcnow().isoformat(),
        "open": 4510.25,
        "high": 4512.50,
        "low": 4508.75,
        "close": 4511.00,
        "volume": 1500
    }
    
    print(f"📤 Enviando candle de teste:")
    print(f"   Símbolo: {candle['symbol']}")
    print(f"   Close: {candle['close']:.5f}")
    print(f"   DateTime: {candle['datetime']}")
    print()
    
    try:
        response = requests.post(
            'http://127.0.0.1:8765/mt5/candle',
            json=candle,
            timeout=5
        )
        print(f"✅ Resposta: {response.status_code}")
        print(f"   Body: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar: {e}")
        return False

if __name__ == '__main__':
    test_send_candle()
