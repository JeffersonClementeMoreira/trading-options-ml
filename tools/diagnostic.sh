#!/bin/bash

# Comando de Debug - Ver status do sistema em tempo real

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                ║"
echo "║                   🔍 DIAGNOSTIC - MONITOR STATUS 🔍                           ║"
echo "║                                                                                ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# 1. Processos
echo "1️⃣  PROCESSOS ATIVOS"
echo "────────────────────────────────────────────────────────────────────────────────"
SERVIDOR=$(ps aux | grep "mt5_websocket_server_demo" | grep -v grep)
MONITOR=$(ps aux | grep "live_websocket_monitor_debug" | grep -v grep)

if [ -z "$SERVIDOR" ]; then
    echo "❌ Servidor Bridge: INATIVO"
else
    PID_S=$(echo "$SERVIDOR" | awk '{print $2}')
    CPU_S=$(echo "$SERVIDOR" | awk '{print $3}')
    MEM_S=$(echo "$SERVIDOR" | awk '{print $4}')
    echo "✅ Servidor Bridge (Demo)"
    echo "   ├─ PID: $PID_S"
    echo "   ├─ CPU: $CPU_S%"
    echo "   └─ RAM: $MEM_S%"
fi

echo ""

if [ -z "$MONITOR" ]; then
    echo "❌ Monitor Debug: INATIVO"
else
    PID_M=$(echo "$MONITOR" | awk '{print $2}')
    CPU_M=$(echo "$MONITOR" | awk '{print $3}')
    MEM_M=$(echo "$MONITOR" | awk '{print $4}')
    echo "✅ Monitor WebSocket (Debug)"
    echo "   ├─ PID: $PID_M"
    echo "   ├─ CPU: $CPU_M%"
    echo "   └─ RAM: $MEM_M%"
fi

echo ""
echo "2️⃣  CONECTIVIDADE"
echo "────────────────────────────────────────────────────────────────────────────────"

# Verificar porta
if netstat -ln 2>/dev/null | grep -q ":9001 "; then
    echo "✅ Porta WebSocket 9001: ABERTA"
else
    echo "❌ Porta WebSocket 9001: FECHADA"
fi

echo ""
echo "3️⃣  ÚLTIMAS ATIVIDADES"
echo "────────────────────────────────────────────────────────────────────────────────"

# Ver últimas linhas dos logs se existirem
if [ -f "/tmp/websocket_monitor.log" ]; then
    echo "📋 Log do Monitor:"
    tail -5 /tmp/websocket_monitor.log | sed 's/^/   /'
else
    echo "📋 Nenhum log de monitor encontrado"
fi

echo ""
echo "4️⃣  TESTE RÁPIDO"
echo "────────────────────────────────────────────────────────────────────────────────"

# Tentar conectar ao servidor
echo "Testando conexão com servidor..."
python3 << 'PYTHON_END'
import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('127.0.0.1', 9001))

if result == 0:
    print("   ✅ Servidor respondendo em ws://localhost:9001")
else:
    print("   ❌ Servidor não respondendo")

sock.close()
PYTHON_END

echo ""
echo "5️⃣  COMANDOS ÚTEIS"
echo "────────────────────────────────────────────────────────────────────────────────"
echo ""
echo "Ver em tempo real:"
echo "  $ tail -f /tmp/websocket_monitor.log"
echo ""
echo "Ver processos:"
echo "  $ ps aux | grep -E 'mt5_websocket|live_websocket_monitor_debug'"
echo ""
echo "Ver estatísticas de CPU/RAM:"
echo "  $ top -p \$(pgrep -f mt5_websocket_server_demo | head -1)"
echo ""
echo "Parar sistema:"
echo "  $ pkill -9 -f 'mt5_websocket_server_demo|live_websocket_monitor_debug'"
echo ""
echo "Reiniciar:"
echo "  $ cd /home/ubuntu/pessoal/options/src"
echo "  $ python3 mt5_websocket_server_demo.py &"
echo "  $ sleep 2"
echo "  $ python3 live_websocket_monitor_debug.py &"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
