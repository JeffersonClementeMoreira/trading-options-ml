#!/usr/bin/env python3
"""
Monitor WebSocket - MODO DEBUG COM VERBOSIDADE
Envia CADA CANDLE ao Telegram com logs detalhados
"""

import json
import requests
from datetime import datetime

try:
    import websocket
    from websocket import WebSocketApp
except ImportError:
    print("❌ websocket-client não instalado")
    exit(1)

# ═══════════════════════════════════════════════════════════════════════════

class TelegramAlerts:
    """Gerenciador de alertas Telegram"""
    
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    def send_message(self, message):
        """Enviar mensagem para Telegram"""
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(self.api_url, json=payload, timeout=5)
            if response.status_code == 200:
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"✅ {timestamp} - Mensagem enviada ao Telegram")
                return True
            else:
                print(f"❌ Erro ao enviar: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return False


class WebSocketMonitorDebugVerbose:
    """Monitor WebSocket - DEBUG MODE COM VERBOSIDADE"""
    
    def __init__(self, bot_token, chat_id, ws_url='ws://localhost:9001'):
        self.telegram = TelegramAlerts(bot_token, chat_id)
        self.ws_url = ws_url
        self.ws = None
        self.last_times = {}
        self.message_count = 0
    
    def on_message(self, ws, message):
        """Receber mensagem com DEBUG"""
        try:
            print(f"\n📨 [WEBSOCKET] Dados recebidos")
            
            data = json.loads(message)
            
            symbol = data.get('symbol')
            time_str = data.get('time')
            
            print(f"   Symbol: {symbol}")
            print(f"   Time: {time_str}")
            
            # Verificar se é novo candle
            if symbol in self.last_times:
                if self.last_times[symbol] == time_str:
                    print(f"   → Candle duplicado, ignorando")
                    return
            
            self.last_times[symbol] = time_str
            
            print(f"   → Novo candle detectado!")
            
            # Formatar e enviar
            msg = self.format_message_debug(data)
            
            self.message_count += 1
            print(f"\n📨 Enviando mensagem #{self.message_count}...")
            
            self.telegram.send_message(msg)
            
            print(f"✅ Mensagem #{self.message_count} enviada com sucesso!\n")
        
        except Exception as e:
            print(f"❌ Erro ao processar mensagem: {str(e)}\n")
    
    def on_error(self, ws, error):
        """Erro"""
        print(f"\n❌ WebSocket erro: {error}\n")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Desconexão"""
        print(f"\n⚠️  WebSocket desconectado")
        print(f"   Código: {close_status_code}")
        print(f"   Mensagem: {close_msg}\n")
    
    def on_open(self, ws):
        """Conexão aberta"""
        print(f"\n✅ WebSocket conectado!")
        
        # Inscrever-se nos pares
        for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
            ws.send(json.dumps({'action': 'subscribe', 'symbol': symbol}))
            print(f"   ✓ Inscrito em {symbol}")
        
        # Notificar Telegram - Startup
        msg = """<b>🚀 MONITOR DEBUG INICIADO (VERBOSE)</b>

<b>📡 Conectado ao Bridge MT5</b>
├─ URL: ws://localhost:9001
├─ Pares: GBPUSD, EURUSD, XAUUSD
├─ Timeframe: M15
└─ Modo: 🔍 DEBUG VERBOSE

<b>📊 Status:</b>
└─ Aguardando candles...

<b>ℹ️ Modo Verbose:</b>
└─ Cada candle M15 = Uma mensagem detalhada"""
        
        print(f"\n📨 Enviando mensagem de startup...\n")
        self.telegram.send_message(msg)
    
    def format_message_debug(self, data):
        """Formatar mensagem para DEBUG"""
        symbol = data['symbol']
        time_dt = datetime.fromisoformat(data['time'])
        time_str = time_dt.strftime('%Y/%m/%d %H:%M')
        
        ohlc = data.get('ohlc', {})
        ind = data.get('indicators', {})
        xgb = data.get('xgboost', {})
        
        close = ohlc.get('close', 0)
        score = xgb.get('score', 0)
        category = xgb.get('category', 'N/A')
        signal = xgb.get('signal')
        confluence = ind.get('confluence', 0)
        
        # Determinar categoria de sinal
        if score > 0.7:
            category_display = f"🟢 HIGH (>{score*100:.1f}%)"
            action = "POSICIONAR ORDEM"
        elif score > 0.5:
            category_display = f"🟡 MEDIUM ({score*100:.1f}%)"
            action = "OBSERVAR"
        else:
            category_display = f"🔴 LOW (<{score*100:.1f}%)"
            action = "NÃO POSICIONAR ORDEM"
        
        msg = f"""<b>📡 MONITOR WEBSOCKET EM ANDAMENTO</b>

<b>📡 Conectado ao Bridge MT5</b>
├─ URL: ws://localhost:9001
├─ Par: {symbol}
├─ Timeframe: M15
├─ DateTime: {time_str}
├─ Close: {close:.5f}
└─ Status: 🟢 ONLINE

<b>📊 Indicadores Resultado:</b>
├─ RSI(14): {ind.get('rsi_14', 0):.2f}
├─ MACD: {ind.get('macd', 0):.6f}
├─ EMA-12: {ind.get('ema_12', 0):.5f}
├─ SMA-20: {ind.get('sma_20', 0):.5f}
├─ ATR%: {ind.get('atr_pct', 0):.4f}
├─ Stoch-K: {ind.get('stoch_k', 0):.2f}
├─ Confluence: {confluence}/4
└─ <b>XGBoost Score + Signal = {category_display}</b>

<b>🎯 Ação:</b>
└─ {action}

<b>🔔 Aguardando próximo candle...</b>"""
        
        return msg
    
    def connect(self):
        """Conectar ao WebSocket"""
        print(f"🔌 Conectando a {self.ws_url}...\n")
        
        self.ws = WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        self.ws.run_forever()
    
    def run(self):
        """Executar"""
        print(f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║              🔍 MONITOR WEBSOCKET - MODO DEBUG VERBOSE 🔍                     ║
║           (Logs detalhados + Enviando CADA candle ao Telegram)               ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
""")
        
        print(f"⚙️  Configuração:")
        print(f"├─ WebSocket: {self.ws_url}")
        print(f"├─ Pares: GBPUSD, EURUSD, XAUUSD")
        print(f"├─ Timeframe: M15")
        print(f"├─ Modo: DEBUG VERBOSE (logs + Telegram)")
        print(f"└─ Duração: 1-2 semanas de teste\n")
        
        print(f"🔗 Conectando...\n")
        
        self.connect()


def main():
    """Main"""
    BOT_TOKEN = '6024515460:AAFGPwqNStgL0mv3VfxCQ_ZyQS3CtdzOeF0'
    CHAT_ID = -1001735082183
    WS_URL = 'ws://localhost:9001'
    
    monitor = WebSocketMonitorDebugVerbose(BOT_TOKEN, CHAT_ID, WS_URL)
    monitor.run()


if __name__ == '__main__':
    main()
