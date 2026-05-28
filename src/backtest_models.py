#!/usr/bin/env python3
"""
Backtest dos Modelos XGBoost com Alvos de Pips
Mostra: Taxa de acerto por alvo (10, 15, 20, 25 pips) e confiabilidade
"""

import pickle
import numpy as np
import os
from datetime import datetime, timedelta
from collections import defaultdict

class IndicatorCalculator:
    """Calcular indicadores para features"""
    
    @staticmethod
    def calculate_rsi(closes, period=14):
        """Calcular RSI"""
        if len(closes) < period + 1:
            return np.full(len(closes), 50.0)
        
        rsi = np.zeros(len(closes))
        rsi[:period] = 50.0  # Primeiros valores neutros
        
        for i in range(period, len(closes)):
            # Ganhos e perdas
            gains = []
            losses = []
            
            for j in range(i - period + 1, i + 1):
                change = closes[j] - closes[j-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(-change)
            
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            
            if avg_loss == 0:
                rsi[i] = 100 if avg_gain > 0 else 50
            else:
                rs = avg_gain / avg_loss
                rsi[i] = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_sma(closes, period):
        return np.convolve(closes, np.ones(period)/period, mode='same')
    
    @staticmethod
    def calculate_atr(highs, lows, closes, period=14):
        # True Range
        tr = np.zeros(len(closes))
        tr[0] = highs[0] - lows[0]
        
        for i in range(1, len(closes)):
            tr[i] = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
        
        # ATR
        atr = np.convolve(tr, np.ones(period)/period, mode='same')
        atr_pct = (atr / closes) * 100
        return atr_pct
    
    @staticmethod
    def extract_features(opens, highs, lows, closes, volumes):
        """Extrair 8 features"""
        n = len(closes)
        rsi_14 = IndicatorCalculator.calculate_rsi(closes, 14)
        sma_20 = IndicatorCalculator.calculate_sma(closes, 20)
        sma_50 = IndicatorCalculator.calculate_sma(closes, 50)
        atr_pct = IndicatorCalculator.calculate_atr(highs, lows, closes, 14)
        momentum = closes - sma_20
        confluence = np.zeros(n)
        for i in range(n):
            score = 0
            if closes[i] > sma_20[i]: score += 1
            if closes[i] > sma_50[i]: score += 1
            if rsi_14[i] > 50: score += 1
            confluence[i] = score
        volume_ma = IndicatorCalculator.calculate_sma(volumes.astype(float), 20)
        features = np.column_stack([
            rsi_14, sma_20, sma_50, atr_pct, momentum, confluence, closes, volume_ma
        ])
        return features


class BacktestAnalyzer:
    """Analisar performance dos modelos com diferentes alvos de pips"""
    
    def __init__(self, models_dir="/home/ubuntu/pessoal/options/src"):
        self.models_dir = models_dir
        self.models = {}
        self.symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
        self.pip_targets = [10, 15, 20, 25]  # Alvos em pips
        self.confidence_ranges = [
            (0.70, 1.0, '>70%'),
            (0.50, 0.70, '50-70%'),
            (0.0, 0.50, '<50%')
        ]
    
    def load_models(self):
        """Carregar modelos"""
        for symbol in self.symbols:
            filepath = f"{self.models_dir}/xgboost_{symbol}.pkl"
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    self.models[symbol] = pickle.load(f)
                print(f"✅ {symbol} carregado")
    
    def generate_synthetic_history(self, symbol, num_candles=500):
        """Gerar dados históricos sintéticos (simulação)"""
        # Para demo, geramos dados realistas
        prices = {'EURUSD': 1.0850, 'GBPUSD': 1.2700, 'XAUUSD': 2400.0}
        price = prices.get(symbol, 100)
        
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        for i in range(num_candles):
            # Movimento browniano realista
            change = np.random.normal(0, 0.00015) * price
            open_p = price
            close_p = price + change
            high_p = max(open_p, close_p) + np.random.uniform(0, 0.0001) * price
            low_p = min(open_p, close_p) - np.random.uniform(0, 0.0001) * price
            volume = np.random.randint(100000, 1000000)
            
            opens.append(open_p)
            highs.append(high_p)
            lows.append(low_p)
            closes.append(close_p)
            volumes.append(volume)
            
            price = close_p
        
        return np.array(opens), np.array(highs), np.array(lows), np.array(closes), np.array(volumes)
    
    def pips_from_price_change(self, symbol, price_change):
        """Converter mudança de preço para pips"""
        if symbol == 'XAUUSD':
            return price_change  # Gold é em centavos (não pips)
        else:
            # EUR/USD, GBP/USD: 1 pip = 0.0001
            return abs(price_change) * 10000
    
    def backtest_symbol(self, symbol):
        """Fazer backtest de um símbolo"""
        if symbol not in self.models:
            return None
        
        model = self.models[symbol]
        
        # Gerar dados históricos
        opens, highs, lows, closes, volumes = self.generate_synthetic_history(symbol, num_candles=300)
        
        # Calcular features para todo o histórico
        features = IndicatorCalculator.extract_features(opens, highs, lows, closes, volumes)
        
        # Fazer previsões (deixar 1 para próximo candle)
        predictions = model.predict(features[:-1])  # Excluir último (não tem próximo)
        confidences = model.predict_proba(features[:-1])  # Confidências
        
        # Pegar a confiança máxima (maior probabilidade)
        max_confidences = np.max(confidences, axis=1)
        
        # Calcular movimentos reais nos próximos candles
        actual_moves = closes[1:] - closes[:-1]  # 299 elementos
        
        # Contar acertos por alvo e confiança
        results = {}
        
        for pip_target in self.pip_targets:
            results[pip_target] = {}
            
            for conf_min, conf_max, label in self.confidence_ranges:
                # Filtrar por faixa de confiança
                mask = (max_confidences >= conf_min) & (max_confidences < conf_max)
                
                if np.sum(mask) == 0:
                    results[pip_target][label] = {'total': 0, 'acertos': 0, 'taxa': 0}
                    continue
                
                # Dados filtrados
                preds_filtered = predictions[mask]
                moves_filtered = actual_moves[mask]
                
                # Verificar acertos
                acertos = 0
                for i, pred in enumerate(preds_filtered):
                    move = moves_filtered[i]
                    pips_moved = self.pips_from_price_change(symbol, move)
                    
                    # pred = 1 (ALTA), pred = 0 (QUEDA)
                    if move > 0:  # Preço subiu
                        if pred == 1 and pips_moved >= pip_target:
                            acertos += 1
                    else:  # Preço caiu
                        if pred == 0 and pips_moved >= pip_target:
                            acertos += 1
                
                total = np.sum(mask)
                taxa = (acertos / total * 100) if total > 0 else 0
                
                results[pip_target][label] = {
                    'total': total,
                    'acertos': acertos,
                    'taxa': taxa
                }
        
        return results
    
    def run_backtest(self):
        """Executar backtest para todos os símbolos"""
        print("\n" + "╔" + "="*76 + "╗")
        print("║" + " "*20 + "📊 BACKTEST - TAXA DE ACERTO POR PIPS" + " "*20 + "║")
        print("╚" + "="*76 + "╝")
        
        print("\n🔄 Carregando modelos...")
        self.load_models()
        
        if not self.models:
            print("\n❌ Nenhum modelo encontrado!")
            return
        
        print("✅ Modelos carregados\n")
        
        # Backtest para cada símbolo
        for symbol in self.symbols:
            self.print_backtest_results(symbol)
    
    def print_backtest_results(self, symbol):
        """Imprimir resultados do backtest"""
        results = self.backtest_symbol(symbol)
        
        if not results:
            print(f"⚠️  {symbol}: Modelo não encontrado\n")
            return
        
        print("="*76)
        print(f"📈 {symbol}")
        print("="*76 + "\n")
        
        for pip_target in self.pip_targets:
            print(f"🎯 Alvo: {pip_target} pips")
            print("─" * 76)
            
            for conf_min, conf_max, label in self.confidence_ranges:
                data = results[pip_target][label]
                total = data['total']
                acertos = data['acertos']
                taxa = data['taxa']
                
                if total == 0:
                    status = "⚪"
                    desc = "SEM DADOS"
                elif taxa >= 60:
                    status = "🟢"
                    desc = "BOM"
                elif taxa >= 50:
                    status = "🟡"
                    desc = "NEUTRO"
                else:
                    status = "🔴"
                    desc = "RUIM"
                
                bar_length = int(taxa / 2)
                bar = "█" * bar_length + "░" * (50 - bar_length)
                
                print(f"  {status} Confiança {label:8} │ {bar} │ {taxa:5.1f}% ({acertos:2}/{total:2}) - {desc}")
            
            print()
    
    def print_summary(self):
        """Imprimir resumo final"""
        print("\n" + "="*76)
        print("📊 INTERPRETAÇÃO DOS RESULTADOS")
        print("="*76 + "\n")
        
        print("Taxa de Acerto:")
        print("  🟢 > 60% = BOM (use para trading)")
        print("  🟡 50-60% = NEUTRO (apenas com MM)")
        print("  🔴 < 50% = RUIM (não usar)")
        print()
        
        print("O que significa cada coluna:")
        print("  • Confiança >70% = Modelo MUITO seguro da previsão")
        print("  • Confiança 50-70% = Modelo MODERADAMENTE seguro")
        print("  • Confiança <50% = Modelo INCERTO (perto de 50/50)")
        print()
        
        print("Como usar:")
        print("  1. Se taxa >60% com confiança >70%:")
        print("     └─ Ótimo! Use este alvo")
        print()
        print("  2. Se taxa 50-60% com confiança >70%:")
        print("     └─ Bom, mas use com Money Management")
        print()
        print("  3. Se taxa <50%:")
        print("     └─ Não use, ou mude o alvo de pips")
        print()


def main():
    analyzer = BacktestAnalyzer()
    analyzer.run_backtest()
    analyzer.print_summary()
    
    print("\n" + "╔" + "="*76 + "╗")
    print("║  Backtest concluído! Estes são dados simulados para demonstração.  ║")
    print("║  Com dados reais do MT5, resultados serão muito mais acurados.   ║")
    print("╚" + "="*76 + "╝\n")


if __name__ == '__main__':
    main()
