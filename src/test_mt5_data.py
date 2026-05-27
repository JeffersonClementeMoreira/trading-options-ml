#!/usr/bin/env python3
"""
Quick test script to validate MT5 data flow
Allows you to test server responses immediately without waiting 15 minutes
"""

import requests
import json
import sys
from datetime import datetime, timedelta

SERVER_URL = "http://127.0.0.1:8765/mt5/candle"

def send_candle(symbol, dt_str, open_price, high, low, close, volume):
    """Send a candle to the server"""
    data = {
        "symbol": symbol,
        "datetime": dt_str,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume
    }
    
    try:
        response = requests.post(SERVER_URL, json=data, timeout=5)
        
        print(f"\n{'='*80}")
        print(f"[SENT] {symbol} @ {close}")
        print(f"{'='*80}")
        print(f"Symbol:    {symbol}")
        print(f"DateTime:  {dt_str}")
        print(f"OHLC:      {open_price} / {high} / {low} / {close}")
        print(f"Volume:    {volume}")
        print(f"{'='*80}")
        
        if response.status_code == 200:
            print(f"[OK] Server response: {response.text}")
            return True
        else:
            print(f"[ERROR] Server returned: {response.status_code}")
            print(f"[ERROR] Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to server at {SERVER_URL}")
        print(f"[ERROR] Make sure the system is running:")
        print(f"        bash /home/ubuntu/pessoal/options/bin/start_system.sh")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_eurusd_real():
    """Test with REAL EURUSD data (~1.16)"""
    print("\n" + "="*80)
    print("TEST: EURUSD REAL DATA (should be ~1.16)")
    print("="*80)
    
    now = datetime.now()
    dt_str = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Real EURUSD prices (approximately 1.16)
    return send_candle(
        symbol="EURUSD",
        dt_str=dt_str,
        open_price=1.1598,
        high=1.1602,
        low=1.1595,
        close=1.1599,
        volume=5000
    )


def test_xauusd_real():
    """Test with REAL XAUUSD data (~2500)"""
    print("\n" + "="*80)
    print("TEST: XAUUSD REAL DATA (should be ~2500)")
    print("="*80)
    
    now = datetime.now()
    dt_str = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Real XAUUSD prices (approximately 2500)
    return send_candle(
        symbol="XAUUSD",
        dt_str=dt_str,
        open_price=2498.50,
        high=2501.20,
        low=2497.80,
        close=2500.15,
        volume=3000
    )


def test_gbpusd_real():
    """Test with REAL GBPUSD data (~1.27)"""
    print("\n" + "="*80)
    print("TEST: GBPUSD REAL DATA (should be ~1.27)")
    print("="*80)
    
    now = datetime.now()
    dt_str = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Real GBPUSD prices (approximately 1.27)
    return send_candle(
        symbol="GBPUSD",
        dt_str=dt_str,
        open_price=1.2698,
        high=1.2702,
        low=1.2695,
        close=1.2700,
        volume=4000
    )


def test_custom():
    """Test with custom data entered by user"""
    print("\n" + "="*80)
    print("CUSTOM TEST - Enter data manually")
    print("="*80)
    
    symbol = input("Symbol (EURUSD/XAUUSD/GBPUSD): ").strip().upper()
    
    try:
        open_price = float(input(f"Open price: "))
        high = float(input(f"High price: "))
        low = float(input(f"Low price: "))
        close = float(input(f"Close price: "))
        volume = int(input(f"Volume: "))
        
        now = datetime.now()
        dt_str = now.strftime("%Y-%m-%dT%H:%M:%S")
        
        return send_candle(symbol, dt_str, open_price, high, low, close, volume)
        
    except ValueError:
        print("[ERROR] Invalid input. Please enter numbers.")
        return False


def main():
    print("\n" + "="*80)
    print("MT5 DATA TEST - Validate server and data")
    print("="*80)
    print("\nOptions:")
    print("  1 = Test EURUSD (real data ~1.16)")
    print("  2 = Test XAUUSD (real data ~2500)")
    print("  3 = Test GBPUSD (real data ~1.27)")
    print("  4 = Custom test (enter your data)")
    print("  q = Quit")
    print("\n" + "="*80 + "\n")
    
    while True:
        choice = input("Choose option (1-4, q=quit): ").strip().lower()
        
        if choice == 'q':
            print("\n[OK] Goodbye!")
            break
        elif choice == '1':
            test_eurusd_real()
        elif choice == '2':
            test_xauusd_real()
        elif choice == '3':
            test_gbpusd_real()
        elif choice == '4':
            test_custom()
        else:
            print("[ERROR] Invalid option. Try again.")


if __name__ == "__main__":
    main()
