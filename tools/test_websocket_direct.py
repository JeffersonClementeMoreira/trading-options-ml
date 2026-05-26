#!/usr/bin/env python3
"""
Teste direto do WebSocket - Debug simples
Conecta e mostra o que recebe
"""

import json
import asyncio

try:
    import websockets
except:
    print("❌ websockets não instalado")
    exit(1)

async def test():
    uri = "ws://localhost:9001"
    print(f"🔗 Conectando a {uri}...\n")
    
    async with websockets.connect(uri) as websocket:
        print(f"✅ Conectado!\n")
        
        # Inscrever
        await websocket.send(json.dumps({'action': 'subscribe', 'symbol': 'GBPUSD'}))
        print(f"📨 Inscrição enviada\n")
        
        # Receber por 30 segundos
        import time
        start = time.time()
        count = 0
        
        while time.time() - start < 30:
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(msg)
                count += 1
                
                print(f"\n📨 Mensagem #{count} recebida:")
                print(f"   Symbol: {data.get('symbol')}")
                print(f"   Time: {data.get('time')}")
                print(f"   Close: {data.get('ohlc', {}).get('close')}")
                print(f"   XGBoost: {data.get('xgboost', {}).get('category')}")
                
            except asyncio.TimeoutError:
                print("⏱️  Timeout (nenhum dado recebido por 5 segundos)")
            except Exception as e:
                print(f"❌ Erro: {str(e)}")
                break
        
        print(f"\n\n📊 Resultado: Recebeu {count} mensagens em 30 segundos")
        
        if count == 0:
            print("❌ PROBLEMA: Servidor não enviou NENHUM dado!")
            print("\nPossíveis causas:")
            print("1. Servidor não está respondendo")
            print("2. Servidor não tem clientes conectados no momento do broadcast")
            print("3. Dados históricos não carregados corretamente")
        else:
            print(f"✅ Servidor está funcionando! Recebeu ~{count*10} segundos de dados")

if __name__ == '__main__':
    asyncio.run(test())
