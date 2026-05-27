#!/usr/bin/env python3
"""
Teste simulado do SendCandlesToServer.mq5 v2.0
Emula exatamente o comportamento do script MQL5
"""

import json
import requests
from datetime import datetime, timedelta
import time

def simulate_mt5_init():
    """Simular anexação do script no MT5"""
    
    print("╔═══════════════════════════════════════════════════════════════════════════╗")
    print("║         🧪 TESTE: Simulando Comportamento do MQL5 v2.0                  ║")
    print("║        (Como se fosse anexado ao gráfico XAUUSD M15 no MT5)             ║")
    print("╚═══════════════════════════════════════════════════════════════════════════╝")
    print()
    
    print("📋 FASE 1: OnStart() - Script Inicializa ao Anexar")
    print("─" * 73)
    print()
    
    # Simular datetimes (últimas 60 candles = 900 minutos = 15 horas)
    base_time = datetime.utcnow() - timedelta(minutes=60*15)
    
    print("✓ Rastreando últimos datetimes para detectar novos candles...")
    print()
    
    # PRIMEIRO: Enviar ÚLTIMO CANDLE FECHADO (index=1)
    print("🚀 Enviando ÚLTIMO CANDLE FECHADO inicial (index=1)...")
    print()
    
    candles_initial = [
        {
            "symbol": "XAUUSD",
            "datetime": (base_time + timedelta(minutes=45*15)).isoformat(),
            "open": 4510.00,
            "high": 4512.50,
            "low": 4508.75,
            "close": 4511.25,
            "volume": 1500
        },
        {
            "symbol": "EURUSD",
            "datetime": (base_time + timedelta(minutes=45*15)).isoformat(),
            "open": 1.0848,
            "high": 1.0852,
            "low": 1.0845,
            "close": 1.0851,
            "volume": 2500
        },
        {
            "symbol": "GBPUSD",
            "datetime": (base_time + timedelta(minutes=45*15)).isoformat(),
            "open": 1.2648,
            "high": 1.2652,
            "low": 1.2645,
            "close": 1.2650,
            "volume": 1800
        }
    ]
    
    for candle in candles_initial:
        print(f"  POST → {candle['symbol']} | {candle['datetime']}")
        try:
            response = requests.post(
                'http://127.0.0.1:8765/mt5/candle',
                json=candle,
                timeout=5
            )
            if response.status_code == 200:
                print(f"    ✅ OK (Close: {candle['close']})")
            else:
                print(f"    ❌ ERROR {response.status_code}")
        except Exception as e:
            print(f"    ❌ ERRO: {e}")
        time.sleep(0.5)
    
    print()
    print("═" * 73)
    print()
    print("✓ Iniciando monitoramento de NOVOS candles...")
    print("  (simulando próximos 3 candles a cada 15 minutos)")
    print()
    
    # DEPOIS: Monitorar novos candles (simular 3 candles novos)
    print("📋 FASE 2: Monitoramento - Novo Candle Detectado")
    print("─" * 73)
    print()
    
    for new_candle_idx in range(1, 4):
        time_new = base_time + timedelta(minutes=(45+new_candle_idx)*15)
        
        print(f"⏳ Novo candle M15 detectado em {time_new.isoformat()}...")
        print()
        
        # Enviar 3 moedas
        new_candles = [
            {
                "symbol": "XAUUSD",
                "datetime": time_new.isoformat(),
                "open": 4511.00 + (new_candle_idx * 0.5),
                "high": 4513.50 + (new_candle_idx * 0.5),
                "low": 4509.75 + (new_candle_idx * 0.5),
                "close": 4512.25 + (new_candle_idx * 0.5),
                "volume": 1600 + (new_candle_idx * 50)
            },
            {
                "symbol": "EURUSD",
                "datetime": time_new.isoformat(),
                "open": 1.0850 + (new_candle_idx * 0.0002),
                "high": 1.0854 + (new_candle_idx * 0.0002),
                "low": 1.0847 + (new_candle_idx * 0.0002),
                "close": 1.0853 + (new_candle_idx * 0.0002),
                "volume": 2600 + (new_candle_idx * 50)
            },
            {
                "symbol": "GBPUSD",
                "datetime": time_new.isoformat(),
                "open": 1.2650 + (new_candle_idx * 0.0002),
                "high": 1.2654 + (new_candle_idx * 0.0002),
                "low": 1.2647 + (new_candle_idx * 0.0002),
                "close": 1.2652 + (new_candle_idx * 0.0002),
                "volume": 1900 + (new_candle_idx * 50)
            }
        ]
        
        for candle in new_candles:
            print(f"  POST → {candle['symbol']} | {candle['datetime']}")
            try:
                response = requests.post(
                    'http://127.0.0.1:8765/mt5/candle',
                    json=candle,
                    timeout=5
                )
                if response.status_code == 200:
                    print(f"    ✅ OK (Close: {candle['close']})")
                else:
                    print(f"    ❌ ERROR {response.status_code}")
            except Exception as e:
                print(f"    ❌ ERRO: {e}")
            time.sleep(0.5)
        
        print()
        if new_candle_idx < 3:
            print("⏳ Aguardando próximo candle M15...")
            time.sleep(2)
            print()
    
    print("=" * 73)
    print()
    print("✅ TESTE COMPLETO!")
    print()
    print("Agora verifique nos logs:")
    print("  • /tmp/test_send.log (Servidor)")
    print("  • /tmp/test_monitor.log (Monitor)")
    print()
    print("Procure por:")
    print("  ✓ 'NOVO CANDLE' no servidor")
    print("  ✓ 'Conectado' no monitor")
    print("  ✓ 'XGBoost' no monitor")
    print()

if __name__ == '__main__':
    simulate_mt5_init()
