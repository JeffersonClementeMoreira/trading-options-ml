#!/usr/bin/env python3
"""
TREINAMENTO XGBOOST COM DADOS HISTÓRICOS
Lê CSVs históricos de MT5, calcula indicadores, labels e treina XGBoost
"""

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import pickle
from pathlib import Path
from datetime import datetime
import sys

# Configurações
DATA_DIR = Path("/home/ubuntu/pessoal/options/data")
MODELS_DIR = Path("/home/ubuntu/pessoal/options/src/models")
CSV_FILES = {
    "GBPUSD": "GBPUSD_M15_202601012000_202603012345_processed.csv",
    "EURUSD": "EURUSD_M15_202301012200_202605222015_processed.csv",
    "XAUUSD": "XAUUSD_M15_202001020600_202604131545.csv"
}

MODELS_DIR.mkdir(exist_ok=True)


class IndicatorCalculator:
    """Calcula 25+ indicadores técnicos"""
    
    @staticmethod
    def calculate_all_indicators(closes, highs, lows, volumes):
        """Retorna dicionário com todos os indicadores"""
        if len(closes) < 50:
            return None
            
        closes_arr = np.array(closes, dtype=float)
        highs_arr = np.array(highs, dtype=float)
        lows_arr = np.array(lows, dtype=float)
        volumes_arr = np.array(volumes, dtype=float)
        
        indicators = {}
        
        # RSI-14 e RSI-7
        indicators["rsi_14"] = IndicatorCalculator._rsi(closes_arr, 14)
        indicators["rsi_7"] = IndicatorCalculator._rsi(closes_arr, 7)
        
        # EMA-12 e EMA-26
        indicators["ema_12"] = IndicatorCalculator._ema(closes_arr, 12)
        indicators["ema_26"] = IndicatorCalculator._ema(closes_arr, 26)
        
        # SMA-20 e SMA-50
        indicators["sma_20"] = np.mean(closes_arr[-20:])
        indicators["sma_50"] = np.mean(closes_arr[-50:])
        
        # ATR e ATR%
        atr = IndicatorCalculator._atr(highs_arr, lows_arr, closes_arr, 14)
        indicators["atr"] = atr
        indicators["atr_pct"] = (atr / closes_arr[-1]) * 100 if closes_arr[-1] != 0 else 0
        
        # Momentum
        indicators["momentum"] = closes_arr[-1] - closes_arr[-13]
        
        # Confluence (0-4 scale)
        confluence = 0
        if closes_arr[-1] > np.mean(closes_arr[-20:]):
            confluence += 1
        if indicators["rsi_14"] > 50:
            confluence += 1
        if closes_arr[-1] > np.mean(closes_arr[-50:]):
            confluence += 1
        if indicators["ema_12"] > indicators["ema_26"]:
            confluence += 1
        indicators["confluence"] = confluence
        
        # Volume MA
        indicators["volume_ma"] = np.mean(volumes_arr[-20:])
        
        # Bollinger Bands
        sma_20 = indicators["sma_20"]
        std = np.std(closes_arr[-20:])
        indicators["bb_upper"] = sma_20 + (2 * std)
        indicators["bb_mid"] = sma_20
        indicators["bb_lower"] = sma_20 - (2 * std)
        
        # MACD
        ema12 = indicators["ema_12"]
        ema26 = indicators["ema_26"]
        indicators["macd"] = ema12 - ema26
        indicators["signal"] = indicators["macd"]  # Simplified
        indicators["histogram"] = indicators["macd"] - indicators["signal"]
        
        # Stochastic
        k_pct = IndicatorCalculator._stochastic_k(highs_arr, lows_arr, closes_arr, 14)
        indicators["stoch_k"] = k_pct
        indicators["stoch_d"] = k_pct  # Simplified
        
        # OBV
        indicators["obv"] = IndicatorCalculator._obv(closes_arr, volumes_arr)
        
        # ROC-12 e ROC-6
        indicators["roc_12"] = ((closes_arr[-1] - closes_arr[-13]) / closes_arr[-13] * 100) if closes_arr[-13] != 0 else 0
        indicators["roc_6"] = ((closes_arr[-1] - closes_arr[-7]) / closes_arr[-7] * 100) if closes_arr[-7] != 0 else 0
        
        # Candle analysis
        open_price = closes_arr[-2] if len(closes_arr) > 1 else closes_arr[-1]
        close_price = closes_arr[-1]
        body = abs(close_price - open_price)
        indicators["candle_body"] = body
        indicators["upper_wick"] = highs_arr[-1] - max(open_price, close_price)
        indicators["lower_wick"] = min(open_price, close_price) - lows_arr[-1]
        
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
    def _ema(prices, period=12):
        return prices[-1] if len(prices) < period else np.mean(prices[-period:])
    
    @staticmethod
    def _atr(highs, lows, closes, period=14):
        tr = np.maximum(highs[-period:] - lows[-period:], 
                       np.maximum(np.abs(highs[-period:] - closes[-period-1:-1]), 
                                 np.abs(lows[-period:] - closes[-period-1:-1])))
        return np.mean(tr)
    
    @staticmethod
    def _stochastic_k(highs, lows, closes, period=14):
        low_min = np.min(lows[-period:])
        high_max = np.max(highs[-period:])
        if high_max - low_min == 0:
            return 50
        return ((closes[-1] - low_min) / (high_max - low_min)) * 100
    
    @staticmethod
    def _obv(closes, volumes):
        obv = 0
        for i in range(len(closes)-20, len(closes)):
            if closes[i] > closes[i-1]:
                obv += volumes[i]
            elif closes[i] < closes[i-1]:
                obv -= volumes[i]
        return obv
    

class HistoricalTrainer:
    """Treina XGBoost com dados históricos"""
    
    def __init__(self):
        self.all_data = {}
        
    def load_csv(self, symbol, filepath):
        """Carrega CSV do MT5"""
        print(f"\n📂 Carregando {symbol}...")
        try:
            df = pd.read_csv(
                filepath,
                sep='\t',
                names=['date', 'time', 'open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread'],
                dtype={'date': str, 'time': str, 'open': float, 'high': float, 'low': float, 
                       'close': float, 'tickvol': float, 'vol': float, 'spread': float},
                skiprows=1
            )
            # Limpar valores NaN
            df = df.dropna()
            df = df[df['close'] > 0]  # Remover dados inválidos
            
            print(f"   ✅ Carregado: {len(df)} candles (após limpeza)")
            print(f"   Data range: {df['date'].iloc[0]} a {df['date'].iloc[-1]}")
            return df
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return None
    
    def calculate_features_and_labels(self, df, symbol):
        """Calcula features e labels para treinamento"""
        print(f"\n🔢 Calculando indicadores para {symbol}...")
        
        features_list = []
        labels_list = []
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        volumes = df['vol'].values
        
        for i in range(50, len(df)):
            window_closes = closes[:i+1]
            window_highs = highs[:i+1]
            window_lows = lows[:i+1]
            window_volumes = volumes[:i+1]
            
            indicators = IndicatorCalculator.calculate_all_indicators(
                window_closes, window_highs, window_lows, window_volumes
            )
            
            if indicators is None:
                continue
            
            # Features (8 principais)
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
            
            # Label: WIN se Confluence >= 3, LOSS se < 2
            label = 1 if indicators["confluence"] >= 3 else 0
            labels_list.append(label)
        
        print(f"   ✅ {len(features_list)} amostras calculadas")
        print(f"   Distribuição: {labels_list.count(0)} LOSS / {labels_list.count(1)} WIN")
        
        return np.array(features_list), np.array(labels_list)
    
    def train_model(self, symbol, X, y):
        """Treina XGBoost para o par"""
        if len(X) < 10:
            print(f"   ⚠️  {symbol}: Dados insuficientes")
            return None
        
        print(f"\n🤖 Treinando {symbol}...")
        
        model = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            verbosity=0
        )
        
        model.fit(X, y)
        
        # Validação
        train_score = model.score(X, y)
        print(f"   ✅ Accuracy: {train_score*100:.2f}%")
        print(f"   Amostras: {len(X)}")
        
        return model
    
    def train_all(self):
        """Treina todos os pares"""
        print("\n" + "="*70)
        print("🚀 TREINAMENTO XGBOOST COM DADOS HISTÓRICOS")
        print("="*70)
        
        results = {}
        
        for symbol, csv_filename in CSV_FILES.items():
            filepath = DATA_DIR / csv_filename
            
            if not filepath.exists():
                print(f"\n❌ {symbol}: Arquivo não encontrado ({csv_filename})")
                continue
            
            # Carregar
            df = self.load_csv(symbol, filepath)
            if df is None:
                continue
            
            # Calcular features
            X, y = self.calculate_features_and_labels(df, symbol)
            if len(X) == 0:
                continue
            
            # Treinar
            model = self.train_model(symbol, X, y)
            if model is None:
                continue
            
            # Salvar
            model_path = MODELS_DIR / f"xgboost_{symbol}.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            print(f"   💾 Salvo em: {model_path}")
            
            results[symbol] = {
                'model': model,
                'samples': len(X),
                'accuracy': model.score(X, y)
            }
        
        # Resumo
        print("\n" + "="*70)
        print("📊 RESUMO DO TREINAMENTO")
        print("="*70)
        
        for symbol, data in results.items():
            print(f"\n{symbol}:")
            print(f"  Accuracy: {data['accuracy']*100:.2f}%")
            print(f"  Amostras: {data['samples']}")
            print(f"  Modelo: ✅ Salvo")
        
        print("\n" + "="*70)
        print("✅ TREINAMENTO CONCLUÍDO!")
        print("="*70)
        
        return results


if __name__ == "__main__":
    trainer = HistoricalTrainer()
    results = trainer.train_all()
    
    if results:
        print("\n🚀 Modelos prontos para usar!")
        print("   Reinicie o monitor para carregar novos modelos:")
        print("   killall -9 python3 && python3 server_mt5_http.py &")
        print("   sleep 2 && python3 monitor_mt5_real.py &")
    else:
        print("\n❌ Nenhum modelo foi treinado")
        sys.exit(1)
