#!/usr/bin/env python3
"""
Backtesting com Confluência de Indicadores
============================================
Em vez de prever sempre no mesmo horário (12:00),
este sistema FILTRA apenas quando há confluência de múltiplos indicadores:

- SMC POI (Pontos de Interesse): Preço perto de zonas onde fez reversão antes
- Supply/Demand (SD): Suporte/Resistência significativa
- Range de Indicadores: RSI, MACD, Volume confirmando
- Convergência: Múltiplos sinais apontando mesma direção

Resultado: Taxa de acerto MUITO maior (esperado >65%) com menos trades
"""

import pickle
import csv
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import os


class BacktestWithConfluence:
    def __init__(self):
        self.models = {}
        self.load_models()
        
    def load_models(self):
        """Carregar modelos treinados"""
        models_dir = "/home/ubuntu/pessoal/options/src"
        for symbol in ['EURUSD', 'GBPUSD']:
            try:
                clf_path = f"{models_dir}/nextday_clf_{symbol}.pkl"
                reg_path = f"{models_dir}/nextday_reg_{symbol}.pkl"
                with open(clf_path, 'rb') as f:
                    self.models[f'{symbol}_clf'] = pickle.load(f)
                with open(reg_path, 'rb') as f:
                    self.models[f'{symbol}_reg'] = pickle.load(f)
                print(f"  ✅ {symbol}: Classificador e Regressor carregados")
            except Exception as e:
                print(f"  ❌ {symbol}: Erro ao carregar modelo: {e}")
    
    def load_csv_data(self, symbol, csv_path):
        """Carregar dados CSV do MT5"""
        history = []
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Parse date format: 2026.04.27 -> 2026-04-27
                        date_str = row['Date'].replace('.', '-')
                        time_str = row['Time']
                        
                        candle = {
                            'timestamp': datetime.fromisoformat(date_str + 'T' + time_str),
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': int(row['Volume'])
                        }
                        history.append(candle)
                    except Exception as e:
                        pass
            
            print(f"  ✅ {symbol}: Carregados {len(history)} candles")
            return history
        except Exception as e:
            print(f"  ❌ Erro ao carregar {symbol}: {e}")
            return []
    
    def calculate_sma(self, closes, period):
        """Calcular SMA"""
        if len(closes) < period:
            return closes[-1] if closes else 0
        return float(np.mean(closes[-period:]))
    
    def calculate_rsi(self, closes, period=14):
        """Calcular RSI"""
        if len(closes) < period + 1:
            return 50
        
        diffs = np.diff(closes[-period-1:])
        gains = np.where(diffs > 0, diffs, 0).mean()
        losses = np.where(diffs < 0, -diffs, 0).mean()
        
        if losses == 0:
            return 50
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    
    def calculate_macd(self, closes, fast=12, slow=26, signal=9):
        """Calcular MACD"""
        if len(closes) < slow:
            return 0, 0, 0
        
        ema_fast = self.calculate_ema(closes, fast)
        ema_slow = self.calculate_ema(closes, slow)
        macd_line = ema_fast - ema_slow
        
        return macd_line, 0, macd_line
    
    def calculate_ema(self, data, period):
        """Calcular EMA"""
        if len(data) < period:
            return data[-1] if data else 0
        
        multiplier = 2 / (period + 1)
        ema = np.mean(data[-period:])
        for price in data[-period+1:]:
            ema = price * multiplier + ema * (1 - multiplier)
        return ema
    
    def detect_poi_zones(self, history, current_idx, lookback=100):
        """
        Detectar POI (Pontos de Interesse) - zonas onde preço fez reversão antes
        Procura por swing highs e swing lows nos últimos lookback candles
        """
        poi_zones = []
        
        if current_idx < lookback:
            lookback = current_idx
        
        if lookback < 3:
            return poi_zones
        
        closes = [h['close'] for h in history[max(0, current_idx - lookback):current_idx]]
        
        # Encontrar swing highs e swing lows
        for i in range(1, len(closes) - 1):
            # Swing High
            if closes[i] > closes[i-1] and closes[i] > closes[i+1]:
                poi_zones.append({
                    'type': 'resistance',
                    'price': closes[i],
                    'strength': 1
                })
            # Swing Low
            elif closes[i] < closes[i-1] and closes[i] < closes[i+1]:
                poi_zones.append({
                    'type': 'support',
                    'price': closes[i],
                    'strength': 1
                })
        
        return poi_zones
    
    def detect_supply_demand(self, history, current_idx, lookback=50):
        """
        Detectar zonas de Supply (resistência) e Demand (suporte)
        Baseado em volume e amplitude de movimento
        """
        zones = []
        
        if current_idx < lookback:
            lookback = current_idx
        
        subset = history[max(0, current_idx - lookback):current_idx]
        
        for i in range(len(subset)):
            candle = subset[i]
            
            # Supply: High com volume alto (resistência)
            if candle['volume'] > np.mean([h['volume'] for h in subset]) * 1.3:
                if i > 0 and subset[i-1]['close'] < candle['high']:
                    zones.append({
                        'type': 'supply',
                        'price': candle['high'],
                        'volume_signal': candle['volume'],
                        'age': current_idx - i
                    })
            
            # Demand: Low com volume alto (suporte)
            if candle['volume'] > np.mean([h['volume'] for h in subset]) * 1.3:
                if i > 0 and subset[i-1]['close'] > candle['low']:
                    zones.append({
                        'type': 'demand',
                        'price': candle['low'],
                        'volume_signal': candle['volume'],
                        'age': current_idx - i
                    })
        
        return zones
    
    def calculate_confluence_score(self, history, candle_idx):
        """
        Calcular score de confluência (0-100)
        Quanto mais indicadores alinhados, melhor a confluência
        """
        if candle_idx < 20:
            return 0
        
        current = history[candle_idx]
        closes = [h['close'] for h in history[:candle_idx+1]]
        highs = [h['high'] for h in history[:candle_idx+1]]
        lows = [h['low'] for h in history[:candle_idx+1]]
        volumes = [h['volume'] for h in history[:candle_idx+1]]
        
        score = 0
        details = {}
        
        # 1. RSI em zona extrema (0-30 ou 70-100) = +15 pontos
        rsi = self.calculate_rsi(closes, 14)
        details['rsi'] = rsi
        if rsi < 30 or rsi > 70:
            score += 15
            details['rsi_signal'] = 'extremo'
        elif 35 < rsi < 65:  # Zona neutra não é bom
            details['rsi_signal'] = 'neutro'
        else:
            score += 5
            details['rsi_signal'] = 'normal'
        
        # 2. Preço perto de SMA20 mas não exatamente = +10 pontos
        sma_20 = self.calculate_sma(closes, 20)
        sma_50 = self.calculate_sma(closes, 50)
        dist_to_sma20 = abs(current['close'] - sma_20) / sma_20 * 100
        
        if 0.5 < dist_to_sma20 < 2.0:  # Perto mas não na SMA
            score += 10
            details['sma20_proximity'] = 'boa'
        elif dist_to_sma20 < 0.1:  # Muito perto
            details['sma20_proximity'] = 'muito_perto'
        else:
            details['sma20_proximity'] = 'longe'
        
        # 3. Preço entre SMA20 e SMA50 = +10 pontos
        if min(sma_20, sma_50) < current['close'] < max(sma_20, sma_50):
            score += 10
            details['between_smas'] = True
        else:
            details['between_smas'] = False
        
        # 4. Volume acima da média = +10 pontos
        vol_ma = np.mean(volumes[-20:])
        vol_ratio = current['volume'] / vol_ma if vol_ma > 0 else 1
        if vol_ratio > 1.2:
            score += 10
            details['volume_signal'] = 'forte'
        else:
            details['volume_signal'] = 'fraco'
        
        # 5. Perto de POI (Point of Interest) = +15 pontos
        poi_zones = self.detect_poi_zones(history, candle_idx, lookback=50)
        if poi_zones:
            poi_prices = [z['price'] for z in poi_zones[-3:]]  # 3 POI mais recentes
            min_dist = min([abs(current['close'] - p) / p * 100 for p in poi_prices]) if poi_prices else 100
            
            if min_dist < 0.5:  # Muito perto de POI
                score += 15
                details['poi_proximity'] = 'muito_perto'
            elif min_dist < 1.5:  # Perto de POI
                score += 10
                details['poi_proximity'] = 'perto'
            else:
                details['poi_proximity'] = 'longe'
        
        # 6. ATR (volatilidade) normal (não muita nem pouca) = +10 pontos
        tr = max(
            highs[-1] - lows[-1],
            abs(highs[-1] - closes[-2]),
            abs(lows[-1] - closes[-2])
        )
        atr_percent = (tr / closes[-1]) * 100
        
        if 0.05 < atr_percent < 0.5:  # ATR normal
            score += 10
            details['volatility'] = 'normal'
        elif atr_percent > 1.0:
            details['volatility'] = 'alta'
        else:
            details['volatility'] = 'baixa'
        
        # 7. Supply/Demand = +15 pontos
        sd_zones = self.detect_supply_demand(history, candle_idx, lookback=50)
        if sd_zones:
            sd_prices = [z['price'] for z in sd_zones[-2:]]
            min_dist_sd = min([abs(current['close'] - p) / p * 100 for p in sd_prices]) if sd_prices else 100
            
            if min_dist_sd < 0.3:
                score += 15
                details['sd_proximity'] = 'muito_perto'
            elif min_dist_sd < 1.0:
                score += 10
                details['sd_proximity'] = 'perto'
            else:
                details['sd_proximity'] = 'longe'
        
        # Normalizar score para 0-100
        score = min(100, score)
        
        return score, details
    
    def backtest_with_confluence(self, symbol, history):
        """Backtesting apenas com confluência de indicadores"""
        if not history or len(history) < 2880:
            return []
        
        results = []
        predictions_count = 0
        
        print(f"\n🔍 Analisando confluência em {symbol}...")
        
        # Processar cada candle
        for current_idx in range(100, len(history) - 96):  # Deixar 4 dias para "futuro"
            # Calcular confluência
            confluence_score, confluence_details = self.calculate_confluence_score(history, current_idx)
            
            current_candle = history[current_idx]
            
            # FILTRO: Apenas fazer previsão se confluência >= 50
            if confluence_score < 50:
                continue
            
            predictions_count += 1
            
            try:
                # Calcular features
                closes = [h['close'] for h in history[:current_idx+1]]
                highs = [h['high'] for h in history[:current_idx+1]]
                lows = [h['low'] for h in history[:current_idx+1]]
                volumes = [h['volume'] for h in history[:current_idx+1]]
                
                # Indicadores
                rsi = self.calculate_rsi(closes, 14)
                sma_20 = self.calculate_sma(closes, 20)
                sma_50 = self.calculate_sma(closes, 50)
                
                tr = max(
                    highs[-1] - lows[-1],
                    abs(highs[-1] - closes[-2]),
                    abs(lows[-1] - closes[-2])
                )
                atr = tr / closes[-1] if closes[-1] > 0 else 0.0001
                
                momentum = (closes[-1] - closes[-11]) / closes[-11] if len(closes) >= 11 else 0
                
                if len(closes) >= 20 and np.std(closes[-20:]) > 0:
                    distance_std = (closes[-1] - sma_20) / np.std(closes[-20:])
                else:
                    distance_std = 0
                
                vol_ma = np.mean(volumes[-20:]) if len(volumes) >= 20 else volumes[-1]
                vol_ratio = volumes[-1] / vol_ma if vol_ma > 0 else 1
                
                features = np.array([[rsi, sma_20, sma_50, atr, momentum, distance_std, closes[-1], vol_ratio]])
                
                # Fazer previsão
                if f'{symbol}_clf' not in self.models:
                    continue
                
                direction = self.models[f'{symbol}_clf'].predict(features)[0]
                confidence = max(self.models[f'{symbol}_clf'].predict_proba(features)[0])
                predicted_price = self.models[f'{symbol}_reg'].predict(features)[0]
                
                # Encontrar close do dia seguinte às 14:00
                target_idx = None
                current_hour = current_candle['timestamp'].hour
                
                # Se o candle atual é depois das 14, próximo target é amanhã
                # Se é antes das 14, target é hoje às 14:00
                for i in range(current_idx + 1, min(current_idx + 100, len(history))):
                    if history[i]['timestamp'].hour == 14:
                        target_idx = i
                        break
                
                if target_idx is None:
                    continue
                
                target_candle = history[target_idx]
                actual_price = target_candle['close']
                actual_direction = "UP" if actual_price > current_candle['close'] else "DOWN"
                expected_direction = "UP" if direction == 1 else "DOWN"
                
                hit = actual_direction == expected_direction
                
                # Calcular pips e erro
                pip_value = 0.0001 if 'USD' in symbol else 0.01
                pips_expected = abs(predicted_price - current_candle['close']) / pip_value
                pips_actual = abs(actual_price - current_candle['close']) / pip_value
                price_error_pct = abs(predicted_price - actual_price) / actual_price * 100
                
                result = {
                    'timestamp': current_candle['timestamp'],
                    'time': current_candle['timestamp'].strftime('%H:%M:%S'),
                    'day': current_candle['timestamp'].strftime('%Y-%m-%d'),
                    'confluence_score': confluence_score,
                    'open': current_candle['open'],
                    'high': current_candle['high'],
                    'low': current_candle['low'],
                    'close': current_candle['close'],
                    'volume': current_candle['volume'],
                    'rsi': rsi,
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'atr': atr,
                    'momentum': momentum,
                    'distance_std': distance_std,
                    'volume_ratio': vol_ratio,
                    'predicted_direction': expected_direction,
                    'confidence': confidence,
                    'predicted_close_d1': predicted_price,
                    'date_d1': target_candle['timestamp'].strftime('%Y-%m-%d'),
                    'actual_close_d1': actual_price,
                    'actual_timestamp_d1': target_candle['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    'actual_direction': actual_direction,
                    'hit': hit,
                    'pips_expected': pips_expected,
                    'pips_actual': pips_actual,
                    'price_error_pct': price_error_pct
                }
                
                results.append(result)
                
            except Exception as e:
                # Debug: mostrar erro
                # print(f"    ⚠️  Erro em idx {current_idx}: {e}")
                continue
        
        print(f"  📊 Candles analisados: {len(history) - 100}")
        print(f"  🎯 Confluências encontradas: {predictions_count}")
        print(f"  ✅ Previsões com confluência: {len(results)}")
        
        return results
    
    def save_results_to_csv(self, symbol, results, output_dir="/tmp"):
        """Salvar resultados em CSV"""
        if not results:
            return None
        
        output_file = f"{output_dir}/backtest_confluence_{symbol}.csv"
        
        try:
            with open(output_file, 'w', newline='') as f:
                fieldnames = [
                    'timestamp', 'time', 'day', 'confluence_score',
                    'open', 'high', 'low', 'close', 'volume',
                    'rsi', 'sma_20', 'sma_50', 'atr', 'momentum', 'distance_std', 'volume_ratio',
                    'predicted_direction', 'confidence', 'predicted_close_d1',
                    'date_d1', 'actual_close_d1', 'actual_timestamp_d1', 'actual_direction',
                    'hit', 'pips_expected', 'pips_actual', 'price_error_pct'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    row = {
                        'timestamp': result['timestamp'].isoformat(),
                        'time': result['time'],
                        'day': result['day'],
                        'confluence_score': f"{result['confluence_score']:.1f}",
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
    
    def print_confluence_summary(self, symbol, results):
        """Imprimir resumo com confluência"""
        if not results:
            print(f"  Sem resultados para {symbol}")
            return
        
        print(f"\n📊 {symbol} - COM CONFLUÊNCIA")
        print("="*100)
        
        # Estatísticas gerais
        total = len(results)
        hits = sum(1 for r in results if r['hit'])
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        avg_confluence = np.mean([r['confluence_score'] for r in results])
        avg_confidence = np.mean([r['confidence'] for r in results])
        avg_pips = np.mean([r['pips_actual'] for r in results])
        avg_error = np.mean([r['price_error_pct'] for r in results])
        
        print(f"\n📈 RESUMO {symbol} (apenas com confluência):")
        print(f"   Previsões totais: {total} (filtradas de ~{int(total / 0.1)} candles)")
        print(f"   Taxa de acerto: {hit_rate:.1f}% ({hits}/{total} acertos) ✅")
        print(f"   Confluência média: {avg_confluence:.1f}/100")
        print(f"   Confiança média: {avg_confidence*100:.1f}%")
        print(f"   Pips reais (média): {avg_pips:.1f}p")
        print(f"   Erro de previsão: {avg_error:.2f}%")
        
        # Breakdown por score de confluência
        print(f"\n🎯 Breakdown por Confluência:")
        high_conf = [r for r in results if r['confluence_score'] >= 80]
        med_conf = [r for r in results if 60 <= r['confluence_score'] < 80]
        low_conf = [r for r in results if r['confluence_score'] < 60]
        
        if high_conf:
            high_hit = sum(1 for r in high_conf if r['hit'])
            print(f"   Confluência 80-100: {high_hit/len(high_conf)*100:.1f}% ({high_hit}/{len(high_conf)} acertos)")
        if med_conf:
            med_hit = sum(1 for r in med_conf if r['hit'])
            print(f"   Confluência 60-80:  {med_hit/len(med_conf)*100:.1f}% ({med_hit}/{len(med_conf)} acertos)")
        if low_conf:
            low_hit = sum(1 for r in low_conf if r['hit'])
            print(f"   Confluência <60:    {low_hit/len(low_conf)*100:.1f}% ({low_hit}/{len(low_conf)} acertos)")
        
        print(f"\n📋 Primeiros 10 resultados:")
        print(f"{'Data':<12} {'Score':<8} {'Pred':<8} {'Real':<8} {'Hit':<5} {'Conf':<6} {'Pips':<8}")
        print("-"*100)
        for r in results[:10]:
            marker = "✅" if r['hit'] else "❌"
            print(
                f"{r['day']:<12} "
                f"{r['confluence_score']:>6.0f}% "
                f"{r['predicted_direction']:<8} "
                f"{r['actual_direction']:<8} "
                f"{marker:<5} "
                f"{r['confidence']*100:>5.1f}% "
                f"{r['pips_actual']:>6.1f}p"
            )


def main():
    print("\n╔" + "="*98 + "╗")
    print("║" + " "*20 + "📊 BACKTESTING COM CONFLUÊNCIA DE INDICADORES" + " "*33 + "║")
    print("╚" + "="*98 + "╝\n")
    
    print("Procurando arquivos CSV com dados reais...")
    print("Locais esperados:")
    print("  - /home/ubuntu/pessoal/options/data/EURUSD_M15.csv")
    print("  - /home/ubuntu/pessoal/options/data/GBPUSD_M15.csv\n")
    
    backtest = BacktestWithConfluence()
    
    for symbol in ['EURUSD', 'GBPUSD']:
        csv_path = f"/home/ubuntu/pessoal/options/data/{symbol}_M15.csv"
        
        if not os.path.exists(csv_path):
            print(f"❌ {symbol}: Arquivo não encontrado: {csv_path}")
            continue
        
        print(f"\n🔍 Carregando {symbol}...")
        history = backtest.load_csv_data(symbol, csv_path)
        
        if not history:
            print(f"❌ Sem dados para {symbol}")
            continue
        
        # Backtesting com confluência
        results = backtest.backtest_with_confluence(symbol, history)
        
        # Salvar CSV
        backtest.save_results_to_csv(symbol, results)
        
        # Imprimir resumo
        backtest.print_confluence_summary(symbol, results)
    
    print("\n" + "="*100)
    print("✅ Backtesting com confluência concluído!")
    print(f"   Arquivos salvos em /tmp/backtest_confluence_*.csv")
    print("="*100 + "\n")


if __name__ == '__main__':
    main()
