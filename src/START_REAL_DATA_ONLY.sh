#!/bin/bash
# ⚠️ SCRIPT PARA USAR APENAS DADOS REAIS DO MT5

echo "🧹 Parando todos os scripts antigos..."
pkill -9 -f "server_final\|server_mt5_real\|mt5_websocket\|test_mt5" 2>/dev/null
sleep 2

echo "🚀 Iniciando APENAS servidor correto com dados reais..."
cd /home/ubuntu/pessoal/options/src

# ✅ Servidor HTTP que RECEBE dados do MT5 via POST
python3 server_mt5_http.py > /tmp/server_real.log 2>&1 &
SERVER_PID=$!
echo "✅ Server HTTP iniciado (PID: $SERVER_PID)"

sleep 2

# ✅ Monitor que ENVIA para Telegram
python3 monitor_mt5_real.py > /tmp/monitor_real.log 2>&1 &
MONITOR_PID=$!
echo "✅ Monitor iniciado (PID: $MONITOR_PID)"

sleep 2

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ SISTEMA CONFIGURADO PARA DADOS REAIS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🔗 Endpoint HTTP: http://127.0.0.1:8765/mt5/candle"
echo "📡 WebSocket: ws://localhost:9001"
echo "📞 Telegram: Ativo"
echo ""
echo "⚠️  PRÓXIMO PASSO:"
echo "1. Compilar SendCandlesToServer.mq5 no MT5 MetaEditor"
echo "2. Tools → Options → Expert Advisors → WebRequest ✅"
echo "3. Attach script ao chart (EURUSD M15)"
echo ""
echo "🔍 Logs:"
echo "   Server: tail -f /tmp/server_real.log"
echo "   Monitor: tail -f /tmp/monitor_real.log"
echo "════════════════════════════════════════════════════════════════"
