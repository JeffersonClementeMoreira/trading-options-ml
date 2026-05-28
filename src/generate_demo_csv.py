#!/usr/bin/env python3
"""
Criar CSV de TESTE com dados realistas para demonstração

IMPORTANTE: Este é apenas um CSV de teste para demonstração!
Para resultados REAIS, exporte dados do MT5 conforme instruções.

Gera dados realistas baseados em flutuações pequenas de preços reais.
"""

import csv
from datetime import datetime, timedelta
import numpy as np

def generate_demo_csv(symbol, filename, days=30):
    """Gerar CSV de teste com dados realistas"""
    
    # Preços iniciais reais aproximados
    initial_prices = {
        'EURUSD': 1.0850,
        'GBPUSD': 1.2750,
        'XAUUSD': 2350.00
    }
    
    current_price = initial_prices.get(symbol, 1.0000)
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
        
        # Gerar candles
        start_date = datetime.now() - timedelta(days=days)
        current_date = start_date
        
        while current_date <= datetime.now():
            # 96 candles por dia (24h * 60min / 15min)
            for hour in range(24):
                for minute in [0, 15, 30, 45]:
                    timestamp = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # Gerar OHLC realista
                    daily_change = np.random.normal(0, 0.0005)  # Pequeña fluctuación
                    open_price = current_price
                    close_price = current_price * (1 + daily_change)
                    high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.0002)))
                    low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.0002)))
                    volume = int(np.random.uniform(50000, 150000))
                    
                    writer.writerow([
                        timestamp.strftime('%Y.%m.%d'),
                        timestamp.strftime('%H:%M'),
                        f'{open_price:.5f}',
                        f'{high_price:.5f}',
                        f'{low_price:.5f}',
                        f'{close_price:.5f}',
                        volume
                    ])
                    
                    current_price = close_price
            
            current_date += timedelta(days=1)
    
    print(f"✅ CSV de TESTE criado: {filename}")
    print(f"   Símbolo: {symbol}")
    print(f"   Período: {days} dias")
    print(f"   Candles: {days * 96}")
    print(f"\n⚠️  IMPORTANTE: Este é apenas um CSV de TESTE!")
    print(f"   Para resultados REAIS, exporte dados do MT5:")
    print(f"   MT5 → History Center → {symbol} M15 → Export")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("📊 Gerando CSVs de TESTE para demonstração")
    print("="*80)
    
    symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
    
    for symbol in symbols:
        filename = f'/home/ubuntu/pessoal/options/data/{symbol}_M15.csv'
        generate_demo_csv(symbol, filename, days=30)
        print()
    
    print("="*80)
    print("✅ CSVs de teste criados em /home/ubuntu/pessoal/options/data/")
    print("\n⚠️  AVISO:")
    print("   Estes são dados de TESTE para demonstração!")
    print("   Para análise REAL, exporte dados do MT5.")
    print("="*80)
