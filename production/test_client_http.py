#!/usr/bin/env python3
"""
MT5 HTTP Test Client - Simula MT5 enviando candles M15
Útil para testar servidor sem precisar de MT5 rodando
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta
import random
import pandas as pd

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ════════════════════════════════════════════════════════════════════════════

SERVER_URL = 'http://localhost:8765'
PAIRS = ['EURUSD', 'GBPUSD']

# Dados simulados (próximos a preços reais)
PRICES = {
    'EURUSD': {'open': 1.0850, 'close': 1.0855, 'variation': 0.0010},
    'GBPUSD': {'open': 1.2750, 'close': 1.2755, 'variation': 0.0015},
}

# ════════════════════════════════════════════════════════════════════════════
# FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def send_candle(pair, timestamp, o, h, l, c, v):
    """Envia candle para o servidor HTTP"""
    
    payload = {
        'symbol': pair,
        'datetime': timestamp.isoformat(),
        'open': o,
        'high': h,
        'low': l,
        'close': c,
        'volume': v
    }
    
    try:
        response = requests.post(
            f'{SERVER_URL}/mt5/candle',
            json=payload,
            timeout=5
        )
        
        if response.ok:
            result = response.json()
            signal = result.get('signal', 0)
            confidence = result.get('confidence', 0)
            
            print(f"  ✅ {pair} @ {timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"     O={o:.5f} | H={h:.5f} | L={l:.5f} | C={c:.5f} | V={v}")
            print(f"     🎯 Signal: {signal} | Confidence: {confidence:.1%}")
            print()
            
            return True
        else:
            print(f"  ❌ {pair}: Server error: {response.status_code}")
            print(f"     {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"  ❌ {pair}: Cannot connect to server at {SERVER_URL}")
        print(f"     Make sure server is running: python3 production/server_mt5_http.py")
        return False
    except Exception as e:
        print(f"  ❌ {pair}: Error: {e}")
        return False

def simulate_candles(pair, count=21, interval_hours=0.25):
    """Simula candles históricos (21 últimos M15)"""
    
    print(f"\n📊 Simulando {count} candles históricos para {pair}...")
    
    base_price = PRICES[pair]['open']
    variation = PRICES[pair]['variation']
    
    current_time = datetime.utcnow() - timedelta(minutes=15*count)
    
    for i in range(count):
        # Preço varia aleatoriamente
        trend = random.choice([-1, 0, 1])
        o = base_price + (trend * variation * 0.5)
        c = o + (random.random() * variation - variation/2)
        h = max(o, c) + (random.random() * variation * 0.1)
        l = min(o, c) - (random.random() * variation * 0.1)
        v = random.randint(500, 2000)
        
        send_candle(pair, current_time, o, h, l, c, v)
        
        base_price = c  # Próximo candle começa no close
        current_time += timedelta(minutes=15)
        
        time.sleep(0.1)  # Pequeno delay entre requests

def send_real_candles(pair, count=5):
    """Envia candles reais (próximos 5 M15)"""
    
    print(f"\n📨 Enviando {count} candles reais para {pair}...")
    
    base_price = PRICES[pair]['close']
    variation = PRICES[pair]['variation']
    
    current_time = datetime.utcnow()
    
    for i in range(count):
        # Candle realista
        trend = random.choice([-1, 0, 1])
        o = base_price + (trend * variation * 0.3)
        c = o + (random.random() * variation - variation/2)
        h = max(o, c) + (random.random() * variation * 0.05)
        l = min(o, c) - (random.random() * variation * 0.05)
        v = random.randint(1000, 5000)
        
        send_candle(pair, current_time, o, h, l, c, v)
        
        base_price = c
        current_time += timedelta(minutes=15)
        
        # Esperar 1 segundo entre candles
        if i < count - 1:
            time.sleep(1)

# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                            ║")
    print("║                  🧪 MT5 HTTP SERVER TEST CLIENT                           ║")
    print("║                                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print("")
    
    # Verificar conexão
    print("🔌 Verificando conexão com servidor...")
    try:
        response = requests.get(f'{SERVER_URL}/mt5/status', timeout=5)
        status = response.json()
        print(f"✅ Servidor conectado!")
        print(f"   Status: {status.get('status')}")
        print(f"   Pares: {status.get('pairs_tracked')}")
        print(f"   Modelos carregados: {status.get('models_loaded')}")
    except:
        print(f"❌ Não conseguiu conectar a {SERVER_URL}")
        print(f"   Execute primeiro: python3 production/server_mt5_http.py")
        sys.exit(1)
    
    print("")
    
    # Enviar candles históricos + reais
    for pair in PAIRS:
        print(f"\n{'='*80}")
        print(f"  {pair}")
        print('='*80)
        
        # Histórico (buffer de 21 candles)
        simulate_candles(pair, count=21, interval_hours=0.25)
        
        # Reais (próximos candles)
        send_real_candles(pair, count=3)
        
        print()
        time.sleep(2)
    
    print("")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                          ✅ TEST COMPLETO                                 ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print("")
    print("📊 RESULTADOS:")
    print("")
    print("   Ver logs detalhados:")
    print("   $ tail -f /tmp/mt5_server.log")
    print("")
    print("   Sinais enviados:")
    print("   $ grep 'SINAL GERADO' /tmp/mt5_server.log")
    print("")
    print("   Telegram enviado:")
    print("   $ grep 'Telegram enviado' /tmp/mt5_server.log")
    print("")
