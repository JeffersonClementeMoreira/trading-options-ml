#!/usr/bin/env python3
"""
Backtest Detalhado - Com OHLC + Indicadores + XGBoost

Salva para cada dia:
- Open, High, Low, Close
- Indicadores: SMA20, SMA50, SMA200, RSI, MACD
- Predição XGBoost com confiança
- Confluência M15 vs H4
- Resultado (acerto ou não)

Perfeto para análise manual!
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import pickle

sys.path.insert(0, '/home/ubuntu/pessoal/options')

from core.multi_timeframe_confluence import MultiTimeframeConfluence


def calcular_indicadores(df_day: pd.DataFrame) -> dict:
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
        if len(close) >= 200:
            indicators['sma200'] = close[-200:].mean()
        
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
        
        # Momentum (últimos 10 candles)
        if len(close) >= 10:
            momentum = (close[-1] - close[-10]) / close[-10] * 100
            indicators['momentum10'] = momentum
        
    except Exception as e:
        print(f"⚠️ Erro ao calcular indicadores: {e}")
    
    return indicators


def obter_predicao_xgboost(df_day: pd.DataFrame, xgb_model) -> tuple:
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
        if len(close) >= 200:
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


def backtest_detalhado(data_path: str, model_path: str, start_date: str = None, end_date: str = None):
    """Executa backtest detalhado com todos os indicadores."""
    
    print("\n" + "="*100)
    print("📊 BACKTEST DETALHADO COM OHLC + INDICADORES + XGBOOST")
    print("="*100 + "\n")
    
    # Carregar dados (com separador correto)
    print(f"📥 Carregando dados de {data_path}...")
    df = pd.read_csv(data_path, sep='\t')
    
    # Limpar nomes das colunas
    df.columns = [col.strip('<>').lower() for col in df.columns]
    
    # Combinar DATE e TIME se ambas existem
    if 'date' in df.columns and 'time' in df.columns:
        df['datetime'] = pd.to_datetime(
            df['date'].astype(str).str.replace('.', '-') + ' ' + df['time'],
            format='%Y-%m-%d %H:%M:%S'
        )
        df.set_index('datetime', inplace=True)
    elif 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
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
    
    for date_ts in unique_dates:
        date = date_ts.to_pydatetime()
        
        # Dados do dia
        next_day = date + timedelta(days=1)
        day_data = df[(df.index.date >= date.date()) & (df.index.date < next_day.date())]
        
        if len(day_data) < 20:
            continue
        
        # OHLC do dia
        open_price = day_data['open'].iloc[0]
        high_price = day_data['high'].max()
        low_price = day_data['low'].min()
        close_price = day_data['close'].iloc[-1]
        volume_total = day_data['volume'].sum() if 'volume' in day_data.columns else 0
        
        # Indicadores
        indicators = calcular_indicadores(day_data)
        
        # XGBoost
        xgb_pred, xgb_conf, xgb_features = obter_predicao_xgboost(day_data, xgb_model)
        
        # Confluência
        conf_analysis = confluence.analyze_confluence(day_data)
        
        # Resultado (próximo dia)
        next_day_end = next_day + timedelta(days=1)
        next_day_data = df[(df.index.date >= next_day.date()) & (df.index.date < next_day_end.date())]
        
        if len(next_day_data) > 0:
            next_close = next_day_data['close'].iloc[-1]
            change_pct = (next_close - close_price) / close_price * 100
            result = "UP" if change_pct > 0 else "DOWN"
            acertou = (xgb_pred == "BUY" and change_pct > 0) or (xgb_pred == "SELL" and change_pct < 0)
        else:
            next_close = None
            change_pct = None
            result = "NO_DATA"
            acertou = None
        
        # Montar resultado
        row = {
            # Data
            'date': date.strftime('%Y-%m-%d'),
            'day_of_week': date.strftime('%A'),
            
            # OHLC
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
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
        print(f"{status} {row['date']} | "
              f"OHLC: {open_price:.5f}-{high_price:.5f}-{low_price:.5f}-{close_price:.5f} | "
              f"XGBoost: {xgb_pred} {conf_str} | "
              f"Resultado: {result} {change_str}")
    
    # Salvar CSV
    df_results = pd.DataFrame(results)
    
    filename = f"backtest_results/backtest_detalhado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_results.to_csv(filename, index=False)
    
    print(f"\n✅ Backtest detalhado salvo em: {filename}")
    print(f"   Linhas: {len(df_results)}")
    print(f"   Colunas: {len(df_results.columns)}")
    
    # Estatísticas
    df_valid = df_results[df_results['acertou'].isin(['✅', '❌'])]
    if len(df_valid) > 0:
        acertos = len(df_valid[df_valid['acertou'] == '✅'])
        total = len(df_valid)
        win_rate = acertos / total * 100
        
        print(f"\n📊 Estatísticas:")
        print(f"   Total de trades: {total}")
        print(f"   Acertos: {acertos} ({win_rate:.1f}%)")
        print(f"   Erros: {total - acertos}")
        
        # Com confluência
        aligned = df_valid[df_valid['is_aligned'] == '✅']
        if len(aligned) > 0:
            aligned_correct = len(aligned[aligned['acertou'] == '✅'])
            aligned_wr = aligned_correct / len(aligned) * 100
            print(f"\n   Com confluência: {aligned_correct}/{len(aligned)} ({aligned_wr:.1f}%)")
        
        divergent = df_valid[df_valid['is_aligned'] == '❌']
        if len(divergent) > 0:
            divergent_correct = len(divergent[divergent['acertou'] == '✅'])
            divergent_wr = divergent_correct / len(divergent) * 100
            print(f"   Sem confluência: {divergent_correct}/{len(divergent)} ({divergent_wr:.1f}%)")
    
    # Mostrar primeiras linhas
    print(f"\n📋 Primeiras 5 linhas do resultado:\n")
    print(df_results.head(5).to_string())
    
    return filename


if __name__ == '__main__':
    # Caminhos
    data_path = '/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv'
    model_path = '/home/ubuntu/pessoal/options/models/xgboost_model.pkl'
    
    # Rodar backtest
    csv_file = backtest_detalhado(
        data_path=data_path,
        model_path=model_path,
        start_date='2026-01-01',
        end_date='2026-03-01'
    )
    
    print(f"\n✨ Análise completa! Abra o CSV para visualizar todos os detalhes.")
    print(f"   Arquivo: {csv_file}")

