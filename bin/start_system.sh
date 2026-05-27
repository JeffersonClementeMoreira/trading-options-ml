#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                 🚀 INICIAR SISTEMA - DADOS REAIS DO MT5 🚀               ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

cd /home/ubuntu/pessoal/options/src

echo "🧹 Parando processos antigos..."
pkill -9 -f "server_mt5_http" 2>/dev/null
pkill -9 -f "monitor_mt5_real" 2>/dev/null
sleep 2
echo "✅ Limpo"
echo ""

echo "📊 Removendo logs antigos..."
rm -f /tmp/server_real.log /tmp/monitor_real.log
echo "✅ Limpo"
echo ""

echo "🚀 INICIANDO SISTEMA:"
echo ""

echo "  1️⃣  Servidor HTTP (port 8765)..."
python3 server_mt5_http.py > /tmp/server_real.log 2>&1 &
SERVER_PID=$!
sleep 2
echo "     ✅ PID: $SERVER_PID"
echo ""

echo "  2️⃣  Monitor WebSocket..."
python3 monitor_mt5_real.py > /tmp/monitor_real.log 2>&1 &
MONITOR_PID=$!
sleep 2
echo "     ✅ PID: $MONITOR_PID"
echo ""

echo "═════════════════════════════════════════════════════════════════════════════"
echo "✅ SISTEMA PRONTO!"
echo "═════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Processos rodando:"
echo "   • server_mt5_http.py (PID $SERVER_PID)"
echo "   • monitor_mt5_real.py (PID $MONITOR_PID)"
echo ""
echo "📊 Para monitorar em tempo real:"
echo ""
echo "   SERVIDOR:"
echo "   tail -f /tmp/server_real.log"
echo ""
echo "   MONITOR:"
echo "   tail -f /tmp/monitor_real.log"
echo ""
echo "═════════════════════════════════════════════════════════════════════════════"
echo "⏳ Aguardando primeiro candle real M15 do MT5..."
echo ""

# Manter vivo
wait
