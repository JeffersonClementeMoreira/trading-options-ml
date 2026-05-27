#!/usr/bin/env python3
"""
ANÁLISE MULTI-ALVO - Backtest com múltiplos targets
Testa: 50, 75, 100, 150, 200 pips
Requisito: Mínimo 50 pips para cobrir custos operacionais
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from datetime import datetime

MODELS_DIR = Path("/home/ubuntu/pessoal/options/models")
DATA_DIR = Path("/home/ubuntu/pessoal/options/data")

class MultiTargetAnalysis:
    def __init__(self):
        self.targets = [50, 75, 100, 150, 200]
        
    @staticmethod
    def _rsi(closes, period=14):
        """Calcula RSI"""
        deltas = np.diff(closes)
        up = deltas.copy()
        up[up < 0] = 0
        down = -deltas.copy()
        down[down < 0] = 0
        
        rs = np.zeros_like(closes)
        rs[period] = up[:period].sum() / (down[:period].sum() + 1e-10)
        
        for i in range(period + 1, len(closes)):
            rs[i] = (up[i-1] * (period - 1) + rs[i-1] * period) / period / \
                    ((down[i-1] * (period - 1) + rs[i-1] * period) / period + 1e-10)
        
        return 100 - (100 / (1 + rs + 1e-10))

    @staticmethod
    def _atr(highs, lows, closes, period=14):
        """Calcula ATR"""
        tr1 = highs - lows
        tr2 = np.abs(highs - closes[:-1])
        tr3 = np.abs(lows - closes[:-1])
        
        tr = np.concatenate(([tr1[0]], np.maximum(np.maximum(tr1[1:], tr2), tr3)))
        atr = np.mean(tr[-period:])
        return atr

    def calculate_indicators(self, closes, highs, lows, volumes):
        """Retorna dicionário com indicadores"""
        if len(closes) < 50:
            return None
        
        closes_arr = np.array(closes, dtype=float)
        highs_arr = np.array(highs, dtype=float)
        lows_arr = np.array(lows, dtype=float)
        
        indicators = {
            "rsi_14": self._rsi(closes_arr, 14),
            "sma_20": np.mean(closes_arr[-20:]),
            "sma_50": np.mean(closes_arr[-50:]),
            "close": closes_arr[-1],
            "high": highs_arr[-1],
            "low": lows_arr[-1],
        }
        
        atr = self._atr(highs_arr, lows_arr, closes_arr, 14)
        indicators["atr_pct"] = (atr / closes_arr[-1]) * 100 if closes_arr[-1] != 0 else 0
        indicators["momentum"] = closes_arr[-1] - closes_arr[-13]
        indicators["volume"] = volumes[-1] if volumes else 1
        indicators["confluence"] = 0  # placeholder
        
        return indicators

    def backtest_symbol(self, symbol, csv_path, model_path, pip_unit):
        """Faz backtest para um símbolo"""
        print(f"\n📊 {symbol}")
        print("─" * 80)
        
        # Carregar dados
        try:
            df = pd.read_csv(csv_path, sep='\t', index_col=False)
            if len(df.columns) == 1:
                df = pd.read_csv(csv_path)
            df.columns = df.columns.str.lower()
            df.columns = df.columns.str.strip('<>')
            df.columns = df.columns.str.strip()
            print(f"✅ Dados: {len(df):,} candles")
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return None
        
        # Carregar modelo
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            print(f"✅ Modelo carregado")
        except Exception as e:
            print(f"❌ Erro ao carregar modelo: {e}")
            return None
        
        results = {}
        
        # Testar cada target
        for target_pips in self.targets:
            target_price = target_pips * pip_unit
            stop_loss = 10 * pip_unit
            
            wins = 0
            losses = 0
            total_pips = 0
            trades = 0
            
            # Backtest
            for i in range(50, len(df) - 96):
                try:
                    closes = df['close'].values[:i+1].astype(float)
                    highs = df['high'].values[:i+1].astype(float)
                    lows = df['low'].values[:i+1].astype(float)
                    volumes = df['vol'].values[:i+1] if 'vol' in df.columns else df['tickvol'].values[:i+1]
                    
                    indicators = self.calculate_indicators(closes, highs, lows, volumes)
                    if not indicators:
                        continue
                    
                    # Preparar features
                    features = np.array([[
                        indicators["rsi_14"],
                        indicators["sma_20"],
                        indicators["sma_50"],
                        indicators["atr_pct"],
                        indicators["momentum"],
                        indicators["confluence"],
                        indicators["close"],
                        indicators["volume"]
                    ]])
                    
                    # Previsão
                    try:
                        if hasattr(model, 'predict_proba'):
                            prob = model.predict_proba(features)[0]
                            pred = 1 if prob[1] > 0.5 else 0
                        else:
                            pred = model.predict(features)[0]
                    except:
                        continue
                    
                    entry_price = closes[-1]
                    
                    # Simular saída
                    for j in range(i + 1, min(i + 97, len(df))):
                        high = float(df.iloc[j]['high'])
                        low = float(df.iloc[j]['low'])
                        
                        if pred == 1:  # COMPRA
                            if high >= entry_price + target_price:
                                wins += 1
                                total_pips += target_pips
                                trades += 1
                                break
                            elif low <= entry_price - stop_loss:
                                losses += 1
                                total_pips -= 10
                                trades += 1
                                break
                        else:  # VENDA
                            if low <= entry_price - target_price:
                                wins += 1
                                total_pips += target_pips
                                trades += 1
                                break
                            elif high >= entry_price + stop_loss:
                                losses += 1
                                total_pips -= 10
                                trades += 1
                                break
                
                except Exception as e:
                    continue
            
            if trades > 0:
                win_rate = (wins / trades) * 100
                avg_pips = total_pips / trades
                results[target_pips] = {
                    "wins": wins,
                    "losses": losses,
                    "trades": trades,
                    "win_rate": win_rate,
                    "total_pips": total_pips,
                    "avg_pips": avg_pips
                }
        
        return results

    def print_results(self, symbol, results):
        """Imprime resultados"""
        if not results:
            print("⚠️ Nenhum trade realizado\n")
            return
        
        print(f"\n{'Target':>8} | {'Trades':>8} | {'Wins':>8} | {'Win%':>8} | {'Pips/Trade':>12} | {'Total Pips':>12} | {'Viável':>10}")
        print("─" * 80)
        
        best_target = None
        best_rate = 0
        
        for target in sorted(results.keys()):
            r = results[target]
            viable = "✅ SIM" if (r['win_rate'] >= 50 and r['total_pips'] > 0) else "❌ NÃO"
            
            print(f"{target:>8} | {r['trades']:>8,} | {r['wins']:>8,} | {r['win_rate']:>7.1f}% | "
                  f"{r['avg_pips']:>11.2f} | {r['total_pips']:>11.0f} | {viable:>10}")
            
            if r['win_rate'] >= 50 and r['total_pips'] > 0 and r['win_rate'] > best_rate:
                best_rate = r['win_rate']
                best_target = target
        
        if best_target:
            r = results[best_target]
            print(f"\n🎯 RECOMENDAÇÃO: {best_target} pips (WR: {r['win_rate']:.1f}%)\n")
        else:
            print("\n⚠️ Nenhum target viável\n")

    def run(self):
        """Executa análise completa"""
        print("\n" + "╔" + "=" * 78 + "╗")
        print("║" + "ANÁLISE MULTI-ALVO - EURUSD E GBPUSD".center(78) + "║")
        print("╚" + "=" * 78 + "╝")
        
        # EURUSD
        eurusd_csv = DATA_DIR / "EURUSD_M15_202301012200_202605222015.csv"
        eurusd_model = MODELS_DIR / "xgboost_eurusd.pkl"
        
        results_eurusd = self.backtest_symbol("EURUSD", eurusd_csv, eurusd_model, 0.0001)
        if results_eurusd:
            self.print_results("EURUSD", results_eurusd)
        
        # GBPUSD
        gbpusd_csv = DATA_DIR / "GBPUSD_M15_202601012000_202603012345_processed.csv"
        gbpusd_model = MODELS_DIR / "xgboost_gbpusd.pkl"
        
        results_gbpusd = self.backtest_symbol("GBPUSD", gbpusd_csv, gbpusd_model, 0.0001)
        if results_gbpusd:
            self.print_results("GBPUSD", results_gbpusd)
        
        # XAUUSD (referência)
        xauusd_csv = DATA_DIR / "XAUUSD_M15_202001020600_202604131545.csv"
        xauusd_model = MODELS_DIR / "xgboost_xauusd.pkl"
        
        results_xauusd = self.backtest_symbol("XAUUSD", xauusd_csv, xauusd_model, 0.01)
        if results_xauusd:
            self.print_results("XAUUSD", results_xauusd)

if __name__ == "__main__":
    analysis = MultiTargetAnalysis()
    analysis.run()
