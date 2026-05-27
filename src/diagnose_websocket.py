#!/usr/bin/env python3
"""
Diagnóstico - Mostra EXATAMENTE o que servidor está enviando
Útil para validar que não há duplicatas
"""

import json
import asyncio
from datetime import datetime

try:
    import websockets
except:
    print("❌ websockets não instalado")
    exit(1)

async def diagnose():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🔍 DIAGNÓSTICO WEBSOCKET 🔍                        ║
║                                                                            ║
║  Mostra EXATAMENTE o que servidor está enviando                          ║
║  para validar que não há duplicatas ou dados antigos                      ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

🔗 Conectando...\n""")
    
    async with websockets.connect('ws://localhost:9001') as ws:
        print("✅ Conectado!\n")
        
        # Inscrever
        await ws.send(json.dumps({'action': 'subscribe', 'symbol': 'GBPUSD'}))
        await ws.send(json.dumps({'action': 'subscribe', 'symbol': 'EURUSD'}))
        await ws.send(json.dumps({'action': 'subscribe', 'symbol': 'XAUUSD'}))
        
        print("📨 Inscrito em 3 pares\n")
        print("=" * 80)
        print("Recebendo candles... (mostra DateTime + Close para cada)\n")
        print("=" * 80)
        
        received = {}
        count = 0
        
        async for msg in ws:
            try:
                data = json.loads(msg)
                
                symbol = data['symbol']
                time_str = data['time']
                close = data['ohlc']['close']
                
                key = f"{symbol}:{time_str}"
                
                count += 1
                
                # Verificar se é duplicado
                if key in received:
                    print(f"\n⚠️  DUPLICADO #{count}! {symbol} {time_str}")
                    print(f"    Já foi recebido em mensagem #{received[key]}")
                else:
                    received[key] = count
                    print(f"#{count:3d} ✅ {symbol:7s} | {time_str} | Close: {close:.5f}")
                
                # Sair após 20 mensagens
                if count >= 20:
                    print("\n" + "=" * 80)
                    print(f"\n📊 RESULTADO: Recebeu {count} mensagens, {len(received)} únicas\n")
                    
                    if count == len(received):
                        print("✅ TUDO OK: Nenhuma duplicata detectada!")
                    else:
                        print(f"⚠️  ATENÇÃO: {count - len(received)} duplicatas foram ignoradas")
                    
                    break
            except Exception as e:
                print(f"❌ Erro: {e}")

if __name__ == '__main__':
    asyncio.run(diagnose())
