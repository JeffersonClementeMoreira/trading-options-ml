#!/usr/bin/env python3
"""
MT5 LIVE REAL DATA SERVER
Recebe últimos candles REAIS fechados do MT5 via HTTP
Processa com ML e envia sinais Telegram
SEM SIMULAÇÃO - APENAS DADOS REAIS
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from collections import deque

import pandas as pd
import numpy as np
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import warnings
warnings.filterwarnings('ignore')

# Adicionar paths
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / 'src'))

from indicators import calculate_all_indicators, get_model_features

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mt5_live_real.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

OPTIMAL_THRESHOLDS = {
    'EURUSD': 0.85,
    'GBPUSD': 0.70,
    'EURJPY': 0.50,
    'NZDUSD': 0.50,
    'EURAUD': 0.90,
}

# ════════════════════════════════════════════════════════════════════════════
# SIGNAL MANAGER - DADOS REAIS DO MT5
# ════════════════════════════════════════════════════════════════════════════

class RealDataSignalManager:
    """Gerencia sinais com dados REAIS do MT5 (sem simulação)"""
    
    def __init__(self):
        self.candle_history = {}  # {pair: deque(últimos 21 candles reais)}
        self.sent_today = {}
        self.lock = Lock()
        self.models = {}
        self.loaded = False
        self.last_close_time = {}  # {pair: timestamp do último candle fechado}
    
    def load_models(self):
        """Carrega modelos ML"""
        if self.loaded:
            return
        
        try:
            logger.info("🤖 Carregando modelos ML...")
            from backtest_classification_optimized import train_models, load_and_process_data, predict_on_test
            
            DATA_DIR = BASE_DIR / 'data'
            csv_file = DATA_DIR / 'EURUSD_M15_2024.01.01_2026.05.31.txt'
            
            if not csv_file.exists():
                logger.warning(f"⚠️  Usando fallback (sem treino)")
                self.loaded = True
                return True
            
            logger.info("📊 Carregando dados de treino...")
            df_train, df_test = load_and_process_data(str(csv_file), 'EURUSD')
            
            logger.info("🧠 Treinando modelos...")
            xgb_model, rf_model, scaler, feature_names = train_models(df_train)
            
            self.models = {
                'xgb_model': xgb_model,
                'rf_model': rf_model,
                'scaler': scaler,
                'feature_names': feature_names
            }
            
            self.loaded = True
            logger.info("✅ Modelos carregados!")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Erro ao carregar modelos: {e}")
            self.loaded = True
            return True
    
    def process_real_candle(self, pair, timestamp, o, h, l, c, v):
        """
        Processa CANDLE REAL fechado do MT5
        SEM SIMULAÇÃO - apenas dados reais
        
        Args:
            pair: 'EURUSD'
            timestamp: datetime do candle fechado
            o, h, l, c, v: OHLCV real
            
        Returns:
            {'signal': 0|1, 'confidence': 0-1, ...}
        """
        with self.lock:
            # Inicializar
            if pair not in self.candle_history:
                self.candle_history[pair] = deque(maxlen=21)
                self.sent_today[pair] = False
                self.last_close_time[pair] = None
            
            # ⭐ IMPORTANTE: Verificar se é novo candle (não repetir o mesmo)
            current_close_time = pd.Timestamp(timestamp).floor('15min')  # Arredondar para 15min
            
            if pair in self.last_close_time and self.last_close_time[pair] == current_close_time:
                logger.debug(f"⏭️  {pair}: Ignorando candle repetido ({current_close_time})")
                return {'signal': 0, 'confidence': 0.0, 'status': 'duplicate_candle'}
            
            # Marcar como recebido
            self.last_close_time[pair] = current_close_time
            
            # Adicionar ao histórico
            self.candle_history[pair].append({
                'timestamp': timestamp,
                'open': o,
                'high': h,
                'low': l,
                'close': c,
                'volume': v
            })
            
            # Precisa de 21 candles para calcular indicadores
            if len(self.candle_history[pair]) < 21:
                logger.info(f"⏳ {pair}: Bufferizando candles reais ({len(self.candle_history[pair])}/21)")
                return {
                    'signal': 0,
                    'confidence': 0.0,
                    'entry_price': c,
                    'status': f'buffering_{len(self.candle_history[pair])}_of_21'
                }
            
            # Já enviou sinal hoje?
            today = pd.Timestamp(timestamp).date()
            if self.sent_today[pair]:
                logger.info(f"📋 {pair}: Já enviou sinal hoje ({today})")
                return {
                    'signal': 0,
                    'confidence': 0.0,
                    'entry_price': c,
                    'status': 'already_sent_today'
                }
            
            # Construir DataFrame a partir do histórico real
            history_list = list(self.candle_history[pair])
            df = pd.DataFrame(history_list)
            
            # Calcular indicadores
            try:
                df = calculate_all_indicators(df)
            except Exception as e:
                logger.error(f"❌ {pair}: Erro ao calcular indicadores: {e}")
                return {
                    'signal': 0,
                    'confidence': 0.0,
                    'entry_price': c,
                    'status': 'indicator_error'
                }
            
            # Usar modelo ML ou fallback
            if self.models:
                try:
                    last_row = df.iloc[-1]
                    feature_names = self.models['feature_names']
                    
                    X = np.array([last_row[feature_names].values])
                    X_scaled = self.models['scaler'].transform(X)
                    
                    pred_proba_xgb = self.models['xgb_model'].predict_proba(X_scaled)[0, 1]
                    pred_proba_rf = self.models['rf_model'].predict_proba(X_scaled)[0, 1]
                    
                    confidence = (pred_proba_xgb + pred_proba_rf) / 2
                    
                    logger.debug(f"{pair}: XGB={pred_proba_xgb:.2%}, RF={pred_proba_rf:.2%}, Ens={confidence:.2%}")
                    
                except Exception as e:
                    logger.error(f"❌ {pair}: Erro ao fazer predict: {e}")
                    confidence = 0.5
            else:
                # Fallback: RSI
                last_row = df.iloc[-1]
                rsi = last_row.get('RSI', 50)
                
                if rsi < 30:
                    confidence = 0.85
                elif rsi > 70:
                    confidence = 0.80
                else:
                    confidence = 0.50
                
                logger.info(f"📊 {pair}: Fallback RSI={rsi:.1f}")
            
            # Aplicar threshold
            threshold = OPTIMAL_THRESHOLDS.get(pair, 0.50)
            signal = 1 if confidence > threshold else 0
            
            if signal == 1:
                self.sent_today[pair] = True
                logger.info(f"🎯 SINAL REAL GERADO: {pair} = {signal} (conf={confidence:.2%}, threshold={threshold})")
                logger.info(f"   Close: ${c:.5f} | Time: {timestamp}")
            else:
                logger.info(f"📊 {pair}: confidence={confidence:.2%} < threshold={threshold} → sem sinal")
            
            return {
                'signal': signal,
                'confidence': float(confidence),
                'entry_price': float(c),
                'threshold': float(threshold),
                'timestamp': pd.Timestamp(timestamp).isoformat(),
                'open': float(o),
                'high': float(h),
                'low': float(l),
                'volume': int(v),
                'status': 'ok'
            }
    
    def reset_daily(self, pair):
        """Reset para novo dia"""
        with self.lock:
            if pair in self.sent_today:
                self.sent_today[pair] = False
                logger.info(f"🔄 Reset diário: {pair}")

manager = RealDataSignalManager()

# ════════════════════════════════════════════════════════════════════════════
# TELEGRAM
# ════════════════════════════════════════════════════════════════════════════

def send_telegram_real_signal(pair, signal, confidence, entry_price, threshold, o, h, l, v, timestamp):
    """Envia Telegram com sinal REAL"""
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️  Telegram não configurado")
        return
    
    if signal == 0:
        return
    
    direction = "🟢 BUY" if signal == 1 else "🔴 SELL"
    time_str = pd.Timestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    message = (
        f"{direction} {pair} 🎯\n\n"
        f"Entry: ${entry_price:.5f}\n"
        f"High: ${h:.5f}\n"
        f"Low: ${l:.5f}\n"
        f"Open: ${o:.5f}\n"
        f"Volume: {v}\n\n"
        f"Confidence: {confidence*100:.1f}%\n"
        f"Threshold: {threshold:.2f}\n"
        f"Time: {time_str} UTC\n"
        f"Status: ✅ REAL DATA"
    )
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
        response = requests.post(url, json=data, timeout=5)
        
        if response.ok:
            logger.info(f"💬 Telegram REAL enviado: {pair}")
        else:
            logger.error(f"❌ Telegram erro: {response.text}")
    except Exception as e:
        logger.error(f"❌ Erro Telegram: {e}")

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@app.route('/mt5/candle/real', methods=['POST'])
def receive_real_candle():
    """
    Endpoint REAL para receber último candle fechado do MT5
    SEM SIMULAÇÃO
    
    Esperado JSON:
    {
        "symbol": "EURUSD",
        "datetime": "2026-05-31T14:30:00",
        "open": 1.0850,
        "high": 1.0851,
        "low": 1.0849,
        "close": 1.0850,
        "volume": 1000
    }
    """
    try:
        data = request.get_json()
        
        pair = data.get('symbol', '').upper()
        timestamp_str = data.get('datetime', '')
        o = float(data.get('open', 0))
        h = float(data.get('high', 0))
        l = float(data.get('low', 0))
        c = float(data.get('close', 0))
        v = int(data.get('volume', 0))
        
        timestamp = pd.to_datetime(timestamp_str)
        
        logger.info(f"📨 REAL: {pair} @ {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | O={o:.5f} C={c:.5f} V={v}")
        
        # Processar candle REAL
        result = manager.process_real_candle(pair, timestamp, o, h, l, c, v)
        
        # Enviar Telegram se há sinal
        if result['signal'] == 1:
            send_telegram_real_signal(pair, result['signal'], result['confidence'], 
                                     result['entry_price'], result['threshold'],
                                     o, h, l, v, timestamp)
        
        return jsonify({
            'status': 'ok',
            'pair': pair,
            'signal': result['signal'],
            'confidence': result['confidence'],
            'entry_price': result['entry_price'],
            'data_type': 'REAL',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'error': str(e)}), 400

@app.route('/mt5/status', methods=['GET'])
def status():
    """Status do servidor"""
    return jsonify({
        'status': 'running',
        'mode': 'REAL DATA ONLY',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'pairs_tracked': list(manager.candle_history.keys()),
        'models_loaded': manager.loaded,
        'data_type': 'REAL - NO SIMULATION'
    })

@app.route('/mt5/reset', methods=['POST'])
def reset():
    """Reset diário"""
    data = request.get_json()
    pair = data.get('symbol', '').upper()
    manager.reset_daily(pair)
    return jsonify({'status': 'ok', 'pair': pair, 'action': 'daily_reset'})

# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logger.info("="*80)
    logger.info("🚀 MT5 LIVE REAL DATA SERVER")
    logger.info("📊 APENAS DADOS REAIS - SEM SIMULAÇÃO")
    logger.info("="*80)
    logger.info("")
    
    logger.info("📦 Carregando modelos ML...")
    manager.load_models()
    
    logger.info("")
    logger.info("🌐 Iniciando servidor em http://0.0.0.0:8765")
    logger.info("📨 Aguardando últimos candles REAIS do MT5...")
    logger.info("   Endpoint: POST http://127.0.0.1:8765/mt5/candle/real")
    logger.info("")
    logger.info("="*80)
    logger.info("")
    
    app.run(host='0.0.0.0', port=8765, debug=False, threaded=True)
