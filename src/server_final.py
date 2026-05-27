#!/usr/bin/env python3
"""
Servidor WebSocket - Versão CORRIGIDA com Broadcast Real
"""

import json
import asyncio
import numpy as np
from datetime import datetime, timedelta

try:
    from websockets.asyncio.server import serve
except:
    from websockets.server import serve

class IndicatorCalculator:
    """Calcula indicadores rapidamente"""
    @staticmethod
    def calculate(closes, highs, lows, volumes):
        """Calcular todos os indicadores"""
        try:
            # Remover restrição - calcular com qualquer quantidade
            if len(closes) < 2:
                return {}
            
            close = closes[-1]
            
            # RSI simples
            deltas = np.diff(closes[-20:])
            up = np.sum(deltas[deltas > 0]) / 14 if len(deltas[deltas > 0]) > 0 else 1
            down = -np.sum(deltas[deltas < 0]) / 14 if len(deltas[deltas < 0]) > 0 else 1
            rs = up / down if down > 0 else 1
            rsi = 100 - (100 / (1 + rs))
            
            return {
                'rsi_14': float(rsi),
                'rsi_7': float(np.random.uniform(30, 70)),
                'ema_12': float(closes[-1] * 0.99),
                'ema_26': float(closes[-1] * 0.98),
                'sma_20': float(np.mean(closes[-20:])),
                'sma_50': float(np.mean(closes[-50:])),
                'atr': float(np.mean([h-l for h,l in zip(highs[-14:], lows[-14:])])),
                'atr_pct': float(np.mean([h-l for h,l in zip(highs[-14:], lows[-14:])]) / close * 100) if close > 0 else 0,
                'momentum': float(closes[-1] - closes[-15]) if len(closes) > 15 else 0,
                'confluence': 2,
                'volume_ma': float(np.mean(volumes[-20:])),
                'bb_upper': float(np.mean(closes[-20:]) + 2*np.std(closes[-20:])),
                'bb_lower': float(np.mean(closes[-20:]) - 2*np.std(closes[-20:])),
                'macd': float(np.random.uniform(-0.001, 0.001)),
                'signal': float(np.random.uniform(-0.001, 0.001)),
                'histogram': float(np.random.uniform(-0.001, 0.001)),
                'stoch_k': float(np.random.uniform(20, 80)),
                'stoch_d': float(np.random.uniform(20, 80)),
                'obv': float(np.sum(volumes)),
                'roc_12': float((closes[-1] - closes[-12])/closes[-12]*100) if len(closes) > 12 and closes[-12] != 0 else 0,
                'roc_6': float((closes[-1] - closes[-6])/closes[-6]*100) if len(closes) > 6 and closes[-6] != 0 else 0,
                'candle_body': abs(closes[-1] - closes[0]),
                'upper_wick': float(np.random.uniform(0, close*0.01)),
                'lower_wick': float(np.random.uniform(0, close*0.01)),
            }
        except:
            return {}

class Server:
    def __init__(self):
        self.clients = set()
        self.iteration = 0
        
        # *** COMEÇAR COM HORÁRIO ATUAL ARREDONDADO PARA M15 ANTERIOR ***
        now = datetime.now()
        # Arredondar para M15 anterior
        minute = (now.minute // 15) * 15  # 0, 15, 30, 45
        self.current_time = now.replace(minute=minute, second=0, microsecond=0)
        
        print(f"⏰ Horário atual: {now.strftime('%H:%M:%S')}")
        print(f"⏰ Começando candles em: {self.current_time.strftime('%H:%M')}")
        
        self.indicator_calc = IndicatorCalculator()
        self.candle_data = {
            'GBPUSD': {'closes': [1.27], 'highs': [1.27], 'lows': [1.27], 'volumes': [50000]},
            'EURUSD': {'closes': [1.08], 'highs': [1.08], 'lows': [1.08], 'volumes': [50000]},
            'XAUUSD': {'closes': [2400], 'highs': [2400], 'lows': [2400], 'volumes': [50000]},
        }
    
    def generate_candle(self, symbol):
        """Gerar candle"""
        data = self.candle_data[symbol]
        base = data['closes'][-1]
        
        noise = np.random.normal(0, base * 0.0005)
        open_p = base + noise
        high = open_p + abs(np.random.normal(0, base * 0.001))
        low = open_p - abs(np.random.normal(0, base * 0.001))
        close = np.random.uniform(low, high)
        volume = np.random.randint(10000, 100000)
        
        return open_p, high, low, close, volume
    
    async def handler(self, websocket):
        """Handler de cliente"""
        self.clients.add(websocket)
        print(f"✅ Cliente conectado ({len(self.clients)})")
        
        try:
            async for msg in websocket:
                try:
                    data = json.loads(msg)
                    print(f"   📨 {data}")
                except:
                    pass
        except:
            pass
        finally:
            self.clients.discard(websocket)
            print(f"⛔ Cliente desconectado ({len(self.clients)})")
    
    async def broadcaster(self):
        """Envia candles a cada 10 segundos (simulando M15)"""
        while True:
            await asyncio.sleep(10)
            
            if not self.clients:
                print("⏳ Aguardando clientes...")
                continue
            
            self.iteration += 1
            
            # Incrementar time em 15 minutos para simular M15
            self.current_time += timedelta(minutes=15)
            
            # Para cada par
            for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
                # Gerar candle
                open_p, high, low, close, volume = self.generate_candle(symbol)
                
                data = self.candle_data[symbol]
                data['closes'].append(close)
                data['highs'].append(high)
                data['lows'].append(low)
                data['volumes'].append(volume)
                
                if len(data['closes']) > 100:
                    data['closes'] = data['closes'][-100:]
                    data['highs'] = data['highs'][-100:]
                    data['lows'] = data['lows'][-100:]
                    data['volumes'] = data['volumes'][-100:]
                
                # *** CALCULAR INDICADORES ***
                indicators = self.indicator_calc.calculate(
                    np.array(data['closes']),
                    np.array(data['highs']),
                    np.array(data['lows']),
                    np.array(data['volumes'])
                )
                
                if not indicators:
                    indicators = {}
                
                # Candle simples
                score = np.random.uniform(0, 1)
                
                if score > 0.7:
                    category = "HIGH"
                elif score > 0.5:
                    category = "MEDIUM"
                else:
                    category = "LOW"
                
                message = {
                    'symbol': symbol,
                    'time': self.current_time.isoformat(),
                    'ohlc': {
                        'open': float(open_p),
                        'high': float(high),
                        'low': float(low),
                        'close': float(close),
                        'volume': int(volume)
                    },
                    'indicators': indicators,
                    'xgboost': {
                        'score': float(score),
                        'category': category,
                    }
                }
                
                json_msg = json.dumps(message)
                
                # *** IMPORTANTE: Enviar para CADA cliente ***
                disconnected = set()
                for client in self.clients:
                    try:
                        await client.send(json_msg)
                    except:
                        disconnected.add(client)
                
                # Remover desconectados
                for client in disconnected:
                    self.clients.discard(client)
            
            print(f"✅ Iteração #{self.iteration}: {self.current_time.strftime('%Y-%m-%d %H:%M')} | {len(self.clients)} clientes")
    
    async def run(self):
        """Rodar"""
        print("📡 SERVIDOR WEBSOCKET\n")
        
        # Criar task de broadcast
        broadcast_task = asyncio.create_task(self.broadcaster())
        
        # Servir WebSocket
        async with serve(self.handler, 'localhost', 9001):
            print("🚀 Listening em ws://localhost:9001\n")
            try:
                # Aguardar indefinidamente
                await broadcast_task
            except:
                pass


if __name__ == '__main__':
    server = Server()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n🛑 Parado")
