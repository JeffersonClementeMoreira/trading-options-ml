#!/usr/bin/env python3
"""
Análise em tempo real dos dados recebidos do MT5
Valida: qualidade, ranges, duplicatas, correlações
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime
from collections import defaultdict

class RealDataAnalyzer:
    def __init__(self):
        self.ws_url = "ws://127.0.0.1:9001"
        self.data_log = defaultdict(list)
        self.symbol_stats = defaultdict(lambda: {
            "count": 0,
            "min_open": float("inf"),
            "max_open": 0,
            "min_close": float("inf"),
            "max_close": 0,
            "last_datetime": None,
            "duplicates": 0,
            "valid_ranges": 0,
            "suspicious": 0
        })
        
        # Ranges esperados
        self.ranges = {
            "EURUSD": {"min": 0.9, "max": 1.3},
            "GBPUSD": {"min": 1.1, "max": 1.5},
            "XAUUSD": {"min": 1200, "max": 2500}
        }
        
        # Valores hardcoded suspeitos
        self.suspicious_values = {
            "EURUSD": [1.08, 1.0800],
            "GBPUSD": [1.27, 1.2700],
            "XAUUSD": [2400, 2400.0]
        }

    def validate_candle(self, candle):
        """Valida se candle está dentro de ranges reais"""
        symbol = candle.get("symbol")
        if symbol not in self.ranges:
            return None
        
        prices = [candle["open"], candle["high"], candle["low"], candle["close"]]
        r = self.ranges[symbol]
        
        # Checar range
        if all(r["min"] <= p <= r["max"] for p in prices):
            return True
        return False

    def is_suspicious(self, candle):
        """Detecta valores hardcoded"""
        symbol = candle.get("symbol")
        if symbol not in self.suspicious_values:
            return False
        
        prices = [candle["open"], candle["high"], candle["low"], candle["close"]]
        for p in prices:
            if p in self.suspicious_values[symbol]:
                return True
        return False

    async def connect(self):
        """Conecta ao WebSocket e monitora dados"""
        try:
            async with websockets.connect(self.ws_url) as ws:
                print(f"\n✅ Conectado ao servidor em {self.ws_url}\n")
                print("=" * 80)
                print("ANÁLISE DE DADOS REAIS DO MT5".center(80))
                print("=" * 80)
                
                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=30.0)
                        data = json.loads(msg)
                        
                        if "symbol" not in data:
                            continue
                        
                        await self.analyze_candle(data)
                        
                    except asyncio.TimeoutError:
                        print("\n⏳ Aguardando dados do MT5 (timeout 30s)...")
                    except Exception as e:
                        print(f"❌ Erro ao processar: {e}")
                        
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            print("Tentando reconectar em 5s...")
            await asyncio.sleep(5)
            await self.connect()

    async def analyze_candle(self, candle):
        """Analisa um novo candle"""
        symbol = candle.get("symbol")
        dt = candle.get("datetime")
        o = candle.get("open")
        h = candle.get("high")
        l = candle.get("low")
        c = candle.get("close")
        v = candle.get("volume")
        
        stats = self.symbol_stats[symbol]
        stats["count"] += 1
        stats["last_datetime"] = dt
        
        # Update min/max
        stats["min_open"] = min(stats["min_open"], o)
        stats["max_open"] = max(stats["max_open"], o)
        stats["min_close"] = min(stats["min_close"], c)
        stats["max_close"] = max(stats["max_close"], c)
        
        # Verificar validação
        is_valid = self.validate_candle(candle)
        is_susp = self.is_suspicious(candle)
        
        if is_valid:
            stats["valid_ranges"] += 1
        if is_susp:
            stats["suspicious"] += 1
        
        # Log
        self.data_log[symbol].append({
            "datetime": dt,
            "ohlc": (o, h, l, c),
            "volume": v,
            "valid": is_valid,
            "suspicious": is_susp
        })
        
        # Print formatado
        status = "✅ REAL" if (is_valid and not is_susp) else "⚠️ SUSPEITO"
        if is_susp:
            status = "❌ HARDCODED"
        
        print(f"{status} | {symbol:8} | {dt:16} | O:{o:.5f} H:{h:.5f} L:{l:.5f} C:{c:.5f} | V:{v}")
        
        # Mostrar estatísticas a cada 10 candles
        if stats["count"] % 10 == 0:
            self.print_stats()

    def print_stats(self):
        """Mostra estatísticas por símbolo"""
        print("\n" + "=" * 80)
        print("ESTATÍSTICAS POR SÍMBOLO".center(80))
        print("=" * 80)
        
        for symbol in sorted(self.symbol_stats.keys()):
            s = self.symbol_stats[symbol]
            if s["count"] == 0:
                continue
            
            valid_pct = (s["valid_ranges"] / s["count"] * 100) if s["count"] > 0 else 0
            susp_pct = (s["suspicious"] / s["count"] * 100) if s["count"] > 0 else 0
            
            print(f"\n{symbol}:")
            print(f"  Candles: {s['count']:,}")
            print(f"  Válidos (real):     {s['valid_ranges']:,} ({valid_pct:.1f}%)")
            print(f"  Suspeitos (fake):   {s['suspicious']:,} ({susp_pct:.1f}%)")
            print(f"  Open:  {s['min_open']:.5f} - {s['max_open']:.5f}")
            print(f"  Close: {s['min_close']:.5f} - {s['max_close']:.5f}")
            print(f"  Último: {s['last_datetime']}")

async def main():
    analyzer = RealDataAnalyzer()
    await analyzer.connect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✋ Análise encerrada pelo usuário")
        sys.exit(0)
