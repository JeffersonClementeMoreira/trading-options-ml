#!/usr/bin/env python3
"""
Monitor WebSocket - Recebe dados com indicadores do Bridge MT5
Envia para Telegram os dados já processados
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
                print(f"✅ {datetime.now().strftime('%H:%M:%S')} - Telegram OK")
                return True
            else:
                print(f"❌ Erro: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return False


class WebSocketMonitor:
    """Monitor WebSocket simples"""
    
    def __init__(self, bot_token, chat_id, ws_url='ws://localhost:9001'):
        self.telegram = TelegramAlerts(bot_token, chat_id)
        self.ws_url = ws_url
        self.ws = None
        self.last_times = {}
    
    def on_message(self, ws, message):
        """Receber mensagem"""
        try:
            data = json.loads(message)
            
            symbol = data.get('symbol')
            time_str = data.get('time')
            
            # Verificar se é novo candle
            if symbol in self.last_times:
                if self.last_times[symbol] == time_str:
                    return
            
            self.last_times[symbol] = time_str
            
            # Formatar e enviar
            msg = self.format_message(data)
            
            print(f"📨 {symbol} {datetime.fromisoformat(time_str).strftime('%H:%M:%S')}")
            self.telegram.send_message(msg)
        
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
    
    def on_error(self, ws, error):
        """Erro"""
        print(f"❌ WebSocket erro: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Desconexão"""
        print(f"⚠️  Desconectado")
    
    def on_open(self, ws):
        """Conexão"""
        print(f"✅ WebSocket conectado!")
        
        # Inscrever-se nos pares
        for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
            ws.send(json.dumps({'action': 'subscribe', 'symbol': symbol}))
            print(f"   → Inscrito em {symbol}")
        
        # Notificar Telegram
        msg = """
<b>✅ MONITOR WEBSOCKET INICIADO</b>

<b>📡 Conectado ao Bridge MT5</b>
├─ URL: ws://localhost:9001
├─ Pares: GBPUSD, EURUSD, XAUUSD
├─ Timeframe: M15
└─ Status: 🟢 ONLINE

<b>📊 Indicadores Inclusos:</b>
├─ RSI, MACD, Bollinger Bands
├─ EMA, SMA, ATR, Momentum
├─ Stochastic, OBV, Volume
├─ SMC (Confluence)
└─ XGBoost Score + Signal

<b>🔔 Aguardando candles...</b>
"""
        self.telegram.send_message(msg)
    
    def format_message(self, data):
        """Formatar mensagem com indicadores"""
        symbol = data['symbol']
        time_str = datetime.fromisoformat(data['time']).strftime('%Y-%m-%d %H:%M:%S')
        
        ohlc = data.get('ohlc', {})
        ind = data.get('indicators', {})
        xgb = data.get('xgboost', {})
        
        # Cores baseadas no score
        score = xgb.get('score', 0)
        category = xgb.get('category', 'N/A')
        signal = xgb.get('signal')
        
        # OHLC
        msg = f"""
<b>📊 {symbol} - {time_str}</b>

<b>💰 Candle M15:</b>
├─ Open:  <code>{ohlc.get('open', 0):.5f}</code>
├─ High:  <code>{ohlc.get('high', 0):.5f}</code>
├─ Low:   <code>{ohlc.get('low', 0):.5f}</code>
└─ Close: <code>{ohlc.get('close', 0):.5f}</code>

<b>📈 Indicadores Principais:</b>
├─ RSI(14):       <code>{ind.get('rsi_14', 0):.2f}</code>
├─ MACD:          <code>{ind.get('macd', 0):.6f}</code>
├─ MACD Signal:   <code>{ind.get('macd_signal', 0):.6f}</code>
├─ BB Upper:      <code>{ind.get('bb_upper', 0):.5f}</code>
├─ BB Middle:     <code>{ind.get('bb_middle', 0):.5f}</code>
├─ EMA 12:        <code>{ind.get('ema_12', 0):.5f}</code>
├─ SMA 20:        <code>{ind.get('sma_20', 0):.5f}</code>
├─ SMA 50:        <code>{ind.get('sma_50', 0):.5f}</code>
├─ ATR%:          <code>{ind.get('atr_pct', 0):.4f}</code>
├─ Momentum:      <code>{ind.get('momentum', 0):.6f}</code>
├─ Stoch K:       <code>{ind.get('stoch_k', 0):.2f}</code>
├─ ROC:           <code>{ind.get('roc_12', 0):.4f}</code>
└─ SMC Conf:      <code>{ind.get('confluence', 0)}</code>

<b>🤖 XGBoost Avaliação:</b>
├─ Score:        <code>{score*100:.1f}%</code>
├─ Categoria:    {'🟢 HIGH (>70%)' if category == 'HIGH' else '🟡 MEDIUM (50-70%)' if category == 'MEDIUM' else '🔴 LOW (<50%)'}
└─ Status:       {'✅ ATIVO' if score > 0.7 else '⏳ Aguardando'}"""
        
        if signal and score > 0.7:
            msg += f"\n\n<b>🎯 SINAL DETECTADO: {signal.upper()}</b>\n"
            msg += f"├─ Entrada: <code>{ohlc.get('close', 0):.5f}</code>\n"
            msg += f"└─ Confiança: <code>{score*100:.1f}%</code>"
        
        return msg
    
    def connect(self):
        """Conectar ao WebSocket"""
        print(f"🔌 Conectando a {self.ws_url}...")
        
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
        print(f"\n{'='*100}")
        print(f"📡 MONITOR WEBSOCKET - DADOS COM INDICADORES")
        print(f"{'='*100}\n")
        
        print(f"⚙️  Configuração:")
        print(f"├─ WebSocket: {self.ws_url}")
        print(f"├─ Pares: GBPUSD, EURUSD, XAUUSD")
        print(f"├─ Timeframe: M15")
        print(f"└─ Indicadores: 25+ técnicos + SMC + XGBoost\n")
        
        print(f"🔗 Conectando...\n")
        
        self.connect()


def main():
    """Main"""
    BOT_TOKEN = '6024515460:AAFGPwqNStgL0mv3VfxCQ_ZyQS3CtdzOeF0'
    CHAT_ID = -1001735082183
    WS_URL = 'ws://localhost:9001'
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║  📡 MONITOR WEBSOCKET - RECEBE DADOS JÁ PROCESSADOS DO BRIDGE MT5             ║
╚════════════════════════════════════════════════════════════════════════════════╝

Este monitor:
✅ Se conecta ao servidor Bridge MT5 via WebSocket
✅ Recebe OHLC + 25 indicadores + SMC + XGBoost score
✅ Envia tudo formatado ao Telegram
✅ Detecta sinais (COMPRA/VENDA) quando score >70%

Certifique-se que o servidor está rodando:
   python3 mt5_websocket_server.py

Depois inicie este monitor:
   python3 live_websocket_monitor.py
    """)
    
    monitor = WebSocketMonitor(BOT_TOKEN, CHAT_ID, WS_URL)
    monitor.run()


if __name__ == '__main__':
    main()
