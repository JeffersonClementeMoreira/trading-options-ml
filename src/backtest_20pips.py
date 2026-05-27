#!/usr/bin/env python3
"""
BACKTEST COM ALVO DE 20 PIPS
Valida se o sistema XGBoost está correto
Mostra: Horário entrada/saída, Preço entrada/saída, Resultado, Recomendação
"""

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import pickle
from pathlib import Path
from datetime import datetime

# Configurações
MODELS_DIR = Path("/home/ubuntu/pessoal/options/src/models")
DATA_DIR = Path("/home/ubuntu/pessoal/options/data")

TARGET_PIPS = 20  # 20 pips para EURUSD (0,002)
TARGET_PIPS_XAUUSD = 2  # 2 pips para XAUUSD (1 pip = 0.01)

class IndicatorCalculator:
    """Calcula indicadores"""
    
    @staticmethod
    def calculate_all_indicators(closes, highs, lows, volumes):
        if len(closes) < 50:
            return None
            
        closes_arr = np.array(closes, dtype=float)
        highs_arr = np.array(highs, dtype=float)
        lows_arr = np.array(lows, dtype=float)
        volumes_arr = np.array(volumes, dtype=float)
        
        indicators = {}
        
        indicators["rsi_14"] = IndicatorCalculator._rsi(closes_arr, 14)
        indicators["sma_20"] = np.mean(closes_arr[-20:])
        indicators["sma_50"] = np.mean(closes_arr[-50:])
        
        atr = IndicatorCalculator._atr(highs_arr, lows_arr, closes_arr, 14)
        indicators["atr_pct"] = (atr / closes_arr[-1]) * 100 if closes_arr[-1] != 0 else 0
        
        indicators["momentum"] = closes_arr[-1] - closes_arr[-13]
        
        confluence = 0
        if closes_arr[-1] > np.mean(closes_arr[-20:]):
            confluence += 1
        if indicators["rsi_14"] > 50:
            confluence += 1
        if closes_arr[-1] > np.mean(closes_arr[-50:]):
            confluence += 1
        indicators["confluence"] = confluence
        
        return indicators
    
    @staticmethod
    def _rsi(prices, period=14):
        deltas = np.diff(prices[-period-1:])
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def _atr(highs, lows, closes, period=14):
        tr = np.maximum(highs[-period:] - lows[-period:], 
                       np.maximum(np.abs(highs[-period:] - closes[-period-1:-1]), 
                                 np.abs(lows[-period:] - closes[-period-1:-1])))
        return np.mean(tr)

print("\n" + "="*100)
print("🎯 BACKTEST COM ALVO 20 PIPS - VALIDAÇÃO DO SISTEMA XGBOOST")
print("="*100)

# Carregar modelos
models = {}
for symbol in ["EURUSD", "XAUUSD"]:
    model_path = MODELS_DIR / f"xgboost_{symbol}.pkl"
    if model_path.exists():
        with open(model_path, 'rb') as f:
            models[symbol] = pickle.load(f)
        print(f"✅ Modelo {symbol} carregado")
    else:
        print(f"⚠️  Modelo {symbol} não encontrado")

# Executar backtest por símbolo
for symbol, model in models.items():
    print(f"\n{'='*100}")
    print(f"📊 SÍMBOLO: {symbol}")
    print(f"{'='*100}")
    
    # Carregar dados
    if symbol == "EURUSD":
        csv_file = DATA_DIR / "EURUSD_M15_HALF.csv"
        pip_value = 0.0001  # 1 pip para EURUSD
        target_pips = TARGET_PIPS
    else:  # XAUUSD
        csv_file = DATA_DIR / "XAUUSD_M15_202001020600_202604131545.csv"
        pip_value = 0.01  # 1 pip para XAUUSD
        target_pips = TARGET_PIPS_XAUUSD
    
    if not csv_file.exists():
        print(f"❌ Arquivo não encontrado: {csv_file}")
        continue
    
    # Carregar CSV
    try:
        df = pd.read_csv(csv_file, sep='\t', skiprows=1,
                        names=['date', 'time', 'open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread'],
                        dtype={'open': float, 'high': float, 'low': float, 'close': float, 'vol': float},
                        on_bad_lines='skip')
        
        df = df[['open', 'high', 'low', 'close', 'vol']].dropna()
        df = df[df['close'] > 0]
        
        print(f"✅ Carregado: {len(df)} candles")
        
    except Exception as e:
        print(f"❌ Erro ao carregar: {e}")
        continue
    
    # Executar backtest
    trades = []
    
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    volumes = df['vol'].values
    
    print(f"\n🔄 Processando {len(df)} candles...\n")
    print(f"{'#':<5} {'Entrada':<12} {'Saída':<12} {'Preço Ent':<12} {'Preço Saí':<12} {'Pips':<8} {'Resultado':<12} {'Rec':<15}")
    print("-" * 100)
    
    trade_count = 0
    
    for i in range(50, len(df) - 1):
        # Calcular indicadores
        indicators = IndicatorCalculator.calculate_all_indicators(
            closes[:i+1], highs[:i+1], lows[:i+1], volumes[:i+1]
        )
        
        if indicators is None:
            continue
        
        # Preparar features
        features = [
            indicators["rsi_14"],
            indicators["sma_20"],
            indicators["sma_50"],
            indicators["atr_pct"],
            indicators["momentum"],
            indicators["confluence"],
            closes[i],
            volumes[i]
        ]
        
        # Predição
        prob = model.predict_proba([features])[0][1]  # Probabilidade de WIN
        prediction = 1 if prob > 0.5 else 0
        
        # Recomendação
        if prediction == 1 and prob > 0.7:
            rec = "🟢 COMPRA+"
            direction = "LONG"
        elif prediction == 1:
            rec = "🟡 COMPRA"
            direction = "LONG"
        elif prediction == 0 and prob < 0.3:
            rec = "🔴 VENDA+"
            direction = "SHORT"
        else:
            rec = "⚪ NEUTRO"
            direction = "SKIP"
        
        if direction == "SKIP":
            continue
        
        # Preço de entrada
        entry_price = closes[i]
        entry_candle = i
        
        # Procurar saída (próximos 96 candles = 1 dia)
        target_distance = target_pips * pip_value
        exited = False
        exit_candle = None
        exit_price = None
        result = None
        pips_reached = 0
        
        for j in range(i + 1, min(i + 97, len(df))):  # Próximos 96 candles (1 dia)
            high_price = highs[j]
            low_price = lows[j]
            
            if direction == "LONG":
                # Procura subida
                if high_price >= entry_price + target_distance:
                    exit_price = entry_price + target_distance
                    exit_candle = j
                    result = "✅ GANHO"
                    pips_reached = target_pips
                    exited = True
                    break
                # Checa stop loss (-10 pips)
                elif low_price <= entry_price - (10 * pip_value):
                    exit_price = entry_price - (10 * pip_value)
                    exit_candle = j
                    result = "❌ PERDA"
                    pips_reached = -10
                    exited = True
                    break
            else:  # SHORT
                # Procura queda
                if low_price <= entry_price - target_distance:
                    exit_price = entry_price - target_distance
                    exit_candle = j
                    result = "✅ GANHO"
                    pips_reached = target_pips
                    exited = True
                    break
                # Checa stop loss (+10 pips)
                elif high_price >= entry_price + (10 * pip_value):
                    exit_price = entry_price + (10 * pip_value)
                    exit_candle = j
                    result = "❌ PERDA"
                    pips_reached = -10
                    exited = True
                    break
        
        if not exited:
            # Não saiu em 1 dia, usar preço do último candle
            exit_price = closes[min(i + 96, len(df) - 1)]
            exit_candle = min(i + 96, len(df) - 1)
            pips_reached = (exit_price - entry_price) / pip_value
            result = "⏱️ TIMEOUT"
        
        # Imprimir resultado
        trade_count += 1
        print(f"{trade_count:<5} {entry_candle:<12} {exit_candle:<12} {entry_price:<12.5f} {exit_price:<12.5f} {pips_reached:<8.1f} {result:<12} {rec:<15}")
        
        trades.append({
            'entry_candle': entry_candle,
            'exit_candle': exit_candle,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pips': pips_reached,
            'direction': direction,
            'result': result,
            'rec': rec,
            'prob': prob
        })
    
    if not trades:
        print("❌ Nenhum trade gerado")
        continue
    
    # Resumo
    print("\n" + "="*100)
    print("📊 RESUMO DOS RESULTADOS")
    print("="*100)
    
    df_trades = pd.DataFrame(trades)
    
    total_trades = len(df_trades)
    ganhos = len(df_trades[df_trades['result'] == '✅ GANHO'])
    perdas = len(df_trades[df_trades['result'] == '❌ PERDA'])
    timeouts = len(df_trades[df_trades['result'] == '⏱️ TIMEOUT'])
    
    wr = (ganhos / total_trades * 100) if total_trades > 0 else 0
    total_pips = df_trades['pips'].sum()
    avg_pips = df_trades['pips'].mean()
    
    print(f"\nTotal de Trades: {total_trades}")
    print(f"Ganhos: {ganhos} ({ganhos/total_trades*100:.1f}%)")
    print(f"Perdas: {perdas} ({perdas/total_trades*100:.1f}%)")
    print(f"Timeouts: {timeouts} ({timeouts/total_trades*100:.1f}%)")
    print(f"\n🎯 Win Rate: {wr:.1f}%")
    print(f"📈 Total Pips: {total_pips:.1f}")
    print(f"📊 Média Pips/Trade: {avg_pips:.1f}")
    
    # Análise por probabilidade
    print(f"\n{'='*100}")
    print("📈 ANÁLISE POR NÍVEL DE CONFIANÇA")
    print(f"{'='*100}")
    
    for prob_threshold in [0.6, 0.7, 0.8]:
        filtered = df_trades[df_trades['prob'] >= prob_threshold]
        if len(filtered) > 0:
            wr_filtered = len(filtered[filtered['result'] == '✅ GANHO']) / len(filtered) * 100
            print(f"Prob >= {prob_threshold}: {len(filtered)} trades | WR: {wr_filtered:.1f}% | Pips: {filtered['pips'].sum():.1f}")

print("\n✅ BACKTEST CONCLUÍDO\n")
