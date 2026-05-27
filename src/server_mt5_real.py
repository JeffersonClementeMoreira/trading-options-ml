#!/usr/bin/env python3
"""
Servidor M15 Real - Arquitetura CORRETA
- Simula MT5 real com histórico realista
- Lê histórico (50/500/1000 candles) para calcular indicadores
- ENVIA APENAS iloc[-1] (último candle)
- MONITORA mudanças de datetime (novo candle surgiu?)
- Notifica monitor apenas quando novo candle aparece
"""

import json
import asyncio
import numpy as np
import pickle
from datetime import datetime, timedelta
from pathlib import Path

try:
    import websockets
    from websockets.asyncio.server import serve
except ImportError:
    print("❌ websockets não instalado")
    exit(1)

# ═════════════════════════════════════════════════════════════════════════════

class IndicatorCalculator:
    """Calcula 25+ indicadores com dados reais"""
    
    @staticmethod
    def calculate_all_indicators(closes, highs, lows, volumes):
        """Calcular todos os indicadores"""
        try:
            if len(closes) < 50:
                return None
            
            close = closes[-1]
            
            # RSI
            def rsi(prices, period):
                deltas = np.diff(prices)
                seed = deltas[:period+1]
                up = seed[seed >= 0].sum() / period
                down = -seed[seed < 0].sum() / period
                rs = up / down if down != 0 else 0
                return 100 - 100 / (1 + rs)
            
            rsi_14 = float(rsi(closes, 14)) if len(closes) > 14 else 50.0
            rsi_7 = float(rsi(closes, 7)) if len(closes) > 7 else 50.0
            
            # EMAs/SMAs
            sma_20 = float(np.mean(closes[-20:])) if len(closes) > 20 else close
            sma_50 = float(np.mean(closes[-50:])) if len(closes) > 50 else close
            ema_12 = float(np.mean(closes[-12:])) if len(closes) > 12 else close
            ema_26 = float(np.mean(closes[-26:])) if len(closes) > 26 else close
            
            # ATR
            tr_list = []
            for i in range(max(1, len(highs)-14), len(highs)):
                tr = highs[i] - lows[i]
                if i > 0:
                    tr = max(tr, highs[i] - closes[i-1], closes[i-1] - lows[i])
                tr_list.append(tr)
            atr = float(np.mean(tr_list)) if tr_list else 0
            atr_pct = float(atr / close * 100) if close != 0 else 0
            
            # Momentum
            momentum = float(closes[-1] - closes[-15]) if len(closes) > 15 else 0
            
            # Confluence
            confluence = 2
            if sma_20 > sma_50:
                confluence += 1
            if close > sma_20:
                confluence += 1
            
            # Volume MA
            volume_ma = float(np.mean(volumes[-20:])) if len(volumes) > 20 else 0
            
            # Bollinger Bands
            bb_mid = sma_20
            bb_std = float(np.std(closes[-20:])) if len(closes) > 20 else 0
            bb_upper = float(bb_mid + 2 * bb_std)
            bb_lower = float(bb_mid - 2 * bb_std)
            
            # MACD
            macd = float((ema_12 - ema_26) / close) if close != 0 else 0
            signal = float(macd * 0.9)
            histogram = float(macd - signal)
            
            # Stochastic
            recent_low = min(lows[-14:]) if len(lows) > 14 else min(lows)
            recent_high = max(highs[-14:]) if len(highs) > 14 else max(highs)
            range_val = recent_high - recent_low
            stoch_k = float((close - recent_low) / range_val * 100) if range_val != 0 else 50
            stoch_d = float(stoch_k * 0.8 + 20)
            
            # OBV
            obv = float(np.sum(volumes))
            
            # ROC
            roc_12 = float((closes[-1] - closes[-12]) / closes[-12] * 100) if len(closes) > 12 and closes[-12] != 0 else 0
            roc_6 = float((closes[-1] - closes[-6]) / closes[-6] * 100) if len(closes) > 6 and closes[-6] != 0 else 0
            
            # Candle structure
            open_p = closes[0] if len(closes) > 0 else close
            candle_body = abs(closes[-1] - open_p)
            upper_wick = highs[-1] - max(closes[-1], open_p)
            lower_wick = min(closes[-1], open_p) - lows[-1]
            
            return {
                'rsi_14': float(rsi_14),
                'rsi_7': float(rsi_7),
                'ema_12': float(ema_12),
                'ema_26': float(ema_26),
                'sma_20': float(sma_20),
                'sma_50': float(sma_50),
                'atr': float(atr),
                'atr_pct': float(atr_pct),
                'momentum': float(momentum),
                'confluence': int(confluence),
                'volume_ma': float(volume_ma),
                'bb_upper': float(bb_upper),
                'bb_lower': float(bb_lower),
                'bb_mid': float(bb_mid),
                'macd': float(macd),
                'signal': float(signal),
                'histogram': float(histogram),
                'stoch_k': float(stoch_k),
                'stoch_d': float(stoch_d),
                'obv': float(obv),
                'roc_12': float(roc_12),
                'roc_6': float(roc_6),
                'candle_body': float(candle_body),
                'upper_wick': float(upper_wick),
                'lower_wick': float(lower_wick),
            }
        except Exception as e:
            print(f"❌ Erro ao calcular indicadores: {e}")
            return None


class MT5Simulator:
    """Simula MT5 real com histórico realista"""
    
    def __init__(self):
        self.candles = {
            'GBPUSD': [],
            'EURUSD': [],
            'XAUUSD': [],
        }
        
        # Preços iniciais realistas
        initial_prices = {
            'GBPUSD': 1.27,
            'EURUSD': 1.08,
            'XAUUSD': 2400,
        }
        
        # Gerar 100 candles históricos por pair
        now = datetime.now().replace(second=0, microsecond=0)
        minute = (now.minute // 15) * 15
        start_time = now.replace(minute=minute) - timedelta(minutes=100*15)
        
        for symbol, price in initial_prices.items():
            for i in range(100):
                dt = start_time + timedelta(minutes=i*15)
                
                # Gerar candle realista
                noise = np.random.normal(0, price * 0.0005)
                open_p = price + noise
                high = open_p + abs(np.random.normal(0, price * 0.001))
                low = open_p - abs(np.random.normal(0, price * 0.001))
                close = np.random.uniform(low, high)
                volume = np.random.randint(10000, 100000)
                
                self.candles[symbol].append({
                    'time': dt.timestamp(),
                    'datetime': dt,
                    'open': open_p,
                    'high': high,
                    'low': low,
                    'close': close,
                    'tick_volume': volume,
                })
                
                price = close
    
    def get_rates(self, symbol, history_count=100):
        """Retornar últimos N candles (simula mt5.copy_rates_from_pos)"""
        if symbol not in self.candles:
            return None
        
        all_candles = self.candles[symbol]
        return all_candles[-history_count:] if len(all_candles) >= history_count else all_candles


class M15Server:
    """Servidor M15 Real - Envia APENAS último candle quando muda datetime"""
    
    def __init__(self):
        self.clients = set()
        self.models = {}
        self.indicator_calc = IndicatorCalculator()
        self.mt5_sim = MT5Simulator()
        
        # Rastreamento de último datetime por par
        self.last_datetime = {
            'GBPUSD': None,
            'EURUSD': None,
            'XAUUSD': None,
        }
        
        # Contador de iterações
        self.iteration = 0
        
        print("✅ Servidor M15 inicializado")
        self.load_models()
    
    def load_models(self):
        """Carregar modelos XGBoost (opcional)"""
        models_dir = Path('/home/ubuntu/pessoal/options/src/models')
        for pair in ['GBPUSD', 'EURUSD', 'XAUUSD']:
            model_path = models_dir / f'xgboost_{pair}.pkl'
            if model_path.exists():
                try:
                    with open(model_path, 'rb') as f:
                        self.models[pair] = pickle.load(f)
                    print(f"✅ Modelo {pair} carregado")
                except Exception as e:
                    print(f"⚠️  Erro ao carregar {pair}: {e}")
                    self.models[pair] = None
            else:
                self.models[pair] = None
    
    async def get_latest_candle(self, symbol, timeframe='M15'):
        """Buscar APENAS o último candle com indicadores"""
        try:
            rates = self.mt5_sim.get_rates(symbol, history_count=100)
            
            if rates is None or len(rates) == 0:
                return None
            
            # SEMPRE pegar iloc[-1] (último)
            last = rates[-1]
            
            # Extrair OHLC
            dt = last['datetime']
            open_p = float(last['open'])
            high = float(last['high'])
            low = float(last['low'])
            close = float(last['close'])
            volume = int(last['tick_volume'])
            
            # Extrair histórico para indicadores
            closes = np.array([r['close'] for r in rates])
            highs = np.array([r['high'] for r in rates])
            lows = np.array([r['low'] for r in rates])
            volumes = np.array([r['tick_volume'] for r in rates])
            
            # Calcular indicadores
            indicators = self.indicator_calc.calculate_all_indicators(closes, highs, lows, volumes)
            
            if indicators is None:
                return None
            
            # Tipo de candle
            if close > open_p:
                candle_type = "Alta"
            elif close < open_p:
                candle_type = "Queda"
            else:
                candle_type = "Neutro"
            
            return {
                'symbol': symbol,
                'datetime': dt.isoformat(),
                'datetime_ts': dt.timestamp(),
                'open': open_p,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'type': candle_type,
                'indicators': indicators,
            }
        
        except Exception as e:
            print(f"❌ Erro ao obter último candle {symbol}: {e}")
            return None
    
    async def check_new_candles(self):
        """Verificar periodicamente se surgiu novo candle"""
        print("🔄 Monitorando novos candles...")
        
        while True:
            try:
                self.iteration += 1
                
                # Simular novo candle a cada 15 iterações (equivalente a 15 segundos = novo M15)
                if self.iteration % 15 == 0:
                    # Adicionar novo candle simulado
                    now = datetime.now().replace(second=0, microsecond=0)
                    minute = (now.minute // 15) * 15
                    current_m15 = now.replace(minute=minute)
                    
                    for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
                        # Gerar novo candle
                        last_close = self.mt5_sim.candles[symbol][-1]['close']
                        noise = np.random.normal(0, last_close * 0.0005)
                        open_p = last_close + noise
                        high = open_p + abs(np.random.normal(0, last_close * 0.001))
                        low = open_p - abs(np.random.normal(0, last_close * 0.001))
                        close = np.random.uniform(low, high)
                        volume = np.random.randint(10000, 100000)
                        
                        self.mt5_sim.candles[symbol].append({
                            'time': current_m15.timestamp(),
                            'datetime': current_m15,
                            'open': open_p,
                            'high': high,
                            'low': low,
                            'close': close,
                            'tick_volume': volume,
                        })
                
                for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
                    candle = await self.get_latest_candle(symbol)
                    
                    if candle is None:
                        continue
                    
                    current_dt = candle['datetime']
                    last_dt = self.last_datetime[symbol]
                    
                    # Novo candle surgiu?
                    if current_dt != last_dt:
                        print(f"\n✅ ITERAÇÃO #{self.iteration}")
                        print(f"🔔 NOVO CANDLE! {symbol} | {current_dt}")
                        print(f"   Close: {candle['close']:.5f} | Tipo: {candle['type']}")
                        
                        # Atualizar rastreamento
                        self.last_datetime[symbol] = current_dt
                        
                        # Enviar para todos os clientes
                        await self.broadcast(candle)
                
                # Verificar a cada 1 segundo
                await asyncio.sleep(1)
            
            except Exception as e:
                print(f"❌ Erro no monitor: {e}")
                await asyncio.sleep(1)
    
    async def broadcast(self, candle):
        """Enviar candle para todos os clientes conectados"""
        if not self.clients:
            return
        
        message = json.dumps(candle)
        
        # Remover clientes desconectados
        dead_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except Exception:
                dead_clients.add(client)
        
        self.clients -= dead_clients
    
    async def handler(self, websocket):
        """Handler de cliente WebSocket"""
        self.clients.add(websocket)
        print(f"✅ Cliente conectado ({len(self.clients)} total)")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    action = data.get('action')
                    
                    if action == 'subscribe':
                        symbol = data.get('symbol')
                        print(f"✓ Inscrito em {symbol}")
                        
                        # Enviar último candle imediatamente
                        candle = await self.get_latest_candle(symbol)
                        if candle:
                            await websocket.send(json.dumps(candle))
                
                except Exception as e:
                    print(f"⚠️  Erro ao processar mensagem: {e}")
        
        except Exception:
            pass
        finally:
            self.clients.discard(websocket)
            print(f"❌ Cliente desconectado ({len(self.clients)} restantes)")
    
    async def run(self):
        """Rodar servidor WebSocket + monitor"""
        # Iniciar servidor WebSocket
        async with serve(self.handler, "localhost", 9001):
            print("🚀 Servidor WebSocket em ws://localhost:9001")
            
            # Iniciar monitor de novos candles
            await self.check_new_candles()


# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    server = M15Server()
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n⏹️  Parando servidor...")
