#!/usr/bin/env python3
"""
Backtest com dados DIRETO do MT5 em tempo real

Usa o stream NDJSON que o realtime_executor.py está salvando.
Permite testar os últimos N candles de qualquer ativo/timeframe.

Uso:
    python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 2000
    
    python3 backtest_realtime.py --symbol GBPUSD --tf M15 --last 500 --show-stats
    
    python3 backtest_realtime.py --symbol GOLD --tf M15 --last 1000 --save-json resultado.json
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════════════════════

class RealtimeBacktest:
    """Backtest usando dados em tempo real do MT5"""
    
    def __init__(self, symbol, timeframe="M15"):
        self.symbol = symbol
        self.timeframe = timeframe
        self.data = []
    
    def _find_stream_file(self):
        """Procura arquivo NDJSON do stream"""
        stream_dir = Path("/home/ubuntu/pessoal/options/src/analytics/realtime")
        
        if not stream_dir.exists():
            return None
        
        # Procura stream_SYMBOL_TIMEFRAME.ndjson
        pattern = f"stream_{self.symbol}_{self.timeframe}.ndjson"
        stream_file = stream_dir / pattern
        
        if stream_file.exists():
            return stream_file
        
        return None
    
    def load_data(self, last_n=2000):
        """Carrega últimos N candles do stream NDJSON"""
        stream_file = self._find_stream_file()
        
        if not stream_file:
            print(f"❌ Arquivo não encontrado: stream_{self.symbol}_{self.timeframe}.ndjson")
            print(f"   Procurou em: /home/ubuntu/pessoal/options/src/analytics/realtime/")
            print(f"\n💡 Dica: Adicione EA {self.symbol} M15 no MT5 e aguarde dados chegarem!")
            return False
        
        print(f"✅ Encontrado: {stream_file.name}")
        print(f"   Tamanho: {stream_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        try:
            # Ler última N linhas do arquivo (mais eficiente)
            with open(stream_file, 'rb') as f:
                f.seek(0, 2)  # Vai pro final
                file_size = f.tell()
                
                # Lê de trás pra frente para pegar últimas linhas
                buffer = bytearray(min(file_size, 1024*1024))  # 1MB buffer
                f.seek(max(0, file_size - len(buffer)))
                f.readinto(buffer)
                
                text = buffer.decode('utf-8', errors='ignore')
                lines = text.split('\n')
                
                # Se não temos linha suficientes, lê tudo
                if len(lines) < last_n:
                    with open(stream_file, 'r') as f:
                        lines = f.readlines()
            
            # Parse JSONs
            candles = []
            for line in lines:
                if not line.strip():
                    continue
                try:
                    candles.append(json.loads(line))
                except:
                    continue
            
            # Pega últimos N
            self.data = candles[-last_n:] if len(candles) > last_n else candles
            
            print(f"   Carregados: {len(self.data)} candles")
            if self.data:
                first_time = self.data[0].get('datetime', 'unknown')
                last_time = self.data[-1].get('datetime', 'unknown')
                print(f"   Período: {first_time} a {last_time}")
            
            return True
        
        except Exception as e:
            print(f"❌ Erro lendo arquivo: {e}")
            return False
    
    def _get_trigger_score(self, candle):
        """Calcula score do trigger (0-100)"""
        # Usa dados já calculados pelo MT5
        
        # Se temos dist_to_high e dist_to_low
        if 'dist_to_high' not in candle or 'dist_to_low' not in candle:
            return 50  # Score padrão se não tem dados
        
        dist_high = abs(candle.get('dist_to_high', 100))
        dist_low = abs(candle.get('dist_to_low', 100))
        dist = min(dist_high, dist_low)
        
        if dist <= 20:
            return 95
        elif dist <= 50:
            return 85
        elif dist <= 100:
            return 70
        else:
            return 50
    
    def _get_recommendation(self, candle):
        """Retorna recomendação CALL ou PUT"""
        dist_high = candle.get('dist_to_high', 100)
        dist_low = candle.get('dist_to_low', 100)
        
        if dist_high < dist_low:
            return "CALL"
        else:
            return "PUT"
    
    def _validate_trade(self, idx, entry_price, recommendation, lookback=96):
        """Valida trade com strike 250 pts"""
        if idx + lookback >= len(self.data):
            return None
        
        future_candles = self.data[idx:idx+lookback+1]
        
        # Extrai highs/lows
        highs = [c.get('high', entry_price) for c in future_candles]
        lows = [c.get('low', entry_price) for c in future_candles]
        
        max_future = max(highs)
        min_future = min(lows)
        
        if recommendation == "CALL":
            strike = entry_price + (250 * 0.0001)
            if max_future >= strike:
                return {"outcome": "LOSS"}
            else:
                return {"outcome": "WIN", "pnl": 50}
        
        elif recommendation == "PUT":
            strike = entry_price - (250 * 0.0001)
            if min_future <= strike:
                return {"outcome": "LOSS"}
            else:
                return {"outcome": "WIN", "pnl": 50}
        
        return None
    
    def backtest(self, min_score=60):
        """Executa backtest"""
        if not self.data:
            print("❌ Nenhum dado carregado!")
            return False
        
        print(f"\n📊 Backtesting {self.symbol} {self.timeframe}")
        print("─" * 60)
        
        triggers = []
        fixed_time = []
        
        for idx, candle in enumerate(self.data):
            # TRIGGERS
            score = self._get_trigger_score(candle)
            if score >= min_score:
                recommendation = self._get_recommendation(candle)
                entry_price = candle.get('close', 0)
                
                validation = self._validate_trade(idx, entry_price, recommendation)
                if validation:
                    triggers.append(validation)
            
            # FIXED TIME (20:00)
            candle_time = candle.get('datetime', '')
            if '20:00' in candle_time:
                recommendation = self._get_recommendation(candle)
                entry_price = candle.get('close', 0)
                
                validation = self._validate_trade(idx, entry_price, recommendation)
                if validation:
                    fixed_time.append(validation)
        
        # Calcular métricas
        if triggers:
            wins_t = sum(1 for t in triggers if t['outcome'] == 'WIN')
            wr_t = (wins_t / len(triggers) * 100) if triggers else 0
            print(f"✅ Triggers: {len(triggers)} trades, {wr_t:.1f}% win rate")
        else:
            print(f"⚠️  Triggers: 0 trades (score mínimo: {min_score}%)")
        
        if fixed_time:
            wins_f = sum(1 for t in fixed_time if t['outcome'] == 'WIN')
            wr_f = (wins_f / len(fixed_time) * 100) if fixed_time else 0
            print(f"✅ 20:00:    {len(fixed_time)} trades, {wr_f:.1f}% win rate")
        else:
            print(f"⚠️  20:00:    0 trades")
        
        self.results = {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "candles_tested": len(self.data),
            "triggers": triggers,
            "fixed_time": fixed_time,
            "metrics": {
                "triggers_total": len(triggers),
                "triggers_wins": sum(1 for t in triggers if t['outcome'] == 'WIN'),
                "triggers_wr": (sum(1 for t in triggers if t['outcome'] == 'WIN') / len(triggers) * 100) if triggers else 0,
                "fixed_total": len(fixed_time),
                "fixed_wins": sum(1 for t in fixed_time if t['outcome'] == 'WIN'),
                "fixed_wr": (sum(1 for t in fixed_time if t['outcome'] == 'WIN') / len(fixed_time) * 100) if fixed_time else 0,
            }
        }
        
        return True
    
    def export_json(self, output_file):
        """Exporta resultado em JSON"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "backtest": self.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Exportado: {output_file}")


# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Backtest com dados em TEMPO REAL do MT5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 2000
  
  python3 backtest_realtime.py --symbol GBPUSD --tf M15 --last 500
  
  python3 backtest_realtime.py --symbol GOLD --tf M15 --last 1000 --save-json resultado.json
        """
    )
    
    parser.add_argument("--symbol", required=True, help="Símbolo (EURUSD, GBPUSD, GOLD, etc)")
    parser.add_argument("--tf", default="M15", help="Timeframe (M15, M30, H1, etc) - padrão: M15")
    parser.add_argument("--last", type=int, default=2000, help="Últimos N candles - padrão: 2000")
    parser.add_argument("--min-score", type=int, default=60, help="Score mínimo - padrão: 60")
    parser.add_argument("--save-json", help="Salvar resultado em JSON")
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🚀 BACKTEST TEMPO REAL - DADOS DIRETO DO MT5".center(80))
    print("="*80)
    
    backtest = RealtimeBacktest(args.symbol, args.tf)
    
    print(f"\n📡 Carregando dados...")
    if not backtest.load_data(last_n=args.last):
        print("\n💡 Solução:")
        print("   1. Adicione EA no gráfico {0} {1} do MT5".format(args.symbol, args.tf))
        print("   2. Execute: python3 realtime_executor.py")
        print("   3. Aguarde 5-10 minutos para dados chegarem")
        print("   4. Execute este script novamente")
        return
    
    if backtest.backtest(min_score=args.min_score):
        if args.save_json:
            backtest.export_json(args.save_json)
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
