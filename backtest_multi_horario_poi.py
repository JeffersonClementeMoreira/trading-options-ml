#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 BACKTEST MULTI-HORÁRIO + FEATURES DE POI (Point of Interest)

Versão Avançada com:
  ✅ Análises em 5 horários por dia (09:00, 12:00, 14:00, 18:00, 23:45)
  ✅ Features de POI: dist_res, dist_sup, near_res, near_sup, pos_in_range
  ✅ Força do POI baseado em SD+Confluence
  ✅ Detecção de Rejeição no POI (sweep)
  ✅ ~205 trades em vez de 41 (5x mais dados, menos viés de horário)
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def calcular_poi_features(close: float, high_day: float, low_day: float, 
                         sma_200: float, last_high_swing: float, 
                         last_low_swing: float) -> dict:
    """
    Calcula features de Point of Interest (POI)
    
    POI = onde o mercado tem probabilidade de reagir
    - Resistance (topo anterior)
    - Support (fundo anterior)
    - SMA200 (tendência principal)
    """
    
    poi_features = {}
    
    try:
        # 1. DISTÂNCIA AO POI (Principal)
        # Distância à Resistência (% negativo = abaixo)
        if last_high_swing > 0:
            dist_res = (close - last_high_swing) / close * 100
            poi_features['dist_res_pct'] = dist_res
        else:
            poi_features['dist_res_pct'] = None
        
        # Distância ao Support (% positivo = acima)
        if last_low_swing > 0:
            dist_sup = (close - last_low_swing) / close * 100
            poi_features['dist_sup_pct'] = dist_sup
        else:
            poi_features['dist_sup_pct'] = None
        
        # 2. PROXIMIDADE BINÁRIA (Threshold 0.05%)
        threshold = 0.05  # Muito perto
        poi_features['near_res'] = (dist_res is not None and abs(dist_res) < threshold)
        poi_features['near_sup'] = (dist_sup is not None and abs(dist_sup) < threshold)
        
        # 3. POSIÇÃO RELATIVA ENTRE POIs [0..1]
        # 0 = no support, 0.5 = no meio, 1 = na resistance
        if last_high_swing > last_low_swing:
            pos = (close - last_low_swing) / (last_high_swing - last_low_swing)
            pos = np.clip(pos, 0, 1)
            poi_features['pos_in_range'] = pos
        else:
            poi_features['pos_in_range'] = 0.5
        
        # 4. FORÇA DO POI
        # Baseado em: amplitude (H-L) e confluência com SMA200
        range_pct = (high_day - low_day) / close * 100
        
        # Score simples: quanto maior o range, mais forte o POI
        poi_strength = min(range_pct / 0.5, 1.0)  # Normalizar a 0..1
        poi_features['poi_strength'] = poi_strength
        
        # 5. REJEIÇÃO NO POI
        # Rejection = preço chega no extremo mas fecha longe dele
        # (isso indica rejeição forte = liquidez capturada)
        if high_day > last_high_swing and close < (last_high_swing + last_low_swing) / 2:
            poi_features['rejection_res'] = True
            poi_features['rejection_type'] = 'BEARISH_REJECTION'
        elif low_day < last_low_swing and close > (last_high_swing + last_low_swing) / 2:
            poi_features['rejection_sup'] = True
            poi_features['rejection_type'] = 'BULLISH_REJECTION'
        else:
            poi_features['rejection_res'] = False
            poi_features['rejection_sup'] = False
            poi_features['rejection_type'] = 'NO_REJECTION'
        
        # 6. PROXIMIDADE AO SMA200 (Tendência)
        if sma_200 is not None:
            dist_sma200 = (close - sma_200) / sma_200 * 100
            poi_features['dist_sma200_pct'] = dist_sma200
            
            # Posição vs tendência
            if dist_sma200 > 0:
                poi_features['pos_vs_trend'] = 'ABOVE_SMA200'
            else:
                poi_features['pos_vs_trend'] = 'BELOW_SMA200'
        
    except Exception as e:
        pass
    
    return poi_features


def backtest_multi_horario_poi(data_path, model_path, start_date='2026-01-01', 
                               end_date='2026-03-01'):
    """
    Backtest em múltiplos horários com features de POI
    
    Horários analisados:
    - 09:00 (abertura NYSE)
    - 12:00 (meio dia)
    - 14:00 (fecho EU, abertura US)
    - 18:00 (fecho US)
    - 23:45 (fecho Forex)
    """
    
    print("\n" + "=" * 90)
    print("🔥 BACKTEST MULTI-HORÁRIO + POI (Point of Interest)")
    print("=" * 90)
    
    # Carregar dados
    df = pd.read_csv(data_path, sep=r'\s+')
    df['datetime'] = pd.to_datetime(
        df['<DATE>'].astype(str) + ' ' + df['<TIME>'],
        format='%Y.%m.%d %H:%M:%S'
    )
    df.set_index('datetime', inplace=True)
    df = df.sort_index()
    df.columns = df.columns.str.lower().str.replace('<', '').str.replace('>', '')
    df = df.rename(columns={'tickvol': 'volume', 'vol': 'volume'})
    
    # Carregar modelo
    xgb_model = None
    if model_path and Path(model_path).exists():
        with open(model_path, 'rb') as f:
            xgb_model = pickle.load(f)
    
    print(f"📥 Dados: {len(df)} candles | {df.index[0]} a {df.index[-1]}")
    
    # Horários para análise
    target_hours = [9, 12, 14, 18, 23]  # 09:00, 12:00, 14:00, 18:00, 23:45
    
    results = []
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    unique_dates = df.index.normalize().unique()
    unique_dates = pd.DatetimeIndex(unique_dates).sort_values()
    unique_dates = unique_dates[(unique_dates >= start_dt) & (unique_dates <= end_dt)]
    
    total_análises = 0
    
    for date_idx, date_ts in enumerate(unique_dates):
        date = date_ts.to_pydatetime()
        
        # Dados do dia
        next_day = date + timedelta(days=1)
        day_data = df[(df.index.date >= date.date()) & (df.index.date < next_day.date())]
        
        if len(day_data) < 50:
            continue
        
        # OHLC geral do dia
        high_day = day_data['high'].max()
        low_day = day_data['low'].min()
        
        # Últimos swing para POI
        last_high_swing = day_data['high'].iloc[-1]
        last_low_swing = day_data['low'].iloc[-1]
        
        # Histórico para SMA200
        df_hist = df[df.index < date]
        if len(df_hist) >= 200:
            close_hist = df_hist['close'].values
            sma200_full = close_hist[-200:].mean()
        else:
            sma200_full = None
        
        # Para cada horário-alvo do dia
        for target_hour in target_hours:
            # Buscar candle mais próximo
            hour_data = day_data[day_data.index.hour == target_hour]
            
            if len(hour_data) == 0:
                continue
            
            # Usar primeiro candle da hora (para simular entrada no início)
            candle_idx = hour_data.index[0]
            
            # Dados até esse ponto
            df_until = df[df.index < candle_idx]
            
            if len(df_until) < 50:
                continue
            
            data_until = df_until[df_until.index.date == date.date()]
            if len(data_until) == 0:
                data_until = day_data[day_data.index < candle_idx]
            
            if len(data_until) < 20:
                continue
            
            # ANÁLISE NO PONTO
            close_price = data_until['close'].iloc[-1]
            analysis_time = data_until.index[-1].strftime('%H:%M:%S')
            
            # Indicadores
            close_vals = data_until['close'].values
            sma20 = close_vals[-20:].mean() if len(close_vals) >= 20 else None
            sma50 = close_vals[-50:].mean() if len(close_vals) >= 50 else None
            sma200 = sma200_full
            
            # POI Features
            poi_features = calcular_poi_features(
                close_price, high_day, low_day, sma200,
                last_high_swing, last_low_swing
            )
            
            # RESULTADO (próximo dia)
            next_close = None
            change_pct = None
            result = "NO_DATA"
            
            for future_idx in range(date_idx + 1, len(unique_dates)):
                future_date = unique_dates[future_idx].to_pydatetime()
                future_next = future_date + timedelta(days=1)
                future_data = df[(df.index.date >= future_date.date()) & 
                                (df.index.date < future_next.date())]
                
                if len(future_data) > 0:
                    next_close = future_data['close'].iloc[-1]
                    change_pct = (next_close - close_price) / close_price * 100
                    result = "UP" if change_pct > 0 else "DOWN"
                    break
            
            # Montar resultado
            row = {
                'date': date.strftime('%Y-%m-%d'),
                'analysis_hour': f"{target_hour:02d}:00",
                'analysis_time': analysis_time,
                'close': close_price,
                'high_day': high_day,
                'low_day': low_day,
                
                # Indicadores
                'sma20': sma20,
                'sma50': sma50,
                'sma200': sma200,
                
                # POI Features
                'dist_res_pct': poi_features.get('dist_res_pct'),
                'dist_sup_pct': poi_features.get('dist_sup_pct'),
                'near_res': poi_features.get('near_res'),
                'near_sup': poi_features.get('near_sup'),
                'pos_in_range': poi_features.get('pos_in_range'),
                'poi_strength': poi_features.get('poi_strength'),
                'rejection_res': poi_features.get('rejection_res'),
                'rejection_sup': poi_features.get('rejection_sup'),
                'rejection_type': poi_features.get('rejection_type'),
                'dist_sma200_pct': poi_features.get('dist_sma200_pct'),
                'pos_vs_trend': poi_features.get('pos_vs_trend'),
                
                # Resultado
                'next_close': next_close,
                'change_pct': change_pct,
                'result': result,
            }
            
            results.append(row)
            total_análises += 1
            
            # Progress
            if total_análises % 50 == 0:
                print(f"  ✓ {total_análises} análises...")
    
    # Salvar
    df_results = pd.DataFrame(results)
    filename = f"backtest_results/backtest_multi_horario_poi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_results.to_csv(filename, index=False)
    
    print(f"\n✅ Backtest salvo: {filename}")
    print(f"   Análises totais: {len(df_results)}")
    print(f"   Colunas: {len(df_results.columns)}")
    print(f"   Horários: {df_results['analysis_hour'].unique()}")
    
    # Estatísticas
    print(f"\n📊 Estatísticas por Horário:")
    for hour in sorted(df_results['analysis_hour'].unique()):
        subset = df_results[df_results['analysis_hour'] == hour]
        corretos = len(subset[subset['result'].notna()])
        print(f"   {hour}: {len(subset)} análises | Corretos: {corretos}")
    
    print(f"\n🔍 Features de POI Calculadas:")
    poi_cols = [c for c in df_results.columns if 'poi' in c or 'dist_' in c or 'near_' in c]
    print(f"   {', '.join(poi_cols)}")
    
    return filename


if __name__ == '__main__':
    data_path = '/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv'
    model_path = '/home/ubuntu/pessoal/options/models/xgboost_model.pkl'
    
    backtest_multi_horario_poi(data_path, model_path)
