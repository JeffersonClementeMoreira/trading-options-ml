#!/usr/bin/env python3
"""
Monitor em Tempo Real com Alertas Telegram
Acompanha sinais SMC com XGBoost e envia para Telegram
"""

import pandas as pd
import numpy as np
import requests
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import json
import time
from threading import Thread

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


class SMCMonitor:
    """Monitor SMC com XGBoost em tempo real"""
    
    def __init__(self, bot_token, chat_id):
        self.telegram = TelegramAlerts(bot_token, chat_id)
        self.pares = {
            'GBPUSD': '../output/gbpusd_with_scores.csv',
            'EURUSD': '../output/eurusd_with_scores.csv',
            'XAUUSD': '../output/xauusd_with_scores.csv',
            'USDJPY': None,
            'AUDUSD': None
        }
        self.sinais_enviados = {}  # Rastrear sinais já enviados
    
    def load_signals(self, par):
        """Carregar sinais do CSV"""
        csv_path = self.pares[par]
        
        if csv_path is None:
            return None
        
        try:
            df = pd.read_csv(csv_path)
            return df[df['score_category'] == 'HIGH (>70%)'].copy()
        except Exception as e:
            print(f"❌ Erro ao carregar {par}: {str(e)}")
            return None
    
    def format_signal_message(self, par, signal):
        """Formatar mensagem com sinal"""
        datetime_str = signal['datetime']
        sig = signal['signal'].replace(' (BEARISH)', '').replace(' (BULLISH)', '')
        entrada = signal['entry_price']
        conf = int(signal['confluence'])
        prob = signal['win_probability']
        
        # Calcular alvo e SL
        if 'SELL' in signal['signal']:
            # SELL: alvo abaixo, SL acima
            alvo = entrada * 0.998  # 0.2% abaixo
            sl = entrada * 1.002    # 0.2% acima
            direcao = "📉 VENDER CALL"
        else:
            # BUY: alvo acima, SL abaixo
            alvo = entrada * 1.002  # 0.2% acima
            sl = entrada * 0.998    # 0.2% abaixo
            direcao = "📈 VENDER PUT"
        
        # Formatar mensagem
        message = f"""
<b>🎯 NOVO SINAL IDENTIFICADO!</b>

<b>📊 {par}</b>
<b>Horário:</b> {datetime_str}

<b>{direcao}</b>

<b>📈 Preço de ENTRADA:</b> {entrada:.5f}
<b>🎁 Preço ALVO (+0.2%):</b> {alvo:.5f}
<b>⛔ STOP LOSS (-0.2%):</b> {sl:.5f}

<b>🔍 Detalhes do Sinal:</b>
├─ Confluência: {conf}
├─ Probabilidade XGBoost: {prob*100:.1f}% ✅
├─ Expiração: Hoje às 14:00 GMT
└─ Esperado: +0.2% movimento

<b>⏰ Aguarde o sinal para abertura da ordem</b>
"""
        return message
    
    def get_key_signal(self, par, row):
        """Gerar chave única para sinal"""
        return f"{par}_{row['datetime']}"
    
    def monitor_pair(self, par):
        """Monitorar um par específico"""
        print(f"\n📊 Monitorando {par}...")
        
        signals = self.load_signals(par)
        
        if signals is None or len(signals) == 0:
            print(f"⚠️ Nenhum sinal HIGH para {par}")
            return
        
        # Verificar apenas sinais do hoje
        today = datetime.now().date()
        
        for idx, signal in signals.iterrows():
            signal_datetime = pd.to_datetime(signal['datetime']).date()
            
            # Usar apenas sinais de hoje ou muito recentes
            if signal_datetime != today:
                continue
            
            key = self.get_key_signal(par, signal)
            
            # Se sinal já foi enviado, skip
            if key in self.sinais_enviados:
                continue
            
            # Marcar como enviado
            self.sinais_enviados[key] = True
            
            # Formatar e enviar mensagem
            message = self.format_signal_message(par, signal)
            print(f"\n📲 Enviando alerta para {par}...")
            self.telegram.send_message(message)
            
            # Aguardar um pouco entre mensagens
            time.sleep(1)
    
    def send_startup_message(self):
        """Enviar mensagem inicial"""
        startup_msg = """
<b>🤖 MONITOR SMC + XGBOOST INICIADO</b>

<b>📡 Pares Monitorados:</b>
✅ GBPUSD (64% WR → 92% com XGBoost)
✅ EURUSD (44% WR → 93% com XGBoost)
✅ XAUUSD (GOLD) - 4.200 sinais HIGH
⏳ USDJPY
⏳ AUDUSD

<b>⚙️ Configuração:</b>
├─ Score Mínimo: HIGH (>70%)
├─ Timeframe: M15
├─ Alvo: +0.2% (20 pips)
└─ SL: -0.2% (20 pips)

<b>🎯 Modo:</b> BACKTESTING (dados históricos)

<b>📊 Verificando sinais...</b>
"""
        self.telegram.send_message(startup_msg)
    
    def run_continuous_monitoring(self, interval_seconds=300):
        """Executar monitoramento contínuo"""
        print(f"\n{'='*100}")
        print(f"🤖 INICIANDO MONITOR TELEGRAM - SMC + XGBOOST")
        print(f"{'='*100}\n")
        
        self.send_startup_message()
        
        iteration = 0
        
        while True:
            iteration += 1
            print(f"\n[{datetime.now()}] Ciclo #{iteration}")
            print(f"{'─'*100}\n")
            
            # Monitorar cada par
            for par in self.pares.keys():
                try:
                    self.monitor_pair(par)
                except Exception as e:
                    print(f"❌ Erro ao monitorar {par}: {str(e)}")
            
            # Aguardar próximo ciclo
            print(f"\n⏳ Próxima checagem em {interval_seconds} segundos...")
            print(f"   (Pressione Ctrl+C para parar)\n")
            
            try:
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                print(f"\n\n⛔ Monitor parado pelo usuário")
                break


def main():
    """Main - Iniciar monitor"""
    
    # Credenciais Telegram
    BOT_TOKEN = '6024515460:AAFGPwqNStgL0mv3VfxCQ_ZyQS3CtdzOeF0'
    CHAT_ID = -1001735082183
    
    # Intervalo de monitoramento (em segundos)
    CHECK_INTERVAL = 300  # 5 minutos
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════════╗
║         📲 MONITOR TELEGRAM - SMC + XGBOOST EM TEMPO REAL                     ║
╚════════════════════════════════════════════════════════════════════════════════╝

⚙️  CONFIGURAÇÃO:
├─ BOT TOKEN: {BOT_TOKEN[:20]}...
├─ CHAT ID: {CHAT_ID}
├─ INTERVALO: {CHECK_INTERVAL} segundos
└─ PARES: GBPUSD, EURUSD, XAUUSD, USDJPY, AUDUSD

Iniciando monitoramento...
    """)
    
    # Criar monitor
    monitor = SMCMonitor(BOT_TOKEN, CHAT_ID)
    
    # Iniciar monitoramento contínuo
    monitor.run_continuous_monitoring(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
