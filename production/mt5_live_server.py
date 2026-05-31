#!/usr/bin/env python3
"""
MT5 LIVE SERVER - Dados REAIS do MT5 em produção
Conecta ao MT5 rodando, pega últimos candles M15 fechados
Processa com ML e envia sinais Telegram
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread, Lock
import traceback

import pandas as pd
import numpy as np
import requests
import warnings
warnings.filterwarnings('ignore')

# Adicionar paths
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / 'src'))

from indicators import calculate_all_indicators, get_model_features

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("⚠️  MetaTrader5 não instalado. Instale: pip install MetaTrader5")

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mt5_live.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Pares para monitorar
PAIRS_TO_MONITOR = ['EURUSD', 'GBPUSD', 'EURJPY', 'NZDUSD', 'EURAUD']

# Thresholds otimizados
OPTIMAL_THRESHOLDS = {
    'EURUSD': 0.85,
    'GBPUSD': 0.70,
    'EURAUD': 0.90,
    'EURJPY': 0.50,
    'NZDUSD': 0.50,
}

# ════════════════════════════════════════════════════════════════════════════
# MT5 CONNECTOR
# ════════════════════════════════════════════════════════════════════════════

class MT5LiveConnector:
    """Conecta ao MT5 real e pega dados últimos candles"""
    
    def __init__(self):
        self.connected = False
        self.lock = Lock()
        self.last_candles = {}  # {pair: deque(últimos 21 candles)}
        self.sent_today = {}     # {pair: booleano - sinal já enviado?}
        self.models = {}
        self.loaded = False
        
    def connect(self):
        """Conecta ao MT5"""
        if not MT5_AVAILABLE:
            logger.error("❌ MetaTrader5 não instalado")
            return False
        
        try:
            logger.info("🔌 Conectando ao MT5...")
            
            # Conectar
            if not mt5.initialize():
                logger.error(f"❌ Falha ao inicializar MT5: {mt5.last_error()}")
                return False
            
            logger.info("✅ Conectado ao MT5!")
            self.connected = True
            
            # Verificar pares
            logger.info("📊 Verificando símbolos...")
            for pair in PAIRS_TO_MONITOR:
                if mt5.symbol_select(pair, True):
                    logger.info(f"   ✅ {pair}: OK")
                else:
                    logger.warning(f"   ⚠️  {pair}: não encontrado")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar: {e}")
            traceback.print_exc()
            return False
    
    def get_latest_candles(self, pair, count=21):
        """
        Pega os últimos N candles fechados do MT5
        
        Args:
            pair: 'EURUSD', 'GBPUSD', etc
            count: número de candles
            
        Returns:
            DataFrame com OHLCV
        """
        try:
            if not self.connected or not mt5.symbol_select(pair, True):
                logger.warning(f"⚠️  {pair}: símbolo não selecionado")
                return None
            
            # Pegar candles (M15 = PERIOD_M15 = 15)
            rates = mt5.copy_rates_from_pos(pair, mt5.TIMEFRAME_M15, 0, count)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"⚠️  {pair}: nenhum candle encontrado")
                return None
            
            # Converter para DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']].copy()
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            logger.info(f"✅ {pair}: {len(df)} candles obtidos")
            return df
            
        except Exception as e:
            logger.error(f"❌ {pair}: Erro ao pegar candles: {e}")
            return None
    
    def load_models(self):
        """Carrega modelos ML"""
        if self.loaded:
            return
        
        try:
            logger.info("🤖 Carregando modelos ML...")
            from backtest_classification_optimized import train_models, load_and_process_data, predict_on_test
            
            # Carregar dados de treino
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
            self.loaded = True  # Mesmo assim continua com fallback
            return True
    
    def get_signal(self, pair):
        """
        Processa último candle e retorna sinal
        
        Args:
            pair: 'EURUSD', etc
            
        Returns:
            {'signal': 0|1, 'confidence': 0-1, 'entry_price': float, ...}
        """
        with self.lock:
            # Pegar últimos 21 candles reais
            df = self.get_latest_candles(pair, count=21)
            
            if df is None or len(df) < 21:
                logger.warning(f"⚠️  {pair}: insuficientes candles ({len(df) if df is not None else 0}/21)")
                return {
                    'signal': 0,
                    'confidence': 0.0,
                    'entry_price': 0.0,
                    'status': 'waiting_candles'
                }
            
            # Já enviou sinal hoje?
            today = df.iloc[-1]['timestamp'].date()
            if pair not in self.sent_today:
                self.sent_today[pair] = False
            
            if self.sent_today[pair]:
                return {
                    'signal': 0,
                    'confidence': 0.0,
                    'entry_price': float(df.iloc[-1]['close']),
                    'status': 'already_sent_today'
                }
            
            # Calcular indicadores
            try:
                df['timestamp'] = df['timestamp'].astype('object')  # Para compatibilidade
                df_calc = calculate_all_indicators(df)
            except Exception as e:
                logger.error(f"❌ {pair}: Erro ao calcular indicadores: {e}")
                return {
                    'signal': 0,
                    'confidence': 0.0,
                    'entry_price': float(df.iloc[-1]['close']),
                    'status': 'indicator_error'
                }
            
            # Usar modelo ML ou fallback
            if self.models:
                try:
                    last_row = df_calc.iloc[-1]
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
                last_row = df_calc.iloc[-1]
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
                logger.info(f"🎯 SINAL GERADO: {pair} = {signal} (conf={confidence:.2%}, threshold={threshold})")
            else:
                logger.info(f"📊 {pair}: confidence={confidence:.2%} < threshold={threshold} → no signal")
            
            return {
                'signal': signal,
                'confidence': float(confidence),
                'entry_price': float(df.iloc[-1]['close']),
                'threshold': float(threshold),
                'timestamp': df.iloc[-1]['timestamp'].isoformat(),
                'status': 'ok',
                'high': float(df.iloc[-1]['high']),
                'low': float(df.iloc[-1]['low']),
                'open': float(df.iloc[-1]['open']),
                'volume': int(df.iloc[-1]['volume'])
            }
    
    def reset_daily(self):
        """Reset sinais diários (00:00 UTC)"""
        with self.lock:
            for pair in self.sent_today:
                self.sent_today[pair] = False
            logger.info("🔄 Reset diário realizado")

# ════════════════════════════════════════════════════════════════════════════
# TELEGRAM
# ════════════════════════════════════════════════════════════════════════════

def send_telegram_alert(pair, signal, confidence, entry_price, threshold, o, h, l):
    """Envia alerta Telegram"""
    
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️  Telegram não configurado")
        return
    
    if signal == 0:
        return
    
    direction = "🟢 BUY" if signal == 1 else "🔴 SELL"
    message = (
        f"{direction} {pair}\n\n"
        f"Entry: ${entry_price:.5f}\n"
        f"High: ${h:.5f}\n"
        f"Low: ${l:.5f}\n"
        f"Open: ${o:.5f}\n"
        f"Confidence: {confidence*100:.1f}%\n"
        f"Threshold: {threshold:.2f}\n"
        f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
        response = requests.post(url, json=data, timeout=5)
        
        if response.ok:
            logger.info(f"💬 Telegram enviado: {pair}")
        else:
            logger.error(f"❌ Telegram erro: {response.text}")
    except Exception as e:
        logger.error(f"❌ Erro Telegram: {e}")

# ════════════════════════════════════════════════════════════════════════════
# MONITOR LOOP
# ════════════════════════════════════════════════════════════════════════════

def monitor_loop(connector, check_interval=60):
    """
    Loop principal que monitora MT5 e gera sinais
    
    Args:
        connector: MT5LiveConnector
        check_interval: segundos entre checks (padrão 60s, será 15min em produção)
    """
    logger.info(f"📡 Iniciando monitor (intervalo: {check_interval}s)")
    
    last_reset = datetime.utcnow().date()
    
    while True:
        try:
            # Reset diário (00:00 UTC)
            today = datetime.utcnow().date()
            if today != last_reset:
                connector.reset_daily()
                last_reset = today
            
            # Processar cada par
            for pair in PAIRS_TO_MONITOR:
                try:
                    result = connector.get_signal(pair)
                    
                    if result['signal'] == 1:
                        # Enviar Telegram
                        send_telegram_alert(
                            pair,
                            result['signal'],
                            result['confidence'],
                            result['entry_price'],
                            result['threshold'],
                            result.get('open', 0),
                            result.get('high', 0),
                            result.get('low', 0)
                        )
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao processar {pair}: {e}")
                    traceback.print_exc()
            
            # Aguardar próxima iteração
            logger.info(f"✅ Ciclo completo. Próximo em {check_interval}s...")
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            logger.info("⛔ Monitoramento interrompido pelo usuário")
            break
        except Exception as e:
            logger.error(f"❌ Erro no monitor: {e}")
            traceback.print_exc()
            time.sleep(5)

# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logger.info("="*80)
    logger.info("🚀 MT5 LIVE SERVER - DADOS REAIS")
    logger.info("="*80)
    logger.info("")
    
    if not MT5_AVAILABLE:
        logger.error("❌ MetaTrader5 não instalado!")
        logger.info("Instale: pip install MetaTrader5")
        sys.exit(1)
    
    # Criar connector
    connector = MT5LiveConnector()
    
    # Conectar ao MT5
    if not connector.connect():
        logger.error("❌ Falha ao conectar ao MT5")
        sys.exit(1)
    
    # Carregar modelos
    connector.load_models()
    
    # Monitor loop
    logger.info("")
    logger.info("📨 Aguardando últimos candles fechados...")
    logger.info("   (Novo sinal a cada 15 minutos)")
    logger.info("")
    
    try:
        # Em produção: intervalo = 60s (checar a cada minuto se novo candle fechou)
        # Para teste: intervalo = 10s
        MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', '60'))
        monitor_loop(connector, check_interval=MONITOR_INTERVAL)
    except KeyboardInterrupt:
        logger.info("⛔ Servidor parado")
    finally:
        if mt5.initialize():
            mt5.shutdown()
            logger.info("✅ MT5 desconectado")
