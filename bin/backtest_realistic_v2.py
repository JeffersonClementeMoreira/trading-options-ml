#!/usr/bin/env python3
"""
BACKTEST REALISTA - Com strikes, TP/SL e validação completa
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json

# ═══════════════════════════════════════════════════════════════════════════════

class RealisticTriggerBacktest:
    """Backtest realista com strikes, TP/SL e validação de preço"""
    
    STRIKE_DISTANCES = [150, 200, 250, 300]  # pontos
    TP_DISTANCE = 50  # pontos (quanto ganha em TP)
    SL_DISTANCE = 200  # pontos (quanto perde em SL)
    
    def __init__(self, csv_path):
        print(f"📂 Carregando: {csv_path}")
        self.df = pd.read_csv(csv_path, sep='\t', skipinitialspace=True)
        
        # Renomear colunas
        self.df.columns = [col.strip('<>').lower() for col in self.df.columns]
        
        # Combinar DATE + TIME
        self.df['time'] = pd.to_datetime(self.df['date'].astype(str) + ' ' + self.df['time'].astype(str))
        self.df['close'] = self.df.get('close', self.df.get('c'))
        self.df['open'] = self.df.get('open', self.df.get('o'))
        self.df['high'] = self.df.get('high', self.df.get('h'))
        self.df['low'] = self.df.get('low', self.df.get('l'))
        
        self.df = self.df.sort_values('time').reset_index(drop=True)
        
        print(f"   ✅ {len(self.df)} candles")
        print(f"   Período: {self.df['time'].min().date()} a {self.df['time'].max().date()}")
        
        self._calculate_features()
        
        self.results_trigger = {}
        self.results_fixed = {}
        for sd in self.STRIKE_DISTANCES:
            self.results_trigger[sd] = []
            self.results_fixed[sd] = []
    
    def _calculate_features(self):
        """Features básicas"""
        print("📊 Calculando features...")
        
        # Distância para extremos
        high_20 = self.df['high'].rolling(20).max()
        low_20 = self.df['low'].rolling(20).min()
        
        self.df['dist_to_high'] = ((high_20 - self.df['close']) / self.df['close'] * 10000)  # pts
        self.df['dist_to_low'] = ((self.df['close'] - low_20) / self.df['close'] * 10000)
        
        print("   ✅ Features calculadas")
    
    def _get_trigger_score(self, row):
        """Score flexível"""
        dist_to_high = row.get('dist_to_high', 100)
        dist_to_low = row.get('dist_to_low', 100)
        min_dist = min(abs(dist_to_high), abs(dist_to_low))
        
        if min_dist <= 20:
            return 95
        elif min_dist <= 50:
            return 85
        elif min_dist <= 100:
            return 70
        else:
            return 50
    
    def _get_recommendation(self, row):
        """Recomendação: CALL ou PUT"""
        dist_to_high = row.get('dist_to_high', 100)
        dist_to_low = row.get('dist_to_low', 100)
        
        if dist_to_high < dist_to_low:
            return "SELL_CALL"
        else:
            return "SELL_PUT"
    
    def _validate_trade_realistic(self, idx, entry_price, recommendation, strike_distance, lookback=96):
        """
        Valida trade com strikes, TP, SL reais
        
        SELL_CALL: Vende call a 200 pts acima
            - Ganha 50 pts se preço ficar abaixo do strike
            - Perde 200 pts se preço toca acima do SL
        
        SELL_PUT: Vende put a 200 pts abaixo
            - Ganha 50 pts se preço ficar acima do strike
            - Perde 200 pts se preço toca abaixo do SL
        """
        
        if idx + lookback >= len(self.df):
            return None
        
        future_bars = self.df.iloc[idx:idx+lookback+1]
        
        if recommendation == "SELL_CALL":
            # Strike = entrada + strike_distance pts
            strike_price = entry_price + (strike_distance * 0.0001)
            tp_price = strike_price - (self.TP_DISTANCE * 0.0001)  # TP abaixo do strike
            sl_price = strike_price + (self.SL_DISTANCE * 0.0001)  # SL acima do strike
            
            # Verifica próximos candles
            max_future = future_bars['high'].max()
            min_future = future_bars['low'].min()
            
            result = {
                "recommendation": recommendation,
                "strike_distance": strike_distance,
                "strike": strike_price,
                "tp": tp_price,
                "sl": sl_price
            }
            
            # Se toca SL primeiro = perda
            if max_future >= sl_price:
                result["outcome"] = "LOSS"
                result["pnl"] = -self.SL_DISTANCE
                result["bars"] = min(len(future_bars) - 1, lookback)
            
            # Se toca TP primeiro = ganho
            elif min_future <= tp_price:
                result["outcome"] = "WIN"
                result["pnl"] = self.TP_DISTANCE
                result["bars"] = min(len(future_bars) - 1, lookback)
            
            # Preço nunca toca SL = ganho (ficou na range)
            else:
                # Sai com profit parcial (metade do TP)
                result["outcome"] = "WIN_PARTIAL"
                result["pnl"] = self.TP_DISTANCE // 2
                result["bars"] = lookback
        
        elif recommendation == "SELL_PUT":
            # Strike = entrada - strike_distance pts
            strike_price = entry_price - (strike_distance * 0.0001)
            tp_price = strike_price + (self.TP_DISTANCE * 0.0001)  # TP acima do strike
            sl_price = strike_price - (self.SL_DISTANCE * 0.0001)  # SL abaixo do strike
            
            max_future = future_bars['high'].max()
            min_future = future_bars['low'].min()
            
            result = {
                "recommendation": recommendation,
                "strike_distance": strike_distance,
                "strike": strike_price,
                "tp": tp_price,
                "sl": sl_price
            }
            
            # Se toca SL primeiro = perda
            if min_future <= sl_price:
                result["outcome"] = "LOSS"
                result["pnl"] = -self.SL_DISTANCE
                result["bars"] = min(len(future_bars) - 1, lookback)
            
            # Se toca TP primeiro = ganho
            elif max_future >= tp_price:
                result["outcome"] = "WIN"
                result["pnl"] = self.TP_DISTANCE
                result["bars"] = min(len(future_bars) - 1, lookback)
            
            # Preço nunca toca SL = ganho
            else:
                result["outcome"] = "WIN_PARTIAL"
                result["pnl"] = self.TP_DISTANCE // 2
                result["bars"] = lookback
        
        return result
    
    def backtest_triggers(self, min_score=60):
        """Backtest com triggers"""
        print(f"\n🔍 Backtesting TRIGGERS (score ≥{min_score})...")
        
        count = 0
        for idx, row in self.df.iterrows():
            if idx % 5000 == 0:
                print(f"   {idx}/{len(self.df)}")
            
            if pd.isna(row.get('dist_to_high')):
                continue
            
            score = self._get_trigger_score(row)
            if score >= min_score:
                recommendation = self._get_recommendation(row)
                
                for sd in self.STRIKE_DISTANCES:
                    validation = self._validate_trade_realistic(idx, row['close'], recommendation, sd)
                    if validation:
                        validation['time'] = row['time']
                        validation['score'] = score
                        self.results_trigger[sd].append(validation)
                        count += 1
        
        print(f"✅ {count} trades analisados")
    
    def backtest_fixed_time(self, entry_time="20:00"):
        """Backtest com horário fixo"""
        print(f"\n⏰ Backtesting HORÁRIO FIXO ({entry_time})...")
        
        count = 0
        for idx, row in self.df.iterrows():
            if idx % 5000 == 0:
                print(f"   {idx}/{len(self.df)}")
            
            if row['time'].strftime("%H:%M") != entry_time:
                continue
            
            if pd.isna(row.get('dist_to_high')):
                continue
            
            recommendation = self._get_recommendation(row)
            
            for sd in self.STRIKE_DISTANCES:
                validation = self._validate_trade_realistic(idx, row['close'], recommendation, sd)
                if validation:
                    validation['time'] = row['time']
                    validation['score'] = 0
                    self.results_fixed[sd].append(validation)
                    count += 1
        
        print(f"✅ {count} trades analisados")
    
    def _calculate_metrics(self, results, name):
        """Calcula métricas por strike distance"""
        metrics = {}
        
        for sd, trades in results.items():
            if not trades:
                metrics[sd] = None
                continue
            
            df_trades = pd.DataFrame(trades)
            
            total = len(df_trades)
            wins = ((df_trades['outcome'] == 'WIN') | (df_trades['outcome'] == 'WIN_PARTIAL')).sum()
            losses = (df_trades['outcome'] == 'LOSS').sum()
            win_rate = (wins / total * 100) if total > 0 else 0
            
            total_pnl = df_trades['pnl'].sum()
            avg_pnl = total_pnl / total if total > 0 else 0
            
            metrics[sd] = {
                "strike_distance": sd,
                "total": total,
                "wins": int(wins),
                "losses": int(losses),
                "win_rate": round(win_rate, 2),
                "total_pnl": int(total_pnl),
                "avg_pnl": round(avg_pnl, 2)
            }
        
        return metrics
    
    def print_results(self):
        """Imprime resultados"""
        print("\n" + "="*90)
        print(" BACKTEST REALISTA - COM STRIKES E TP/SL ".center(90, "="))
        print("="*90)
        
        metrics_trigger = self._calculate_metrics(self.results_trigger, "Triggers")
        metrics_fixed = self._calculate_metrics(self.results_fixed, "Fixed Time")
        
        for sd in self.STRIKE_DISTANCES:
            mt = metrics_trigger[sd]
            mf = metrics_fixed[sd]
            
            if not mt or not mf:
                continue
            
            print(f"\n📊 STRIKE DISTANCE: {sd} pts")
            print("─" * 90)
            
            print(f"  TRIGGERS:")
            print(f"    Total:     {mt['total']} trades")
            print(f"    Ganhas:    {mt['wins']} ({mt['win_rate']}%)")
            print(f"    Perdidas:  {mt['losses']}")
            print(f"    PnL Total: {mt['total_pnl']} pts")
            print(f"    PnL Médio: {mt['avg_pnl']} pts/trade")
            
            print(f"\n  HORÁRIO FIXO (20:00):")
            print(f"    Total:     {mf['total']} trades")
            print(f"    Ganhas:    {mf['wins']} ({mf['win_rate']}%)")
            print(f"    Perdidas:  {mf['losses']}")
            print(f"    PnL Total: {mf['total_pnl']} pts")
            print(f"    PnL Médio: {mf['avg_pnl']} pts/trade")
            
            improvement = mt['win_rate'] - mf['win_rate']
            pnl_improvement = mt['total_pnl'] - mf['total_pnl']
            
            print(f"\n  MELHORIA COM TRIGGERS:")
            print(f"    Win rate:  {improvement:+.2f}% (triggers {mt['win_rate']}% vs 20:00 {mf['win_rate']}%)")
            print(f"    PnL total: {pnl_improvement:+} pts")
            
            if improvement > 0:
                print(f"    ✅ TRIGGERS MELHOR por {improvement:.2f}%")
            elif improvement < 0:
                print(f"    ⚠️  HORÁRIO FIXO MELHOR por {-improvement:.2f}%")
            else:
                print(f"    🤔 EMPATE")
        
        print("\n" + "="*90)
        
        # Salvar
        self._save_results(metrics_trigger, metrics_fixed)
    
    def _save_results(self, metrics_trigger, metrics_fixed):
        """Salva JSON"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "strike_distances": self.STRIKE_DISTANCES,
                "tp_distance": self.TP_DISTANCE,
                "sl_distance": self.SL_DISTANCE,
            },
            "results": {
                "triggers": metrics_trigger,
                "fixed_time": metrics_fixed
            }
        }
        
        output_file = Path(__file__).parent / "backtest_results_realistic.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"💾 Salvo em: {output_file}\n")


# ═══════════════════════════════════════════════════════════════════════════════

def main():
    data_file = Path("/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv")
    
    if not data_file.exists():
        print(f"❌ {data_file}")
        return
    
    backtest = RealisticTriggerBacktest(data_file)
    backtest.backtest_triggers(min_score=60)
    backtest.backtest_fixed_time(entry_time="20:00")
    backtest.print_results()


if __name__ == "__main__":
    main()
