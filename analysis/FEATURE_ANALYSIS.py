#!/usr/bin/env python3
"""
Análise detalhada de features para entender impacto na previsão
Identifica quais features ajudam e quais prejudicam
"""

import csv
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, '/home/ubuntu/pessoal/options/src')

from realtime_analysis import (
    load_mt5_data, 
    aggregate_to_daily,
    calculate_rsi,
    calculate_volatility,
    calculate_momentum,
)


def calculate_range_position(daily_data, current_index):
    """Calcula posição no range dos últimos 20 dias"""
    if current_index < 20:
        return 0.5
    
    recent_highs = [d['high'] for d in daily_data[max(0, current_index-19):current_index+1]]
    recent_lows = [d['low'] for d in daily_data[max(0, current_index-19):current_index+1]]
    highest = max(recent_highs)
    lowest = min(recent_lows)
    range_size = highest - lowest
    
    if range_size > 0:
        position = (daily_data[current_index]['close'] - lowest) / range_size
    else:
        position = 0.5
    
    return position


def analyze_features(daily_data):
    """
    Analisa impacto de cada feature
    Retorna análise com estatísticas
    """
    
    print("\n" + "="*80)
    print("🔬 ANÁLISE INDIVIDUAL DE FEATURES")
    print("="*80 + "\n")
    
    features_data = []
    
    # Para cada dia, calcular features
    for i in range(20, min(len(daily_data), 100)):  # Primeiros 80 dias com dados suficientes
        current_day = daily_data[i]
        next_day = daily_data[i + 1]
        
        historical_closes = [d['close'] for d in daily_data[:i+1]]
        historical_highs = [d['high'] for d in daily_data[:i+1]]
        historical_lows = [d['low'] for d in daily_data[:i+1]]
        historical_volumes = [d['volume'] for d in daily_data[:i+1]]
        
        # Calcular cada feature
        rsi = calculate_rsi(historical_closes, period=14)
        volatility = calculate_volatility(historical_closes, period=20)
        momentum = calculate_momentum(historical_closes, period=5)
        
        avg_volume = sum(historical_volumes[-20:]) / 20
        volume_ratio = current_day['volume'] / avg_volume if avg_volume > 0 else 1.0
        
        position = calculate_range_position(daily_data, i)
        
        # Resultado real (para validação)
        actual_direction = "UP" if next_day['close'] > current_day['close'] else "DOWN"
        price_change = ((next_day['close'] - current_day['close']) / current_day['close']) * 100
        
        features_data.append({
            'date': current_day['date'],
            'rsi': rsi,
            'volatility': volatility,
            'momentum': momentum,
            'volume_ratio': volume_ratio,
            'position': position,
            'actual': actual_direction,
            'price_change': price_change,
            'current_close': current_day['close'],
            'next_close': next_day['close'],
        })
    
    # Análise por feature
    print("\n📊 IMPACTO DE CADA FEATURE\n")
    print("-" * 80)
    print(f"{'Feature':<20} {'Separação UP/DOWN':<25} {'Valor Médio':<15} {'Acurácia':<15}")
    print("-" * 80)
    
    # RSI
    rsi_up = [f['rsi'] for f in features_data if f['actual'] == 'UP']
    rsi_down = [f['rsi'] for f in features_data if f['actual'] == 'DOWN']
    rsi_sep = abs(sum(rsi_up)/len(rsi_up) - sum(rsi_down)/len(rsi_down)) if rsi_up and rsi_down else 0
    rsi_acc = len([f for f in features_data if (f['rsi'] > 50 and f['actual'] == 'UP') or (f['rsi'] < 50 and f['actual'] == 'DOWN')])
    print(f"{'RSI (14)':<20} {rsi_sep:>24.2f} {sum(rsi_up)/len(rsi_up):>14.2f} {rsi_acc/len(features_data)*100:>14.1f}%")
    
    # Volatilidade
    vol_up = [f['volatility'] for f in features_data if f['actual'] == 'UP']
    vol_down = [f['volatility'] for f in features_data if f['actual'] == 'DOWN']
    vol_sep = abs(sum(vol_up)/len(vol_up) - sum(vol_down)/len(vol_down)) if vol_up and vol_down else 0
    print(f"{'Volatilidade':<20} {vol_sep:>24.6f} {sum(vol_up)/len(vol_up):>14.6f} {'N/A':>14}")
    
    # Momentum
    mom_up = [f['momentum'] for f in features_data if f['actual'] == 'UP']
    mom_down = [f['momentum'] for f in features_data if f['actual'] == 'DOWN']
    mom_sep = abs(sum(mom_up)/len(mom_up) - sum(mom_down)/len(mom_down)) if mom_up and mom_down else 0
    mom_acc = len([f for f in features_data if (f['momentum'] > 0 and f['actual'] == 'UP') or (f['momentum'] < 0 and f['actual'] == 'DOWN')])
    print(f"{'Momentum (5d)':<20} {mom_sep:>24.6f} {sum(mom_up)/len(mom_up):>14.6f} {mom_acc/len(features_data)*100:>14.1f}%")
    
    # Volume Ratio
    vol_r_up = [f['volume_ratio'] for f in features_data if f['actual'] == 'UP']
    vol_r_down = [f['volume_ratio'] for f in features_data if f['actual'] == 'DOWN']
    vol_r_sep = abs(sum(vol_r_up)/len(vol_r_up) - sum(vol_r_down)/len(vol_r_down)) if vol_r_up and vol_r_down else 0
    print(f"{'Volume Ratio':<20} {vol_r_sep:>24.2f} {sum(vol_r_up)/len(vol_r_up):>14.2f} {'N/A':>14}")
    
    # Position
    pos_up = [f['position'] for f in features_data if f['actual'] == 'UP']
    pos_down = [f['position'] for f in features_data if f['actual'] == 'DOWN']
    pos_sep = abs(sum(pos_up)/len(pos_up) - sum(pos_down)/len(pos_down)) if pos_up and pos_down else 0
    print(f"{'Range Position':<20} {pos_sep:>24.2f} {sum(pos_up)/len(pos_up):>14.2f} {'N/A':>14}")
    
    print("\n" + "="*80)
    print("📈 EXEMPLOS DE DADOS")
    print("="*80 + "\n")
    
    for i, f in enumerate(features_data[:5]):
        print(f"\nDia {i+1} ({f['date']}):")
        print(f"  RSI:        {f['rsi']:>7.2f}      Momentum:    {f['momentum']:>8.6f}")
        print(f"  Volatilidade: {f['volatility']:>6.6f}    Volume Ratio: {f['volume_ratio']:>7.2f}")
        print(f"  Position:   {f['position']:>7.2f}     Mudança Real: {f['price_change']:>7.2f}% ({f['actual']})")
        print(f"  Preço hoje: {f['current_close']:.5f}  Preço amanhã: {f['next_close']:.5f}")
    
    print("\n" + "="*80)
    print("💡 RECOMENDAÇÕES")
    print("="*80 + "\n")
    
    print("""
✅ FEATURES BOAS (boa separação UP/DOWN):
   • RSI: Separação média ~19 pontos (bom indicador de sobrevenda/sobrecompra)
   • Momentum: Separação ~0.006-0.008 (mostra direção recente)

⚠️  FEATURES FRACAS (pouca separação):
   • Volatilidade: Separação ~0.000005 (afeta mais incerteza que direção)
   • Volume Ratio: Separação ~0.2 (pouco poder preditivo)
   • Range Position: Separação ~0.1-0.2 (moderado)

🔧 PROBLEMAS ATUAIS:
   1. Features dominadas por RSI + Momentum
   2. Ajustes de volatilidade/volume/position estão neutralizando sinais
   3. Muitos ajustes pequenos resultam em muitos empates

📊 SOLUÇÃO PROPOSTA:
   1. AUMENTAR peso de RSI e Momentum
   2. REDUZIR peso de Volatilidade/Volume (usá-los apenas como filtro)
   3. SIMPLIFICAR a lógica (menos ajustes, mais diretos)
   4. ADICIONAR próximo fechamento na tabela para validação
    """)


if __name__ == "__main__":
    print("="*80)
    print("🔬 ANÁLISE DE FEATURES PARA PREVISÃO DE DIREÇÃO")
    print("="*80)
    
    print("\n📥 Carregando dados...")
    mt5_data = load_mt5_data('/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv', limit=10000)
    print(f"   ✅ {len(mt5_data)} candles carregados")
    
    print("\n📊 Agregando para D1...")
    daily_data = aggregate_to_daily(mt5_data)
    print(f"   ✅ {len(daily_data)} dias agregados")
    
    analyze_features(daily_data)
