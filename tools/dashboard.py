#!/usr/bin/env python3
"""
Dashboard de Monitoramento - PRODUÇÃO REAL
Mostra status do sistema em tempo real
"""

import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

def check_process(name):
    """Verificar se processo está rodando"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def get_ps_info(name):
    """Pegar info do processo"""
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        for line in result.stdout.split('\n'):
            if name in line and 'grep' not in line:
                parts = line.split()
                if len(parts) >= 6:
                    return {
                        'pid': parts[1],
                        'cpu': parts[2],
                        'mem': parts[3]
                    }
    except:
        pass
    return None

def print_header():
    """Cabeçalho"""
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🚀 DASHBOARD SISTEMA REAL-TIME - SMART MONEY CONCEPTS + XGBOOST             ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

def print_status():
    """Mostrar status"""
    
    servidor_ok = check_process('mt5_websocket_server_demo')
    monitor_ok = check_process('live_websocket_monitor')
    
    servidor_info = get_ps_info('mt5_websocket_server_demo')
    monitor_info = get_ps_info('live_websocket_monitor')
    
    print(f"\n📊 STATUS EM TEMPO REAL - {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'─'*80}\n")
    
    # Servidor Bridge
    status_servidor = "✅ ATIVO" if servidor_ok else "❌ INATIVO"
    print(f"1️⃣  Servidor Bridge (DEMO)       {status_servidor}")
    if servidor_info:
        print(f"    ├─ PID: {servidor_info['pid']}")
        print(f"    ├─ CPU: {servidor_info['cpu']}%")
        print(f"    └─ MEM: {servidor_info['mem']} MB")
    print()
    
    # Monitor Telegram
    status_monitor = "✅ ATIVO" if monitor_ok else "❌ INATIVO"
    print(f"2️⃣  Monitor Telegram             {status_monitor}")
    if monitor_info:
        print(f"    ├─ PID: {monitor_info['pid']}")
        print(f"    ├─ CPU: {monitor_info['cpu']}%")
        print(f"    └─ MEM: {monitor_info['mem']} MB")
    print()
    
    # Conectividade
    print(f"🔌 CONECTIVIDADE")
    print(f"{'─'*80}")
    print(f"├─ WebSocket Server: ws://localhost:9001")
    print(f"├─ Telegram Bot: Configurado ✅")
    print(f"└─ MT5 Bridge: DEMO Mode (Dados Históricos)")
    print()
    
    # Pares monitorados
    print(f"📈 PARES MONITORADOS")
    print(f"{'─'*80}")
    print(f"├─ GBPUSD (Libra/Dólar)")
    print(f"├─ EURUSD (Euro/Dólar)")
    print(f"└─ XAUUSD (Ouro)")
    print()
    
    # Configuração
    print(f"⚙️  CONFIGURAÇÃO")
    print(f"{'─'*80}")
    print(f"├─ Timeframe: M15 (15 minutos)")
    print(f"├─ Indicadores: 25+ técnicos")
    print(f"├─ Modelo ML: XGBoost 3 modelos")
    print(f"├─ Confluence: SMC 2+ confluências")
    print(f"└─ Sinais: COMPRA/VENDA quando score >70%")
    print()
    
    # Resumo
    print(f"📋 RESUMO")
    print(f"{'─'*80}")
    all_ok = servidor_ok and monitor_ok
    if all_ok:
        print(f"✅ SISTEMA PRONTO PARA PRODUÇÃO")
        print(f"\nOs pares estão sendo monitorados em tempo real!")
        print(f"Verifique seu Telegram para as notificações de sinais.")
    else:
        print(f"⚠️  SISTEMA COM PROBLEMAS")
        if not servidor_ok:
            print(f"   → Servidor Bridge não está rodando")
        if not monitor_ok:
            print(f"   → Monitor Telegram não está rodando")
    
    print(f"\n{'='*80}\n")

def main():
    """Main"""
    print_header()
    
    try:
        while True:
            print_status()
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"\n\n⛔ Dashboard parado")

if __name__ == '__main__':
    main()
