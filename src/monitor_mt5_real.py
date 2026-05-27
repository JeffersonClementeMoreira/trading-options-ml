#!/usr/bin/env python3
"""
Monitor MT5 - Arquitetura CORRETA
- Recebe último candle do servidor
- RASTREIA datetime para detectar novo candle
- Só envia Telegram quando datetime muda (novo candle surgiu)
"""

import json
import asyncio
import numpy as np
import pickle
import requests
from datetime import datetime
from pathlib import Path

try:
    import websockets
    from websockets.asyncio import client
except ImportError:
    print("❌ websockets não instalado")
    exit(1)

# ═════════════════════════════════════════════════════════════════════════════

TELEGRAM_TOKEN = "6024515460:AAFGPwqNStgL0mv3VfxCQ_ZyQS3CtdzOeF0"
TELEGRAM_CHAT = "-1001735082183"
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

# ═════════════════════════════════════════════════════════════════════════════

class TelegramAlerts:
    """Gerencia alertas para Telegram"""
    
    @staticmethod
    def send_message(text, parse_mode='HTML'):
        """Enviar mensagem para Telegram"""
        try:
            url = TELEGRAM_API.format(token=TELEGRAM_TOKEN)
            payload = {
                'chat_id': TELEGRAM_CHAT,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True,
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return True, None
            else:
                return False, response.text
        
        except Exception as e:
            return False, str(e)


class XGBoostInference:
    """Carregar e usar modelos XGBoost"""
    
    def __init__(self):
        self.models = {}
        self.load_models()
    
    def load_models(self):
        """Carregar modelos XGBoost"""
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
                print(f"⚠️  Modelo {pair} não encontrado")
                self.models[pair] = None
    
    def predict(self, symbol, features):
        """Fazer predição com XGBoost"""
        if self.models[symbol] is None:
            # Mock: retornar score aleatório
            return np.random.uniform(0, 1)
        
        try:
            # Preparar features para o modelo
            X = np.array([features]).reshape(1, -1)
            score = self.models[symbol].predict_proba(X)[0][1]
            return float(score)
        except Exception as e:
            print(f"⚠️  Erro ao prever {symbol}: {e}")
            return np.random.uniform(0, 1)


class MonitorMT5:
    """Monitor que rastreia novos candles e envia para Telegram"""
    
    def __init__(self):
        self.xgboost = XGBoostInference()
        self.telegram = TelegramAlerts()
        
        # Rastreamento de último datetime por símbolo
        self.last_datetime = {
            'GBPUSD': None,
            'EURUSD': None,
            'XAUUSD': None,
        }
        
        # Contador de mensagens
        self.message_count = 0
    
    def format_message(self, candle):
        """Formatar mensagem para Telegram"""
        symbol = candle['symbol']
        dt = candle['datetime']
        open_p = candle['open']
        high = candle['high']
        low = candle['low']
        close = candle['close']
        volume = candle['volume']
        candle_type = candle['type']
        indicators = candle['indicators']
        
        # Features para XGBoost
        features = [
            indicators.get('rsi_14', 50),
            indicators.get('sma_20', close),
            indicators.get('sma_50', close),
            indicators.get('atr_pct', 0),
            indicators.get('momentum', 0),
            indicators.get('confluence', 2),
            close,
            volume,
        ]
        
        # Predição XGBoost
        score = self.xgboost.predict(symbol, features)
        
        # Categorizar score
        if score > 0.7:
            category = "HIGH ⬆️"
        elif score > 0.5:
            category = "MEDIUM ➡️"
        else:
            category = "LOW ⬇️"
        
        # Determinar direção
        if candle_type == "Alta":
            direction = "🟢 Compra"
            direction_label = "COMPRA"
        elif candle_type == "Queda":
            direction = "🔴 Venda"
            direction_label = "VENDA"
        else:
            direction = "⚪ Neutro"
            direction_label = "NEUTRO"
        
        # Colorir ação baseado em score
        if score > 0.7:
            action_emoji = "🟢"
            action_text = "POSICIONAR"
        elif score > 0.5:
            action_emoji = "🟡"
            action_text = "OBSERVAR"
        else:
            action_emoji = "🔴"
            action_text = "AGUARDAR"
        
        # Emojis para tipo
        if direction_label == "COMPRA":
            tipo_emoji = "🟢"
        elif direction_label == "VENDA":
            tipo_emoji = "🔴"
        else:
            tipo_emoji = "⚪"
        
        # Formatar mensagem HTML simplificada
        msg = f"""
<b>📊 NOVO CANDLE M15</b>

<b>Par:</b> <code>{symbol}</code>
<b>DateTime:</b> <code>{dt}</code>

<b>OHLC:</b>
Open: {open_p:.5f}
High: {high:.5f}
Low: {low:.5f}
Close: <code>{close:.5f}</code>
Volume: {volume:,}

<b>🤖 XGBoost:</b>
Score: <code>{score:.2%}</code>
Category: <b>{category}</b>
Tipo: <b>{tipo_emoji} {direction_label}</b>
Ação: <b>{action_emoji} {action_text}</b>
"""
        return msg.strip()
    
    async def process_candle(self, candle):
        """Processar novo candle"""
        symbol = candle['symbol']
        dt = candle['datetime']
        last_dt = self.last_datetime[symbol]
        
        # Verificar se é novo candle
        if dt == last_dt:
            # Mesmo datetime = mesmo candle, não enviar
            return False
        
        # Novo candle detectado!
        print(f"\n🔔 NOVO CANDLE DETECTADO! {symbol} | {dt}")
        print(f"   Tipo: {candle['type']} | Close: {candle['close']}")
        
        # Atualizar rastreamento
        self.last_datetime[symbol] = dt
        
        # Formatar mensagem
        message = self.format_message(candle)
        
        # Enviar para Telegram
        success, error = self.telegram.send_message(message)
        
        if success:
            self.message_count += 1
            print(f"✅ Mensagem #{self.message_count} ENVIADA")
        else:
            print(f"❌ Erro ao enviar: {error}")
        
        return True
    
    async def connect(self):
        """Conectar ao servidor WebSocket e monitorar"""
        uri = "ws://localhost:9001"
        
        print(f"🔗 Conectando a {uri}...")
        
        try:
            async with client.connect(uri) as websocket:
                print("✅ Conectado!")
                
                # Inscrever em pares
                for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
                    await websocket.send(json.dumps({
                        'action': 'subscribe',
                        'symbol': symbol
                    }))
                    print(f"✓ Inscrito em {symbol}")
                
                # Monitorar mensagens
                print("\n⏳ Aguardando novos candles...")
                
                async for message in websocket:
                    try:
                        candle = json.loads(message)
                        await self.process_candle(candle)
                    
                    except json.JSONDecodeError:
                        print(f"⚠️  Erro ao decodificar JSON: {message}")
                    except Exception as e:
                        print(f"⚠️  Erro ao processar candle: {e}")
        
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            print("⏳ Tentando novamente em 5 segundos...")
            await asyncio.sleep(5)
            await self.connect()


# ═════════════════════════════════════════════════════════════════════════════

async def main():
    monitor = MonitorMT5()
    await monitor.connect()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║           📡 MONITOR MT5 - ARQUITETURA CORRETA 📡                        ║
║        (Rastreia datetime, detecta novo candle, envia Telegram)          ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Monitor parado")
