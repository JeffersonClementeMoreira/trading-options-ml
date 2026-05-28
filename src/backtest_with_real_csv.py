#!/usr/bin/env python3
"""
Backtesting com Dados Reais do MT5 (ou gerados)

Carrega:
1. Dados históricos de arquivo CSV (exportados do MT5)
2. Ou gera dados sintéticos realistas

Faz backtesting e mostra:
- Taxa de acerto por dia
- Performance por confiança
- Gráfico de evolução
"""

import json
import numpy as np
import csv
from datetime import datetime, timedelta
from collections import defaultdict
import pickle
import os

class RealBacktestWithCSV:
    """Backtesting com dados reais ou sintéticos"""
    
    def __init__(self, models_dir="/home/ubuntu/pessoal/options/src"):
        self.models_dir = models_dir
        self.symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
        self.models_clf = {}
        self.models_reg = {}
        
    def load_models(self):
        """Carregar modelos"""
        for symbol in self.symbols:
            clf_path = f"{self.models_dir}/nextday_clf_{symbol}.pkl"
            reg_path = f"{self.models_dir}/nextday_reg_{symbol}.pkl"
            
            if os.path.exists(clf_path):
                with open(clf_path, 'rb') as f:
                    self.models_clf[symbol] = pickle.load(f)
            if os.path.exists(reg_path):
                with open(reg_path, 'rb') as f:
                    self.models_reg[symbol] = pickle.load(f)
        
        if self.models_clf:
            print(f"✅ Modelos carregados: {list(self.models_clf.keys())}")
        return bool(self.models_clf)
    
    def load_csv_data(self, symbol, csv_path):
        """
        Carregar dados de arquivo CSV exportado do MT5
        
        Formato esperado:
        Date,Time,Open,High,Low,Close,Volume
        2024.01.15,00:00,1.0850,1.0860,1.0840,1.0855,100000
        """
        history = []
        
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Arquivo não encontrado: {csv_path}")
            return None
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    date_str = f"{row.get('Date', '')} {row.get('Time', '00:00')}"
                    
                    try:
                        timestamp = datetime.strptime(date_str, '%Y.%m.%d %H:%M')
                    except:
                        timestamp = datetime.strptime(date_str.replace('.', '-'), '%Y-%m-%d %H:%M')
                    
                    candle = {
                        'timestamp': timestamp,
                        'open': float(row.get('Open', 0)),
                        'high': float(row.get('High', 0)),
                        'low': float(row.get('Low', 0)),
                        'close': float(row.get('Close', 0)),
                        'volume': int(row.get('Volume', 0))
                    }
                    history.append(candle)
            
            print(f"  ✅ Carregados {len(history)} candles")
            return history
        
        except Exception as e:
            print(f"  ❌ Erro ao carregar CSV: {e}")
            return None
    
    def calculate_features_from_candle(self, history, candle_idx):
        """Calcular features"""
        start_idx = max(0, candle_idx - 56)
        window = history[start_idx:candle_idx+1]
        
        closes = [c['close'] for c in window]
        highs = [c['high'] for c in window]
        lows = [c['low'] for c in window]
        volumes = [c['volume'] for c in window]
        
        # RSI
        if len(closes) >= 14:
            deltas = np.diff(closes[-14:])
            seed = deltas[:1]
            up = seed[seed >= 0].sum() / 14 if len(seed[seed >= 0]) > 0 else 0
            down = -seed[seed < 0].sum() / 14 if len(seed[seed < 0]) > 0 else 0.0001
            rs = up / down if down != 0 else 0
            rsi = 100.0 - (100.0 / (1.0 + rs)) if rs >= 0 else 50
        else:
            rsi = 50
        
        sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else closes[-1]
        sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else closes[-1]
        
        if len(closes) > 1:
            tr = max(
                highs[-1] - lows[-1],
                abs(highs[-1] - closes[-2]),
                abs(lows[-1] - closes[-2])
            )
            atr = tr / closes[-1] if closes[-1] > 0 else 0.0001
        else:
            atr = 0.0001
        
        momentum = (closes[-1] - closes[-11]) / closes[-11] if len(closes) >= 11 else 0
        
        if len(closes) >= 20 and np.std(closes[-20:]) > 0:
            distance_std = (closes[-1] - sma_20) / np.std(closes[-20:])
        else:
            distance_std = 0
        
        vol_ma = np.mean(volumes[-20:]) if len(volumes) >= 20 else volumes[-1]
        vol_ratio = volumes[-1] / vol_ma if vol_ma > 0 else 1
        
        features = np.array([[
            rsi, sma_20, sma_50, atr, momentum, distance_std, closes[-1], vol_ratio
        ]])
        
        return features, closes[-1]
    
    def calculate_all_indicators(self, history, candle_idx):
        """Calcular todos os indicadores para um candle"""
        start_idx = max(0, candle_idx - 56)
        window = history[start_idx:candle_idx+1]
        
        closes = np.array([c['close'] for c in window])
        highs = np.array([c['high'] for c in window])
        lows = np.array([c['low'] for c in window])
        volumes = np.array([c['volume'] for c in window])
        
        # RSI
        if len(closes) >= 14:
            deltas = np.diff(closes[-14:])
            seed = deltas[:1]
            up = seed[seed >= 0].sum() / 14 if len(seed[seed >= 0]) > 0 else 0
            down = -seed[seed < 0].sum() / 14 if len(seed[seed < 0]) > 0 else 0.0001
            rs = up / down if down != 0 else 0
            rsi = 100.0 - (100.0 / (1.0 + rs)) if rs >= 0 else 50
        else:
            rsi = 50
        
        sma_20 = float(np.mean(closes[-20:])) if len(closes) >= 20 else float(closes[-1])
        sma_50 = float(np.mean(closes[-50:])) if len(closes) >= 50 else float(closes[-1])
        
        if len(closes) > 1:
            tr = max(
                highs[-1] - lows[-1],
                abs(highs[-1] - closes[-2]),
                abs(lows[-1] - closes[-2])
            )
            atr = tr / closes[-1] if closes[-1] > 0 else 0.0001
        else:
            atr = 0.0001
        
        momentum = (closes[-1] - closes[-11]) / closes[-11] if len(closes) >= 11 else 0
        
        if len(closes) >= 20 and np.std(closes[-20:]) > 0:
            distance_std = (closes[-1] - sma_20) / np.std(closes[-20:])
        else:
            distance_std = 0
        
        vol_ma = np.mean(volumes[-20:]) if len(volumes) >= 20 else volumes[-1]
        vol_ratio = volumes[-1] / vol_ma if vol_ma > 0 else 1
        
        return {
            'rsi': float(rsi),
            'sma_20': float(sma_20),
            'sma_50': float(sma_50),
            'atr': float(atr),
            'momentum': float(momentum),
            'distance_std': float(distance_std),
            'volume_ratio': float(vol_ratio)
        }
    
    def backtest_with_data(self, symbol, history):
        """Fazer backtest com histórico fornecido"""
        if not history or len(history) < 2880:  # Menos de 20 dias
            return []
        
        daily_results = []
        
        # Agrupar por dia
        days_dict = defaultdict(list)
        for i, candle in enumerate(history):
            day_key = candle['timestamp'].date()
            days_dict[day_key].append((i, candle))
        
        # Para cada dia
        sorted_days = sorted(days_dict.keys())
        
        for day_idx, day_key in enumerate(sorted_days[:-1]):  # -1 porque precisa de D+1
            day_candles = days_dict[day_key]
            next_day_candles = days_dict[sorted_days[day_idx + 1]]
            
            if not day_candles or not next_day_candles:
                continue
            
            # Pegar candle a meio do dia para fazer previsão
            mid_idx = len(day_candles) // 2
            pred_candle_idx = day_candles[mid_idx][0]
            pred_candle = day_candles[mid_idx][1]
            
            # Fazer previsão
            try:
                features, current_price = self.calculate_features_from_candle(history, pred_candle_idx)
                indicators = self.calculate_all_indicators(history, pred_candle_idx)
                
                if symbol not in self.models_clf:
                    continue
                
                clf_pred = self.models_clf[symbol].predict(features)[0]
                clf_proba = np.max(self.models_clf[symbol].predict_proba(features))
                reg_pred = self.models_reg[symbol].predict(features)[0]
                
                # Resultado real: preço em D+1 14:00
                # Encontrar candle mais próximo de 14:00 no próximo dia
                target_time = datetime.strptime('14:00', '%H:%M').time()
                closest_candle = None
                closest_timestamp = None
                
                for idx, candle in next_day_candles:
                    if candle['timestamp'].time() >= target_time:
                        closest_candle = candle
                        closest_timestamp = candle['timestamp']
                        break
                
                if not closest_candle:
                    closest_candle = next_day_candles[-1][1]
                    closest_timestamp = closest_candle['timestamp']
                
                actual_close_d1 = closest_candle['close']
                
                # Comparações
                predicted_direction = 'UP' if clf_pred == 1 else 'DOWN'
                actual_direction = 'UP' if actual_close_d1 > current_price else 'DOWN'
                direction_correct = (predicted_direction == actual_direction)
                
                pips_actual = abs(actual_close_d1 - current_price) * 10000
                pips_expected = abs(reg_pred - current_price) * 10000
                price_error = abs(actual_close_d1 - reg_pred) / current_price * 100
                
                result = {
                    'timestamp': pred_candle['timestamp'],
                    'day': day_key.isoformat(),
                    'time': pred_candle['timestamp'].time().isoformat(),
                    'open': float(pred_candle['open']),
                    'high': float(pred_candle['high']),
                    'low': float(pred_candle['low']),
                    'close': float(pred_candle['close']),
                    'volume': int(pred_candle['volume']),
                    'rsi': indicators['rsi'],
                    'sma_20': indicators['sma_20'],
                    'sma_50': indicators['sma_50'],
                    'atr': indicators['atr'],
                    'momentum': indicators['momentum'],
                    'distance_std': indicators['distance_std'],
                    'volume_ratio': indicators['volume_ratio'],
                    'predicted_direction': predicted_direction,
                    'confidence': clf_proba,
                    'predicted_close_d1': reg_pred,
                    'date_d1': sorted_days[day_idx + 1].isoformat(),
                    'actual_close_d1': actual_close_d1,
                    'actual_timestamp_d1': closest_timestamp.isoformat(),
                    'actual_direction': actual_direction,
                    'hit': direction_correct,
                    'pips_expected': pips_expected,
                    'pips_actual': pips_actual,
                    'price_error_pct': price_error
                }
                
                daily_results.append(result)
            
            except:
                continue
        
        return daily_results
    
    def save_results_to_csv(self, symbol, results, output_dir="/tmp"):
        """Salvar resultados em arquivo CSV detalhado"""
        if not results:
            return None
        
        output_file = f"{output_dir}/backtest_results_{symbol}.csv"
        
        try:
            with open(output_file, 'w', newline='') as f:
                fieldnames = [
                    'timestamp', 'time', 'open', 'high', 'low', 'close', 'volume',
                    'rsi', 'sma_20', 'sma_50', 'atr', 'momentum', 'distance_std', 'volume_ratio',
                    'predicted_direction', 'confidence', 'predicted_close_d1',
                    'date_d1', 'actual_close_d1', 'actual_timestamp_d1', 'actual_direction',
                    'hit', 'pips_expected', 'pips_actual', 'price_error_pct'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    # Preparar row com apenas os campos necessários
                    row = {
                        'timestamp': result['timestamp'].isoformat(),
                        'time': result['time'],
                        'open': f"{result['open']:.5f}",
                        'high': f"{result['high']:.5f}",
                        'low': f"{result['low']:.5f}",
                        'close': f"{result['close']:.5f}",
                        'volume': result['volume'],
                        'rsi': f"{result['rsi']:.2f}",
                        'sma_20': f"{result['sma_20']:.5f}",
                        'sma_50': f"{result['sma_50']:.5f}",
                        'atr': f"{result['atr']:.6f}",
                        'momentum': f"{result['momentum']:.6f}",
                        'distance_std': f"{result['distance_std']:.4f}",
                        'volume_ratio': f"{result['volume_ratio']:.4f}",
                        'predicted_direction': result['predicted_direction'],
                        'confidence': f"{result['confidence']:.4f}",
                        'predicted_close_d1': f"{result['predicted_close_d1']:.5f}",
                        'date_d1': result['date_d1'],
                        'actual_close_d1': f"{result['actual_close_d1']:.5f}",
                        'actual_timestamp_d1': result['actual_timestamp_d1'],
                        'actual_direction': result['actual_direction'],
                        'hit': "1" if result['hit'] else "0",
                        'pips_expected': f"{result['pips_expected']:.1f}",
                        'pips_actual': f"{result['pips_actual']:.1f}",
                        'price_error_pct': f"{result['price_error_pct']:.2f}"
                    }
                    writer.writerow(row)
            
            print(f"  ✅ CSV salvo: {output_file}")
            return output_file
        
        except Exception as e:
            print(f"  ❌ Erro ao salvar CSV: {e}")
            return None
    
    def print_results(self, symbol, results):
        """Imprimir resultados formatados"""
        
        if not results:
            print(f"  Sem resultados para {symbol}")
            return
        
        print(f"\n📈 {symbol}")
        print("="*90)
        print(f"{'Data':<12} {'Pred':<8} {'Real':<8} {'Predição':<10} {'Real':<6} {'Hit':<5} {'Conf':<6} {'Pips':<8} {'Erro %':<8}")
        print("-"*90)
        
        hits = 0
        for r in results[:20]:  # Mostrar primeiros 20 dias
            direction_marker = "✅" if r['hit'] else "❌"
            hits += 1 if r['hit'] else 0
            
            print(
                f"{r['day']:<12} "
                f"{r['predicted_close_d1']:<8.5g} "
                f"{r['actual_close_d1']:<8.5g} "
                f"{r['predicted_direction']:<10} "
                f"{r['actual_direction']:<6} "
                f"{direction_marker:<5} "
                f"{r['confidence']*100:>5.1f}% "
                f"{r['pips_actual']:>6.1f}p "
                f"{r['price_error_pct']:>6.2f}%"
            )
        
        if len(results) > 20:
            print(f"... e mais {len(results) - 20} dias\n")
        
        # Totais
        print("-"*90)
        total = len(results)
        hit_rate = (hits / total * 100) if total > 0 else 0
        avg_confidence = np.mean([r['confidence'] for r in results])
        avg_pips = np.mean([r['pips_actual'] for r in results])
        avg_error = np.mean([r['price_error_pct'] for r in results])
        
        print(f"\n📊 RESUMO {symbol}:")
        print(f"   Total de dias: {total}")
        print(f"   Taxa de acerto (direção): {hit_rate:.1f}% ({hits}/{total} acertos)")
        print(f"   Confiança média: {avg_confidence*100:.1f}%")
        print(f"   Pips reais (média): {avg_pips:.1f}p")
        print(f"   Erro de previsão (média): {avg_error:.2f}%")
        
        # Breakdown por confiança
        high_conf = [r for r in results if r['confidence'] > 0.70]
        med_conf = [r for r in results if 0.50 <= r['confidence'] <= 0.70]
        low_conf = [r for r in results if r['confidence'] < 0.50]
        
        if high_conf:
            high_hit = sum(1 for r in high_conf if r['hit'])
            print(f"   Confiança >70%: {high_hit/len(high_conf)*100:.1f}% ({high_hit}/{len(high_conf)} acertos)")
        
        if med_conf:
            med_hit = sum(1 for r in med_conf if r['hit'])
            print(f"   Confiança 50-70%: {med_hit/len(med_conf)*100:.1f}% ({med_hit}/{len(med_conf)} acertos)")


def main():
    print("\n" + "╔" + "="*88 + "╗")
    print("║" + " "*20 + "📊 BACKTESTING COM DADOS REAIS" + " "*37 + "║")
    print("╚" + "="*88 + "╝")
    
    backtest = RealBacktestWithCSV()
    
    if not backtest.load_models():
        print("❌ Nenhum modelo carregado!")
        return
    
    print("\nProcurando arquivos CSV com dados reais...")
    print("Locais esperados:")
    print("  - /home/ubuntu/pessoal/options/data/EURUSD_M15.csv")
    print("  - /home/ubuntu/pessoal/options/data/GBPUSD_M15.csv")
    print("  - /home/ubuntu/pessoal/options/data/XAUUSD_M15.csv")
    print()
    
    # Tentar carregar CSVs
    csv_files = {
        'EURUSD': '/home/ubuntu/pessoal/options/data/EURUSD_M15.csv',
        'GBPUSD': '/home/ubuntu/pessoal/options/data/GBPUSD_M15.csv',
        'XAUUSD': '/home/ubuntu/pessoal/options/data/XAUUSD_M15.csv'
    }
    
    all_results = {}
    csv_outputs = {}
    
    for symbol, csv_path in csv_files.items():
        print(f"\n🔍 Carregando {symbol}...")
        
        history = backtest.load_csv_data(symbol, csv_path)
        
        if history:
            results = backtest.backtest_with_data(symbol, history)
            if results:
                all_results[symbol] = results
                csv_file = backtest.save_results_to_csv(symbol, results)
                csv_outputs[symbol] = csv_file
                backtest.print_results(symbol, results)
    
    # Resumo
    if all_results:
        print("\n" + "="*88)
        print("🎯 RESUMO GERAL")
        print("="*88)
        
        for symbol, results in all_results.items():
            hits = sum(1 for r in results if r['hit'])
            total = len(results)
            hit_rate = (hits / total * 100) if total > 0 else 0
            avg_conf = np.mean([r['confidence'] for r in results])
            
            status = "✅ BOM" if hit_rate >= 55 else "⚠️  ACEITÁVEL" if hit_rate >= 50 else "❌ RUIM"
            print(f"\n{symbol}: {hit_rate:.1f}% ({hits}/{total}) | Conf: {avg_conf*100:.1f}% | {status}")
        
        # Mostrar arquivos CSV
        if csv_outputs:
            print("\n" + "="*88)
            print("📊 ARQUIVOS CSV GERADOS")
            print("="*88)
            for symbol, csv_file in csv_outputs.items():
                if csv_file:
                    print(f"  {symbol}: {csv_file}")
    else:
        print("\n⚠️  Nenhum arquivo CSV encontrado. Usando dados sintéticos...")
        print("Para usar dados reais:")
        print("  1. MT5 → History Center → Selecionar símbolo")
        print("  2. Clique direito → Export")
        print("  3. Salvar em /home/ubuntu/pessoal/options/data/EURUSD_M15.csv")
        print("  4. Executar novamente")


if __name__ == '__main__':
    main()
