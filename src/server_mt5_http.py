#!/usr/bin/env python3
"""
Servidor HTTP - Recebe dados do MT5 via HTTP POST
Envia via WebSocket para Monitor
"""

import json
import asyncio
import numpy as np
import pickle
import queue
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    import websockets
    from websockets.asyncio.server import serve
except ImportError:
    print("❌ websockets não instalado")
    exit(1)

# ═════════════════════════════════════════════════════════════════════════════

class IndicatorCalculator:
    """Calcula indicadores com dados reais do MT5"""
    
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
            
            # SMAs
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


class MT5HTTPServer:
    """Servidor que recebe dados do MT5 e envia via WebSocket"""
    
    def __init__(self):
        self.ws_clients = set()
        self.indicator_calc = IndicatorCalculator()
        self.candle_queue = queue.Queue()  # Fila para comunicação entre HTTP e WebSocket
        
        # Rastreamento de histórico por par
        self.candle_history = {
            'GBPUSD': {'closes': [], 'highs': [], 'lows': [], 'volumes': [], 'times': []},
            'EURUSD': {'closes': [], 'highs': [], 'lows': [], 'volumes': [], 'times': []},
            'XAUUSD': {'closes': [], 'highs': [], 'lows': [], 'volumes': [], 'times': []},
        }
        
        # Rastreamento de último datetime por par
        self.last_datetime = {
            'GBPUSD': None,
            'EURUSD': None,
            'XAUUSD': None,
        }
    
    def add_candle_to_history(self, symbol, datetime_obj, ohlc):
        """Adicionar candle ao histórico"""
        if symbol not in self.candle_history:
            return
        
        history = self.candle_history[symbol]
        history['closes'].append(ohlc['close'])
        history['highs'].append(ohlc['high'])
        history['lows'].append(ohlc['low'])
        history['volumes'].append(ohlc['volume'])
        history['times'].append(datetime_obj)
        
        # Manter últimos 100
        if len(history['closes']) > 100:
            history['closes'] = history['closes'][-100:]
            history['highs'] = history['highs'][-100:]
            history['lows'] = history['lows'][-100:]
            history['volumes'] = history['volumes'][-100:]
            history['times'] = history['times'][-100:]
    
    def process_mt5_data(self, data):
        """Processar dados recebidos do MT5"""
        try:
            symbol = data.get('symbol')
            datetime_str = data.get('datetime')
            
            # Parse datetime
            dt = datetime.fromisoformat(datetime_str)
            
            # OHLC
            ohlc = {
                'open': float(data.get('open')),
                'high': float(data.get('high')),
                'low': float(data.get('low')),
                'close': float(data.get('close')),
                'volume': int(data.get('volume', 0)),
            }
            
            # Adicionar ao histórico
            self.add_candle_to_history(symbol, dt, ohlc)
            
            # Só processar se temos histórico suficiente (50+ candles)
            history = self.candle_history[symbol]
            if len(history['closes']) < 50:
                return True  # Silenciosamente ignorar até ter 50
            
            # Verificar se é novo candle
            current_dt_str = dt.isoformat()
            last_dt_str = self.last_datetime.get(symbol)
            
            if current_dt_str != last_dt_str:
                # Novo candle!
                print(f"\n✅ NOVO CANDLE! {symbol} | {current_dt_str}")
                print(f"   Close: {ohlc['close']:.5f}")
                
                # Atualizar rastreamento
                self.last_datetime[symbol] = current_dt_str
                
                # Calcular indicadores
                indicators = self.indicator_calc.calculate_all_indicators(
                    np.array(history['closes']),
                    np.array(history['highs']),
                    np.array(history['lows']),
                    np.array(history['volumes'])
                )
                
                if indicators is None:
                    print(f"⚠️  Erro ao calcular indicadores para {symbol}")
                    return False
                
                # Tipo de candle
                if ohlc['close'] > ohlc['open']:
                    candle_type = "Alta"
                elif ohlc['close'] < ohlc['open']:
                    candle_type = "Queda"
                else:
                    candle_type = "Neutro"
                
                # Preparar mensagem
                candle = {
                    'symbol': symbol,
                    'datetime': current_dt_str,
                    'datetime_ts': dt.timestamp(),
                    'open': ohlc['open'],
                    'high': ohlc['high'],
                    'low': ohlc['low'],
                    'close': ohlc['close'],
                    'volume': ohlc['volume'],
                    'type': candle_type,
                    'indicators': indicators,
                }
                
                # Colocar na fila para enviar via WebSocket
                self.candle_queue.put(candle)
            
            return True
        
        except Exception as e:
            print(f"❌ Erro ao processar dados MT5: {e}")
            return False
    
    async def broadcast_candle(self, candle):
        """Enviar candle para todos os clientes WebSocket"""
        if not self.ws_clients:
            return
        
        message = json.dumps(candle)
        dead_clients = set()
        
        for client in self.ws_clients:
            try:
                await client.send(message)
            except Exception:
                dead_clients.add(client)
        
        self.ws_clients -= dead_clients
    
    async def ws_handler(self, websocket):
        """Handler de cliente WebSocket"""
        self.ws_clients.add(websocket)
        print(f"✅ Cliente WebSocket conectado ({len(self.ws_clients)} total)")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    action = data.get('action')
                    
                    if action == 'subscribe':
                        symbol = data.get('symbol')
                        print(f"✓ Inscrito em {symbol}")
                except Exception as e:
                    print(f"⚠️  Erro: {e}")
        except Exception:
            pass
        finally:
            self.ws_clients.discard(websocket)
            print(f"❌ Cliente desconectado ({len(self.ws_clients)} restantes)")
    
    async def start_websocket(self):
        """Iniciar servidor WebSocket"""
        async with serve(self.ws_handler, "0.0.0.0", 9001):
            print("🚀 WebSocket servidor em ws://0.0.0.0:9001")
            
            # Task para processar fila
            asyncio.create_task(self.process_queue())
            
            await asyncio.Future()  # run forever
    
    async def process_queue(self):
        """Processar fila de candles e enviar via WebSocket"""
        while True:
            try:
                # Checar fila (não-bloqueante)
                try:
                    candle = self.candle_queue.get_nowait()
                    await self.broadcast_candle(candle)
                except queue.Empty:
                    pass
                
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"❌ Erro na fila: {e}")
                await asyncio.sleep(1)


class HTTPRequestHandler(BaseHTTPRequestHandler):
    """Handler HTTP para receber dados do MT5"""
    
    # Referência ao servidor
    server_instance = None
    
    def do_POST(self):
        """Receber POST do MT5"""
        if self.path != "/mt5/candle":
            self.send_response(404)
            self.end_headers()
            return
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # Remove null terminators that MQL5 might add
            body = body.rstrip(b'\x00').strip()
            
            # Parse JSON (with error handling)
            try:
                data = json.loads(body.decode('utf-8', errors='ignore'))
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON decode failed: {e}")
                print(f"[ERROR] Body: {body}")
                self.send_response(400)
                self.end_headers()
                return
            
            # Processar dados
            if self.server_instance.process_mt5_data(data):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True}).encode())
            else:
                print(f"[ERROR] process_mt5_data returned False for {data.get('symbol')}")
                self.send_response(400)
                self.end_headers()
        
        except Exception as e:
            print(f"❌ Erro HTTP: {e}")
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suprimir logs de acesso"""
        pass


def run_http_server(server_instance, port=8765):
    """Rodar servidor HTTP em thread separada"""
    HTTPRequestHandler.server_instance = server_instance
    http_server = ThreadingHTTPServer(('0.0.0.0', port), HTTPRequestHandler)
    http_server.allow_reuse_address = True
    http_server.socket.setsockopt(1, 15, 1)  # SO_REUSEADDR
    print(f"🌐 HTTP servidor em http://0.0.0.0:{port}/mt5/candle")
    http_server.serve_forever()


# ═════════════════════════════════════════════════════════════════════════════

async def main():
    server = MT5HTTPServer()
    
    # Iniciar HTTP em thread
    import threading
    http_thread = threading.Thread(target=run_http_server, args=(server, 8765), daemon=True)
    http_thread.start()
    
    # Iniciar WebSocket
    await server.start_websocket()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         🚀 SERVIDOR MT5 HTTP/WEBSOCKET - DADOS REAIS 🚀                ║
║      (Recebe HTTP POST do MT5, envia via WebSocket para Monitor)         ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Servidor parado")
