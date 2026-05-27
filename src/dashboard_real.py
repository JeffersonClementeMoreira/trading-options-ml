#!/usr/bin/env python3
"""
Dashboard em tempo real - Monitoramento completo do sistema
Acompanha: Dados, Modelos, Alertas, Performance
"""

import asyncio
import websockets
import json
from collections import defaultdict, deque
from datetime import datetime
import sys

class SystemDashboard:
    def __init__(self):
        self.ws_url = "ws://127.0.0.1:9001"
        self.metrics = defaultdict(lambda: {
            "candles_received": 0,
            "alerts_sent": 0,
            "last_update": None,
            "last_values": None,
            "daily_alerts": defaultdict(int)
        })
        self.alert_log = deque(maxlen=50)  # Últimos 50 alertas
        self.start_time = datetime.now()

    async def connect(self):
        """Conecta ao WebSocket e monitora"""
        try:
            async with websockets.connect(self.ws_url) as ws:
                print("\n" + "=" * 100)
                print("🎯 DASHBOARD DO SISTEMA DE TRADING - DADOS REAIS".center(100))
                print("=" * 100)
                print(f"Horário: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 100 + "\n")
                
                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=60.0)
                        data = json.loads(msg)
                        
                        if "symbol" not in data:
                            continue
                        
                        symbol = data["symbol"]
                        dt = data.get("datetime", "")
                        o = data.get("open", 0)
                        h = data.get("high", 0)
                        l = data.get("low", 0)
                        c = data.get("close", 0)
                        v = data.get("volume", 0)
                        
                        # Atualizar métricas
                        m = self.metrics[symbol]
                        m["candles_received"] += 1
                        m["last_update"] = dt
                        m["last_values"] = {"o": o, "h": h, "l": l, "c": c, "v": v}
                        
                        # Registrar no log
                        self.alert_log.append({
                            "symbol": symbol,
                            "datetime": dt,
                            "close": c,
                            "timestamp": datetime.now()
                        })
                        
                        # Display
                        self.print_candle(symbol, dt, o, h, l, c, v)
                        
                        # Status a cada 30 candles
                        total_candles = sum(m["candles_received"] for m in self.metrics.values())
                        if total_candles % 30 == 0:
                            self.print_status()
                            
                    except asyncio.TimeoutError:
                        print("⏳ [TIMEOUT] Aguardando dados do MT5 (60s)...")
                        self.print_status()
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"❌ Erro: {e}")
                        
        except Exception as e:
            print(f"❌ Conexão: {e}")
            print("🔄 Reconectando em 5s...")
            await asyncio.sleep(5)
            await self.connect()

    def print_candle(self, symbol, dt, o, h, l, c, v):
        """Imprime um candle recebido"""
        change_pct = ((c - o) / o * 100) if o != 0 else 0
        arrow = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
        
        print(f"{arrow} {symbol:8} | {dt:16} | O:{o:10.5f} H:{h:10.5f} L:{l:10.5f} C:{c:10.5f} | "
              f"Chg: {change_pct:+6.2f}% | Vol: {v:,}")

    def print_status(self):
        """Status geral do sistema"""
        print("\n" + "─" * 100)
        print("📊 STATUS DO SISTEMA".center(100))
        print("─" * 100)
        
        uptime = datetime.now() - self.start_time
        print(f"⏱️  Uptime: {str(uptime).split('.')[0]}")
        
        print("\n📈 SÍMBOLOS MONITORADOS:")
        for symbol in sorted(self.metrics.keys()):
            m = self.metrics[symbol]
            print(f"  {symbol:8} | Candles: {m['candles_received']:6,} | "
                  f"Último: {m['last_update']:16} | "
                  f"Close: {m['last_values']['c']:.5f if m['last_values'] else 'N/A'}")
        
        print(f"\n{'─' * 100}\n")

    async def run(self):
        """Inicia o dashboard"""
        await self.connect()

async def main():
    dashboard = SystemDashboard()
    await dashboard.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✋ Dashboard encerrado")
        sys.exit(0)
