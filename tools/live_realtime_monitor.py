#!/usr/bin/env python3
"""
Monitor Tempo Real - Dados Reais + XGBoost
Lê dados reais do MT5, calcula indicadores, avalia XGBoost, envia sinais
"""

import pandas as pd
import numpy as np
import requests
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import time
import warnings

warnings.filterwarnings('ignore')

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
                print(f"✅ Mensagem enviada ao Telegram")
                return True
            else:
                print(f"❌ Erro ao enviar: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro na conexão: {str(e)}")
            return False


class FeatureEngineer:
    """Calcula todos os 25 indicadores técnicos"""
    
    @staticmethod
    def calculate_rsi(series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calculate_macd(series, fast=12, slow=26, signal=9):
        ema_fast = series.ewm(span=fast).mean()
        ema_slow = series.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(series, period=20, std_dev=2):
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    @staticmethod
    def calculate_atr(high, low, close, period=14):
        tr = pd.concat([
            high - low,
            abs(high - close.shift(1)),
            abs(low - close.shift(1))
        ], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(series, period):
        return series.ewm(span=period).mean()
    
    @staticmethod
    def calculate_sma(series, period):
        return series.rolling(window=period).mean()
    
    @staticmethod
    def calculate_roc(series, period=12):
        return ((series - series.shift(period)) / series.shift(period)) * 100
    
    @staticmethod
    def calculate_stochastic(high, low, close, period=14):
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k = ((close - lowest_low) / (highest_high - lowest_low)) * 100
        d = k.rolling(window=3).mean()
        return k, d
    
    def engineer_features(self, df):
        """Calcular todos os indicadores"""
        df = df.copy()
        
        # RSI
        df['rsi'] = self.calculate_rsi(df['close'])
        
        # MACD
        df['macd'], df['macd_signal'], df['macd_histogram'] = self.calculate_macd(df['close'])
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = self.calculate_bollinger_bands(df['close'])
        
        # ATR
        df['atr'] = self.calculate_atr(df['high'], df['low'], df['close'])
        df['atr_pct'] = (df['atr'] / df['close']) * 100
        
        # ATR Ratio
        df['atr_ratio'] = (df['atr'] / df['close']) * 100
        
        # EMAs
        df['ema_12'] = self.calculate_ema(df['close'], 12)
        df['ema_26'] = self.calculate_ema(df['close'], 26)
        
        # SMAs
        df['sma_20'] = self.calculate_sma(df['close'], 20)
        df['sma_50'] = self.calculate_sma(df['close'], 50)
        
        # Momentum
        df['momentum'] = df['close'] - df['close'].shift(10)
        
        # ROC
        df['roc'] = self.calculate_roc(df['close'])
        
        # Stochastic
        df['stoch_k'], df['stoch_d'] = self.calculate_stochastic(df['high'], df['low'], df['close'])
        
        # OBV
        obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        df['obv'] = obv
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / (df['volume_sma'] + 0.0001)
        
        # Candle patterns
        df['body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
        df['high_low_ratio'] = df['upper_wick'] / (df['lower_wick'] + 0.0001)
        
        # Trend
        df['sma_trend'] = (df['sma_20'] - df['sma_50']) / (df['sma_50'] + 0.0001) * 100
        
        # Confluence (SmartMoney)
        high_20 = df['high'].rolling(window=20).max().shift(1)
        low_20 = df['low'].rolling(window=20).min().shift(1)
        atr_75th = df['atr_pct'].rolling(window=20).quantile(0.75)
        
        confluence = 0
        
        for i in range(len(df)):
            c = 0
            if df['high'].iloc[i] >= high_20.iloc[i]:
                c += 1
            if df['atr_pct'].iloc[i] > atr_75th.iloc[i]:
                c += 1
            if (df['body'].iloc[i] / (df['high'].iloc[i] - df['low'].iloc[i] + 0.0001)) < 0.25:
                c += 1
            confluence += c / 3
        
        df['confluence'] = confluence / len(df)
        
        return df


class RealTimeMonitor:
    """Monitor em tempo real com dados reais do MT5"""
    
    def __init__(self, bot_token, chat_id):
        self.telegram = TelegramAlerts(bot_token, chat_id)
        self.feature_engineer = FeatureEngineer()
        
        # Carregar modelos XGBoost
        self.models = {}
        self.load_models()
        
        # Pares com dados
        self.pares_config = {
            'GBPUSD': '../data/GBPUSD_REALTIME.csv',
            'EURUSD': '../data/EURUSD_REALTIME.csv',
            'XAUUSD': '../data/XAUUSD_REALTIME.csv'
        }
        
        # Estado
        self.last_candle_times = {}
        self.sinais_enviados = set()
    
    def load_models(self):
        """Carregar modelos XGBoost"""
        models_dir = Path('../models')
        
        for par in ['GBPUSD', 'EURUSD', 'XAUUSD']:
            model_file = models_dir / f'xgboost_{par.lower()}.pkl'
            if model_file.exists():
                try:
                    with open(model_file, 'rb') as f:
                        self.models[par] = pickle.load(f)
                    print(f"✅ Modelo XGBoost carregado: {par}")
                except Exception as e:
                    print(f"❌ Erro ao carregar modelo {par}: {str(e)}")
    
    def load_realtime_data(self, symbol):
        """Carregar dados reais do arquivo CSV"""
        csv_path = self.pares_config.get(symbol)
        
        if not csv_path or not Path(csv_path).exists():
            print(f"⚠️  Arquivo não encontrado: {csv_path}")
            return None
        
        try:
            df = pd.read_csv(csv_path)
            
            # Detectar formato e converter datetime
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
            elif '<DATE>' in df.columns and '<TIME>' in df.columns:
                df['datetime'] = pd.to_datetime(df['<DATE>'] + ' ' + df['<TIME>'], format='%Y.%m.%d %H:%M:%S')
            
            # Renomear colunas
            df.columns = df.columns.str.strip().str.lower().str.replace('<', '').str.replace('>', '')
            
            df.set_index('datetime', inplace=True)
            df = df.sort_index()
            
            return df[['open', 'high', 'low', 'close', 'volume']]
        
        except Exception as e:
            print(f"❌ Erro ao carregar {symbol}: {str(e)}")
            return None
    
    def detect_smc_signal(self, df):
        """Detectar sinal SMC do último candle"""
        if len(df) < 20:
            return None
        
        df = df.copy()
        
        # ATR
        atr = self.feature_engineer.calculate_atr(df['high'], df['low'], df['close'])
        atr_pct = (atr / df['close']) * 100
        
        # Extremos
        high_20 = df['high'].rolling(window=20).max().shift(1)
        low_20 = df['low'].rolling(window=20).min().shift(1)
        atr_75th = atr_pct.rolling(window=20).quantile(0.75)
        
        # Último candle
        last = df.iloc[-1]
        
        atr_pct_val = atr_pct.iloc[-1]
        
        # Critérios
        touched_high = last['high'] >= high_20.iloc[-1]
        touched_low = last['low'] <= low_20.iloc[-1]
        high_atr = atr_pct_val > atr_75th.iloc[-1]
        small_body = (abs(last['close'] - last['open']) / (last['high'] - last['low'])) < 0.25
        
        confluence = 0
        signal = None
        
        if touched_high:
            confluence += 1
            if high_atr:
                confluence += 1
            if small_body:
                confluence += 1
            
            if confluence >= 2:
                signal = 'VENDA'
        
        if touched_low:
            confluence += 1
            if high_atr:
                confluence += 1
            if small_body:
                confluence += 1
            
            if confluence >= 2:
                signal = 'COMPRA'
        
        if signal:
            return {
                'signal': signal,
                'confluence': confluence,
                'entry_price': last['close']
            }
        
        return None
    
    def get_xgboost_score(self, df, symbol):
        """Calcular score XGBoost"""
        if symbol not in self.models or len(df) < 50:
            return 0.5
        
        try:
            df_features = self.feature_engineer.engineer_features(df)
            
            feature_cols = ['confluence', 'atr_pct', 'rsi', 'macd', 'macd_signal', 
                           'macd_histogram', 'bb_upper', 'bb_middle', 'bb_lower',
                           'atr_ratio', 'ema_12', 'ema_26', 'sma_20', 'sma_50',
                           'momentum', 'roc', 'stoch_k', 'stoch_d', 'obv', 
                           'volume_ratio', 'body', 'upper_wick', 'lower_wick',
                           'high_low_ratio', 'sma_trend', 'atr']
            
            df_features = df_features.fillna(0)
            
            X = df_features[feature_cols].iloc[-1:].values
            proba = self.models[symbol].predict_proba(X)[0][1]
            
            return proba
        
        except Exception as e:
            print(f"⚠️  Erro ao calcular score: {str(e)}")
            return 0.5
    
    def format_candle_message(self, symbol, df):
        """Formatar mensagem com dados do candle"""
        last = df.iloc[-1]
        last_time = df.index[-1]
        
        # Calcular indicadores para mensagem
        df_calc = self.feature_engineer.engineer_features(df)
        last_calc = df_calc.iloc[-1]
        
        # Obter score XGBoost
        score = self.get_xgboost_score(df, symbol)
        
        # Detectar sinal
        signal_info = self.detect_smc_signal(df)
        signal_status = ""
        
        if signal_info and score > 0.7:
            signal_status = f"\n\n<b>🎯 SINAL DETECTADO: {signal_info['signal'].upper()}</b>"
            signal_status += f"\n├─ Tipo: {signal_info['signal']}"
            signal_status += f"\n├─ Preço: {signal_info['entry_price']:.5f}"
            signal_status += f"\n└─ Confiança: {score*100:.1f}%"
        
        # Montar mensagem
        message = f"""
<b>📊 {symbol} - {last_time.strftime('%Y-%m-%d %H:%M:%S')}</b>

<b>💰 OHLC (M15):</b>
├─ Open:  <code>{last['open']:.5f}</code>
├─ High:  <code>{last['high']:.5f}</code>
├─ Low:   <code>{last['low']:.5f}</code>
└─ Close: <code>{last['close']:.5f}</code>

<b>📈 Indicadores Principais:</b>
├─ RSI(14):      <code>{last_calc['rsi']:.2f}</code>
├─ MACD:         <code>{last_calc['macd']:.6f}</code>
├─ BB Upper:     <code>{last_calc['bb_upper']:.5f}</code>
├─ EMA 12:       <code>{last_calc['ema_12']:.5f}</code>
├─ SMA 20:       <code>{last_calc['sma_20']:.5f}</code>
├─ ATR%:         <code>{last_calc['atr_pct']:.4f}</code>
├─ Momentum:     <code>{last_calc['momentum']:.6f}</code>
└─ Volume:       <code>{last['volume']:.0f}</code>

<b>🤖 XGBoost Avaliação:</b>
├─ Score: <code>{score*100:.1f}%</code>
├─ Categoria: {'🟢 HIGH' if score > 0.7 else '🟡 MEDIUM' if score > 0.5 else '🔴 LOW'}
└─ Status: {'✅ Ativo para Sinais' if score > 0.7 else '⏳ Aguardando'}{signal_status}
"""
        
        return message
    
    def monitor_pair(self, symbol):
        """Monitorar um par"""
        print(f"\n📊 {symbol}...")
        
        # Carregar dados
        df = self.load_realtime_data(symbol)
        if df is None or len(df) == 0:
            print(f"⚠️  Sem dados para {symbol}")
            return
        
        # Tempo do último candle
        last_time = df.index[-1]
        
        # Verificar se é novo candle
        if symbol in self.last_candle_times:
            if last_time == self.last_candle_times[symbol]:
                return  # Mesmo candle
        
        self.last_candle_times[symbol] = last_time
        
        # Formatar e enviar
        message = self.format_candle_message(symbol, df)
        print(f"✅ Candle {last_time.strftime('%H:%M:%S')} detectado")
        self.telegram.send_message(message)
    
    def run(self, interval_seconds=30):
        """Executar monitoramento"""
        print(f"\n{'='*100}")
        print(f"📡 MONITOR TEMPO REAL - DADOS REAIS DO MT5")
        print(f"{'='*100}\n")
        
        # Enviar status inicial
        startup_msg = """
<b>🤖 MONITOR TEMPO REAL INICIADO</b>

<b>⚙️ Configuração:</b>
├─ Hora Sistema: <code>""" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</code>
├─ Pares: GBPUSD, EURUSD, XAUUSD
├─ Timeframe: M15
├─ Indicadores: 25 técnicos completos
└─ XGBoost: Ativo

<b>📊 Aguardando novos candles...</b>
"""
        self.telegram.send_message(startup_msg)
        
        print("🚀 Monitorando dados reais...\n")
        
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checando...")
            
            for symbol in self.pares_config.keys():
                try:
                    self.monitor_pair(symbol)
                except Exception as e:
                    print(f"❌ Erro: {str(e)}")
            
            print(f"   ⏳ Aguardando próximo check...")
            
            try:
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                print(f"\n\n⛔ Monitor parado")
                break


def main():
    """Main"""
    BOT_TOKEN = '6024515460:AAFGPwqNStgL0mv3VfxCQ_ZyQS3CtdzOeF0'
    CHAT_ID = -1001735082183
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║    📡 MONITOR TEMPO REAL - DADOS REAIS + INDICADORES + XGBOOST                ║
╚════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    monitor = RealTimeMonitor(BOT_TOKEN, CHAT_ID)
    monitor.run(30)  # Checar a cada 30 segundos


if __name__ == '__main__':
    main()
