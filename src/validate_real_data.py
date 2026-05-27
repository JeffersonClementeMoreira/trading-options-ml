#!/usr/bin/env python3
"""
🔍 VALIDADOR DE DADOS REAIS
Verifica se os dados recebidos são REAIS (do MT5) ou simulados
"""

import asyncio
import json
from websockets.asyncio.client import connect

# Ranges realistas para validação
VALID_RANGES = {
    'EURUSD': {'min': 0.9000, 'max': 1.3000},
    'GBPUSD': {'min': 1.1000, 'max': 1.5000},
    'XAUUSD': {'min': 1200, 'max': 2500},
}

INVALID_HARDCODED = {
    'EURUSD': [1.08, 1.07970],
    'GBPUSD': [1.27],
    'XAUUSD': [2400],
}

class DataValidator:
    def __init__(self):
        self.candles_received = 0
        self.real_data_count = 0
        self.fake_data_count = 0
        self.last_candle = {}
    
    def check_if_real(self, candle):
        """Verificar se candle é real ou simulado"""
        symbol = candle.get('symbol')
        open_p = float(candle.get('open', 0))
        close = float(candle.get('close', 0))
        
        # ❌ Check 1: Valores hardcoded conhecidos
        if symbol in INVALID_HARDCODED:
            for invalid_val in INVALID_HARDCODED[symbol]:
                if abs(open_p - invalid_val) < 0.0001 or abs(close - invalid_val) < 0.0001:
                    return False, f"Valor hardcoded detectado: {invalid_val}"
        
        # ❌ Check 2: Fora do range realista
        if symbol in VALID_RANGES:
            valid_range = VALID_RANGES[symbol]
            if not (valid_range['min'] <= open_p <= valid_range['max']):
                return False, f"Open {open_p} fora do range [{valid_range['min']}, {valid_range['max']}]"
            if not (valid_range['min'] <= close <= valid_range['max']):
                return False, f"Close {close} fora do range [{valid_range['min']}, {valid_range['max']}]"
        
        # ✅ Check 3: Parece real
        return True, "✅ Dados realistas"
    
    async def validate(self):
        """Conectar e validar dados em tempo real"""
        uri = "ws://localhost:9001"
        
        print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         🔍 VALIDADOR DE DADOS REAIS DO MT5                               ║
║         Verificando se recebe dados reais (não simulados)                 ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

🔗 Conectando a {uri}...
⏳ Aguardando candles...
""")
        
        try:
            async with connect(uri) as websocket:
                print("✅ Conectado!\n")
                
                # Inscrever em pares
                for symbol in ['EURUSD', 'GBPUSD', 'XAUUSD']:
                    await websocket.send(json.dumps({
                        'action': 'subscribe',
                        'symbol': symbol
                    }))
                
                # Validar dados
                async for message in websocket:
                    try:
                        candle = json.loads(message)
                        self.candles_received += 1
                        
                        is_real, reason = self.check_if_real(candle)
                        
                        symbol = candle.get('symbol')
                        dt = candle.get('datetime')
                        open_p = candle.get('open')
                        close = candle.get('close')
                        
                        if is_real:
                            self.real_data_count += 1
                            status = "✅ REAL"
                        else:
                            self.fake_data_count += 1
                            status = f"❌ SIMULADO: {reason}"
                        
                        print(f"{status:50} | {symbol:10} | {dt} | Open: {open_p:.5f} | Close: {close:.5f}")
                        
                        # Resumo a cada 10 candles
                        if self.candles_received % 10 == 0:
                            print(f"\n📊 Resumo ({self.candles_received} candles):")
                            print(f"   ✅ Reais: {self.real_data_count}")
                            print(f"   ❌ Simulados: {self.fake_data_count}")
                            print(f"   Taxa de acerto: {(self.real_data_count/self.candles_received)*100:.1f}%\n")
                    
                    except json.JSONDecodeError:
                        print(f"⚠️ Erro ao decodificar: {message}")
                    except Exception as e:
                        print(f"⚠️ Erro: {e}")
        
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            print("⚠️ Servidor WebSocket não está rodando!")
            print("   Execute: python3 server_mt5_http.py &")

async def main():
    validator = DataValidator()
    await validator.validate()

if __name__ == "__main__":
    asyncio.run(main())
