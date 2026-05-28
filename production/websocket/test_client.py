#!/usr/bin/env python3
"""
Test WebSocket + Telegram Alert System
======================================

Simula candles do MT5 para testar o sistema de alertas.
"""

import asyncio
import json
import websockets
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_websocket_alerts():
    """Test the WebSocket server with simulated MT5 candles."""
    
    # Test candles
    test_candles = [
        {
            'timestamp': '2025-09-03T06:00:00',
            'pair': 'EURUSD',
            'open': 1.16700,
            'high': 1.16750,
            'low': 1.16650,
            'close': 1.16733,
            'volume': 1000
        },
        {
            'timestamp': '2025-09-03T10:15:00',
            'pair': 'GBPUSD',
            'open': 1.33980,
            'high': 1.33990,
            'low': 1.33975,
            'close': 1.33981,
            'volume': 800
        },
        {
            'timestamp': '2025-09-04T00:45:00',
            'pair': 'EURUSD',
            'open': 1.16610,
            'high': 1.16650,
            'low': 1.16600,
            'close': 1.16618,
            'volume': 900
        },
    ]
    
    print("=" * 80)
    print("📊 WebSocket + Telegram Alert System Test")
    print("=" * 80)
    print("\n📝 Test Configuration:")
    print("   Server: ws://localhost:8765")
    print("   Test candles: 3 samples")
    print("   Expected: 3 Telegram alerts (1 per signal)")
    
    try:
        # Connect to WebSocket server
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("\n✅ Connected to WebSocket server")
            
            for i, candle in enumerate(test_candles):
                print(f"\n📤 Test {i+1}: Sending {candle['pair']} candle...")
                
                # Send candle
                await websocket.send(json.dumps(candle))
                
                # Get response
                response = await websocket.recv()
                response_data = json.loads(response)
                
                print(f"📩 Response:")
                print(f"   Status: {response_data.get('status')}")
                print(f"   Signal Found: {response_data.get('signal_found')}")
                
                if response_data.get('signal_found'):
                    signal = response_data.get('signal', {})
                    print(f"   ✅ SIGNAL TRIGGERED!")
                    print(f"      Pair: {signal.get('pair')}")
                    print(f"      Direction: {signal.get('direction')}")
                    print(f"      Confidence: {signal.get('confidence')}%")
                    print(f"      Entry: {signal.get('entry_price'):.5f}")
                    print(f"      Target: {signal.get('target_price'):.5f}")
                    print(f"      📲 Telegram alert sent!")
                
                # Wait before next
                await asyncio.sleep(1)
        
        print("\n" + "=" * 80)
        print("✅ Test completed successfully!")
        print("=" * 80)
        
    except ConnectionRefusedError:
        print("\n❌ ERROR: Could not connect to WebSocket server")
        print("   Make sure to start the server first:")
        print("   python3 production/websocket/server.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")


async def test_signal_check():
    """Test checking if signals exist."""
    print("\n" + "=" * 80)
    print("📊 Checking loaded signals...")
    print("=" * 80)
    
    import pandas as pd
    from pathlib import Path
    
    signals_dir = Path('production')
    
    for pair in ['EURUSD', 'GBPUSD']:
        csv_file = signals_dir / f'daily_signals_{pair}.csv'
        
        if csv_file.exists():
            df = pd.read_csv(csv_file)
            print(f"\n✅ {pair}:")
            print(f"   Total signals: {len(df)}")
            print(f"   First signal: {df.iloc[0]['Date']} {df.iloc[0]['Time']}")
            print(f"   Last signal: {df.iloc[-1]['Date']} {df.iloc[-1]['Time']}")
            print(f"   Sample (first 3):")
            for i, row in df.head(3).iterrows():
                print(f"      {row['Date']} {row['Time']} → Entry: {row['EntryPrice']:.5f}, Target: {row['TargetPrice']:.5f}, Conf: {row['Confidence%']:.0f}%")
        else:
            print(f"\n❌ {pair}: No signal file found")


if __name__ == '__main__':
    print("\n🚀 WebSocket + Telegram Alert System - Test Suite\n")
    
    # First, check signals
    asyncio.run(test_signal_check())
    
    # Then test WebSocket
    print("\n\n📡 Testing WebSocket connection...")
    print("(Make sure server is running: python3 production/websocket/server.py)\n")
    
    asyncio.run(test_websocket_alerts())
