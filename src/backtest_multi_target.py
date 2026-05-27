#!/usr/bin/env python3
"""
Análise Multi-Alvo para EURUSD e GBPUSD
Testa diferentes targets (50, 75, 100, 150, 200 pips)
Mínimo 50 pips para cobrir custos operacionais
"""

import pandas as pd
import numpy as np
from datetime import datetime
import pickle
import os

def load_data(symbol):
    """Carrega dados históricos"""
    # Mapear símbolo para arquivo específico
    data_map = {
        "EURUSD": [
            "/home/ubuntu/pessoal/options/data/EURUSD_M15_202301012200_202605222015.csv",
            "/home/ubuntu/pessoal/options/data/EURUSD_M15_202301012200_202605222015_processed.csv",
        ],
        "GBPUSD": [
            "/home/ubuntu/pessoal/options/data/GBPUSD_M15_202601012000_202603012345_processed.csv",
            "/home/ubuntu/pessoal/options/data/GBPUSD_M15_202601012000_202603012345_synthetic.csv",
        ],
        "XAUUSD": [
            "/home/ubuntu/pessoal/options/data/XAUUSD_M15_202001020600_202604131545.csv",
        ]
    }
    
    if symbol not in data_map:
        print(f"❌ Símbolo {symbol} não mapeado")
        return None
    
    for csv_file in data_map[symbol]:
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file)
                print(f"✅ Dados carregados: {os.path.basename(csv_file)} ({len(df)} candles)")
                return df
            except Exception as e:
                print(f"⚠️ Erro ao ler {csv_file}: {e}")
                continue
    
    print(f"❌ Nenhum arquivo encontrado para {symbol}")
    return None

def load_model(symbol):
    """Carrega modelo XGBoost"""
    model_file = f"/home/ubuntu/pessoal/options/models/xgboost_{symbol.lower()}.pkl"
    
    if os.path.exists(model_file):
        with open(model_file, 'rb') as f:
            return pickle.load(f)
    else:
        print(f"⚠️ Modelo não encontrado: {model_file}")
        return None

def backtest_symbol(symbol, targets):
    """Faz backtest para múltiplos targets"""
    
    df = load_data(symbol)
    if df is None:
        return None
    
    model = load_model(symbol)
    if model is None:
        return None
    
    # Converter para formato correto
    if 'close' not in df.columns:
        print(f"Colunas disponíveis: {df.columns.tolist()}")
        return None
    
    results = {}
    
    for target_pips in targets:
        try:
            # Converter pips para preço (depende do símbolo)
            if symbol == "EURUSD":
                target_price = target_pips * 0.0001  # 1 pip = 0.0001
                stop_loss = 10 * 0.0001  # 10 pips
            elif symbol == "GBPUSD":
                target_price = target_pips * 0.0001
                stop_loss = 10 * 0.0001
            elif symbol == "XAUUSD":
                target_price = target_pips * 0.01  # 1 pip = 0.01
                stop_loss = 10 * 0.01
            else:
                continue
            
            # Preparar features (simplificado)
            # Aqui seria necessário calcular os indicadores reais
            # Por enquanto, usar dados como estão
            
            closes = df['close'].values
            highs = df['high'].values
            lows = df['low'].values
            volumes = df['volume'].values if 'volume' in df.columns else np.ones_like(closes)
            
            # Calcular indicadores básicos
            rsi = calculate_rsi(closes, 14)
            sma20 = pd.Series(closes).rolling(20).mean().values
            sma50 = pd.Series(closes).rolling(50).mean().values
            
            wins = 0
            losses = 0
            total_pips = 0
            trades = []
            
            # Simular backtest
            for i in range(50, len(closes) - 96):  # 96 candles = 24 horas em M15
                # Skip NaN
                if np.isnan(rsi[i]) or np.isnan(sma20[i]) or np.isnan(sma50[i]):
                    continue
                
                try:
                    # Features para predição
                    atr = np.mean(np.abs(highs[i-14:i] - lows[i-14:i]))
                    momentum = closes[i] - closes[i-12]
                    vol_ma = np.mean(volumes[max(0, i-20):i])
                    
                    features = np.array([[
                        rsi[i],
                        sma20[i],
                        sma50[i],
                        (atr / closes[i]) * 100,  # ATR%
                        momentum,
                        0,  # confluence placeholder
                        closes[i],
                        volumes[i] if i < len(volumes) else vol_ma
                    ]])
                    
                    # Previsão
                    if hasattr(model, 'predict_proba'):
                        prob = model.predict_proba(features)[0]
                        pred = 1 if prob[1] > 0.5 else 0
                        prob_score = prob[1] if len(prob) > 1 else prob[0]
                    else:
                        pred = model.predict(features)[0]
                        prob_score = 0.5
                    
                    entry_price = closes[i]
                    
                    # Simular saída (verificar se atingiu target ou stop)
                    for j in range(i + 1, min(i + 97, len(closes))):  # 96 candles max
                        high_price = highs[j]
                        low_price = lows[j]
                        
                        if pred == 1:  # COMPRA
                            if high_price >= entry_price + target_price:
                                wins += 1
                                pips = target_pips
                                total_pips += pips
                                trades.append({"type": "BUY", "pips": pips})
                                break
                            elif low_price <= entry_price - stop_loss:
                                losses += 1
                                pips = -10
                                total_pips += pips
                                trades.append({"type": "BUY", "pips": pips})
                                break
                        else:  # VENDA
                            if low_price <= entry_price - target_price:
                                wins += 1
                                pips = target_pips
                                total_pips += pips
                                trades.append({"type": "SELL", "pips": pips})
                                break
                            elif high_price >= entry_price + stop_loss:
                                losses += 1
                                pips = -10
                                total_pips += pips
                                trades.append({"type": "SELL", "pips": pips})
                                break
                
                except Exception as e:
                    continue
            
            total_trades = wins + losses
            if total_trades > 0:
                win_rate = (wins / total_trades) * 100
                avg_pips = total_pips / total_trades
                
                results[target_pips] = {
                    "wins": wins,
                    "losses": losses,
                    "total": total_trades,
                    "win_rate": win_rate,
                    "total_pips": total_pips,
                    "avg_pips": avg_pips,
                    "expectancy": total_pips / total_trades if total_trades > 0 else 0
                }
        
        except Exception as e:
            print(f"Erro no target {target_pips}: {e}")
            continue
    
    return results

def calculate_rsi(closes, period=14):
    """Calcula RSI"""
    deltas = np.diff(closes)
    up = deltas.copy()
    up[up < 0] = 0
    down = -deltas.copy()
    down[down < 0] = 0
    
    rs = np.zeros_like(closes)
    rs[period] = up[:period].sum() / (down[:period].sum() + 1e-10)
    
    for i in range(period + 1, len(closes)):
        rs[i] = (up[i] * (period - 1) + rs[i-1] * period) / period / \
                ((down[i] * (period - 1) + rs[i-1] * period) / period + 1e-10)
    
    rsi = 100 - (100 / (1 + rs))
    return rsi

def print_report(symbol, results):
    """Imprime relatório"""
    print("\n" + "=" * 100)
    print(f"📊 ANÁLISE MULTI-ALVO: {symbol}".center(100))
    print("=" * 100)
    
    print(f"\n{'Target':>8} | {'Trades':>8} | {'Wins':>8} | {'Losses':>8} | {'Win%':>8} | {'Total Pips':>12} | {'Avg/Trade':>10} | {'Viável':>10}")
    print("-" * 100)
    
    best_target = None
    best_winrate = 0
    
    for target in sorted(results.keys()):
        r = results[target]
        viavel = "✅ SIM" if r['win_rate'] >= 50 and r['total_pips'] >= target * 0.5 else "❌ NÃO"
        
        print(f"{target:>8} | {r['total']:>8,} | {r['wins']:>8,} | {r['losses']:>8,} | "
              f"{r['win_rate']:>7.1f}% | {r['total_pips']:>12.0f} | {r['avg_pips']:>9.1f} | {viavel:>10}")
        
        if r['win_rate'] >= 50 and r['win_rate'] > best_winrate:
            best_winrate = r['win_rate']
            best_target = target
    
    if best_target:
        print(f"\n✅ MELHOR ALVO: {best_target} pips (Win Rate: {results[best_target]['win_rate']:.1f}%)")
    else:
        print("\n❌ Nenhum target viável encontrado (todos abaixo de 50% WR)")

def main():
    print("\n" + "╔" + "=" * 98 + "╗")
    print("║" + "ANÁLISE MULTI-ALVO PARA TRADING - MÍNIMO 50 PIPS".center(98) + "║")
    print("╚" + "=" * 98 + "╝\n")
    
    # Targets a testar (mínimo 50 pips)
    targets = [50, 75, 100, 150, 200]
    
    for symbol in ["EURUSD", "GBPUSD", "XAUUSD"]:
        print(f"\n🔄 Testando {symbol}...")
        results = backtest_symbol(symbol, targets)
        
        if results:
            print_report(symbol, results)
            
            # Salvar em arquivo
            report_file = f"/home/ubuntu/pessoal/options/ANALISE_{symbol}_MULTI_ALVO.txt"
            with open(report_file, 'w') as f:
                f.write(f"ANÁLISE MULTI-ALVO: {symbol}\n")
                f.write("=" * 100 + "\n\n")
                
                for target in sorted(results.keys()):
                    r = results[target]
                    f.write(f"\nTarget: {target} pips\n")
                    f.write(f"  Trades: {r['total']:,}\n")
                    f.write(f"  Wins: {r['wins']:,} ({r['win_rate']:.1f}%)\n")
                    f.write(f"  Losses: {r['losses']:,}\n")
                    f.write(f"  Total Pips: {r['total_pips']:.0f}\n")
                    f.write(f"  Avg/Trade: {r['avg_pips']:.1f}\n")
            
            print(f"✅ Relatório salvo: {report_file}")
        else:
            print(f"❌ Não foi possível analisar {symbol}")

if __name__ == "__main__":
    main()
