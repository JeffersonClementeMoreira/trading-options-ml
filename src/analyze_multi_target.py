#!/usr/bin/env python3
"""
Análise Robusta Multi-Alvo para EURUSD e GBPUSD
Testa diferentes targets (50, 75, 100, 150, 200 pips)
Mínimo 50 pips para cobrir custos operacionais
"""

import pandas as pd
import numpy as np
from datetime import datetime
import pickle
import os

class MultiTargetBacktest:
    def __init__(self):
        self.symbols = ["EURUSD", "GBPUSD", "XAUUSD"]
        self.targets = [50, 75, 100, 150, 200]
        
    def load_data(self, symbol):
        """Carrega dados históricos"""
        data_map = {
            "EURUSD": "/home/ubuntu/pessoal/options/data/EURUSD_M15_202301012200_202605222015.csv",
            "GBPUSD": "/home/ubuntu/pessoal/options/data/GBPUSD_M15_202601012000_202603012345_processed.csv",
            "XAUUSD": "/home/ubuntu/pessoal/options/data/XAUUSD_M15_202001020600_202604131545.csv"
        }
        
        if symbol not in data_map:
            print(f"❌ Símbolo {symbol} não mapeado")
            return None
        
        csv_file = data_map[symbol]
        if os.path.exists(csv_file):
            try:
                # Tentar com separador tab primeiro
                df = pd.read_csv(csv_file, sep='\t', index_col=False)
                # Se tiver só uma coluna, é porque não funcionou, tenta com vírgula
                if len(df.columns) == 1:
                    df = pd.read_csv(csv_file)
                # Normalizar nomes de colunas IMEDIATAMENTE
                df.columns = df.columns.str.lower()
                df.columns = df.columns.str.strip('<>')
                df.columns = df.columns.str.strip()
                print(f"  ✅ {len(df):,} candles carregados")
                return df
            except Exception as e:
                print(f"  ❌ Erro: {e}")
                return None
        
        print(f"  ❌ Arquivo não encontrado")
        return None

    def load_model(self, symbol):
        """Carrega modelo XGBoost"""
        model_file = f"/home/ubuntu/pessoal/options/models/xgboost_{symbol.lower()}.pkl"
        
        if os.path.exists(model_file):
            try:
                with open(model_file, 'rb') as f:
                    model = pickle.load(f)
                print(f"  ✅ Modelo carregado")
                return model
            except Exception as e:
                print(f"  ❌ Erro ao carregar modelo: {e}")
                return None
        
        print(f"  ⚠️ Modelo não encontrado")
        return None

    def calculate_indicators(self, df):
        """Calcula indicadores necessários"""
        df = df.copy()
        
        # RSI-14
        closes = df['close'].values
        deltas = np.diff(closes)
        up = np.zeros_like(deltas)
        down = np.zeros_like(deltas)
        up[deltas > 0] = deltas[deltas > 0]
        down[deltas < 0] = -deltas[deltas < 0]
        
        rs = np.zeros(len(closes))
        rs[14] = up[:14].sum() / (down[:14].sum() + 1e-10)
        
        for i in range(15, len(closes)):
            rs[i] = (up[i-1] * 13 + rs[i-1] * 14) / 14 / \
                    ((down[i-1] * 13 + rs[i-1] * 14) / 14 + 1e-10)
        
        rsi = 100 - (100 / (1 + rs + 1e-10))
        df['rsi'] = rsi
        
        # SMA
        df['sma20'] = df['close'].rolling(20).mean()
        df['sma50'] = df['close'].rolling(50).mean()
        
        # ATR
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = tr.rolling(14).mean()
        df['atr_pct'] = (df['atr'] / df['close']) * 100
        
        # Momentum
        df['momentum'] = df['close'].diff(12)
        
        # Volume MA (usar 'vol' ou 'tickvol' se 'volume' não existir)
        vol_col = 'vol' if 'vol' in df.columns else ('tickvol' if 'tickvol' in df.columns else 'volume')
        df['vol_ma'] = df[vol_col].rolling(20).mean() if vol_col in df.columns else 1
        
        return df

    def backtest_target(self, df, model, symbol, target_pips):
        """Backtest para um target específico"""
        
        # Configuração por símbolo
        if symbol == "EURUSD":
            target_price = target_pips * 0.0001
            stop_loss = 10 * 0.0001
        elif symbol == "GBPUSD":
            target_price = target_pips * 0.0001
            stop_loss = 10 * 0.0001
        elif symbol == "XAUUSD":
            target_price = target_pips * 0.01
            stop_loss = 10 * 0.01
        else:
            return None
        
        wins = 0
        losses = 0
        total_pips = 0
        trades = []
        
        # Backtest
        for i in range(50, len(df) - 96):
            row = df.iloc[i]
            
            # Skip se faltar indicadores
            if pd.isna(row['rsi']) or pd.isna(row['sma20']) or pd.isna(row['sma50']):
                continue
            
            try:
                # Volume (buscar coluna correta)
                if 'vol' in df.columns:
                    volume_val = row['vol']
                elif 'tickvol' in df.columns:
                    volume_val = row['tickvol']
                elif 'volume' in df.columns:
                    volume_val = row['volume']
                else:
                    volume_val = 1
                
                # Preparar features
                features = np.array([[
                    row['rsi'],
                    row['sma20'],
                    row['sma50'],
                    row['atr_pct'],
                    row['momentum'],
                    0,  # confluence placeholder
                    row['close'],
                    volume_val
                ]])
                
                # Previsão
                if hasattr(model, 'predict_proba'):
                    prob = model.predict_proba(features)[0]
                    pred = 1 if prob[1] > 0.5 else 0
                else:
                    pred = model.predict(features)[0]
                
                entry_price = row['close']
                
                # Verificar saída (máx 96 candles)
                for j in range(i + 1, min(i + 97, len(df))):
                    exit_row = df.iloc[j]
                    high_price = exit_row['high']
                    low_price = exit_row['low']
                    
                    if pred == 1:  # COMPRA
                        if high_price >= entry_price + target_price:
                            wins += 1
                            pips = target_pips
                            total_pips += pips
                            break
                        elif low_price <= entry_price - stop_loss:
                            losses += 1
                            pips = -10
                            total_pips += pips
                            break
                    else:  # VENDA
                        if low_price <= entry_price - target_price:
                            wins += 1
                            pips = target_pips
                            total_pips += pips
                            break
                        elif high_price >= entry_price + stop_loss:
                            losses += 1
                            pips = -10
                            total_pips += pips
                            break
            
            except Exception as e:
                continue
        
        total_trades = wins + losses
        if total_trades > 0:
            return {
                "wins": wins,
                "losses": losses,
                "total": total_trades,
                "win_rate": (wins / total_trades) * 100,
                "total_pips": total_pips,
                "avg_pips": total_pips / total_trades,
                "expectancy": total_pips / total_trades
            }
        
        return None

    def analyze_symbol(self, symbol):
        """Análise completa de um símbolo"""
        print(f"\n{'=' * 100}")
        print(f"📊 ANÁLISE: {symbol}".center(100))
        print(f"{'=' * 100}\n")
        
        # Carregar dados
        print(f"Carregando dados...")
        df = self.load_data(symbol)
        if df is None:
            print(f"❌ Falha ao carregar dados\n")
            return None
        
        # Calcular indicadores
        print(f"Calculando indicadores...")
        df = self.calculate_indicators(df)
        print(f"  ✅ Feito\n")
        
        # Carregar modelo
        print(f"Carregando modelo...")
        model = self.load_model(symbol)
        if model is None:
            print(f"❌ Falha ao carregar modelo\n")
            return None
        
        # Testar cada target
        print(f"Testando targets...\n")
        results = {}
        
        for target in self.targets:
            print(f"  Testando {target} pips... ", end="", flush=True)
            result = self.backtest_target(df, model, symbol, target)
            if result:
                results[target] = result
                print(f"✅ {result['total']:,} trades, WR: {result['win_rate']:.1f}%")
            else:
                print(f"⚠️ Sem trades")
        
        return results

    def print_results(self, symbol, results):
        """Imprime resultados formatados"""
        if not results:
            return
        
        print(f"\n{'─' * 100}")
        print(f"{'Target':>8} | {'Trades':>8} | {'Wins':>8} | {'Losses':>8} | {'Win%':>8} | {'Total Pips':>12} | {'Avg/Trade':>10} | {'Viável':>10}")
        print(f"{'─' * 100}")
        
        best_target = None
        best_rate = 0
        
        for target in sorted(results.keys()):
            r = results[target]
            
            # Critério de viabilidade: WR >= 50% E pips positivos
            is_viable = r['win_rate'] >= 50.0 and r['total_pips'] > 0
            viable_marker = "✅ SIM" if is_viable else "❌ NÃO"
            
            print(f"{target:>8} | {r['total']:>8,} | {r['wins']:>8,} | {r['losses']:>8,} | "
                  f"{r['win_rate']:>7.1f}% | {r['total_pips']:>12.0f} | {r['avg_pips']:>9.1f} | {viable_marker:>10}")
            
            if is_viable and r['win_rate'] > best_rate:
                best_rate = r['win_rate']
                best_target = target
        
        print(f"{'─' * 100}\n")
        
        if best_target:
            r = results[best_target]
            print(f"🎯 RECOMENDAÇÃO PARA {symbol}:")
            print(f"   Target: {best_target} pips")
            print(f"   Win Rate: {r['win_rate']:.1f}%")
            print(f"   Expectativa: {r['avg_pips']:.2f} pips/trade")
            print(f"   Total em backtest: {r['total_pips']:.0f} pips em {r['total']:,} trades\n")
        else:
            print(f"❌ Nenhum target viável encontrado para {symbol}\n")

    def run(self):
        """Executa análise para todos os símbolos"""
        print("\n" + "╔" + "=" * 98 + "╗")
        print("║" + "ANÁLISE MULTI-ALVO - MÍNIMO 50 PIPS PARA CUSTOS OPERACIONAIS".center(98) + "║")
        print("╚" + "=" * 98 + "╝")
        
        all_results = {}
        
        for symbol in self.symbols:
            results = self.analyze_symbol(symbol)
            if results:
                all_results[symbol] = results
                self.print_results(symbol, results)
        
        # Salvar relatório
        self.save_report(all_results)

    def save_report(self, all_results):
        """Salva relatório em arquivo"""
        report_file = "/home/ubuntu/pessoal/options/ANALISE_MULTI_ALVO_COMPLETA.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("ANÁLISE MULTI-ALVO COMPLETA\n")
            f.write("=" * 100 + "\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for symbol in self.symbols:
                if symbol in all_results:
                    results = all_results[symbol]
                    f.write(f"\n{symbol}\n")
                    f.write("─" * 100 + "\n")
                    
                    for target in sorted(results.keys()):
                        r = results[target]
                        f.write(f"\nTarget: {target} pips\n")
                        f.write(f"  Total de Trades: {r['total']:,}\n")
                        f.write(f"  Wins: {r['wins']:,} ({r['win_rate']:.1f}%)\n")
                        f.write(f"  Losses: {r['losses']:,}\n")
                        f.write(f"  Total de Pips: {r['total_pips']:.0f}\n")
                        f.write(f"  Média por Trade: {r['avg_pips']:.2f} pips\n")
                        f.write(f"  Expectativa: {r['expectancy']:.2f} pips\n")
        
        print(f"✅ Relatório salvo: {report_file}\n")

if __name__ == "__main__":
    backtest = MultiTargetBacktest()
    backtest.run()
