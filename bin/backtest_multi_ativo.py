#!/usr/bin/env python3
"""
Backtest Multi-Ativo - Compare triggers flexíveis vs horário fixo
em MÚLTIPLOS ativos e timeframes.

Uso:
    python3 backtest_multi_ativo.py --symbols EURUSD,GBPUSD,GOLD --timeframe M15
    
    python3 backtest_multi_ativo.py --symbols EURUSD --min-quality 70
    
    python3 backtest_multi_ativo.py --symbols EURUSD,GBPUSD --show-stats
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import json
import argparse

# ═══════════════════════════════════════════════════════════════════════════════

class MultiAtivoBacktest:
    """Backtest para múltiplos ativos"""
    
    def __init__(self):
        self.results = defaultdict(lambda: {"triggers": [], "fixed": []})
        self.stats = {}
    
    def _find_csv(self, symbol, timeframe="M15"):
        """Procura arquivo CSV para símbolo+timeframe"""
        search_paths = [
            Path(f"/home/ubuntu/pessoal/options/dados/{symbol}_{timeframe}*.csv"),
            Path(f"/home/ubuntu/pessoal/options/dados/{symbol}_*.csv"),
            Path(f"/home/ubuntu/options/dados/{symbol}_{timeframe}*.csv"),
            Path(f"/home/ubuntu/options/dados/{symbol}_*.csv"),
        ]
        
        for pattern in search_paths:
            matches = list(pattern.parent.glob(pattern.name))
            if matches:
                return matches[0]
        
        return None
    
    def _load_data(self, symbol, timeframe="M15"):
        """Carrega dados CSV"""
        csv_path = self._find_csv(symbol, timeframe)
        
        if not csv_path:
            print(f"   ❌ Arquivo não encontrado: {symbol} {timeframe}")
            return None
        
        print(f"   ✅ Carregando: {csv_path.name}")
        
        try:
            df = pd.read_csv(csv_path, sep='\t', skipinitialspace=True)
            df.columns = [col.strip('<>').lower() for col in df.columns]
            df['time'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))
            df['close'] = df.get('close', df.get('c'))
            df['open'] = df.get('open', df.get('o'))
            df['high'] = df.get('high', df.get('h'))
            df['low'] = df.get('low', df.get('l'))
            df = df.sort_values('time').reset_index(drop=True)
            
            return df
        
        except Exception as e:
            print(f"   ❌ Erro lendo {csv_path}: {e}")
            return None
    
    def _calculate_features(self, df):
        """Calcula features básicas"""
        high_20 = df['high'].rolling(20).max()
        low_20 = df['low'].rolling(20).min()
        
        df['dist_to_high'] = ((high_20 - df['close']) / df['close'] * 10000)
        df['dist_to_low'] = ((df['close'] - low_20) / df['close'] * 10000)
        
        return df
    
    def _get_trigger_score(self, row):
        """Score 0-100"""
        dist = min(abs(row.get('dist_to_high', 100)), abs(row.get('dist_to_low', 100)))
        
        if dist <= 20:
            return 95
        elif dist <= 50:
            return 85
        elif dist <= 100:
            return 70
        else:
            return 50
    
    def _get_recommendation(self, row):
        """CALL ou PUT"""
        if row.get('dist_to_high', 100) < row.get('dist_to_low', 100):
            return "CALL"
        else:
            return "PUT"
    
    def _validate_trade(self, idx, entry_price, recommendation, df, lookback=96):
        """Valida trade com strike 250 pts"""
        if idx + lookback >= len(df):
            return None
        
        future_bars = df.iloc[idx:idx+lookback+1]
        
        if recommendation == "CALL":
            strike = entry_price + (250 * 0.0001)
            max_future = future_bars['high'].max()
            
            if max_future >= strike:
                return {"outcome": "LOSS"}
            else:
                return {"outcome": "WIN", "pnl": 50}
        
        elif recommendation == "PUT":
            strike = entry_price - (250 * 0.0001)
            min_future = future_bars['low'].min()
            
            if min_future <= strike:
                return {"outcome": "LOSS"}
            else:
                return {"outcome": "WIN", "pnl": 50}
        
        return None
    
    def backtest_symbol(self, symbol, min_score=60):
        """Backtest um ativo"""
        print(f"\n📊 Backtesting {symbol}")
        print("─" * 60)
        
        df = self._load_data(symbol)
        if df is None:
            return
        
        print(f"   Período: {df['time'].min().date()} a {df['time'].max().date()}")
        print(f"   Candles: {len(df)}")
        
        df = self._calculate_features(df)
        
        # Triggers
        print(f"   🔍 Analisando triggers...")
        triggers = []
        for idx, row in df.iterrows():
            if pd.isna(row.get('dist_to_high')):
                continue
            
            score = self._get_trigger_score(row)
            if score >= min_score:
                recommendation = self._get_recommendation(row)
                validation = self._validate_trade(idx, row['close'], recommendation, df)
                
                if validation:
                    triggers.append(validation)
        
        # Fixed time (20:00)
        print(f"   ⏰ Analisando 20:00...")
        fixed = []
        for idx, row in df.iterrows():
            if row['time'].strftime("%H:%M") == "20:00":
                if pd.isna(row.get('dist_to_high')):
                    continue
                
                recommendation = self._get_recommendation(row)
                validation = self._validate_trade(idx, row['close'], recommendation, df)
                
                if validation:
                    fixed.append(validation)
        
        # Calcular metrics
        self.results[symbol]["triggers"] = triggers
        self.results[symbol]["fixed"] = fixed
        
        # Mostrar resultado
        if triggers:
            wins_t = sum(1 for t in triggers if t['outcome'] == 'WIN')
            wr_t = (wins_t / len(triggers) * 100) if triggers else 0
            print(f"   ✅ Triggers: {len(triggers)} trades, {wr_t:.1f}% win rate")
        else:
            print(f"   ⚠️  Triggers: Nenhum trade")
        
        if fixed:
            wins_f = sum(1 for t in fixed if t['outcome'] == 'WIN')
            wr_f = (wins_f / len(fixed) * 100) if fixed else 0
            print(f"   ✅ 20:00:    {len(fixed)} trades, {wr_f:.1f}% win rate")
        else:
            print(f"   ⚠️  20:00:    Nenhum trade")
    
    def print_summary(self):
        """Sumário comparativo"""
        print("\n" + "="*80)
        print("RESULTADO FINAL - MÚLTIPLOS ATIVOS".center(80))
        print("="*80)
        
        summary_data = []
        
        for symbol in self.results.keys():
            triggers = self.results[symbol]["triggers"]
            fixed = self.results[symbol]["fixed"]
            
            t_wins = sum(1 for tr in triggers if tr['outcome'] == 'WIN') if triggers else 0
            t_wr = (t_wins / len(triggers) * 100) if triggers else 0
            
            f_wins = sum(1 for tr in fixed if tr['outcome'] == 'WIN') if fixed else 0
            f_wr = (f_wins / len(fixed) * 100) if fixed else 0
            
            improvement = t_wr - f_wr
            
            summary_data.append({
                "Símbolo": symbol,
                "Trigger Trades": len(triggers),
                "Trigger %": f"{t_wr:.1f}%",
                "Fixed Trades": len(fixed),
                "Fixed %": f"{f_wr:.1f}%",
                "Melhoria": f"{improvement:+.1f}%"
            })
        
        if summary_data:
            df_summary = pd.DataFrame(summary_data)
            print("\n" + df_summary.to_string(index=False))
        
        print("\n" + "="*80)
    
    def export_json(self, output_file):
        """Exporta resultados em JSON"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "ativos": {}
        }
        
        for symbol in self.results.keys():
            triggers = self.results[symbol]["triggers"]
            fixed = self.results[symbol]["fixed"]
            
            t_wins = sum(1 for tr in triggers if tr['outcome'] == 'WIN')
            f_wins = sum(1 for tr in fixed if tr['outcome'] == 'WIN')
            
            output["ativos"][symbol] = {
                "triggers": {
                    "total": len(triggers),
                    "wins": t_wins,
                    "win_rate": (t_wins/len(triggers)*100) if triggers else 0
                },
                "fixed_time": {
                    "total": len(fixed),
                    "wins": f_wins,
                    "win_rate": (f_wins/len(fixed)*100) if fixed else 0
                }
            }
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Resultados exportados: {output_file}")


# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Backtest Multi-Ativo")
    parser.add_argument("--symbols", default="EURUSD", help="Símbolos (ex: EURUSD,GBPUSD,GOLD)")
    parser.add_argument("--min-quality", type=int, default=60, help="Score mínimo")
    parser.add_argument("--save-json", help="Exportar para JSON")
    parser.add_argument("--show-stats", action="store_true", help="Mostrar estatísticas")
    
    args = parser.parse_args()
    
    symbols = args.symbols.split(",")
    
    print("\n" + "="*80)
    print("🚀 BACKTEST MULTI-ATIVO - TRIGGERS vs HORÁRIO FIXO".center(80))
    print("="*80)
    
    backtest = MultiAtivoBacktest()
    
    for symbol in symbols:
        backtest.backtest_symbol(symbol.strip(), min_score=args.min_quality)
    
    backtest.print_summary()
    
    if args.save_json:
        backtest.export_json(args.save_json)


if __name__ == "__main__":
    main()
