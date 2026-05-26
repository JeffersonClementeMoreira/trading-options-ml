#!/usr/bin/env python3
"""
Servidor WebSocket Bridge - MODO DEMO/TESTE
Fornece dados simulados via WebSocket para testes
Em produção real, conectar ao MT5
"""

import json
import asyncio
import pandas as pd
import numpy as np
import pickle
from datetime import datetime, timedelta
from pathlib import Path

try:
    import websockets
    from websockets.server import serve
except ImportError:
    print("❌ websockets não instalado")
    exit(1)

# ═════════════════════════════════════════════════════════════════════════════

class IndicatorCalculator:
    """Calcula indicadores"""
    
    @staticmethod
    def calculate_rsi(series, period=14):
        if len(series) < period:
            return 50.0
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return float(100 - (100 / (1 + rs.iloc[-1])))
    
    @staticmethod
    def calculate_macd(series, fast=12, slow=26, signal=9):
        if len(series) < slow:
            return 0.0, 0.0, 0.0
        ema_fast = series.ewm(span=fast).mean()
        ema_slow = series.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return float(macd.iloc[-1]), float(signal_line.iloc[-1]), float(histogram.iloc[-1])
    
    @staticmethod
    def calculate_atr(high, low, close, period=14):
        if len(high) < period:
            return 0.0
        tr = pd.concat([
            high - low,
            abs(high - close.shift(1)),
            abs(low - close.shift(1))
        ], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return float(atr.iloc[-1])
    
    @staticmethod
    def calculate_ema(series, period):
        if len(series) < period:
            return float(series.iloc[-1])
        return float(series.ewm(span=period).mean().iloc[-1])
    
    @staticmethod
    def calculate_sma(series, period):
        if len(series) < period:
            return float(series.iloc[-1])
        return float(series.rolling(window=period).mean().iloc[-1])
    
    @staticmethod
    def calculate_roc(series, period=12):
        if len(series) < period:
            return 0.0
        return float(((series.iloc[-1] - series.iloc[-period]) / series.iloc[-period]) * 100)
    
    @staticmethod
    def calculate_stochastic(high, low, close, period=14):
        if len(high) < period:
            return 50.0, 50.0
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k = ((close - lowest_low) / (highest_high - lowest_low + 0.0001)) * 100
        d = k.rolling(window=3).mean()
        return float(k.iloc[-1]), float(d.iloc[-1])
    
    @staticmethod
    def calculate_obv(close, volume):
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return float(obv.iloc[-1])
    
    @staticmethod
    def calculate_smc_confluence(df):
        """Calcular confluência SMC"""
        if len(df) < 20:
            return 0
        
        last = df.iloc[-1]
        high_20 = df['high'].tail(20).max()
        low_20 = df['low'].tail(20).min()
        
        atr = IndicatorCalculator.calculate_atr(df['high'], df['low'], df['close'])
        atr_pct = (atr / last['close']) * 100
        atr_75th = df['close'].pct_change().std() * 100 * 0.75
        
        confluence = 0
        
        if last['high'] >= high_20:
            confluence += 1
        if last['low'] <= low_20:
            confluence += 1
        if atr_pct > atr_75th:
            confluence += 1
        
        body_ratio = (abs(last['close'] - last['open']) / (last['high'] - last['low'] + 0.0001))
        if body_ratio < 0.25:
            confluence += 1
        
        return confluence
    
    def calculate_all_indicators(self, df):
        """Calcular todos os indicadores"""
        if len(df) < 50:
            return None
        
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        indicators = {
            'rsi_14': self.calculate_rsi(close, 14),
            'rsi_7': self.calculate_rsi(close, 7),
            'macd': self.calculate_macd(close)[0],
            'macd_signal': self.calculate_macd(close)[1],
            'macd_histogram': self.calculate_macd(close)[2],
            'bb_upper': float(close.rolling(20).mean().iloc[-1] + close.rolling(20).std().iloc[-1] * 2),
            'bb_middle': float(close.rolling(20).mean().iloc[-1]),
            'bb_lower': float(close.rolling(20).mean().iloc[-1] - close.rolling(20).std().iloc[-1] * 2),
            'atr': self.calculate_atr(high, low, close),
            'atr_pct': (self.calculate_atr(high, low, close) / close.iloc[-1]) * 100,
            'atr_ratio': (self.calculate_atr(high, low, close) / close.iloc[-1]) * 100,
            'ema_12': self.calculate_ema(close, 12),
            'ema_26': self.calculate_ema(close, 26),
            'sma_20': self.calculate_sma(close, 20),
            'sma_50': self.calculate_sma(close, 50),
            'sma_trend': ((self.calculate_sma(close, 20) - self.calculate_sma(close, 50)) / self.calculate_sma(close, 50)) * 100,
            'momentum': float(close.iloc[-1] - close.iloc[-10]) if len(close) > 10 else 0.0,
            'roc_12': self.calculate_roc(close, 12),
            'roc_6': self.calculate_roc(close, 6),
            'stoch_k': self.calculate_stochastic(high, low, close)[0],
            'stoch_d': self.calculate_stochastic(high, low, close)[1],
            'obv': self.calculate_obv(close, volume),
            'volume_ratio': float(volume.iloc[-1] / volume.tail(20).mean()) if len(volume) >= 20 else 1.0,
            'body': float(abs(close.iloc[-1] - df['open'].iloc[-1])),
            'upper_wick': float(high.iloc[-1] - max(close.iloc[-1], df['open'].iloc[-1])),
            'lower_wick': float(min(close.iloc[-1], df['open'].iloc[-1]) - low.iloc[-1]),
            'high_low_ratio': float((high.iloc[-1] - max(close.iloc[-1], df['open'].iloc[-1])) / (min(close.iloc[-1], df['open'].iloc[-1]) - low.iloc[-1] + 0.0001)),
            'confluence': self.calculate_smc_confluence(df),
        }
        
        return indicators


class DemoBridge:
    """Bridge Demo que simula dados para testes"""
    
    def __init__(self):
        self.clients = set()
        self.indicator_calc = IndicatorCalculator()
        self.models = {}
        self.dados = {}
        self.current_index = {}
        
        self.load_models()
        self.load_data()
    
    def load_models(self):
        """Carregar modelos XGBoost"""
        models_dir = Path('../models')
        
        for par in ['GBPUSD', 'EURUSD', 'XAUUSD']:
            model_file = models_dir / f'xgboost_{par.lower()}.pkl'
            if model_file.exists():
                try:
                    with open(model_file, 'rb') as f:
                        self.models[par] = pickle.load(f)
                    print(f"✅ Modelo XGBoost: {par}")
                except Exception as e:
                    print(f"⚠️  Modelo {par}: {str(e)}")
    
    def load_data(self):
        """Carregar dados históricos para simular"""
        data_files = {
            'GBPUSD': '../backtest_results/gbpusd_signals_completo.csv',
            'EURUSD': '../backtest_results/eurusd_signals_completo.csv',
            'XAUUSD': '../backtest_results/xauusd_signals_completo.csv'
        }
        
        for symbol, filepath in data_files.items():
            try:
                df = pd.read_csv(filepath)
                
                if 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df.set_index('datetime', inplace=True)
                
                self.dados[symbol] = df.sort_index()
                self.current_index[symbol] = len(df) - 100  # Começar 100 candles antes do final
                
                print(f"✅ Dados carregados: {symbol}")
            except Exception as e:
                print(f"⚠️  Erro ao carregar {symbol}: {str(e)}")
    
    def get_xgboost_score(self, symbol, indicators):
        """Obter score XGBoost"""
        if symbol not in self.models:
            return 0.5, "SEM_MODELO"
        
        try:
            feature_cols = ['confluence', 'atr_pct', 'rsi_14', 'macd', 'macd_signal', 
                           'macd_histogram', 'bb_upper', 'bb_middle', 'bb_lower',
                           'atr_ratio', 'ema_12', 'ema_26', 'sma_20', 'sma_50',
                           'momentum', 'roc_12', 'stoch_k', 'stoch_d', 'obv', 
                           'volume_ratio', 'body', 'upper_wick', 'lower_wick',
                           'high_low_ratio', 'sma_trend', 'atr']
            
            feature_values = []
            for feat in feature_cols:
                feature_values.append(indicators.get(feat, 0.0))
            
            X = np.array([feature_values])
            proba = self.models[symbol].predict_proba(X)[0][1]
            
            if proba > 0.7:
                category = "HIGH"
            elif proba > 0.5:
                category = "MEDIUM"
            else:
                category = "LOW"
            
            return float(proba), category
        
        except Exception as e:
            print(f"⚠️  Erro: {str(e)}")
            return 0.5, "ERRO"
    
    async def broadcast_candle(self, symbol):
        """Enviar candle com indicadores"""
        if not self.clients:
            return
        
        df = self.dados.get(symbol)
        
        if df is None or self.current_index[symbol] >= len(df):
            return
        
        # Pegar dados para calcular indicadores
        start_idx = max(0, self.current_index[symbol] - 50)
        end_idx = self.current_index[symbol] + 1
        
        df_calc = df.iloc[start_idx:end_idx]
        
        last = df_calc.iloc[-1]
        
        # Calcular indicadores
        indicators = self.indicator_calc.calculate_all_indicators(df_calc)
        
        if indicators is None:
            return
        
        # Score XGBoost
        score, category = self.get_xgboost_score(symbol, indicators)
        
        # Sinal SMC
        signal = None
        if indicators['confluence'] >= 2:
            if last['high'] >= df_calc['high'].tail(20).max():
                signal = "VENDA"
            elif last['low'] <= df_calc['low'].tail(20).min():
                signal = "COMPRA"
        
        # Montar JSON
        message = {
            'symbol': symbol,
            'time': str(last.name),  # datetime
            'ohlc': {
                'open': float(last.get('open', 0)),
                'high': float(last.get('high', 0)),
                'low': float(last.get('low', 0)),
                'close': float(last.get('close', 0)),
                'volume': int(last.get('volume', 0))
            },
            'indicators': indicators,
            'xgboost': {
                'score': score,
                'category': category,
                'signal': signal
            }
        }
        
        json_msg = json.dumps(message, default=str)
        
        if self.clients:
            await asyncio.gather(
                *[client.send(json_msg) for client in self.clients],
                return_exceptions=True
            )
    
    async def handle_client(self, websocket, path):
        """Gerenciar cliente"""
        self.clients.add(websocket)
        print(f"✅ Cliente conectado")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    action = data.get('action')
                    
                    if action == 'subscribe':
                        symbol = data.get('symbol')
                        print(f"   → {symbol} inscrito")
                
                except:
                    pass
        
        finally:
            self.clients.discard(websocket)
            print(f"⛔ Cliente desconectado")
    
    async def polling_loop(self):
        """Loop que simula novos candles"""
        while True:
            try:
                for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
                    await self.broadcast_candle(symbol)
                    
                    # Avançar índice
                    df = self.dados.get(symbol)
                    if df is not None:
                        self.current_index[symbol] += 1
                
                # Simular novo candle a cada 10 segundos
                await asyncio.sleep(10)
            
            except Exception as e:
                print(f"❌ Erro: {str(e)}")
                await asyncio.sleep(5)
    
    async def run_server(self, host='localhost', port=9001):
        """Rodar servidor"""
        print(f"\n{'='*100}")
        print(f"📡 SERVIDOR WEBSOCKET - MODO DEMO")
        print(f"{'='*100}\n")
        
        print(f"🔌 Configuração:")
        print(f"├─ Host: {host}:{port}")
        print(f"├─ URL: ws://{host}:{port}")
        print(f"├─ Modo: DEMO (dados históricos)")
        print(f"├─ Modelos XGBoost: {len(self.models)} carregados")
        print(f"└─ Pares: GBPUSD, EURUSD, XAUUSD\n")
        
        async with serve(self.handle_client, host, port):
            print(f"✅ Servidor aguardando conexões...\n")
            
            await self.polling_loop()


async def main():
    """Main"""
    bridge = DemoBridge()
    await bridge.run_server('localhost', 9001)


if __name__ == '__main__':
    print(f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║  📡 SERVIDOR WEBSOCKET - MODO DEMO (para testes)                              ║
╚════════════════════════════════════════════════════════════════════════════════╝

<b>MODO DEMO:</b>
- Usa dados históricos dos backtest
- Simula novos candles a cada 10 segundos
- Calcula indicadores e XGBoost em tempo real
- Pronto para testar o Monitor Telegram

<b>MODO PRODUÇÃO (quando conectar ao MT5 real):</b>
- MT5 WebSocket Server (Windows com MT5 Terminal)
- Dados em tempo real da corretora
- Mesmo script, apenas conexão diferente

Use:
1. Terminal 1: python3 mt5_websocket_server_demo.py
2. Terminal 2: python3 live_websocket_monitor.py

Tanto o Demo quanto o Produção usam a mesma interface WebSocket!
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n⛔ Servidor parado")
