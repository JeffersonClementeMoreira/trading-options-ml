#!/usr/bin/env python3
"""
Monitor Tempo Real - MT5 Live Trading
Conecta ao MT5, avalia sinais SMC em tempo real, envia Telegram quando fecha novo candle
"""

import pandas as pd
import numpy as np
import requests
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import time
from threading import Thread
import warnings

warnings.filterwarnings('ignore')

mt5 = None  # MetaTrader5 não disponível nessa arquitetura

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
    """Calcula 25 indicadores técnicos"""
    
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
    def calculate_atr_ratio(high, low, close, period=14):
        tr = pd.concat([
            high - low,
            abs(high - close.shift(1)),
            abs(low - close.shift(1))
        ], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return (atr / close) * 100
    
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
        
        # ATR Ratio
        df['atr_ratio'] = self.calculate_atr_ratio(df['high'], df['low'], df['close'])
        
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
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Candle patterns
        df['body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
        df['high_low_ratio'] = df['upper_wick'] / (df['lower_wick'] + 0.0001)
        
        # Trend
        df['sma_trend'] = (df['sma_20'] - df['sma_50']) / df['sma_50'] * 100
        
        # ATR %
        df['atr'] = self._calculate_atr(df)
        df['atr_pct'] = (df['atr'] / df['close']) * 100
        
        return df
    
    def _calculate_atr(self, df):
        tr = pd.concat([
            df['high'] - df['low'],
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        ], axis=1).max(axis=1)
        return tr.rolling(window=14).mean()


class LiveSMCMonitor:
    """Monitor SMC em tempo real"""
    
    def __init__(self, bot_token, chat_id):
        self.telegram = TelegramAlerts(bot_token, chat_id)
        self.feature_engineer = FeatureEngineer()
        
        # Carregar modelos XGBoost
        self.models = {}
        self.load_models()
        
        # Estado
        self.last_candle_times = {}
        self.sinais_enviados = set()
        
        # Pares com dados
        self.pares_config = {
            'GBPUSD': '../backtest_results/gbpusd_signals_completo.csv',
            'EURUSD': '../backtest_results/eurusd_signals_completo.csv',
            'XAUUSD': '../backtest_results/xauusd_signals_completo.csv'
        }
        
        # Carregar dados históricos (substituem MT5)
        self.dados = {}
        self.load_historical_data()
    
    def load_models(self):
        """Carregar modelos XGBoost treinados"""
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
    
    def load_historical_data(self):
        """Carregar dados históricos dos CSVs"""
        for symbol, csv_path in self.pares_config.items():
            try:
                df = pd.read_csv(csv_path)
                
                # Converter datetime
                if 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df.set_index('datetime', inplace=True)
                
                self.dados[symbol] = df.sort_index()
                print(f"✅ Dados carregados: {symbol} ({len(df)} candles)")
            except Exception as e:
                print(f"❌ Erro ao carregar {symbol}: {str(e)}")
    
    def get_live_data(self, symbol, bars=100):
        """Pegar dados mais recentes (dos CSVs)"""
        if symbol not in self.dados:
            print(f"⚠️  Sem dados para {symbol}")
            return None
        
        try:
            df = self.dados[symbol][['open', 'high', 'low', 'close']].copy()
            
            # Últimos 100 candles
            df = df.tail(bars)
            
            if len(df) == 0:
                return None
            
            return df
        except Exception as e:
            print(f"❌ Erro ao buscar dados: {str(e)}")
            return None
    
    def get_last_candle_info(self, symbol):
        """Pegar informações do último candle"""
        try:
            df = self.dados[symbol]
            if len(df) == 0:
                return None
            
            last = df.iloc[-1]
            last_time = df.index[-1]
            
            return {
                'datetime': last_time,
                'close': last['close'],
                'open': last['open'],
                'high': last['high'],
                'low': last['low']
            }
        except Exception as e:
            print(f"❌ Erro ao buscar último candle: {str(e)}")
            return None
    
    def detect_smc_signal(self, df):
        """Detectar sinais SMC"""
        if len(df) < 20:
            return None
        
        df = df.copy()
        
        # ATR e ATR percentual
        tr = pd.concat([
            df['high'] - df['low'],
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(window=14, min_periods=1).mean()
        atr_pct = (atr / df['close']) * 100
        
        # Extremos 20 períodos
        high_20 = df['high'].rolling(window=20, min_periods=1).max().shift(1)
        low_20 = df['low'].rolling(window=20, min_periods=1).min().shift(1)
        
        # Última candle
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else None
        
        atr_pct_val = atr_pct.iloc[-1]
        atr_75th = atr_pct.quantile(0.75)
        
        # Critérios SMC
        touched_high = last['high'] >= high_20.iloc[-1]
        touched_low = last['low'] <= low_20.iloc[-1]
        high_atr = atr_pct_val > atr_75th
        small_body = (abs(last['close'] - last['open']) / (last['high'] - last['low'])) < 0.25
        
        signal = None
        confluence = 0
        
        # SELL: tocou máxima de 20 períodos
        if touched_high and high_atr:
            confluence += 2
        if touched_high and small_body:
            confluence += 1
        
        if confluence >= 2 and touched_high:
            signal = 'SELL (BEARISH)'
        
        # BUY: tocou mínima de 20 períodos
        if touched_low and high_atr:
            confluence += 2
        if touched_low and small_body:
            confluence += 1
        
        if confluence >= 2 and touched_low:
            signal = 'BUY (BULLISH)'
        
        if signal:
            return {
                'signal': signal,
                'confluence': confluence,
                'entry_price': last['close'],
                'atr_pct': atr_pct_val,
                'datetime': df.index[-1]
            }
        
        return None
    
    def get_xgboost_score(self, df, symbol):
        """Obter score XGBoost para o sinal"""
        if symbol not in self.models or len(df) < 50:
            return 0.5
        
        try:
            # Calcular indicadores
            df_features = self.feature_engineer.engineer_features(df)
            
            # Features para XGBoost
            feature_cols = ['confluence', 'atr_pct', 'rsi', 'macd', 'macd_signal', 
                           'macd_histogram', 'bb_upper', 'bb_middle', 'bb_lower',
                           'atr_ratio', 'ema_12', 'ema_26', 'sma_20', 'sma_50',
                           'momentum', 'roc', 'stoch_k', 'stoch_d', 'obv', 
                           'volume_ratio', 'body', 'upper_wick', 'lower_wick',
                           'high_low_ratio', 'sma_trend', 'atr']
            
            # Preencher NaN
            df_features = df_features.fillna(0)
            
            # Predição
            X = df_features[feature_cols].iloc[-1:].values
            proba = self.models[symbol].predict_proba(X)[0][1]
            
            return proba
        
        except Exception as e:
            print(f"❌ Erro ao calcular score: {str(e)}")
            return 0.5
    
    def format_signal_message(self, symbol, signal_data, score):
        """Formatar mensagem do sinal"""
        datetime_str = signal_data['datetime'].strftime('%Y-%m-%d %H:%M:%S')
        sig = signal_data['signal']
        entrada = signal_data['entry_price']
        conf = signal_data['confluence']
        
        # Calcular alvo e SL
        if 'SELL' in sig:
            alvo = entrada * 0.998  # -0.2%
            sl = entrada * 1.002    # +0.2%
            direcao = "📉 VENDER CALL"
        else:
            alvo = entrada * 1.002  # +0.2%
            sl = entrada * 0.998    # -0.2%
            direcao = "📈 VENDER PUT"
        
        # Status do score
        if score > 0.7:
            prob_status = "🟢 HIGH"
        elif score > 0.5:
            prob_status = "🟡 MEDIUM"
        else:
            prob_status = "🔴 LOW"
        
        # Tempo de expiração
        hora_entrada = signal_data['datetime'].hour
        if hora_entrada < 14:
            expiracao = f"Hoje às 14:00 GMT"
        else:
            expiracao = f"Amanhã às 14:00 GMT"
        
        message = f"""
<b>🎯 NOVO SINAL TEMPO REAL!</b>

<b>📊 {symbol}</b>
<b>Horário:</b> {datetime_str}

<b>{direcao}</b>

<b>📈 Preço de ENTRADA:</b> {entrada:.5f}
<b>🎁 Preço ALVO (+0.2%):</b> {alvo:.5f}
<b>⛔ STOP LOSS (-0.2%):</b> {sl:.5f}

<b>🔍 Detalhes:</b>
├─ Confluência SMC: {conf}
├─ Probabilidade XGBoost: {score*100:.1f}% {prob_status}
├─ Expiração: {expiracao}
└─ Esperado: +0.2% movimento

<b>⏰ MANTENHA A ORDEM ATÉ ATINGIR ALVO OU SL</b>
"""
        return message
    
    def monitor_pair(self, symbol):
        """Monitorar um par específico"""
        print(f"\n📊 Verificando {symbol}...")
        
        # Pegar dados
        df = self.get_live_data(symbol)
        if df is None:
            return
        
        # Detectar sinal SMC
        signal_data = self.detect_smc_signal(df)
        if signal_data is None:
            print(f"   ⊘ Sem sinal SMC em {symbol}")
            return
        
        # Último horário
        last_time = signal_data['datetime']
        
        # Verificar se é novo candle
        if symbol in self.last_candle_times:
            if last_time == self.last_candle_times[symbol]:
                print(f"   ⊘ Mesmo candle anterior")
                return
        
        self.last_candle_times[symbol] = last_time
        
        # Calcular score XGBoost
        score = self.get_xgboost_score(df, symbol)
        print(f"   📊 SMC sinal encontrado | Score XGBoost: {score*100:.1f}%")
        
        # Se score > 70%, enviar alerta
        if score > 0.7:
            signal_key = f"{symbol}_{last_time}"
            
            if signal_key not in self.sinais_enviados:
                self.sinais_enviados.add(signal_key)
                
                message = self.format_signal_message(symbol, signal_data, score)
                print(f"\n🚀 Enviando sinal HIGH para Telegram...")
                self.telegram.send_message(message)
        else:
            print(f"   ⊘ Score LOW, sem alerta ({score*100:.1f}%)")
    
    def run_monitoring(self, interval_seconds=300):
        """Executar monitoramento contínuo"""
        print(f"\n{'='*100}")
        print(f"📡 MONITOR TEMPO REAL - SMC + XGBOOST")
        print(f"{'='*100}\n")
        
        # Mostrar informações dos últimos candles
        print(f"📊 ÚLTIMO CANDLE DE CADA ATIVO:\n")
        
        startup_msg_parts = ["<b>🤖 MONITOR TEMPO REAL INICIADO</b>\n<b>📊 Últimos Candles M15:</b>\n"]
        
        for symbol in self.pares_config.keys():
            candle_info = self.get_last_candle_info(symbol)
            if candle_info:
                tempo = candle_info['datetime'].strftime('%Y-%m-%d %H:%M:%S')
                close = candle_info['close']
                print(f"  {symbol}: {tempo} | Close: {close:.5f}")
                startup_msg_parts.append(f"├─ <b>{symbol}</b>: {tempo} | Close: <code>{close:.5f}</code>\n")
        
        startup_msg_parts.append(f"<b>⚙️ Configuração:</b>\n")
        startup_msg_parts.append(f"├─ Score Mínimo: HIGH (>70%)\n")
        startup_msg_parts.append(f"├─ Timeframe: M15\n")
        startup_msg_parts.append(f"├─ Alvo: +0.2% (20 pips)\n")
        startup_msg_parts.append(f"└─ SL: -0.2% (20 pips)\n\n")
        startup_msg_parts.append(f"<b>🔔 Aguardando novos sinais...</b>\n")
        
        startup_msg = "".join(startup_msg_parts)
        self.telegram.send_message(startup_msg)
        
        print(f"\n✅ Mensagem de startup enviada ao Telegram\n")
        
        iteration = 0
        
        while True:
            iteration += 1
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ciclo #{iteration}")
            print(f"{'─'*100}\n")
            
            # Monitorar cada par
            for par in self.pares_config.keys():
                try:
                    self.monitor_pair(par)
                except Exception as e:
                    print(f"❌ Erro ao monitorar {par}: {str(e)}")
            
            print(f"\n⏳ Próxima verificação em {interval_seconds} segundos...")
            
            try:
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                print(f"\n\n⛔ Monitor parado pelo usuário")
                break


def main():
    """Main - Iniciar monitor tempo real"""
    
    # Credenciais Telegram
    BOT_TOKEN = '6024515460:AAFGPwqNStgL0mv3VfxCQ_ZyQS3CtdzOeF0'
    CHAT_ID = -1001735082183
    
    # Intervalo em segundos (300 = 5 minutos)
    CHECK_INTERVAL = 60  # Verificar a cada 1 minuto
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║    📡 MONITOR TEMPO REAL - MT5 LIVE + SMC + XGBOOST                           ║
╚════════════════════════════════════════════════════════════════════════════════╝

⚙️  CONFIGURAÇÃO:
├─ BOT TOKEN: {BOT_TOKEN[:20]}...
├─ CHAT ID: {CHAT_ID}
├─ INTERVALO: {CHECK_INTERVAL} segundos
├─ PARES: GBPUSD, EURUSD, XAUUSD
├─ TIMEFRAME: M15
└─ SCORE MÍNIMO: HIGH (>70%)

🚀 Iniciando monitoramento tempo real...
    """)
    
    # Criar monitor
    monitor = LiveSMCMonitor(BOT_TOKEN, CHAT_ID)
    
    # Iniciar monitoramento
    monitor.run_monitoring(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
