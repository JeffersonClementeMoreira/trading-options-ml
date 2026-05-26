#!/usr/bin/env python3
"""
Monitor Simples - Confirmação de Funcionamento
Simula novos candles fechando e envia mensagem simples ao Telegram
"""

import pandas as pd
import requests
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


class SimpleMonitor:
    """Monitor simples para confirmação de funcionamento"""
    
    def __init__(self, bot_token, chat_id):
        self.telegram = TelegramAlerts(bot_token, chat_id)
        
        # Pares
        self.pares_config = {
            'GBPUSD': '../backtest_results/gbpusd_signals_completo.csv',
            'EURUSD': '../backtest_results/eurusd_signals_completo.csv',
            'XAUUSD': '../backtest_results/xauusd_signals_completo.csv'
        }
        
        # Carregar dados
        self.dados = {}
        self.load_data()
        
        # Estado: simular tempo atual começando do último candle
        self.current_time = None
        self.initialize_time()
    
    def load_data(self):
        """Carregar dados de cada par"""
        for symbol, csv_path in self.pares_config.items():
            try:
                df = pd.read_csv(csv_path)
                
                if 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df.set_index('datetime', inplace=True)
                
                self.dados[symbol] = df.sort_index()
                print(f"✅ Dados carregados: {symbol}")
            except Exception as e:
                print(f"❌ Erro ao carregar {symbol}: {str(e)}")
    
    def initialize_time(self):
        """Inicializar tempo simulado a partir do último candle"""
        times = []
        
        for symbol, df in self.dados.items():
            if len(df) > 0:
                times.append(df.index[-1])
        
        if times:
            self.current_time = max(times)
            print(f"⏰ Tempo simulado iniciando em: {self.current_time}")
        else:
            self.current_time = datetime.now()
    
    def simulate_next_candle(self):
        """Simular próximo candle: avança 15 minutos"""
        self.current_time += timedelta(minutes=15)
    
    def get_current_closes(self):
        """Pegar closes mais próximos do tempo simulado"""
        result = {}
        
        for symbol, df in self.dados.items():
            # Pegar candle mais próximo (anterior ou igual) ao tempo simulado
            candles_before = df[df.index <= self.current_time]
            
            if len(candles_before) > 0:
                last_close = candles_before.iloc[-1]
                result[symbol] = {
                    'datetime': candles_before.index[-1],
                    'close': last_close['close']
                }
        
        return result
    
    def send_status_message(self):
        """Enviar mensagem de confirmação de funcionamento"""
        closes = self.get_current_closes()
        
        if not closes:
            print("⚠️  Sem dados para enviar")
            return
        
        # Montar mensagem
        msg_parts = [
            f"<b>✅ MONITOR FUNCIONANDO</b>\n",
            f"<b>Hora Simulada:</b> <code>{self.current_time.strftime('%Y-%m-%d %H:%M:%S')}</code>\n\n",
            f"<b>📊 Últimos Closes M15:</b>\n"
        ]
        
        for symbol, data in closes.items():
            tempo = data['datetime'].strftime('%H:%M:%S')
            close = data['close']
            msg_parts.append(f"├─ <b>{symbol}</b>: {tempo} | Close: <code>{close:.5f}</code>\n")
        
        msg_parts.append(f"\n<b>🔔 Sistema aguardando novos sinais...</b>")
        
        message = "".join(msg_parts)
        
        # Print e enviar
        print(f"\n[{self.current_time.strftime('%Y-%m-%d %H:%M:%S')}] Enviando status...")
        print(message.replace('<b>', '').replace('</b>', '').replace('<code>', '').replace('</code>', ''))
        
        self.telegram.send_message(message)
    
    def run(self, interval_seconds=60):
        """Executar monitoramento contínuo"""
        print(f"\n{'='*100}")
        print(f"📡 MONITOR SIMPLES - CONFIRMAÇÃO DE FUNCIONAMENTO")
        print(f"{'='*100}\n")
        
        # Enviar mensagem inicial
        print("🚀 Iniciando monitoramento...\n")
        self.send_status_message()
        
        iteration = 0
        
        while True:
            iteration += 1
            
            # Aguardar intervalo
            print(f"\n⏳ Próximo candle em {interval_seconds}s...")
            try:
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                print(f"\n\n⛔ Monitor parado pelo usuário")
                break
            
            # Simular novo candle
            self.simulate_next_candle()
            
            # Enviar status
            self.send_status_message()


def main():
    """Main - Iniciar monitor simples"""
    
    # Credenciais Telegram
    BOT_TOKEN = '6024515460:AAFGPwqNStgL0mv3VfxCQ_ZyQS3CtdzOeF0'
    CHAT_ID = -1001735082183
    
    # Intervalo: a cada 1 minuto
    CHECK_INTERVAL = 60
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║         📡 MONITOR SIMPLES - CONFIRMAÇÃO DE FUNCIONAMENTO                     ║
╚════════════════════════════════════════════════════════════════════════════════╝

⚙️  CONFIGURAÇÃO:
├─ Intervalo: {CHECK_INTERVAL} segundos
├─ Pares: GBPUSD, EURUSD, XAUUSD
├─ Timeframe: M15
└─ Modo: Simulação (aguardando dados reais do MT5)

🚀 Iniciando...
    """)
    
    # Criar monitor
    monitor = SimpleMonitor(BOT_TOKEN, CHAT_ID)
    
    # Iniciar
    monitor.run(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
