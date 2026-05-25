#!/usr/bin/env python3
"""
VALIDAÇÃO DE TRIGGERS - Compara trigger flexível vs horário fixo 20:00

Resultado: Win rate + improvement %
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import json

# ═══════════════════════════════════════════════════════════════════════════════

class TriggerBacktest:
    """Valida triggers contra dados históricos reais"""
    
    def __init__(self, csv_path):
        print(f"📂 Carregando: {csv_path}")
        self.df = pd.read_csv(csv_path, sep='\t', skipinitialspace=True)
        
        # Renomear colunas (formato MT5 com <COLUNA>)
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
        
        # Calcular features simples (sem dependências externas)
        self._calculate_features()
        
        self.results_trigger = []
        self.results_fixed = []
    
    def _calculate_features(self):
        """Calcula features básicas (sem SMC complexo)"""
        print("📊 Calculando features...")
        
        # Volatilidade
        returns = self.df['close'].pct_change()
        self.df['volatility'] = returns.rolling(20).std()
        
        # Distância para extremos recentes
        high_20 = self.df['high'].rolling(20).max()
        low_20 = self.df['low'].rolling(20).min()
        
        self.df['dist_to_high'] = ((high_20 - self.df['close']) / self.df['close'] * 10000)  # pts
        self.df['dist_to_low'] = ((self.df['close'] - low_20) / self.df['close'] * 10000)    # pts
        
        # RSI simples
        self.df['rsi'] = self._calculate_rsi(self.df['close'])
        
        print("   ✅ Features calculadas")
    
    def _calculate_rsi(self, prices, period=14):
        """Calcula RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _get_trigger_score(self, row):
        """Calcula score flexível do trigger (0-100)"""
        
        dist_to_high = row.get('dist_to_high', 100)
        dist_to_low = row.get('dist_to_low', 100)
        
        # Quanto PERTO de extremos = score alto
        # Proximidade: 0.2% = 100, 0.5% = 75, 1% = 50, 2% = 25
        
        min_dist = min(abs(dist_to_high), abs(dist_to_low))
        
        if min_dist <= 20:  # ≤0.2%
            score = 95
        elif min_dist <= 50:  # ≤0.5%
            score = 85
        elif min_dist <= 100:  # ≤1%
            score = 70
        elif min_dist <= 200:  # ≤2%
            score = 50
        else:
            score = 20
        
        return score
    
    def _get_recommendation(self, row):
        """SELL_CALL (bullish) vs SELL_PUT (bearish)"""
        
        dist_to_high = row.get('dist_to_high', 100)
        dist_to_low = row.get('dist_to_low', 100)
        rsi = row.get('rsi', 50)
        
        # Se perto do ALTO: vende call (esperando queda)
        # Se perto do BAIXO: vende put (esperando subida)
        
        if dist_to_high < dist_to_low:
            return "SELL_CALL"
        elif dist_to_low < dist_to_high:
            return "SELL_PUT"
        else:
            return "STRANGLE"
    
    def _validate_entry(self, idx, entry_price, recommendation, lookback=96):
        """
        Valida se entrada foi BOA (preço foi a FAVOR ou CONTRA)
        
        Para SELL_CALL: queremos que preço CAIA
        Para SELL_PUT: queremos que preço SUBA
        
        Olha próximos N candles (96 = 24h)
        """
        
        if idx + lookback >= len(self.df):
            return None
        
        future_bars = self.df.iloc[idx:idx+lookback+1]
        
        if recommendation == "SELL_CALL":
            # Queremos que preço CAIA (high não toque acima)
            max_future = future_bars['high'].max()
            min_future = future_bars['low'].min()
            
            # Ganho = entrada - preço mínimo (quanto preço caiu)
            move = entry_price - min_future
            profit = move > 0  # True se preço caiu
            move_pts = move / 0.0001
            
        elif recommendation == "SELL_PUT":
            # Queremos que preço SUBA (low não toque abaixo)
            max_future = future_bars['high'].max()
            min_future = future_bars['low'].min()
            
            # Ganho = preço máximo - entrada (quanto preço subiu)
            move = max_future - entry_price
            profit = move > 0  # True se preço subiu
            move_pts = move / 0.0001
            
        else:  # STRANGLE
            max_future = future_bars['high'].max()
            min_future = future_bars['low'].min()
            
            # STRANGLE ganha se preço fica em range
            # Perde se sai muito dos extremos
            move_up = (max_future - entry_price) / 0.0001
            move_down = (entry_price - min_future) / 0.0001
            move_pts = min(move_up, move_down)
            
            profit = move_pts > 0
        
        return {
            "profit": profit,
            "move_pts": move_pts,
            "win": 1 if profit else 0,
            "recommendation": recommendation
        }
    
    def backtest_trigger(self, min_score=60):
        """Backtest triggers flexíveis"""
        print(f"\n🔍 Backtesting TRIGGERS flexíveis (score ≥{min_score})...")
        
        count = 0
        for idx, row in self.df.iterrows():
            if idx % 1000 == 0:
                print(f"   Processando: {idx}/{len(self.df)}")
            
            if pd.isna(row.get('dist_to_high')) or pd.isna(row.get('dist_to_low')):
                continue
            
            score = self._get_trigger_score(row)
            
            if score >= min_score:
                recommendation = self._get_recommendation(row)
                validation = self._validate_entry(idx, row['close'], recommendation)
                
                if validation:
                    validation['time'] = row['time']
                    validation['price'] = row['close']
                    validation['score'] = score
                    self.results_trigger.append(validation)
                    count += 1
        
        print(f"✅ {count} triggers encontrados")
    
    def backtest_fixed_time(self, entry_time="20:00"):
        """Backtest entrada SEMPRE às 20:00"""
        print(f"\n⏰ Backtesting entrada FIXA às {entry_time}...")
        
        count = 0
        for idx, row in self.df.iterrows():
            if idx % 1000 == 0:
                print(f"   Processando: {idx}/{len(self.df)}")
            
            # Entrar APENAS se hora = 20:00
            if row['time'].strftime("%H:%M") == entry_time:
                
                if pd.isna(row.get('dist_to_high')) or pd.isna(row.get('dist_to_low')):
                    continue
                
                recommendation = self._get_recommendation(row)
                validation = self._validate_entry(idx, row['close'], recommendation)
                
                if validation:
                    validation['time'] = row['time']
                    validation['price'] = row['close']
                    validation['score'] = 0  # Sem score, entrada fixa
                    self.results_fixed.append(validation)
                    count += 1
        
        print(f"✅ {count} entradas às {entry_time}")
    
    def calculate_metrics(self, results, name):
        """Calcula métricas"""
        if not results:
            return None
        
        df_r = pd.DataFrame(results)
        
        total = len(df_r)
        wins = df_r['win'].sum()
        losses = total - wins
        win_rate = (wins / total * 100) if total > 0 else 0
        
        avg_move = df_r['move_pts'].mean()
        
        return {
            "name": name,
            "total": total,
            "wins": int(wins),
            "losses": int(losses),
            "win_rate": round(win_rate, 2),
            "avg_move_pts": round(avg_move, 2)
        }
    
    def print_results(self):
        """Imprime resultados"""
        print("\n" + "="*80)
        print(" RESULTADO DO BACKTEST DE TRIGGERS ".center(80, "="))
        print("="*80)
        
        metrics_trigger = self.calculate_metrics(self.results_trigger, "TRIGGERS FLEXÍVEIS")
        metrics_fixed = self.calculate_metrics(self.results_fixed, "HORÁRIO FIXO 20:00")
        
        if not metrics_trigger or not metrics_fixed:
            print("❌ Dados insuficientes para análise")
            return
        
        print(f"\n📈 TRIGGERS FLEXÍVEIS:")
        print(f"   Total de operações: {metrics_trigger['total']}")
        print(f"   Ganhas:            {metrics_trigger['wins']} ({metrics_trigger['win_rate']}%)")
        print(f"   Perdidas:          {metrics_trigger['losses']}")
        print(f"   Movimento médio:   {metrics_trigger['avg_move_pts']:.0f} pts")
        
        print(f"\n⏰ HORÁRIO FIXO (20:00):")
        print(f"   Total de operações: {metrics_fixed['total']}")
        print(f"   Ganhas:            {metrics_fixed['wins']} ({metrics_fixed['win_rate']}%)")
        print(f"   Perdidas:          {metrics_fixed['losses']}")
        print(f"   Movimento médio:   {metrics_fixed['avg_move_pts']:.0f} pts")
        
        # Comparação
        improvement = metrics_trigger['win_rate'] - metrics_fixed['win_rate']
        
        print(f"\n🎯 COMPARAÇÃO:")
        print(f"   Win rate triggers:  {metrics_trigger['win_rate']}%")
        print(f"   Win rate 20:00:     {metrics_fixed['win_rate']}%")
        print(f"   Melhoria:           {improvement:+.2f}%")
        
        if improvement > 0:
            print(f"\n✅ TRIGGERS SÃO {improvement:.1f}% MELHORES! 🚀")
        elif improvement < 0:
            print(f"\n⚠️  HORÁRIO FIXO É MELHOR por {-improvement:.1f}%")
        else:
            print(f"\n🤔 EMPATE!")
        
        print("="*80)
        
        # Salvar
        output = {
            "timestamp": datetime.now().isoformat(),
            "triggers": metrics_trigger,
            "fixed_time": metrics_fixed,
            "improvement_pct": round(improvement, 2)
        }
        
        output_file = Path(__file__).parent / "backtest_results_triggers.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"💾 Salvo em: {output_file}")


# ═══════════════════════════════════════════════════════════════════════════════

def main():
    # Encontrar dados
    data_file = Path("/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv")
    
    if not data_file.exists():
        print(f"❌ Arquivo não encontrado: {data_file}")
        return
    
    # Executar
    backtest = TriggerBacktest(data_file)
    
    print("\n" + "="*80)
    backtest.backtest_trigger(min_score=60)
    backtest.backtest_fixed_time(entry_time="20:00")
    
    backtest.print_results()


if __name__ == "__main__":
    main()
