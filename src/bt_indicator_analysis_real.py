#!/usr/bin/env python3
"""
Backtesting com Análise Real de Indicadores
- Carrega dados REAIS do MT5
- Calcula indicadores técnicos
- Identifica melhor combinação para prever alvo (próximo dia 14:00)
- Salva análise completa em CSV
"""

import csv
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import sys

class IndicatorAnalyzer:
    def __init__(self, csv_file, symbol):
        self.csv_file = csv_file
        self.symbol = symbol
        self.history = []
        self.results = []
        
    def load_csv(self):
        """Carrega CSV com formato MT5 (com ângulos)"""
        print(f"Carregando {self.symbol} de {self.csv_file}...")
        try:
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for i, row in enumerate(reader):
                    try:
                        # Remove ângulos do formato MT5
                        date_str = row['<DATE>'].strip()
                        time_str = row['<TIME>'].strip()
                        
                        # Parse datetime
                        dt = datetime.strptime(f"{date_str} {time_str}", "%Y.%m.%d %H:%M:%S")
                        
                        candle = {
                            'timestamp': dt,
                            'open': float(row['<OPEN>']),
                            'high': float(row['<HIGH>']),
                            'low': float(row['<LOW>']),
                            'close': float(row['<CLOSE>']),
                            'volume': int(row['<TICKVOL>'])
                        }
                        self.history.append(candle)
                    except Exception as e:
                        if i < 5:  # Skip header
                            continue
                        print(f"Erro na linha {i}: {e}")
                        continue
            
            print(f"✅ Carregados {len(self.history)} candles")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar: {e}")
            return False
    
    def calculate_sma(self, period=20):
        """Média móvel simples"""
        smas = [None] * len(self.history)
        for i in range(period - 1, len(self.history)):
            closes = [c['close'] for c in self.history[i - period + 1:i + 1]]
            smas[i] = np.mean(closes)
        return smas
    
    def calculate_rsi(self, period=14):
        """Relative Strength Index"""
        rsis = [None] * len(self.history)
        if len(self.history) < period:
            return rsis
        
        for i in range(period, len(self.history)):
            gains = []
            losses = []
            for j in range(i - period + 1, i + 1):
                change = self.history[j]['close'] - self.history[j - 1]['close']
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))
            
            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 0
            
            if avg_loss == 0:
                rsis[i] = 100 if avg_gain > 0 else 50
            else:
                rs = avg_gain / avg_loss
                rsis[i] = 100 - (100 / (1 + rs))
        
        return rsis
    
    def calculate_macd(self, fast=12, slow=26):
        """MACD"""
        ema_fast = self.calculate_ema(fast)
        ema_slow = self.calculate_ema(slow)
        
        macd = [None] * len(self.history)
        for i in range(len(self.history)):
            if ema_fast[i] and ema_slow[i]:
                macd[i] = ema_fast[i] - ema_slow[i]
        
        return macd
    
    def calculate_ema(self, period):
        """Exponential Moving Average"""
        emas = [None] * len(self.history)
        if len(self.history) < period:
            return emas
        
        # SMA inicial
        closes = [c['close'] for c in self.history[:period]]
        emas[period - 1] = np.mean(closes)
        
        multiplier = 2 / (period + 1)
        for i in range(period, len(self.history)):
            emas[i] = self.history[i]['close'] * multiplier + emas[i - 1] * (1 - multiplier)
        
        return emas
    
    def calculate_atr(self, period=14):
        """Average True Range"""
        atrs = [None] * len(self.history)
        if len(self.history) < 2:
            return atrs
        
        # Calcular True Range
        trs = []
        for i in range(1, len(self.history)):
            h = self.history[i]['high']
            l = self.history[i]['low']
            c_prev = self.history[i - 1]['close']
            
            tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
            trs.append(tr)
        
        # ATR é SMA do TR
        for i in range(period, len(self.history)):
            atrs[i] = np.mean(trs[i - period:i])
        
        return atrs
    
    def calculate_bollinger_bands(self, period=20, std_dev=2):
        """Bollinger Bands"""
        smv = self.calculate_sma(period)
        
        bbu = [None] * len(self.history)  # Upper Band
        bbl = [None] * len(self.history)  # Lower Band
        
        for i in range(period - 1, len(self.history)):
            closes = [c['close'] for c in self.history[i - period + 1:i + 1]]
            std = np.std(closes)
            bbu[i] = smv[i] + (std_dev * std) if smv[i] else None
            bbl[i] = smv[i] - (std_dev * std) if smv[i] else None
        
        return bbu, bbl
    
    def calculate_momentum(self, period=10):
        """Rate of Change"""
        momentum = [None] * len(self.history)
        for i in range(period, len(self.history)):
            change = self.history[i]['close'] - self.history[i - period]['close']
            momentum[i] = change
        return momentum
    
    def find_target_candle(self, idx):
        """Encontra o candle do próximo dia às 14:00"""
        current_dt = self.history[idx]['timestamp']
        target_date = current_dt.date() + timedelta(days=1)
        target_dt = datetime.combine(target_date, datetime.min.time().replace(hour=14))
        
        for i in range(idx + 1, min(idx + 100, len(self.history))):
            if self.history[i]['timestamp'] == target_dt:
                return i
        return None
    
    def calculate_direction_change(self, current_close, target_close):
        """Calcula se houve mudança de direção"""
        pips = (target_close - current_close) * 10000
        return 1 if pips > 0 else -1 if pips < 0 else 0
    
    def analyze(self):
        """Executa análise principal"""
        print(f"\nAnalisando indicadores para {self.symbol}...")
        
        # Calcular indicadores
        sma_20 = self.calculate_sma(20)
        sma_50 = self.calculate_sma(50)
        rsi = self.calculate_rsi(14)
        macd = self.calculate_macd()
        atr = self.calculate_atr(14)
        bbu, bbl = self.calculate_bollinger_bands(20)
        momentum = self.calculate_momentum(10)
        
        trades_analyzed = 0
        trades_valid = 0
        
        # Para cada candle, tenta prever o alvo
        for idx in range(100, len(self.history) - 100):  # Buffer para indicadores
            target_idx = self.find_target_candle(idx)
            if target_idx is None:
                continue
            
            trades_analyzed += 1
            
            # Dados do candle atual
            current_candle = self.history[idx]
            target_candle = self.history[target_idx]
            
            # Dados do indicador
            sma20_val = sma_20[idx] if sma_20[idx] else 0
            sma50_val = sma_50[idx] if sma_50[idx] else 0
            rsi_val = rsi[idx] if rsi[idx] else 50
            macd_val = macd[idx] if macd[idx] else 0
            atr_val = atr[idx] if atr[idx] else 0
            momentum_val = momentum[idx] if momentum[idx] else 0
            
            # Calcular sinais dos indicadores
            price_above_sma20 = 1 if current_candle['close'] > sma20_val else 0
            price_above_sma50 = 1 if current_candle['close'] > sma50_val else 0
            rsi_oversold = 1 if rsi_val < 30 else 0
            rsi_overbought = 1 if rsi_val > 70 else 0
            macd_positive = 1 if macd_val > 0 else 0
            momentum_positive = 1 if momentum_val > 0 else 0
            
            # Alvo real
            target_direction = self.calculate_direction_change(
                current_candle['close'],
                target_candle['close']
            )
            pips = (target_candle['close'] - current_candle['close']) * 10000
            
            # Score simples: quantos indicadores apontam para CIMA
            score = (price_above_sma20 + price_above_sma50 + 
                    (1 if rsi_val > 50 else 0) + macd_positive + momentum_positive) / 5
            
            # Previsão baseada no score
            predicted_direction = 1 if score > 0.5 else -1
            confidence = abs(score - 0.5) * 200  # 0-100
            accuracy = 1 if predicted_direction == target_direction else 0
            
            # Salvar resultado
            self.results.append({
                'timestamp': current_candle['timestamp'].isoformat(),
                'open': current_candle['open'],
                'high': current_candle['high'],
                'low': current_candle['low'],
                'close': current_candle['close'],
                'volume': current_candle['volume'],
                'sma20': round(sma20_val, 6),
                'sma50': round(sma50_val, 6),
                'rsi': round(rsi_val, 2),
                'macd': round(macd_val, 6),
                'atr': round(atr_val, 6),
                'momentum': round(momentum_val, 6),
                'price_above_sma20': price_above_sma20,
                'price_above_sma50': price_above_sma50,
                'rsi_oversold': rsi_oversold,
                'rsi_overbought': rsi_overbought,
                'macd_positive': macd_positive,
                'momentum_positive': momentum_positive,
                'predicted_direction': 'UP' if predicted_direction > 0 else 'DOWN',
                'confidence': round(confidence, 2),
                'target_direction': 'UP' if target_direction > 0 else 'DOWN',
                'pips': round(pips, 1),
                'accuracy': accuracy
            })
            
            trades_valid += 1
        
        print(f"✅ Analisados {trades_valid} trades com alvo válido")
        return trades_valid
    
    def save_results(self, output_file=None):
        """Salva resultados em CSV"""
        if output_file is None:
            output_file = f"/tmp/bt_analysis_{self.symbol}.csv"
        
        if not self.results:
            print("❌ Nenhum resultado para salvar")
            return False
        
        try:
            with open(output_file, 'w', newline='') as f:
                fieldnames = [
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'sma20', 'sma50', 'rsi', 'macd', 'atr', 'momentum',
                    'price_above_sma20', 'price_above_sma50',
                    'rsi_oversold', 'rsi_overbought', 'macd_positive',
                    'momentum_positive', 'predicted_direction', 'confidence',
                    'target_direction', 'pips', 'accuracy'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
            
            print(f"✅ Resultados salvos em {output_file}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            return False
    
    def print_summary(self):
        """Imprime resumo das análises"""
        if not self.results:
            return
        
        accuracy_values = [r['accuracy'] for r in self.results]
        pips_values = [r['pips'] for r in self.results]
        
        total_trades = len(self.results)
        wins = sum(accuracy_values)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        total_pips = sum(pips_values)
        avg_pips = (total_pips / total_trades) if total_trades > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"RESUMO - {self.symbol}")
        print(f"{'='*60}")
        print(f"Total de trades:        {total_trades}")
        print(f"Wins:                   {wins} ({win_rate:.1f}%)")
        print(f"Total de pips:          {total_pips:.1f}")
        print(f"Pips médios por trade:  {avg_pips:.1f}")
        print(f"{'='*60}")

def main():
    # Analisar EURUSD
    eu = IndicatorAnalyzer(
        "/home/ubuntu/pessoal/options/data/EURUSD_M15_202401012200_20260522201" + "5.csv",
        "EURUSD"
    )
    if eu.load_csv():
        eu.analyze()
        eu.save_results()
        eu.print_summary()
    
    # Analisar GBPUSD
    gb = IndicatorAnalyzer(
        "/home/ubuntu/pessoal/options/data/GBPUSD_M15_202401012200_20260522201" + "5.csv",
        "GBPUSD"
    )
    if gb.load_csv():
        gb.analyze()
        gb.save_results()
        gb.print_summary()
    
    print(f"\n✅ Análise completa!")
    print(f"Arquivos gerados:")
    print(f"  /tmp/bt_analysis_EURUSD.csv")
    print(f"  /tmp/bt_analysis_GBPUSD.csv")

if __name__ == "__main__":
    main()
