#!/usr/bin/env python3
"""
Backtest Detalhado Corrigido - Com Melhorias

CORREÇÕES:
1. Próximo resultado é próximo DIA COM DADOS (não calendário - ignora feriado/fim de semana)
2. Adiciona horário da análise (último candle do dia)
3. OHLC é de todo o dia até o último candle
4. Adiciona features de SD (distância ao nível)
5. Adiciona análise de Sweep/BOS/CHOC
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import pickle

sys.path.insert(0, '/home/ubuntu/pessoal/options')

from core.multi_timeframe_confluence import MultiTimeframeConfluence


def calcular_distancia_sd(df_day: pd.DataFrame) -> dict:
    """
    Calcula distância para níveis de Supply/Demand EM PERCENTUAL
    (Funciona com qualquer ativo)
    
    Returns:
        {
            'ultimobull_dist_pct': distância % para último swing alto,
            'ultimobear_dist_pct': distância % para último swing baixo,
            'trend_type': 'UPTREND' / 'DOWNTREND' / 'RANGING',
        }
    """
    
    indicators = {}
    close = df_day['close'].values
    high = df_day['high'].values
    low = df_day['low'].values
    
    try:
        # Encontrar últimos swings (extremos locais)
        if len(close) >= 5:
            # Último swing alto (resistência)
            ultimo_high_idx = np.argmax(high[-20:]) if len(high) >= 20 else np.argmax(high)
            ultimo_high = high[-(20-ultimo_high_idx)] if len(high) >= 20 else high[ultimo_high_idx]
            
            # Último swing baixo (suporte)
            ultimo_low_idx = np.argmin(low[-20:]) if len(low) >= 20 else np.argmin(low)
            ultimo_low = low[-(20-ultimo_low_idx)] if len(low) >= 20 else low[ultimo_low_idx]
            
            current_price = close[-1]
            
            # Distância em % (universal para qualquer ativo)
            dist_high_pct = (ultimo_high - current_price) / current_price * 100  # Em %
            dist_low_pct = (current_price - ultimo_low) / ultimo_low * 100      # Em %
            
            indicators['ultimobull_dist_pct'] = dist_high_pct  # Positivo = acima, negativo = abaixo
            indicators['ultimobear_dist_pct'] = dist_low_pct   # Positivo = acima, negativo = abaixo
            
            # Determinar trend
            if current_price > ultimo_high:
                indicators['trend_type'] = 'UPTREND_ABOVE'
            elif current_price < ultimo_low:
                indicators['trend_type'] = 'DOWNTREND_BELOW'
            else:
                indicators['trend_type'] = 'BETWEEN_EXTREMES'
        
        # SMA para determinar trend
        if len(close) >= 50:
            sma50 = close[-50:].mean()
            if current_price > sma50:
                indicators['sma_position'] = 'ABOVE_SMA50'
            else:
                indicators['sma_position'] = 'BELOW_SMA50'
    
    except Exception as e:
        print(f"⚠️ Erro ao calcular SD: {e}")
    
    return indicators


def detectar_sweep_bos(df_day: pd.DataFrame) -> dict:
    """
    Detecta se houve Sweep no H4 (simulado com dados M15)
    E se há risco de BOS (Break of Structure) ou CHOC (Change of Character)
    
    Retorna valores em PERCENTUAL (funciona com qualquer ativo)
    
    Returns:
        {
            'em_sweep_h4': bool,
            'prox_bos_pct': float (distância em %),
        }
    """
    
    indicators = {}
    
    try:
        close = df_day['close'].values
        high = df_day['high'].values
        low = df_day['low'].values
        
        if len(close) < 30:
            return indicators
        
        # Simular H4 usando últimos 4*4=16 M15
        # Um H4 = 4 candles de M15
        # Pegar últimos 3 H4 (12 candles) para análise
        
        if len(close) >= 12:
            # Últimos 3 H4 simulados
            h4_1_high = max(high[-12:-8])  # H4 mais antigo
            h4_1_low = min(low[-12:-8])
            
            h4_2_high = max(high[-8:-4])   # H4 meio
            h4_2_low = min(low[-8:-4])
            
            h4_3_high = max(high[-4:])     # H4 mais recente
            h4_3_low = min(low[-4:])
            
            current_price = close[-1]
            
            # Detectar Sweep no último H4
            # Sweep = passou o high/low anterior mas fechou abaixo/acima
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
                
                # Distância para possível BOS em %
                dist_high_bos_pct = (h4_2_high - current_price) / current_price * 100
                dist_low_bos_pct = (current_price - h4_2_low) / h4_2_low * 100
                
                indicators['prox_bos_pct'] = min(abs(dist_high_bos_pct), abs(dist_low_bos_pct))
    
    except Exception as e:
        print(f"⚠️ Erro ao detectar sweep/BOS: {e}")
    
    return indicators


def calcular_indicadores(df_day: pd.DataFrame, df_hist: pd.DataFrame = None) -> dict:
    """Calcula indicadores técnicos para um dia."""
    
    indicators = {}
    close = df_day['close'].values
    high = df_day['high'].values
    low = df_day['low'].values
    
    try:
        # SMA - Usar histórico completo para SMA200
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
            indicators['sma200'] = None  # Não há dados suficientes
        
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


def obter_predicao_xgboost(df_day: pd.DataFrame, xgb_model, df_hist: pd.DataFrame = None) -> tuple:
    """Obtém predição XGBoost com features simples."""
    
    if xgb_model is None:
        return None, None, None
    
    try:
        # Calcular features simples
        close = df_day['close'].values
        
        features_dict = {}
        
        # SMA
        if len(close) >= 20:
            features_dict['sma20'] = close[-20:].mean()
        if len(close) >= 50:
            features_dict['sma50'] = close[-50:].mean()
        
        # SMA200 - Usar histórico se disponível
        if df_hist is not None and len(df_hist) >= 200:
            close_hist = df_hist['close'].values
            all_close = np.concatenate([close_hist[-200:], close[:]])
            features_dict['sma200'] = all_close[-200:].mean()
        elif len(close) >= 200:
            features_dict['sma200'] = close[-200:].mean()
        
        # Momentum
        if len(close) >= 10:
            features_dict['momentum10'] = (close[-1] - close[-10]) / close[-10] * 100
        
        # Volatilidade
        if len(close) >= 20:
            features_dict['volatility'] = np.std(close[-20:]) / np.mean(close[-20:]) * 100
        
        # Preencher com valores padrão
        X_dict = {
            'current_close': close[-1],
            'next_close': close[-1],  # Dummy
            'm15_trend': 'NEUTRAL',
            'h4_trend': 'NEUTRAL',
            'is_aligned': '❌',
        }
        X_dict.update(features_dict)
        
        # Converter para DataFrame
        X = pd.DataFrame([X_dict]).fillna(0)
        
        # Obter apenas colunas esperadas pelo modelo
        model_features = xgb_model['numeric_features'] + xgb_model['categorical_features']
        X_model = pd.DataFrame(index=[0])
        
        for feat in model_features:
            if feat in X.columns:
                X_model[feat] = X[feat].values
            else:
                X_model[feat] = 0
        
        # Codificar categóricos
        for cat_col in xgb_model['categorical_features']:
            if cat_col in X_model.columns:
                try:
                    le = xgb_model['encoded_cols'].get(cat_col)
                    if le:
                        X_model[cat_col] = le.transform([X_model[cat_col].iloc[0]])[0]
                    else:
                        X_model[cat_col] = 0
                except:
                    X_model[cat_col] = 0
        
        # Predição
        pred = xgb_model['model'].predict(X_model)[0]
        prob = xgb_model['model'].predict_proba(X_model)[0]
        
        prediction = "BUY" if pred == 1 else "SELL"
        confidence = prob[1] if pred == 1 else prob[0]
        
        return prediction, confidence, None
    
    except Exception as e:
        print(f"⚠️ Erro ao gerar predição XGBoost: {e}")
        return None, None, None


def backtest_detalhado_corrigido(data_path: str, model_path: str, start_date: str = None, end_date: str = None):
    """Executa backtest detalhado COM CORREÇÕES."""
    
    print("\n" + "="*120)
    print("📊 BACKTEST DETALHADO CORRIGIDO - OHLC + SD + SWEEP/BOS + XGBoost")
    print("="*120 + "\n")
    
    # Carregar dados com separador correto
    print(f"📥 Carregando dados de {data_path}...")
    df = pd.read_csv(data_path, sep='\t')
    
    # Limpar nomes das colunas
    df.columns = [col.strip('<>').lower() for col in df.columns]
    
    # Combinar DATE e TIME
    if 'date' in df.columns and 'time' in df.columns:
        df['datetime'] = pd.to_datetime(
            df['date'].astype(str).str.replace('.', '-') + ' ' + df['time'],
            format='%Y-%m-%d %H:%M:%S'
        )
        df.set_index('datetime', inplace=True)
    else:
        df.index = pd.to_datetime(df.index)
    
    df = df.sort_index()
    print(f"✅ Dados carregados: {len(df)} candles")
    print(f"   Período: {df.index[0]} a {df.index[-1]}\n")
    
    # Padronizar nomes das colunas
    rename_map = {
        'open': 'open', 'o': 'open',
        'high': 'high', 'h': 'high',
        'low': 'low', 'l': 'low',
        'close': 'close', 'c': 'close',
        'volume': 'volume', 'vol': 'volume', 'tickvol': 'volume',
    }
    for old, new in rename_map.items():
        if old in df.columns:
            df[new] = df[old]
            if old != new:
                df = df.drop(old, axis=1)
    
    # Carregar modelo XGBoost
    xgb_model = None
    if model_path and Path(model_path).exists():
        try:
            with open(model_path, 'rb') as f:
                xgb_model = pickle.load(f)
            print(f"✅ Modelo XGBoost carregado\n")
        except Exception as e:
            print(f"⚠️ Erro ao carregar modelo: {e}\n")
    
    # Carregar confluência
    confluence = MultiTimeframeConfluence(verbose=False)
    
    # Definir período
    if start_date:
        start_dt = pd.to_datetime(start_date)
    else:
        start_dt = df.index[0]
    
    if end_date:
        end_dt = pd.to_datetime(end_date)
    else:
        end_dt = df.index[-1]
    
    print(f"🎯 Período: {start_dt.date()} a {end_dt.date()}\n")
    
    # Processar cada dia
    results = []
    unique_dates = df.index.normalize().unique()
    unique_dates = pd.DatetimeIndex(unique_dates).sort_values()
    unique_dates = unique_dates[(unique_dates >= start_dt) & (unique_dates <= end_dt)]
    
    for date_idx, date_ts in enumerate(unique_dates):
        date = date_ts.to_pydatetime()
        
        # Histórico até dia anterior (para calcular SMA200 corretamente)
        df_until_prev_day = df[df.index < date]
        
        # Dados do dia
        next_day = date + timedelta(days=1)
        day_data = df[(df.index.date >= date.date()) & (df.index.date < next_day.date())]
        
        if len(day_data) < 20:
            continue
        
        # Horário do último candle (hora da análise/entrada)
        last_candle_time = day_data.index[-1]
        analysis_time = last_candle_time.strftime('%H:%M:%S')
        
        # OHLC do dia (até último candle)
        open_price = day_data['open'].iloc[0]
        high_price = day_data['high'].max()
        low_price = day_data['low'].min()
        close_price = day_data['close'].iloc[-1]
        volume_total = day_data['volume'].sum() if 'volume' in day_data.columns else 0
        
        # Fechamento às 14:00 (se existir naquele dia)
        close_14h = None
        try:
            time_1400 = day_data[day_data.index.hour == 14]
            if len(time_1400) > 0:
                close_14h = time_1400['close'].iloc[0]
        except:
            pass
        
        # Indicadores - Passar histórico para SMA200
        indicators = calcular_indicadores(day_data, df_until_prev_day)
        
        # SD/Sweep/BOS
        sd_indicators = calcular_distancia_sd(day_data)
        sweep_indicators = detectar_sweep_bos(day_data)
        
        # XGBoost
        xgb_pred, xgb_conf, _ = obter_predicao_xgboost(day_data, xgb_model, df_until_prev_day)
        
        # Confluência
        conf_analysis = confluence.analyze_confluence(day_data)
        
        # RESULTADO: Próximo DIA COM DADOS (não calendário)
        # Procurar próximo dia que tem dados
        next_day_with_data = None
        next_close = None
        change_pct = None
        result = "NO_DATA"
        acertou = None
        
        for future_idx in range(date_idx + 1, len(unique_dates)):
            future_date = unique_dates[future_idx].to_pydatetime()
            future_next = future_date + timedelta(days=1)
            future_data = df[(df.index.date >= future_date.date()) & (df.index.date < future_next.date())]
            
            if len(future_data) > 0:
                next_day_with_data = future_date
                next_close = future_data['close'].iloc[-1]
                change_pct = (next_close - close_price) / close_price * 100
                result = "UP" if change_pct > 0 else "DOWN"
                acertou = (xgb_pred == "BUY" and change_pct > 0) or (xgb_pred == "SELL" and change_pct < 0)
                break
        
        # Montar resultado
        row = {
            # Data e horário
            'date': date.strftime('%Y-%m-%d'),
            'day_of_week': date.strftime('%A'),
            'analysis_time': analysis_time,  # ← NOVO: Horário da análise
            'result_date': next_day_with_data.strftime('%Y-%m-%d') if next_day_with_data else None,
            
            # OHLC DO DIA (até último candle)
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'close_14h': close_14h,  # ← NOVO: Fechamento às 14:00
            'volume': volume_total,
            'range_pct': ((high_price - low_price) / close_price * 100) if close_price > 0 else 0,
            
            # Indicadores
            'sma20': indicators.get('sma20'),
            'sma50': indicators.get('sma50'),
            'sma200': indicators.get('sma200'),
            'rsi14': indicators.get('rsi14'),
            'macd': indicators.get('macd'),
            'volatility': indicators.get('volatility'),
            'momentum10': indicators.get('momentum10'),
            
            # Supply/Demand ← NOVO (em %)
            'dist_ultimo_high_pct': sd_indicators.get('ultimobull_dist_pct'),
            'dist_ultimo_low_pct': sd_indicators.get('ultimobear_dist_pct'),
            'sd_trend_type': sd_indicators.get('trend_type'),
            'sma_position': sd_indicators.get('sma_position'),
            
            # Sweep/BOS ← NOVO (em %)
            'em_sweep_h4': sweep_indicators.get('em_sweep_h4'),
            'sweep_type': sweep_indicators.get('sweep_type'),
            'pct_proximo_bos': sweep_indicators.get('prox_bos_pct'),
            
            # XGBoost
            'xgb_pred': xgb_pred,
            'xgb_confidence': xgb_conf,
            
            # Confluência
            'm15_trend': conf_analysis.m15_trend,
            'h4_trend': conf_analysis.h4_trend,
            'is_aligned': '✅' if conf_analysis.is_aligned else '❌',
            'alignment_score': conf_analysis.alignment_score,
            
            # Resultado
            'next_close': next_close,
            'change_pct': change_pct,
            'result': result,
            'acertou': '✅' if acertou else ('❌' if acertou is not None else '⏳'),
        }
        
        results.append(row)
        
        # Mostrar progresso
        status = '✅' if acertou else ('❌' if acertou is not None else '⏳')
        change_str = f"({change_pct:+.2f}%)" if change_pct is not None else "(N/A)"
        conf_str = f"({xgb_conf:.0%})" if xgb_conf else "(N/A)"
        sweep_str = f"[SWEEP]" if sweep_indicators.get('em_sweep_h4') else ""
        
        print(f"{status} {row['date']} {analysis_time} → {result_date if (result_date := next_day_with_data.strftime('%Y-%m-%d') if next_day_with_data else 'N/A') else 'N/A'} | "
              f"XGBoost: {xgb_pred} {conf_str} | "
              f"Resultado: {result} {change_str} {sweep_str}")
    
    # Salvar CSV
    df_results = pd.DataFrame(results)
    
    filename = f"backtest_results/backtest_corrigido_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_results.to_csv(filename, index=False)
    
    print(f"\n✅ Backtest corrigido salvo em: {filename}")
    print(f"   Linhas: {len(df_results)}")
    print(f"   Colunas: {len(df_results.columns)}\n")
    
    # Estatísticas
    df_valid = df_results[df_results['acertou'].isin(['✅', '❌'])]
    if len(df_valid) > 0:
        acertos = len(df_valid[df_valid['acertou'] == '✅'])
        total = len(df_valid)
        win_rate = acertos / total * 100
        
        print(f"📊 Estatísticas:")
        print(f"   Total de trades: {total}")
        print(f"   Acertos: {acertos} ({win_rate:.1f}%)")
        print(f"   Erros: {total - acertos}")
        
        # Com confluência
        aligned = df_valid[df_valid['is_aligned'] == '✅']
        if len(aligned) > 0:
            aligned_correct = len(aligned[aligned['acertou'] == '✅'])
            aligned_wr = aligned_correct / len(aligned) * 100
            print(f"\n   Com confluência: {aligned_correct}/{len(aligned)} ({aligned_wr:.1f}%)")
        
        # Em sweep
        in_sweep = df_valid[df_valid['em_sweep_h4'] == True]
        if len(in_sweep) > 0:
            sweep_correct = len(in_sweep[in_sweep['acertou'] == '✅'])
            sweep_wr = sweep_correct / len(in_sweep) * 100
            print(f"   Em sweep H4: {sweep_correct}/{len(in_sweep)} ({sweep_wr:.1f}%)")
    
    print(f"\n✨ Correções aplicadas:")
    print(f"   ✅ Resultado usa próximo dia COM DADOS (ignora feriados/fim de semana)")
    print(f"   ✅ Adicionado horário da análise (analysis_time)")
    print(f"   ✅ Adicionado data do resultado (result_date)")
    print(f"   ✅ Distância para SD em % (dist_ultimo_high_pct, dist_ultimo_low_pct) - UNIVERSAL para qualquer ativo")
    print(f"   ✅ Detecção de Sweep H4 e proximidade de BOS em %")
    print(f"   ✅ Tipo de posicionamento vs SD (sd_trend_type)")
    print(f"   ✅ Todas as medidas em PERCENTUAL para funcionar com qualquer ativo (EURUSD, GBPUSD, XAUUSD, etc)")
    
    return filename


if __name__ == '__main__':
    # Caminhos
    data_path = '/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv'
    model_path = '/home/ubuntu/pessoal/options/models/xgboost_model.pkl'
    
    # Rodar backtest
    csv_file = backtest_detalhado_corrigido(
        data_path=data_path,
        model_path=model_path,
        start_date='2026-01-01',
        end_date='2026-03-01'
    )
    
    print(f"\n✨ Análise completa com correções!")
    print(f"   Arquivo: {csv_file}")

