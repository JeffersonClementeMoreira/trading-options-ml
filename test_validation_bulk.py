#!/usr/bin/env python3
"""
Teste completo - Envia 50 candles históricos + 1 novo
Para ativar a lógica de indicadores
"""

import json
import requests
from datetime import datetime, timedelta

def send_historical_candles():
    """Enviar 50 candles históricos para construir base"""
    
    print("📤 Enviando 50 candles históricos (para ativar indicadores)...")
    print()
    
    # Começar 50 candles no passado (cada um é M15, então 50*15 minutos = 750 min = 12.5h)
    base_time = datetime.utcnow() - timedelta(minutes=50*15)
    
    xauusd_price = 4510.00  # Preço ouro
    eurusd_price = 1.0850   # Preço EUR/USD
    
    errors = 0
    success = 0
    
    # Enviar XAUUSD histórico
    print("  XAUUSD histórico:")
    for i in range(50):
        candle_time = base_time + timedelta(minutes=i*15)
        
        # Simular movimento de preço realista
        movement = (i - 25) * 2  # Movimento de -50 a +50
        price = xauusd_price + (movement / 100)  # Oscilação pequena
        
        candle = {
            "symbol": "XAUUSD",
            "datetime": candle_time.isoformat(),
            "open": price - 0.5,
            "high": price + 0.8,
            "low": price - 0.8,
            "close": price,
            "volume": 1000 + i * 50
        }
        
        try:
            response = requests.post(
                'http://127.0.0.1:8765/mt5/candle',
                json=candle,
                timeout=5
            )
            if response.status_code == 200:
                success += 1
            else:
                errors += 1
        except Exception as e:
            errors += 1
            print(f"      ❌ Erro candle {i}: {e}")
    
    print(f"  ✅ {success}/50 candles enviados com sucesso")
    if errors > 0:
        print(f"  ⚠️  {errors} erros")
    
    print()
    print("  EURUSD histórico:")
    success = 0
    errors = 0
    for i in range(50):
        candle_time = base_time + timedelta(minutes=i*15)
        
        # Simular movimento de preço realista
        movement = (i - 25) * 0.0002
        price = eurusd_price + movement
        
        candle = {
            "symbol": "EURUSD",
            "datetime": candle_time.isoformat(),
            "open": price - 0.0005,
            "high": price + 0.0008,
            "low": price - 0.0008,
            "close": price,
            "volume": 2000 + i * 100
        }
        
        try:
            response = requests.post(
                'http://127.0.0.1:8765/mt5/candle',
                json=candle,
                timeout=5
            )
            if response.status_code == 200:
                success += 1
            else:
                errors += 1
        except Exception as e:
            errors += 1
    
    print(f"  ✅ {success}/50 candles enviados com sucesso")
    if errors > 0:
        print(f"  ⚠️  {errors} erros")
    
    print()
    print("="*70)
    print("✅ HISTÓRICO CARREGADO! Agora mandando novos candles acionarão indicadores")
    print("="*70)
    print()
    
    # Agora enviar 1 candle novo
    print("📤 Enviando NOVO candle (deve ativar indicadores + WebSocket)...")
    print()
    
    new_time = datetime.utcnow()
    
    # XAUUSD novo
    new_candle = {
        "symbol": "XAUUSD",
        "datetime": new_time.isoformat(),
        "open": 4510.00,
        "high": 4512.50,
        "low": 4508.75,
        "close": 4511.50,
        "volume": 1500
    }
    
    print(f"  XAUUSD:")
    print(f"    DateTime: {new_candle['datetime']}")
    print(f"    Close: {new_candle['close']:.5f}")
    
    try:
        response = requests.post(
            'http://127.0.0.1:8765/mt5/candle',
            json=new_candle,
            timeout=5
        )
        print(f"    ✅ Resposta HTTP: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Erro: {e}")
    
    print()
    
    # EURUSD novo
    new_candle_eur = {
        "symbol": "EURUSD",
        "datetime": new_time.isoformat(),
        "open": 1.0848,
        "high": 1.0852,
        "low": 1.0845,
        "close": 1.0851,
        "volume": 2500
    }
    
    print(f"  EURUSD:")
    print(f"    DateTime: {new_candle_eur['datetime']}")
    print(f"    Close: {new_candle_eur['close']:.5f}")
    
    try:
        response = requests.post(
            'http://127.0.0.1:8765/mt5/candle',
            json=new_candle_eur,
            timeout=5
        )
        print(f"    ✅ Resposta HTTP: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Erro: {e}")
    
    print()
    print("="*70)
    print("✅ CANDLES REAIS ENVIADOS COM SUCESSO!")
    print("   Verifique no servidor se calculou indicadores corretamente")
    print("="*70)

if __name__ == '__main__':
    send_historical_candles()
