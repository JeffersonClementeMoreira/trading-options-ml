#!/bin/bash

###############################################################################
# START MT5 LIVE REAL DATA SERVER
# 
# Sistema que processa APENAS dados REAIS do MT5
# SEM SIMULAÇÃO
# 
# O EA SendCandlesToServer.ex5 (já compilado no MT5) envia dados para:
# http://127.0.0.1:8765/mt5/candle/real
###############################################################################

set -e

BASE_DIR="/home/ubuntu/pessoal/options"
PRODUCTION_DIR="$BASE_DIR/production"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                            ║"
echo "║            🚀 MT5 LIVE REAL DATA PRODUCTION SERVER                         ║"
echo "║                                                                            ║"
echo "║                    APENAS DADOS REAIS - SEM SIMULAÇÃO                     ║"
echo "║                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# ════════════════════════════════════════════════════════════════════════════
# VERIFICAÇÕES
# ════════════════════════════════════════════════════════════════════════════

echo "✅ Verificando pré-requisitos..."
echo ""

# Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado"
    exit 1
fi

# Flask
python3 -c "import flask" 2>/dev/null || {
    echo "⚠️  Flask não instalado, instalando..."
    pip install flask flask-cors --quiet
    echo "✅ Flask instalado"
}

echo "✅ Tudo pronto"
echo ""

# ════════════════════════════════════════════════════════════════════════════
# LIMPAR E INICIAR
# ════════════════════════════════════════════════════════════════════════════

echo "🧹 Limpando processos antigos..."
pkill -9 -f "mt5_live" 2>/dev/null || true
pkill -9 -f "server_mt5_http" 2>/dev/null || true
sleep 2

echo "✅ Limpo"
echo ""

# Carregar .env
if [ -f "$BASE_DIR/.env" ]; then
    set -a
    source "$BASE_DIR/.env"
    set +a
    echo "✅ Configuração carregada (.env)"
fi

echo ""

# Iniciar servidor
cd "$PRODUCTION_DIR"

echo "🌐 Iniciando servidor MT5 LIVE (port 8765)..."
python3 mt5_live_real_server.py > /tmp/mt5_live_real.log 2>&1 &
SERVER_PID=$!

sleep 2

if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Servidor iniciado (PID $SERVER_PID)"
else
    echo "❌ Servidor falhou"
    tail /tmp/mt5_live_real.log
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                            ║"
echo "║                    ✅ SERVIDOR RODANDO - DADOS REAIS                       ║"
echo "║                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 SISTEMA PRONTO:"
echo ""
echo "   ✅ Servidor: http://0.0.0.0:8765"
echo "   📨 Endpoint: POST /mt5/candle/real"
echo "   🎯 Modo: APENAS DADOS REAIS (sem simulação)"
echo "   🔄 Pares: Todos os que MT5 enviar"
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo ""

echo "🔧 CONFIGURAR MT5 (próximo passo):"
echo ""
echo "   1. Abrir MT5 Terminal"
echo "   2. Abrir arquivo: SendCandlesToServer.mq5"
echo "   3. Editar linha 8:"
echo ""
echo "      input string ServerURL = \"http://127.0.0.1:8765/mt5/candle/real\";"
echo ""
echo "   4. Compilar (F5)"
echo "   5. Anexar EA ao gráfico EURUSD M15"
echo ""
echo "   Resultado: A cada novo candle M15 fechado, MT5 envia dados reais para"
echo "   este servidor, que processa e envia Telegram"
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo ""

echo "📜 MONITORAR EM TEMPO REAL:"
echo ""
echo "   # Logs completos"
echo "   $ tail -f /tmp/mt5_live_real.log"
echo ""
echo "   # Apenas sinais reais"
echo "   $ grep 'SINAL REAL GERADO' /tmp/mt5_live_real.log"
echo ""
echo "   # Status"
echo "   $ curl http://localhost:8765/mt5/status | jq ."
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo ""

echo "⚠️  IMPORTANTE:"
echo ""
echo "   Este servidor RECEBE dados REAIS do MT5 (via EA HTTP)"
echo "   NÃO SIMULA nada"
echo "   Processa APENAS últimos candles REAIS fechados"
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Monitor com auto-restart
echo "✅ Servidor rodando. Pressione Ctrl+C para parar."
echo ""

while true; do
    if ! ps -p $SERVER_PID > /dev/null 2>&1; then
        echo ""
        echo "⚠️  SERVIDOR CAIU! $(date '+%Y-%m-%d %H:%M:%S')"
        echo "   Reiniciando..."
        
        python3 mt5_live_real_server.py > /tmp/mt5_live_real.log 2>&1 &
        SERVER_PID=$!
        
        echo "✅ Servidor reiniciado (PID $SERVER_PID)"
    fi
    
    sleep 10
done
