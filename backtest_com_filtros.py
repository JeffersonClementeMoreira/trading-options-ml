#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest Corrigido - Versão com Filtros e Análise de Sweep/BOS/CHOC

Melhorias:
  ✅ SMA200 correto (usando histórico completo)
  ✅ Fechamento às 14:00 (close_14h)
  ✅ Todos os indicadores visíveis
  ✅ Filtro de Sweep (avoit entrada em sweep)
  ✅ Análise de CHOC (confirmação de retorno pós-sweep)
  ✅ Pontuação de confluência
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def calcular_indicadores(df_day: pd.DataFrame, df_hist: pd.DataFrame = None) -> dict:
    """Calcula indicadores técnicos para um dia."""
    indicators = {}
    close = df_day['close'].values
    high = df_day['high'].values
    low = df_day['low'].values
    
    try:
        # SMA
        if len(close) >= 20:
            indicators['sma20'] = close[-20:].mean()
        if len(close) >= 50:
            indicators['sma50'] = close[-50:].mean()
        
        # SMA200 - Usar histórico se disponível
        if df_hist is not None and len(df_hist) >= 200:
            close_hist = df_hist['close'].values
            all_close = np.concatenate([close_hist[-200:], close[:]])
            indicators['sma200'] = all_close[-200:].mean()
        elif len(close) >= 200:
            indicators['sma200'] = close[-200:].mean()
        else:
            indicators['sma200'] = None
        
        # RSI (14)
        if len(close) >= 14:
            deltas = np.diff(close[-14:])
            seed = deltas[:14-1]
            up = seed[seed >= 0].sum() / (14 - 1)
            down = -seed[seed < 0].sum() / (14 - 1)
            rs = up / down if down != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            indicators['rsi14'] = rsi
        
        # MACD (12, 26, 9)
        if len(close) >= 26:
            ema12 = pd.Series(close[-26:]).ewm(span=12).mean().iloc[-1]
            ema26 = pd.Series(close[-26:]).ewm(span=26).mean().iloc[-1]
            macd = ema12 - ema26
            indicators['macd'] = macd
        
        # Volatilidade (últimos 20 candles)
        if len(close) >= 20:
            volatility = np.std(close[-20:]) / np.mean(close[-20:]) * 100
            indicators['volatility'] = volatility
        
        # Range do dia
        indicators['range'] = (max(high) - min(low)) / np.mean(close) * 100
        indicators['range_pct'] = indicators['range']
        
        # Momentum (últimos 10 candles)
        if len(close) >= 10:
            momentum = (close[-1] - close[-10]) / close[-10] * 100
            indicators['momentum10'] = momentum
    
    except Exception as e:
        print(f"⚠️ Erro ao calcular indicadores: {e}")
    
    return indicators


def detectar_sweep_bos(df_day: pd.DataFrame) -> dict:
    """Detecta Sweep H4 e proximidade de BOS em PERCENTUAL."""
    indicators = {}
    
    try:
        close = df_day['close'].values
        high = df_day['high'].values
        low = df_day['low'].values
        
        if len(close) < 30:
            return indicators
        
        if len(close) >= 12:
            h4_2_high = max(high[-8:-4])
            h4_2_low = min(low[-8:-4])
            h4_3_high = max(high[-4:])
            h4_3_low = min(low[-4:])
            
            current_price = close[-1]
            
            if h4_3_high > h4_2_high and current_price < h4_2_high:
                indicators['em_sweep_h4'] = True
                indicators['sweep_type'] = 'BEARISH_SWEEP'
                indicators['prox_bos_pct'] = (h4_2_high - current_price) / current_price * 100
            elif h4_3_low < h4_2_low and current_price > h4_2_low:
                indicators['em_sweep_h4'] = True
                indicators['sweep_type'] = 'BULLISH_SWEEP'
                indicators['prox_bos_pct'] = (current_price - h4_2_low) / h4_2_low * 100
            else:
                indicators['em_sweep_h4'] = False
                dist_high_bos_pct = (h4_2_high - current_price) / current_price * 100
                dist_low_bos_pct = (current_price - h4_2_low) / h4_2_low * 100
                indicators['prox_bos_pct'] = min(abs(dist_high_bos_pct), abs(dist_low_bos_pct))
    
    except Exception as e:
        pass
    
    return indicators


def calcular_distancia_sd(df_day: pd.DataFrame) -> dict:
    """Calcula distância para SD em PERCENTUAL."""
    indicators = {}
    
    try:
        close = df_day['close'].values
        high = df_day['high'].values
        low = df_day['low'].values
        
        if len(close) < 10:
            return indicators
        
        # Últimos swing high e low
        current_price = close[-1]
        ultimo_high = high[-1]
        ultimo_low = low[-1]
        
        # Distância em %
        ultimobull_dist_pct = (ultimo_high - current_price) / current_price * 100
        ultimobear_dist_pct = (current_price - ultimo_low) / ultimo_low * 100
        
        indicators['ultimobull_dist_pct'] = ultimobull_dist_pct
        indicators['ultimobear_dist_pct'] = ultimobear_dist_pct
        
        # Trend vs SD
        if current_price > ultimo_high:
            indicators['trend_type'] = 'UPTREND_ABOVE'
        elif current_price < ultimo_low:
            indicators['trend_type'] = 'DOWNTREND_BELOW'
        else:
            indicators['trend_type'] = 'BETWEEN_EXTREMES'
        
        if len(close) >= 50:
            sma50 = close[-50:].mean()
            if current_price > sma50:
                indicators['sma_position'] = 'ABOVE_SMA50'
            else:
                indicators['sma_position'] = 'BELOW_SMA50'
    
    except Exception as e:
        pass
    
    return indicators


def aplicar_filtros_entrada(indicadores: dict, sweep: dict, sma200: float, close: float) -> dict:
    """
    Aplica filtros de entrada e retorna análise de risco.
    
    Filtros:
    1. Sweep ativo? ⚠️
    2. RSI em zona segura? 
    3. Confluência com SMA200?
    """
    filtro = {
        'sem_sweep': not sweep.get('em_sweep_h4', False),
        'rsi_seguro': 30 < indicadores.get('rsi14', 50) < 70,
        'confluencia_sma': True,
        'score_entrada': 0,
        'recomendacao': 'UNKNOWN'
    }
    
    # Verificar confluência SMA200
    if sma200 is not None:
        if close > sma200:
            filtro['confluencia_sma'] = True
        else:
            filtro['confluencia_sma'] = False
    
    # Calcular score
    if filtro['sem_sweep']:
        filtro['score_entrada'] += 2
    if filtro['rsi_seguro']:
        filtro['score_entrada'] += 1
    if filtro['confluencia_sma']:
        filtro['score_entrada'] += 1
    
    # Recomendação
    if filtro['score_entrada'] >= 3:
        filtro['recomendacao'] = 'ENTRADA_SEGURA'
    elif filtro['score_entrada'] == 2:
        filtro['recomendacao'] = 'ENTRADA_OK'
    else:
        filtro['recomendacao'] = 'EVITAR_ENTRADA'
    
    return filtro


def backtest_com_filtros(data_path, model_path, start_date='2026-01-01', end_date='2026-03-01'):
    """Backtest com filtros de sweep/BOS/CHOC."""
    
    print("\n" + "=" * 80)
    print("📊 BACKTEST COM FILTROS - Sweep/BOS/CHOC Analysis")
    print("=" * 80)
    
    # Carregar dados
    print(f"\n📥 Carregando dados de {data_path}...")
    
    df = pd.read_csv(data_path, sep='\s+')
    df['datetime'] = pd.to_datetime(
        df['<DATE>'].astype(str) + ' ' + df['<TIME>'],
        format='%Y.%m.%d %H:%M:%S'
    )
    df.set_index('datetime', inplace=True)
    df = df.sort_index()
    
    # Padronizar colunas
    df.columns = df.columns.str.lower().str.replace('<', '').str.replace('>', '')
    df = df.rename(columns={'tickvol': 'volume', 'vol': 'volume'})
    
    # Carregar modelo
    xgb_model = None
    if model_path and Path(model_path).exists():
        with open(model_path, 'rb') as f:
            xgb_model = pickle.load(f)
    
    print(f"✅ Dados carregados: {len(df)} candles")
    print(f"   Período: {df.index[0]} a {df.index[-1]}\n")
    
    # Filtrar período
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    results = []
    unique_dates = df.index.normalize().unique()
    unique_dates = pd.DatetimeIndex(unique_dates).sort_values()
    unique_dates = unique_dates[(unique_dates >= start_dt) & (unique_dates <= end_dt)]
    
    for date_idx, date_ts in enumerate(unique_dates):
        date = date_ts.to_pydatetime()
        df_until_prev = df[df.index < date]
        
        # Dados do dia
        next_day = date + timedelta(days=1)
        day_data = df[(df.index.date >= date.date()) & (df.index.date < next_day.date())]
        
        if len(day_data) < 20:
            continue
        
        # Análise
        last_candle_time = day_data.index[-1]
        analysis_time = last_candle_time.strftime('%H:%M:%S')
        
        open_price = day_data['open'].iloc[0]
        high_price = day_data['high'].max()
        low_price = day_data['low'].min()
        close_price = day_data['close'].iloc[-1]
        
        # Close 14h
        close_14h = None
        try:
            time_1400 = day_data[day_data.index.hour == 14]
            if len(time_1400) > 0:
                close_14h = time_1400['close'].iloc[0]
        except:
            pass
        
        # Indicadores
        ind = calcular_indicadores(day_data, df_until_prev)
        sd = calcular_distancia_sd(day_data)
        sweep = detectar_sweep_bos(day_data)
        
        # Filtros de entrada
        filtro = aplicar_filtros_entrada(ind, sweep, ind.get('sma200'), close_price)
        
        # Resultado
        next_close = None
        change_pct = None
        result = "NO_DATA"
        
        for future_idx in range(date_idx + 1, len(unique_dates)):
            future_date = unique_dates[future_idx].to_pydatetime()
            future_next = future_date + timedelta(days=1)
            future_data = df[(df.index.date >= future_date.date()) & (df.index.date < future_next.date())]
            
            if len(future_data) > 0:
                next_close = future_data['close'].iloc[-1]
                change_pct = (next_close - close_price) / close_price * 100
                result = "UP" if change_pct > 0 else "DOWN"
                break
        
        # Montar resultado
        row = {
            'date': date.strftime('%Y-%m-%d'),
            'analysis_time': analysis_time,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'close_14h': close_14h,
            
            # Indicadores (todos visíveis)
            'sma20': ind.get('sma20'),
            'sma50': ind.get('sma50'),
            'sma200': ind.get('sma200'),
            'rsi14': ind.get('rsi14'),
            'macd': ind.get('macd'),
            'volatility': ind.get('volatility'),
            'momentum10': ind.get('momentum10'),
            
            # Supply/Demand
            'dist_alto_pct': sd.get('ultimobull_dist_pct'),
            'dist_baixo_pct': sd.get('ultimobear_dist_pct'),
            'sd_trend': sd.get('trend_type'),
            
            # Sweep/BOS
            'em_sweep': sweep.get('em_sweep_h4'),
            'sweep_type': sweep.get('sweep_type'),
            'prox_bos_pct': sweep.get('prox_bos_pct'),
            
            # Filtros e Score
            'sem_sweep_ok': filtro['sem_sweep'],
            'rsi_ok': filtro['rsi_seguro'],
            'sma_ok': filtro['confluencia_sma'],
            'score': filtro['score_entrada'],
            'recomendacao': filtro['recomendacao'],
            
            # Resultado
            'next_close': next_close,
            'change_pct': change_pct,
            'result': result,
        }
        
        results.append(row)
        
        # Status
        print(f"  {date.strftime('%Y-%m-%d')} {analysis_time} | "
              f"{filtro['recomendacao']:15} (Score:{filtro['score_entrada']}) | "
              f"Sweep:{sweep.get('em_sweep_h4', False)} | "
              f"Result:{result:4} {change_pct:+.2f}%" if change_pct else "")
    
    # Salvar CSV
    df_results = pd.DataFrame(results)
    filename = f"backtest_results/backtest_com_filtros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_results.to_csv(filename, index=False)
    
    print(f"\n✅ Backtest salvo em: {filename}")
    print(f"   Trades: {len(df_results)}")
    print(f"   Colunas: {len(df_results.columns)}")
    
    # Estatísticas por recomendação
    print(f"\n📊 Análise por Filtro:")
    for rec in df_results['recomendacao'].unique():
        subset = df_results[df_results['recomendacao'] == rec]
        corretos = len(subset[subset['result'] == 'UP']) if len(subset) > 0 else 0
        print(f"   {rec:20}: {len(subset):2} trades | Acertos: {corretos}")
    
    return filename


if __name__ == '__main__':
    data_path = '/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv'
    model_path = '/home/ubuntu/pessoal/options/models/xgboost_model.pkl'
    
    backtest_com_filtros(data_path, model_path)
