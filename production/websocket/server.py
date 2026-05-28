#!/usr/bin/env python3
"""
WebSocket + Telegram Alert System for Options Trading
======================================================

Monitora sinais pré-calculados e envia alertas Telegram quando acionados.

Fluxo:
1. MT5 EA envia candles via WebSocket (OHLC M15)
2. Sistema verifica se há sinal programado para hoje
3. Se receber candle no horário ± 30min: envia alert Telegram
4. Trader entra manualmente com opções
5. MT5 continua monitorando até atingir target
"""

import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
from pathlib import Path
import sys

# WebSocket
import websockets
from websockets.server import WebSocketServerProtocol

# Telegram
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DailySignalMonitor:
    """Monitora sinais diários e envia alertas."""
    
    def __init__(self, signals_dir: str = 'production', 
                 telegram_token: str = None, 
                 telegram_chat_id: str = None):
        """
        Initialize signal monitor.
        
        Parameters:
        -----------
        signals_dir : str
            Directory with daily_signals_*.csv files
        telegram_token : str
            Telegram bot token (set via env: TELEGRAM_TOKEN)
        telegram_chat_id : str
            Telegram chat ID (set via env: TELEGRAM_CHAT_ID)
        """
        self.signals_dir = Path(signals_dir)
        self.telegram_token = telegram_token or ''
        self.telegram_chat_id = telegram_chat_id or ''
        
        # Load daily signals
        self.daily_signals = self._load_daily_signals()
        
        # Track sent alerts (1 per day per pair)
        self.sent_today = {
            'EURUSD': False,
            'GBPUSD': False
        }
        
        logger.info("✅ Signal Monitor Initialized")
    
    def _load_daily_signals(self) -> Dict:
        """Load daily signals from CSV files."""
        signals = {}
        
        for pair in ['EURUSD', 'GBPUSD']:
            csv_file = self.signals_dir / f'daily_signals_{pair}.csv'
            
            if csv_file.exists():
                df = pd.read_csv(csv_file)
                df['DateTime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Time'].astype(str))
                signals[pair] = df.set_index('Date')
                logger.info(f"✅ Loaded {len(df)} signals for {pair}")
            else:
                logger.warning(f"⚠️  No signals file for {pair}")
                signals[pair] = pd.DataFrame()
        
        return signals
    
    def _reset_daily_sent(self):
        """Reset sent tracker if date changed."""
        today = datetime.utcnow().date()
        
        # This will be called each candle, check if we need to reset
        # (In production, check once per day at midnight)
        pass
    
    def check_signal_for_today(self, pair: str, current_time: datetime) -> Optional[Dict]:
        """
        Check if there's a signal programmed for today.
        
        Parameters:
        -----------
        pair : str
            'EURUSD' or 'GBPUSD'
        current_time : datetime
            Current candle time
        
        Returns:
        --------
        Signal dict if found and triggered, else None
        """
        today = current_time.date()
        df = self.daily_signals[pair]
        
        # Check if we already sent today
        if self.sent_today[pair]:
            return None
        
        # Look for signal for today
        today_signals = df.loc[str(today)] if str(today) in df.index else None
        
        if today_signals is None or len(today_signals) == 0:
            return None
        
        # If multiple rows (shouldn't happen), take first
        if isinstance(today_signals, pd.DataFrame):
            today_signals = today_signals.iloc[0]
        
        # Signal time with 30-minute tolerance window
        signal_time = pd.to_datetime(f"{today} {today_signals['Time']}")
        time_diff = abs((current_time - signal_time).total_seconds() / 60)  # minutes
        
        if time_diff <= 30:  # Within 30 minutes of signal time
            logger.info(f"🎯 Signal triggered for {pair} at {current_time}")
            
            self.sent_today[pair] = True
            
            return {
                'pair': pair,
                'timestamp': current_time.isoformat(),
                'entry_price': float(today_signals['EntryPrice']),
                'target_price': float(today_signals['TargetPrice']),
                'confidence': int(today_signals['Confidence%']),
                'time_matched_minutes': round(time_diff, 1),
                'direction': 'UP' if today_signals['TargetPrice'] > today_signals['EntryPrice'] else 'DOWN',
            }
        
        return None
    
    async def send_telegram_alert(self, signal: Dict):
        """Send alert via Telegram."""
        if not self.telegram_token or not self.telegram_chat_id:
            logger.warning("⚠️  Telegram not configured")
            return False
        
        try:
            # Calculate pips
            entry = signal['entry_price']
            target = signal['target_price']
            pips = abs(target - entry) * 10000
            
            message = f"""
🚀 <b>TRADING SIGNAL ALERT</b>

📊 <b>{signal['pair']}</b>
⏰ {signal['timestamp']}

📈 <b>Direction: {signal['direction']}</b>
📍 <b>Confidence: {signal['confidence']}%</b>

💰 <b>Entry Price:</b> {entry:.5f}
🎯 <b>Target Price:</b> {target:.5f}
📌 <b>Pips to Target:</b> {pips:.0f} pips

⚠️ <b>Action:</b> Prepare options entry
✅ Ready to enter with {signal['direction']} binary option
"""
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"✅ Telegram alert sent for {signal['pair']}")
                return True
            else:
                logger.error(f"❌ Telegram error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending Telegram: {e}")
            return False
    
    async def handle_candle(self, candle_data: Dict) -> Dict:
        """
        Process incoming candle from MT5.
        
        Parameters:
        -----------
        candle_data : Dict
            {
                'timestamp': 'ISO format',
                'pair': 'EURUSD' or 'GBPUSD',
                'open': 1.16234,
                'high': 1.16456,
                'low': 1.16123,
                'close': 1.16234,
                'volume': 1000
            }
        
        Returns:
        --------
        Response dict with status and signal info
        """
        try:
            pair = candle_data.get('pair', '').upper()
            current_time = pd.to_datetime(candle_data.get('timestamp'))
            
            # Check for signal
            signal = self.check_signal_for_today(pair, current_time)
            
            response = {
                'status': 'ok',
                'pair': pair,
                'timestamp': current_time.isoformat(),
                'signal_found': signal is not None
            }
            
            if signal:
                # Send Telegram alert
                await self.send_telegram_alert(signal)
                response['signal'] = signal
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error handling candle: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }


class WebSocketServer:
    """WebSocket server for MT5 integration."""
    
    def __init__(self, host: str = 'localhost', port: int = 8765):
        self.host = host
        self.port = port
        self.monitor = DailySignalMonitor()
        self.clients = set()
    
    async def handler(self, websocket: WebSocketServerProtocol, path: str):
        """Handle WebSocket client connection."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.clients.add(websocket)
        logger.info(f"✅ Client connected: {client_id}")
        
        try:
            async for message in websocket:
                try:
                    candle_data = json.loads(message)
                    
                    # Process candle
                    response = await self.monitor.handle_candle(candle_data)
                    
                    # Send response back to MT5
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {client_id}")
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': 'Invalid JSON format'
                    }))
                except Exception as e:
                    logger.error(f"Error: {e}")
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': str(e)
                    }))
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Client error ({client_id}): {e}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"❌ Client disconnected: {client_id}")
    
    async def start(self):
        """Start WebSocket server."""
        server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        )
        
        logger.info(f"🚀 WebSocket Server started on ws://{self.host}:{self.port}")
        logger.info(f"📊 Monitoring {len(self.monitor.daily_signals)} pairs")
        logger.info(f"⏰ Signals configured: EURUSD + GBPUSD")
        
        return server


async def main():
    """Main entry point."""
    import os
    
    # Get Telegram config from environment
    telegram_token = os.getenv('TELEGRAM_TOKEN', '')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
    
    if telegram_token and telegram_chat_id:
        logger.info("✅ Telegram configured")
    else:
        logger.warning("⚠️  Telegram not configured. Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID env vars")
    
    # Update monitor with Telegram config
    server = WebSocketServer(host='0.0.0.0', port=8765)
    server.monitor.telegram_token = telegram_token
    server.monitor.telegram_chat_id = telegram_chat_id
    
    # Start server
    ws_server = await server.start()
    
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
        ws_server.close()
        await ws_server.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())
