#!/usr/bin/env python3
"""
Monitor WebSocket V2 - AGRESSIVO
Envia mensagem IMEDIATAMENTE quando novo candle chega
"""

import json
import requests
from datetime import datetime
import asyncio
import sys

try:
    import websockets
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
                return True
            else:
                print(f"❌ Erro ao enviar: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return False


class Monitor:
    """Monitor WebSocket - V2 AGRESSIVO"""
    
    def __init__(self, bot_token, chat_id, ws_url='ws://localhost:9001'):
        self.telegram = TelegramAlerts(bot_token, chat_id)
        self.ws_url = ws_url
        self.last_sent_datetime = {}  # Rastrear último datetime ENVIADO por símbolo
        self.message_count = 0
        self.last_close = {}  # Rastrear último close para detectar sinal
    
    async def run(self):
        """Executar monitor"""
        print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║            📡 MONITOR WEBSOCKET V2 - AGRESSIVO 📡                        ║
║          (Envia mensagem IMEDIATAMENTE para cada novo candle)             ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

🔗 Conectando a {self.ws_url}...\n""")
        
        async with websockets.connect(self.ws_url) as ws:
            print(f"✅ Conectado!\n")
            
            # Inscrever-se
            for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
                await ws.send(json.dumps({'action': 'subscribe', 'symbol': symbol}))
                print(f"✓ Inscrito em {symbol}")
                self.last_sent_datetime[symbol] = None
                self.last_close[symbol] = None
            
            # Enviar startup
            msg_startup = """<b>🚀 MONITOR DEBUG INICIADO</b>

<b>📡 Conectado ao Bridge MT5</b>
├─ URL: ws://localhost:9001
├─ Pares: GBPUSD, EURUSD, XAUUSD
├─ Timeframe: M15
└─ Modo: 🔍 DEBUG AGRESSIVO

<b>Status:</b>
└─ ✅ ONLINE - Aguardando candles"""
            
            print(f"\n📨 Enviando startup...\n")
            self.telegram.send_message(msg_startup)
            
            # Receber e processar candles
            print("⏳ Aguardando APENAS novos candles...\n")
            
            async for message in ws:
                try:
                    data = json.loads(message)
                    
                    symbol = data.get('symbol')
                    time_str = data.get('time')
                    close = data.get('ohlc', {}).get('close')
                    
                    # *** GARANTIR QUE SÍMBOLO ESTÁ NO RASTREAMENTO ***
                    if symbol not in self.last_sent_datetime:
                        self.last_sent_datetime[symbol] = None
                        self.last_close[symbol] = None
                    
                    # *** VERIFICAÇÃO RIGOROSA: APENAS NOVOS DATETIMES ***
                    # Se já foi enviado este datetime, IGNORAR COMPLETAMENTE
                    if time_str == self.last_sent_datetime[symbol]:
                        # Candle duplicado - ignorar silenciosamente
                        continue
                    
                    # *** É UM NOVO CANDLE! ENVIAR ***
                    print(f"\n🔔 NOVO CANDLE! {symbol} | {time_str}")
                    
                    # Atualizar rastreamento IMEDIATAMENTE (antes de enviar)
                    self.last_sent_datetime[symbol] = time_str
                    
                    # *** ENVIAR IMEDIATAMENTE AO TELEGRAM ***
                    msg = self.format_message(data)
                    
                    self.message_count += 1
                    
                    if self.telegram.send_message(msg):
                        print(f"✅ Mensagem #{self.message_count} ENVIADA")
                        self.last_close[symbol] = close
                    else:
                        print(f"❌ Falha ao enviar")
                
                except Exception as e:
                    print(f"❌ Erro: {str(e)}")
    
    def format_message(self, data):
        """Formatar mensagem para Telegram"""
        symbol = data['symbol']
        time_str = data.get('time', '')
        ohlc = data.get('ohlc', {})
        ind = data.get('indicators', {})
        xgb = data.get('xgboost', {})
        
        open_p = ohlc.get('open', 0)
        high = ohlc.get('high', 0)
        low = ohlc.get('low', 0)
        close = ohlc.get('close', 0)
        volume = ohlc.get('volume', 0)
        
        score = xgb.get('score', 0)
        category = xgb.get('category', 'N/A')
        
        # *** DETERMINAR SINAL: BUY ou SELL ***
        if close > open_p:
            sinal = "📈 BUY (COMPRA)"
            candle_tipo = "Alta"
        elif close < open_p:
            sinal = "📉 SELL (VENDA)"
            candle_tipo = "Queda"
        else:
            sinal = "➡️  DOJI (Neutro)"
            candle_tipo = "Neutro"
        
        # *** DETERMINAR AÇÃO BASEADA NO SCORE ***
        if score > 0.7:
            action_icon = "🟢"
            action = f"POSICIONAR {sinal}"
        elif score > 0.5:
            action_icon = "🟡"
            action = f"OBSERVAR {candle_tipo}"
        else:
            action_icon = "🔴"
            action = "AGUARDAR"
        
        msg = f"""<b>📊 NOVO CANDLE M15</b>

<b>💱 Pair: {symbol}</b>
├─ DateTime: <b>{time_str}</b>
├─ Close: <b>{close:.5f}</b>
├─ Open:  {open_p:.5f}
├─ High:  {high:.5f}
├─ Low:   {low:.5f}
├─ Tipo:  {candle_tipo}
└─ Volume: {volume}

<b>📈 Indicadores:</b>
├─ RSI(14): {ind.get('rsi_14', 0):.2f}
├─ SMA-20: {ind.get('sma_20', 0):.5f}
├─ SMA-50: {ind.get('sma_50', 0):.5f}
├─ ATR%: {ind.get('atr_pct', 0):.4f}
├─ Confluence: {ind.get('confluence', 0)}/4
└─ Bollinger: {ind.get('bb_lower', 0):.5f} - {ind.get('bb_upper', 0):.5f}

<b>🎯 XGBoost Score:</b>
├─ {action_icon} {category} (<b>{score*100:.1f}%</b>)
├─ Sinal: {sinal}
└─ Ação: <b>{action}</b>"""
        
        return msg


async def main():
    """Main"""
    BOT_TOKEN = '6024515460:AAFGPwqNStgL0mv3VfxCQ_ZyQS3CtdzOeF0'
    CHAT_ID = -1001735082183
    WS_URL = 'ws://localhost:9001'
    
    monitor = Monitor(BOT_TOKEN, CHAT_ID, WS_URL)
    await monitor.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n🛑 Monitor interrompido")
