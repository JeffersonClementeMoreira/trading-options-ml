#!/usr/bin/env python3
"""
TREINAR GBPUSD E EURUSD COM DADOS HALF/SUBSET
Rápido e pronto para produção
"""

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import pickle
from pathlib import Path

# Configurações
DATA_DIR = Path("/home/ubuntu/pessoal/options/data")
MODELS_DIR = Path("/home/ubuntu/pessoal/options/src/models")

MODELS_DIR.mkdir(exist_ok=True)

# Usar HALF para mais dados
CSV_FILES = {
    "GBPUSD": "GBPUSD_M15_202601012000_202603012345_processed.csv",
    "EURUSD": "EURUSD_M15_HALF.csv",  # HALF tem bastante dados
}

class IndicatorCalculator:
    """Calcula indicadores técnicos"""
    
    @staticmethod
    def calculate_all_indicators(closes, highs, lows, volumes):
        if len(closes) < 50:
            return None
            
        closes_arr = np.array(closes, dtype=float)
        highs_arr = np.array(highs, dtype=float)
        lows_arr = np.array(lows, dtype=float)
        volumes_arr = np.array(volumes, dtype=float)
        
        indicators = {}
        
        # RSI-14
        indicators["rsi_14"] = IndicatorCalculator._rsi(closes_arr, 14)
        
        # SMA-20 e SMA-50
        indicators["sma_20"] = np.mean(closes_arr[-20:])
        indicators["sma_50"] = np.mean(closes_arr[-50:])
        
        # ATR%
        atr = IndicatorCalculator._atr(highs_arr, lows_arr, closes_arr, 14)
        indicators["atr_pct"] = (atr / closes_arr[-1]) * 100 if closes_arr[-1] != 0 else 0
        
        # Momentum
        indicators["momentum"] = closes_arr[-1] - closes_arr[-13]
        
        # Confluence (0-4)
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


print("\n" + "="*70)
print("🚀 TREINANDO GBPUSD E EURUSD COM DADOS HALF")
print("="*70)

for symbol, csv_file in CSV_FILES.items():
    filepath = DATA_DIR / csv_file
    
    if not filepath.exists():
        print(f"\n❌ {symbol}: {csv_file} não encontrado")
        continue
    
    print(f"\n📂 Carregando {symbol}...")
    
    try:
        # Ler CSV - usar names para ignorar header
        df = pd.read_csv(
            filepath, sep='\t', skiprows=1,
            names=['date', 'time', 'open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread'],
            dtype={'open': float, 'high': float, 'low': float, 'close': float, 'vol': float},
            on_bad_lines='skip'
        )
        
        # Selecionar colunas
        df = df[['open', 'high', 'low', 'close', 'vol']]
        
        # Limpar
        df = df.dropna()
        df = df[df['close'] > 0]
        
        if len(df) < 100:
            print(f"   ⚠️  Dados insuficientes: {len(df)} candles")
            continue
        
        print(f"   ✅ Carregado: {len(df)} candles")
        
        # Calcular features
        print(f"   🔢 Calculando indicadores...")
        
        features_list = []
        labels_list = []
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        volumes = df['vol'].values
        
        for i in range(50, len(df)):
            indicators = IndicatorCalculator.calculate_all_indicators(
                closes[:i+1], highs[:i+1], lows[:i+1], volumes[:i+1]
            )
            
            if indicators is None:
                continue
            
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
            features_list.append(features)
            
            # Label
            label = 1 if indicators["confluence"] >= 3 else 0
            labels_list.append(label)
        
        if len(features_list) < 10:
            print(f"   ❌ Amostras insuficientes após processamento")
            continue
        
        X = np.array(features_list)
        y = np.array(labels_list)
        
        print(f"   ✅ {len(X)} amostras | {y.sum()} WIN / {len(y)-y.sum()} LOSS")
        
        # Treinar
        print(f"   🤖 Treinando XGBoost...")
        
        model = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            verbosity=0
        )
        
        model.fit(X, y)
        
        accuracy = model.score(X, y)
        print(f"   ✅ Accuracy: {accuracy*100:.2f}%")
        
        # Salvar
        model_path = MODELS_DIR / f"xgboost_{symbol}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        print(f"   💾 Salvo em: {model_path}")
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*70)
print("✅ TREINAMENTO CONCLUÍDO!")
print("="*70)
print("\nReinicie os servidores:")
print("  killall -9 python3")
print("  cd /home/ubuntu/pessoal/options/src")
print("  python3 server_mt5_http.py &")
print("  sleep 2 && python3 monitor_mt5_real.py &")
