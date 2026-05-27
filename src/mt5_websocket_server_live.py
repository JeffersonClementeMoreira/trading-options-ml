#!/usr/bin/env python3
"""
Servidor WebSocket Bridge - MODO DEMO (API CORRETA)
Gera dados simulados + calcula indicadores + envia via WebSocket
"""

import json
import asyncio
import numpy as np
import pickle
from datetime import datetime
from pathlib import Path

try:
    import websockets
    from websockets.asyncio.server import serve
except ImportError:
    try:
        from websockets.server import serve
    except ImportError:
        print("❌ websockets não instalado")
        exit(1)

# ═════════════════════════════════════════════════════════════════════════════

class IndicatorCalculator:
    """Calcula 25+ indicadores"""
    
    @staticmethod
    def calculate_all_indicators(closes, highs, lows, volumes):
        """Calcular todos os indicadores de forma rápida"""
        try:
            if len(closes) < 50:
                return None
            
            close = closes[-1]
            
            return {
                'rsi_14': float(np.random.uniform(30, 70)),  # Mock
                'rsi_7': float(np.random.uniform(30, 70)),
                'ema_12': float(closes[-1] * 0.99),
                'ema_26': float(closes[-1] * 0.98),
                'sma_20': float(np.mean(closes[-20:])),
                'sma_50': float(np.mean(closes[-50:])),
                'atr': float(np.mean([h-l for h,l in zip(highs[-14:], lows[-14:])])),
                'atr_pct': float(np.mean([h-l for h,l in zip(highs[-14:], lows[-14:])]) / close * 100),
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
                'roc_12': float((closes[-1] - closes[-12])/closes[-12]*100) if len(closes) > 12 else 0,
                'roc_6': float((closes[-1] - closes[-6])/closes[-6]*100) if len(closes) > 6 else 0,
                'candle_body': abs(closes[-1] - closes[0]),
                'upper_wick': float(np.random.uniform(0, close*0.01)),
                'lower_wick': float(np.random.uniform(0, close*0.01)),
            }
        except:
            return None


class DemoBridge:
    """Bridge Demo - Gera dados em tempo real"""
    
    def __init__(self):
        self.clients = set()
        self.models = {}
        self.indicator_calc = IndicatorCalculator()
        self.candle_data = {
            'GBPUSD': {'closes': [1.27], 'highs': [1.27], 'lows': [1.27], 'volumes': [50000]},
            'EURUSD': {'closes': [1.08], 'highs': [1.08], 'lows': [1.08], 'volumes': [50000]},
            'XAUUSD': {'closes': [2400], 'highs': [2400], 'lows': [2400], 'volumes': [50000]},
        }
        self.load_models()
    
    def load_models(self):
        """Carregar modelos XGBoost (opcional)"""
        models_dir = Path('/home/ubuntu/pessoal/options/src/models')
        for pair in ['GBPUSD', 'EURUSD', 'XAUUSD']:
            self.models[pair] = None  # Mock - usar scores aleatórios
    
    def generate_candle(self, symbol):
        """Gerar candle simulado"""
        data = self.candle_data[symbol]
        base = data['closes'][-1]
        
        # Ruído realista
        noise = np.random.normal(0, base * 0.0005)
        open_p = base + noise
        high = open_p + abs(np.random.normal(0, base * 0.001))
        low = open_p - abs(np.random.normal(0, base * 0.001))
        close = np.random.uniform(low, high)
        volume = np.random.randint(10000, 100000)
        
        return open_p, high, low, close, volume
    
    async def broadcast_candle(self, symbol):
        """Enviar candle com indicadores"""
        # Gerar novo candle
        open_p, high, low, close, volume = self.generate_candle(symbol)
        
        data = self.candle_data[symbol]
        data['closes'].append(close)
        data['highs'].append(high)
        data['lows'].append(low)
        data['volumes'].append(volume)
        
        # Manter últimos 100
        if len(data['closes']) > 100:
            data['closes'] = data['closes'][-100:]
            data['highs'] = data['highs'][-100:]
            data['lows'] = data['lows'][-100:]
            data['volumes'] = data['volumes'][-100:]
        
        # Calcular indicadores
        indicators = self.indicator_calc.calculate_all_indicators(
            np.array(data['closes']),
            np.array(data['highs']),
            np.array(data['lows']),
            np.array(data['volumes'])
        )
        
        if indicators is None:
            return
        
        # Score XGBoost (mock)
        score = np.random.uniform(0, 1)
        
        if score > 0.7:
            category = "HIGH"
            signal = "COMPRA" if np.random.random() > 0.5 else "VENDA"
        elif score > 0.5:
            category = "MEDIUM"
            signal = None
        else:
            category = "LOW"
            signal = None
        
        # Mensagem
        message = {
            'symbol': symbol,
            'time': datetime.now().isoformat(),
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
                'signal': signal
            }
        }
        
        json_msg = json.dumps(message, default=str)
        
        # Enviar a todos os clientes
        if self.clients:
            disconnected = set()
            for client in self.clients:
                try:
                    await client.send(json_msg)
                except Exception as e:
                    print(f"   ⚠️  Erro ao enviar: {e}")
                    disconnected.add(client)
            
            if disconnected:
                self.clients -= disconnected
                print(f"   Clientes removidos: {len(disconnected)}")
    
    async def handle_client(self, websocket):
        """Gerenciar cliente"""
        self.clients.add(websocket)
        print(f"✅ Cliente conectado (Total: {len(self.clients)})")
        
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
        except:
            pass
        finally:
            self.clients.discard(websocket)
            print(f"⛔ Cliente desconectado (Total: {len(self.clients)})")
    
    async def polling_loop(self):
        """Loop que envia candles a cada 10 segundos"""
        iteration = 0
        while True:
            try:
                iteration += 1
                for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
                    await self.broadcast_candle(symbol)
                
                if iteration % 3 == 0:
                    print(f"✅ Iteração #{iteration}: Candles enviados (Clientes: {len(self.clients)})")
                
                await asyncio.sleep(10)
            
            except Exception as e:
                print(f"❌ Erro: {str(e)}")
                await asyncio.sleep(5)
    
    async def run_server(self, host='localhost', port=9001):
        """Rodar servidor"""
        print(f"\n{'='*100}")
        print(f"📡 SERVIDOR WEBSOCKET - MODO DEMO (DADOS EM TEMPO REAL)")
        print(f"{'='*100}\n")
        
        print(f"🔌 Configuração:")
        print(f"├─ Host: {host}:{port}")
        print(f"├─ Pares: GBPUSD, EURUSD, XAUUSD")
        print(f"├─ Interval: 10 segundos")
        print(f"├─ Dados: Gerados simuladamente")
        print(f"└─ Status: Aguardando clientes\n")
        
        # Rodar polling loop em background
        polling_task = asyncio.create_task(self.polling_loop())
        
        # Rodar servidor WebSocket
        async with serve(self.handle_client, host, port):
            print(f"🚀 Servidor iniciado em ws://{host}:{port}\n")
            print(f"💡 Aguardando clientes...\n")
            
            try:
                await polling_task
            except KeyboardInterrupt:
                print(f"\n🛑 Servidor interrompido")


async def main():
    """Main"""
    bridge = DemoBridge()
    await bridge.run_server()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n🛑 Finalizado")
