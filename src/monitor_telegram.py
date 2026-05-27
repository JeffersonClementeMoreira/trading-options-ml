#!/usr/bin/env python3
"""
Monitor WebSocket - MODO DEBUG COM VERBOSIDADE
Envia CADA CANDLE ao Telegram com logs detalhados
"""

import json
import requests
from datetime import datetime

try:
    import websockets
    import asyncio
except ImportError:
    print("❌ websockets não instalado")
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


class WebSocketMonitor:
    """Monitor WebSocket - DEBUG MODE"""
    
    def __init__(self, bot_token, chat_id, ws_url='ws://localhost:9001'):
        self.telegram = TelegramAlerts(bot_token, chat_id)
        self.ws_url = ws_url
        self.last_times = {}
        self.message_count = 0
    
    async def run(self):
        """Executar monitor"""
        print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║            🔍 MONITOR WEBSOCKET - MODO DEBUG 🔍                          ║
║        (Logs detalhados + Enviando CADA candle ao Telegram)              ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

⚙️  Configuração:
├─ WebSocket: {self.ws_url}
├─ Pares: GBPUSD, EURUSD, XAUUSD
├─ Timeframe: M15
├─ Modo: DEBUG (logs + Telegram)
└─ Duração: 1-2 semanas de teste

🔗 Conectando...\n""")
        
        async with websockets.connect(self.ws_url) as ws:
            print(f"✅ WebSocket conectado!")
            
            # Inscrever-se
            for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
                await ws.send(json.dumps({'action': 'subscribe', 'symbol': symbol}))
                print(f"   ✓ Inscrito em {symbol}")
            
            # Notificar startup
            msg = """<b>🚀 MONITOR DEBUG INICIADO</b>

<b>📡 Conectado ao Bridge MT5</b>
├─ URL: ws://localhost:9001
├─ Pares: GBPUSD, EURUSD, XAUUSD
├─ Timeframe: M15
└─ Modo: 🔍 DEBUG

<b>📊 Status:</b>
└─ Aguardando candles...

<b>ℹ️ Modo Debug:</b>
└─ Cada candle M15 = Uma mensagem detalhada"""
            
            print(f"\n📨 Enviando mensagem de startup...\n")
            self.telegram.send_message(msg)
            
            # Receber dados
            async for message in ws:
                try:
                    data = json.loads(message)
                    
                    symbol = data.get('symbol')
                    time_str = data.get('time')
                    
                    print(f"\n📨 [WEBSOCKET] Dados recebidos")
                    print(f"   Symbol: {symbol}")
                    print(f"   Time: {time_str}")
                    
                    # Verificar se é novo candle
                    if symbol in self.last_times:
                        if self.last_times[symbol] == time_str:
                            print(f"   → Candle duplicado, ignorando")
                            continue
                    
                    self.last_times[symbol] = time_str
                    
                    print(f"   → Novo candle detectado!")
                    
                    # Formatar e enviar
                    msg = self.format_message(data)
                    
                    self.message_count += 1
                    print(f"\n📨 Enviando mensagem #{self.message_count}...")
                    
                    self.telegram.send_message(msg)
                    
                    print(f"✅ Mensagem #{self.message_count} enviada com sucesso!\n")
                
                except Exception as e:
                    print(f"❌ Erro ao processar mensagem: {str(e)}\n")
    
    def format_message(self, data):
        """Formatar mensagem para Telegram"""
        symbol = data['symbol']
        time_iso = data.get('time', '')
        ohlc = data.get('ohlc', {})
        ind = data.get('indicators', {})
        xgb = data.get('xgboost', {})
        
        close = ohlc.get('close', 0)
        score = xgb.get('score', 0)
        category = xgb.get('category', 'N/A')
        signal = xgb.get('signal')
        
        # Determinar ação
        if score > 0.7:
            category_display = f"🟢 HIGH (>{score*100:.1f}%)"
            action = "POSICIONAR ORDEM"
        elif score > 0.5:
            category_display = f"🟡 MEDIUM ({score*100:.1f}%)"
            action = "OBSERVAR"
        else:
            category_display = f"🔴 LOW (<{score*100:.1f}%)"
            action = "NÃO POSICIONAR"
        
        msg = f"""<b>📡 MONITOR WEBSOCKET EM ANDAMENTO</b>

<b>📡 Conectado ao Bridge MT5</b>
├─ URL: ws://localhost:9001
├─ Par: <b>{symbol}</b>
├─ Timeframe: M15
├─ DateTime: {time_iso}
├─ Close: <b>{close:.5f}</b>
└─ Status: 🟢 ONLINE

<b>📊 Indicadores:</b>
├─ RSI(14): {ind.get('rsi_14', 0):.2f}
├─ MACD: {ind.get('macd', 0):.6f}
├─ EMA-12: {ind.get('ema_12', 0):.5f}
├─ SMA-20: {ind.get('sma_20', 0):.5f}
├─ ATR%: {ind.get('atr_pct', 0):.4f}
├─ Stoch-K: {ind.get('stoch_k', 0):.2f}
└─ Confluence: {ind.get('confluence', 0)}/4

<b>🎯 XGBoost:</b>
├─ Score: <b>{category_display}</b>
└─ Signal: {signal if signal else 'Nenhum'}

<b>📌 Ação Recomendada:</b>
└─ <b>{action}</b>

<b>🔔 Aguardando próximo candle...</b>"""
        
        return msg


async def main():
    """Main"""
    BOT_TOKEN = '6024515460:AAFGPwqNStgL0mv3VfxCQ_ZyQS3CtdzOeF0'
    CHAT_ID = -1001735082183
    WS_URL = 'ws://localhost:9001'
    
    monitor = WebSocketMonitor(BOT_TOKEN, CHAT_ID, WS_URL)
    await monitor.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n🛑 Monitor interrompido")
