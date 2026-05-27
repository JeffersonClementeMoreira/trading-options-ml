#!/usr/bin/env python3
"""
Servidor WebSocket ULTRA SIMPLES - só testa se envia
"""

import json
import asyncio
import numpy as np
from datetime import datetime

try:
    from websockets.asyncio.server import serve
except:
    from websockets.server import serve

class SimpleServer:
    def __init__(self):
        self.clients = set()
        self.iteration = 0
    
    async def handler(self, websocket):
        self.clients.add(websocket)
        print(f"✅ Client #{len(self.clients)} conectado")
        
        try:
            async for msg in websocket:
                print(f"📨 Recebido: {msg}")
        finally:
            self.clients.discard(websocket)
            print(f"⛔ Client desconectado")
    
    async def broadcaster(self):
        """Envia mensagens a cada 5 segundos"""
        while True:
            await asyncio.sleep(5)
            
            if not self.clients:
                print("⏳ Aguardando clientes...")
                continue
            
            self.iteration += 1
            
            # Criar mensagem simples
            msg = json.dumps({
                'iteration': self.iteration,
                'symbol': 'GBPUSD',
                'close': 1.27 + np.random.uniform(-0.01, 0.01),
                'timestamp': datetime.now().isoformat()
            })
            
            # Enviar
            disconnected = set()
            for client in self.clients:
                try:
                    await client.send(msg)
                    print(f"   ✅ Enviado para cliente")
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
                    disconnected.add(client)
            
            self.clients -= disconnected
    
    async def run(self):
        print("📡 Servidor simples iniciando...\n")
        
        # Tarefas
        broadcast_task = asyncio.create_task(self.broadcaster())
        
        async with serve(self.handler, 'localhost', 9001):
            print("🚀 Servidor listening em ws://localhost:9001\n")
            try:
                await broadcast_task
            except KeyboardInterrupt:
                print("\n🛑 Parado")

if __name__ == '__main__':
    server = SimpleServer()
    asyncio.run(server.run())
