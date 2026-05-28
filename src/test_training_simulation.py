#!/usr/bin/env python3
"""
Teste simulado: Enviar dados fictícios para validar sistema
Este é apenas para demonstração - os dados reais vêm do MT5
"""

import requests
import json
import random
from datetime import datetime, timedelta

def simulate_mt5_data():
    """Simular dados do MT5 (apenas para teste)"""
    
    print("╔════════════════════════════════════════════════════════╗")
    print("║  TESTE: Simular Dados do MT5 → Python Training        ║")
    print("╚════════════════════════════════════════════════════════╝")
    print("")
    
    # Símbolos e preços iniciais
    symbols = {
        'EURUSD': 1.0850,
        'GBPUSD': 1.2700,
        'XAUUSD': 2400.0,
    }
    
    for symbol, initial_price in symbols.items():
        print(f"📊 Simulando {symbol}...")
        
        # Gerar 500 candles com movimento browniano
        candles = []
        price = initial_price
        
        start_time = datetime(2026, 5, 15, 10, 0, 0)
        
        for i in range(500):
            # Movimento aleatório
            change = random.gauss(0, 0.0005) * price
            open_price = price
            close_price = price + change
            high_price = max(open_price, close_price) + random.uniform(0, 0.0002) * price
            low_price = min(open_price, close_price) - random.uniform(0, 0.0002) * price
            volume = random.randint(100000, 1000000)
            
            candle_time = start_time + timedelta(minutes=15*i)
            
            candles.append({
                'datetime': candle_time.strftime('%Y.%m.%d %H:%M:%S'),
                'open': round(open_price, 5),
                'high': round(high_price, 5),
                'low': round(low_price, 5),
                'close': round(close_price, 5),
                'volume': volume,
            })
            
            price = close_price
        
        # Preparar JSON
        data = {
            'symbol': symbol,
            'timeframe': 'M15',
            'data': candles,
        }
        
        # Enviar para servidor
        try:
            print(f"   📤 Enviando {len(candles)} candles...")
            response = requests.post(
                'http://0.0.0.0:9999/train',
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"   ✅ Resposta: {response.json()}")
            else:
                print(f"   ❌ Erro: {response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Erro de conexão: {e}")
        
        print("")
    
    print("✅ Teste concluído!")

if __name__ == '__main__':
    simulate_mt5_data()
