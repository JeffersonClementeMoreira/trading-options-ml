#!/usr/bin/env python3
"""
Servidor WebSocket - Bridge MT5
Conecta ao MT5, calcula todos os indicadores, avalia XGBoost e fornece via WebSocket
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
    print("   pip install websockets")
    exit(1)

try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    print("⚠️  MetaTrader5 não instalado")
    HAS_MT5 = False

# ═════════════════════════════════════════════════════════════════════════════

class IndicatorCalculator:
    """Calcula todos os indicadores"""
    
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
    def calculate_bollinger_bands(series, period=20, std_dev=2):
        if len(series) < period:
            return float(series.iloc[-1]), float(series.iloc[-1]), float(series.iloc[-1])
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        middle = sma
        return float(upper.iloc[-1]), float(middle.iloc[-1]), float(lower.iloc[-1])
    
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
        
        # Tocou extremo?
        if last['high'] >= high_20:
            confluence += 1
        if last['low'] <= low_20:
            confluence += 1
        
        # ATR elevado?
        if atr_pct > atr_75th:
            confluence += 1
        
        # Corpo pequeno?
        body_ratio = (abs(last['close'] - last['open']) / (last['high'] - last['low'] + 0.0001))
        if body_ratio < 0.25:
            confluence += 1
        
        return confluence
    
    def calculate_all_indicators(self, df):
        """Calcular todos os 25+ indicadores"""
        if len(df) < 50:
            return None
        
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        indicators = {
            # Momentum
            'rsi_14': self.calculate_rsi(close, 14),
            'rsi_7': self.calculate_rsi(close, 7),
            
            # MACD
            'macd': self.calculate_macd(close)[0],
            'macd_signal': self.calculate_macd(close)[1],
            'macd_histogram': self.calculate_macd(close)[2],
            
            # Bollinger Bands
            'bb_upper': self.calculate_bollinger_bands(close)[0],
            'bb_middle': self.calculate_bollinger_bands(close)[1],
            'bb_lower': self.calculate_bollinger_bands(close)[2],
            
            # ATR
            'atr': self.calculate_atr(high, low, close),
            'atr_pct': (self.calculate_atr(high, low, close) / close.iloc[-1]) * 100,
            'atr_ratio': (self.calculate_atr(high, low, close) / close.iloc[-1]) * 100,
            
            # EMAs
            'ema_12': self.calculate_ema(close, 12),
            'ema_26': self.calculate_ema(close, 26),
            
            # SMAs
            'sma_20': self.calculate_sma(close, 20),
            'sma_50': self.calculate_sma(close, 50),
            
            # Trend
            'sma_trend': ((self.calculate_sma(close, 20) - self.calculate_sma(close, 50)) / self.calculate_sma(close, 50)) * 100,
            
            # Momentum
            'momentum': float(close.iloc[-1] - close.iloc[-10]) if len(close) > 10 else 0.0,
            'roc_12': self.calculate_roc(close, 12),
            'roc_6': self.calculate_roc(close, 6),
            
            # Stochastic
            'stoch_k': self.calculate_stochastic(high, low, close)[0],
            'stoch_d': self.calculate_stochastic(high, low, close)[1],
            
            # Volume
            'obv': self.calculate_obv(close, volume),
            'volume_ratio': float(volume.iloc[-1] / volume.tail(20).mean()) if len(volume) >= 20 else 1.0,
            
            # Candle patterns
            'body': float(abs(close.iloc[-1] - df['open'].iloc[-1])),
            'upper_wick': float(high.iloc[-1] - max(close.iloc[-1], df['open'].iloc[-1])),
            'lower_wick': float(min(close.iloc[-1], df['open'].iloc[-1]) - low.iloc[-1]),
            'high_low_ratio': float((high.iloc[-1] - max(close.iloc[-1], df['open'].iloc[-1])) / (min(close.iloc[-1], df['open'].iloc[-1]) - low.iloc[-1] + 0.0001)),
            
            # SMC
            'confluence': self.calculate_smc_confluence(df),
        }
        
        return indicators


class MT5Bridge:
    """Bridge entre MT5 e WebSocket"""
    
    def __init__(self):
        self.clients = set()
        self.last_candles = {}
        self.mt5_connected = False
        self.indicator_calc = IndicatorCalculator()
        self.models = {}
        
        if HAS_MT5:
            self.connect_mt5()
        
        self.load_models()
    
    def connect_mt5(self):
        """Conectar ao MT5"""
        try:
            if not mt5.initialize():
                print(f"❌ Erro ao inicializar MT5: {mt5.last_error()}")
                return False
            
            print(f"✅ Conectado ao MT5")
            self.mt5_connected = True
            return True
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return False
    
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
            
            # Categorizar
            if proba > 0.7:
                category = "HIGH"
            elif proba > 0.5:
                category = "MEDIUM"
            else:
                category = "LOW"
            
            return float(proba), category
        
        except Exception as e:
            print(f"⚠️  Erro score {symbol}: {str(e)}")
            return 0.5, "ERRO"
    
    def get_latest_candles(self, symbol, timeframe=None, count=100):
        """Pegar candles mais recentes do MT5"""
        if not self.mt5_connected:
            return None
        
        if timeframe is None:
            timeframe = mt5.TIMEFRAME_M15
        
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                print(f"❌ Nenhum dado para {symbol}")
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.rename(columns={
                'tick_volume': 'volume',
                'real_volume': 'real_volume'
            })
            
            return df
        
        except Exception as e:
            print(f"❌ Erro ao buscar {symbol}: {str(e)}")
            return None
    
    async def broadcast_candle(self, symbol, df):
        """Enviar candle com indicadores para todos os clientes"""
        if not self.clients or len(df) < 50:
            return
        
        last = df.iloc[-1]
        
        # Calcular todos os indicadores
        indicators = self.indicator_calc.calculate_all_indicators(df)
        
        if indicators is None:
            return
        
        # Obter score XGBoost
        score, category = self.get_xgboost_score(symbol, indicators)
        
        # Detectar sinal SMC
        signal = None
        if indicators['confluence'] >= 2:
            if last['high'] >= df['high'].tail(20).max():
                signal = "VENDA"
            elif last['low'] <= df['low'].tail(20).min():
                signal = "COMPRA"
        
        # Montar JSON
        message = {
            'symbol': symbol,
            'time': last['time'].isoformat(),
            'ohlc': {
                'open': float(last['open']),
                'high': float(last['high']),
                'low': float(last['low']),
                'close': float(last['close']),
                'volume': int(last['volume'])
            },
            'indicators': indicators,
            'xgboost': {
                'score': score,
                'category': category,
                'signal': signal
            }
        }
        
        json_msg = json.dumps(message, default=str)
        
        # Enviar para clientes
        if self.clients:
            await asyncio.gather(
                *[client.send(json_msg) for client in self.clients],
                return_exceptions=True
            )
    
    async def handle_client(self, websocket, path):
        """Gerenciar cliente WebSocket"""
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0]
        
        print(f"✅ Cliente conectado: {client_ip}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    action = data.get('action')
                    
                    if action == 'subscribe':
                        symbol = data.get('symbol')
                        print(f"   → {symbol} inscrito")
                
                except json.JSONDecodeError:
                    pass
        
        except asyncio.CancelledError:
            pass
        
        finally:
            self.clients.discard(websocket)
            print(f"⛔ Cliente desconectado: {client_ip}")
    
    async def polling_loop(self):
        """Loop de polling do MT5"""
        if not self.mt5_connected:
            print("⚠️  MT5 não conectado, aguardando...")
            return
        
        symbols = ['GBPUSD', 'EURUSD', 'XAUUSD']
        
        while True:
            try:
                for symbol in symbols:
                    df = self.get_latest_candles(symbol, mt5.TIMEFRAME_M15, 100)
                    
                    if df is not None and len(df) > 0:
                        last_time = df.iloc[-1]['time']
                        
                        if symbol not in self.last_candles or self.last_candles[symbol] != last_time:
                            self.last_candles[symbol] = last_time
                            
                            print(f"📤 {symbol} {last_time.strftime('%H:%M:%S')} → Broadcasting")
                            
                            await self.broadcast_candle(symbol, df)
                
                await asyncio.sleep(10)
            
            except Exception as e:
                print(f"❌ Erro: {str(e)}")
                await asyncio.sleep(5)
    
    async def run_server(self, host='localhost', port=9001):
        """Rodar servidor WebSocket"""
        print(f"\n{'='*100}")
        print(f"📡 SERVIDOR WEBSOCKET - BRIDGE MT5 COM INDICADORES")
        print(f"{'='*100}\n")
        
        print(f"🔌 Configuração:")
        print(f"├─ Host: {host}:{port}")
        print(f"├─ URL: ws://{host}:{port}")
        print(f"├─ MT5: {'✅ Conectado' if self.mt5_connected else '❌ Desconectado'}")
        print(f"├─ Modelos XGBoost: {len(self.models)} carregados")
        print(f"└─ Indicadores: 25+ técnicos\n")
        
        async with serve(self.handle_client, host, port):
            print(f"✅ Servidor aguardando conexões...\n")
            
            if self.mt5_connected:
                await self.polling_loop()
            else:
                await asyncio.Event().wait()


async def main():
    """Main"""
    bridge = MT5Bridge()
    await bridge.run_server('localhost', 9001)


if __name__ == '__main__':
    print(f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║  📡 SERVIDOR WEBSOCKET - BRIDGE MT5 COM INDICADORES + XGBOOST                 ║
╚════════════════════════════════════════════════════════════════════════════════╝

Este servidor fornece dados do MT5 via WebSocket com:
✅ OHLC em tempo real
✅ 25+ indicadores técnicos calculados
✅ SMC (confluence) calculado
✅ Score XGBoost (HIGH/MEDIUM/LOW)
✅ Sinal (COMPRA/VENDA) detectado

JSON enviado ao monitor:
{{
  "symbol": "GBPUSD",
  "time": "2026-05-26T13:45:00",
  "ohlc": {{"open": 1.25, "high": 1.26, "low": 1.24, "close": 1.255, "volume": 1000}},
  "indicators": {{
    "rsi_14": 65.2,
    "macd": 0.00123,
    "bb_upper": 1.26,
    "ema_12": 1.251,
    ...25+ indicadores
  }},
  "xgboost": {{
    "score": 0.87,
    "category": "HIGH",
    "signal": "COMPRA"
  }}
}}

Para usar:
1. python3 mt5_websocket_server.py  (neste terminal)
2. python3 live_websocket_monitor.py (outro terminal)
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n⛔ Servidor parado")

# ═════════════════════════════════════════════════════════════════════════════

class MT5Bridge:
    """Bridge entre MT5 e WebSocket"""
    
    def __init__(self):
        self.clients = set()
        self.last_candles = {}
        self.mt5_connected = False
        
        if HAS_MT5:
            self.connect_mt5()
    
    def connect_mt5(self):
        """Conectar ao MT5"""
        try:
            if not mt5.initialize():
                print(f"❌ Erro ao inicializar MT5: {mt5.last_error()}")
                return False
            
            print(f"✅ Conectado ao MT5")
            self.mt5_connected = True
            return True
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return False
    
    def get_latest_candles(self, symbol, timeframe=mt5.TIMEFRAME_M15, count=100):
        """Pegar candles mais recentes do MT5"""
        if not self.mt5_connected:
            print(f"⚠️  MT5 não conectado")
            return None
        
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                print(f"❌ Nenhum dado para {symbol}")
                return None
            
            # Converter para DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            return df
        
        except Exception as e:
            print(f"❌ Erro ao buscar {symbol}: {str(e)}")
            return None
    
    async def broadcast_candle(self, symbol, candle_data):
        """Enviar candle para todos os clientes conectados"""
        if not self.clients:
            return
        
        message = json.dumps({
            'symbol': symbol,
            'time': candle_data['time'].isoformat(),
            'open': float(candle_data['open']),
            'high': float(candle_data['high']),
            'low': float(candle_data['low']),
            'close': float(candle_data['close']),
            'volume': int(candle_data['tick_volume'])
        })
        
        # Enviar para todos os clientes
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )
    
    async def handle_client(self, websocket, path):
        """Gerenciar cliente WebSocket"""
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0]
        
        print(f"✅ Cliente conectado: {client_ip}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    action = data.get('action')
                    
                    if action == 'subscribe':
                        symbol = data.get('symbol')
                        print(f"   → {symbol} inscrito")
                        
                        # Enviar histórico
                        if self.mt5_connected:
                            df = self.get_latest_candles(symbol)
                            if df is not None:
                                for idx, row in df.tail(50).iterrows():
                                    await self.broadcast_candle(symbol, row)
                    
                    elif action == 'unsubscribe':
                        symbol = data.get('symbol')
                        print(f"   → {symbol} desinscrição")
                
                except json.JSONDecodeError:
                    print(f"⚠️  Mensagem inválida")
        
        except asyncio.CancelledError:
            pass
        
        finally:
            self.clients.discard(websocket)
            print(f"⛔ Cliente desconectado: {client_ip}")
    
    async def polling_loop(self):
        """Loop de polling do MT5"""
        if not self.mt5_connected:
            return
        
        symbols = ['GBPUSD', 'EURUSD', 'XAUUSD']
        
        while True:
            try:
                for symbol in symbols:
                    df = self.get_latest_candles(symbol, mt5.TIMEFRAME_M15, 1)
                    
                    if df is not None and len(df) > 0:
                        last_candle = df.iloc[-1]
                        last_time = last_candle['time']
                        
                        # Se é novo candle
                        if symbol not in self.last_candles or self.last_candles[symbol] != last_time:
                            self.last_candles[symbol] = last_time
                            
                            print(f"📤 {symbol} {last_time.strftime('%H:%M:%S')}")
                            
                            await self.broadcast_candle(symbol, last_candle)
                
                # Checar a cada 10 segundos
                await asyncio.sleep(10)
            
            except Exception as e:
                print(f"❌ Erro no loop: {str(e)}")
                await asyncio.sleep(5)
    
    async def run_server(self, host='localhost', port=9001):
        """Rodar servidor WebSocket"""
        print(f"\n{'='*100}")
        print(f"📡 SERVIDOR WEBSOCKET - BRIDGE MT5")
        print(f"{'='*100}\n")
        
        print(f"🔌 Iniciando servidor:")
        print(f"├─ Host: {host}")
        print(f"├─ Port: {port}")
        print(f"├─ URL: ws://{host}:{port}")
        print(f"└─ MT5: {'✅ Conectado' if self.mt5_connected else '❌ Desconectado'}\n")
        
        async with serve(self.handle_client, host, port):
            print(f"✅ Servidor aguardando conexões...\n")
            
            if self.mt5_connected:
                # Rodar polling em paralelo
                await self.polling_loop()
            else:
                # Só aguardar conexões
                await asyncio.Event().wait()


async def main():
    """Main"""
    bridge = MT5Bridge()
    await bridge.run_server('localhost', 9001)


if __name__ == '__main__':
    print(f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║    📡 SERVIDOR WEBSOCKET - BRIDGE MT5                                         ║
╚════════════════════════════════════════════════════════════════════════════════╝

Este servidor funciona como intermediário entre MT5 e o Monitor.

⚙️  Como usar:
1. Instale MetaTrader5: pip install MetaTrader5
2. Inicie o MT5 Terminal
3. Execute este servidor: python3 mt5_websocket_server.py
4. Em outro terminal, inicie o monitor: python3 live_websocket_monitor.py

📡 O servidor irá:
├─ Conectar ao MT5 automaticamente
├─ Buscar candles M15 a cada 10 segundos
└─ Enviar via WebSocket para clientes

📊 Clientes podem se inscrever e receber dados em tempo real
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n⛔ Servidor parado pelo usuário")
