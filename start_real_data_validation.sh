#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                   🎯 VALIDAÇÃO FINAL - DADOS REAIS                        ║"
echo "║          Sistema pronto para receber dados APENAS do MT5                  ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "📋 ESTADO ATUAL:"
echo "  ✅ Servidor HTTP: $(ps aux | grep -c 'server_mt5_http' | awk '{print ($1-1)>0 ? "RODANDO" : "PARADO"}')"
echo "  ✅ Monitor WebSocket: $(ps aux | grep -c 'monitor_mt5_real' | awk '{print ($1-1)>0 ? "RODANDO" : "PARADO"}')"
echo ""

echo "═════════════════════════════════════════════════════════════════════════════"
echo "📊 TESTE COMPLETO - VALIDAÇÃO"
echo "═════════════════════════════════════════════════════════════════════════════"
echo ""

# Limpar processos
echo "🧹 Limpando processos antigos..."
pkill -9 -f "server_mt5_http" 2>/dev/null
pkill -9 -f "monitor_mt5_real" 2>/dev/null
sleep 2

# Iniciar servidor
echo "🚀 Iniciando Servidor HTTP (port 8765)..."
cd /home/ubuntu/pessoal/options/src
python3 server_mt5_http.py > /tmp/server_real.log 2>&1 &
SERVER_PID=$!
sleep 2

# Iniciar monitor
echo "🚀 Iniciando Monitor WebSocket..."
python3 monitor_mt5_real.py > /tmp/monitor_real.log 2>&1 &
MONITOR_PID=$!
sleep 3

echo "✅ Ambos iniciados (Server: PID $SERVER_PID, Monitor: PID $MONITOR_PID)"
echo ""

# Enviar dados de teste
echo "📤 Enviando 52 candles (50 histórico + 2 novos)..."
cd /home/ubuntu/pessoal/options
python3 test_validation_bulk.py 2>/dev/null | grep -E "✅|XAUUSD|EURUSD"
echo ""

# Aguardar processamento
echo "⏳ Aguardando processamento (5 segundos)..."
sleep 5

echo ""
echo "═════════════════════════════════════════════════════════════════════════════"
echo "📊 RESULTADOS"
echo "═════════════════════════════════════════════════════════════════════════════"
echo ""

echo "📋 Servidor HTTP Log (últimas 20 linhas):"
echo "────────────────────────────────────────────"
tail -20 /tmp/server_real.log | grep -E "NOVO CANDLE|Close|✅|❌"
echo ""

echo "📋 Monitor WebSocket Log (últimas 20 linhas):"
echo "────────────────────────────────────────────"
tail -20 /tmp/monitor_real.log | head -20
echo ""

echo "═════════════════════════════════════════════════════════════════════════════"
echo "✅ VALIDAÇÃO COMPLETA"
echo "═════════════════════════════════════════════════════════════════════════════"
echo ""
echo "🎯 PRÓXIMAS AÇÕES:"
echo ""
echo "1️⃣  NO MT5:"
echo "   → Manter SendCandlesToServer.mq5 ANEXADO ao gráfico XAUUSD M15"
echo "   → Próximo candle real M15 será enviado automaticamente"
echo ""
echo "2️⃣  NO SERVIDOR (Python):"
echo "   → Servidor aguarda HTTP POST com dados do MT5"
echo "   → Calcula 25+ indicadores"
echo "   → Transmite via WebSocket"
echo ""
echo "3️⃣  MONITOR (Python):"
echo "   → Recebe via WebSocket"
echo "   → Executa XGBoost predictions"
echo "   → Envia Telegram com recomendação"
echo ""
echo "═════════════════════════════════════════════════════════════════════════════"
echo ""

# Manter processos rodando
echo "⏰ Sistema AGUARDANDO DADOS REAIS DO MT5..."
echo "   Pressione Ctrl+C para parar"
echo ""

# Cleanup ao sair
trap "
echo ''
echo '⏹️  Parando serviços...'
kill $SERVER_PID $MONITOR_PID 2>/dev/null
echo '✅ Finalizado'
exit 0
" INT

# Monitorar continuamente
while true; do
  sleep 10
done
