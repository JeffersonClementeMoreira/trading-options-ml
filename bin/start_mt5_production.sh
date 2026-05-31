#!/bin/bash

###############################################################################
# START PRODUCTION SYSTEM - MT5 HTTP Server com Modelo ML
# 
# Inicia:
#   1. MT5 rodando em background (via Xvfb)
#   2. Servidor HTTP (porta 8765) - recebe candles MT5
#   3. Monitor de logs
###############################################################################

set -e

BASE_DIR="/home/ubuntu/pessoal/options"
PRODUCTION_DIR="$BASE_DIR/production"
SRC_DIR="$BASE_DIR/src"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                            ║"
echo "║              🚀 PRODUCTION SYSTEM - MT5 + ML SIGNALS                       ║"
echo "║                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# ════════════════════════════════════════════════════════════════════════════
# 1. VERIFICAR DEPENDÊNCIAS
# ════════════════════════════════════════════════════════════════════════════

echo "📦 Verificando dependências..."

# Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado"
    exit 1
fi
echo "✅ Python3: $(python3 --version)"

# Flask
python3 -c "import flask" 2>/dev/null || {
    echo "⚠️  Flask não encontrado, instalando..."
    pip install flask flask-cors --quiet
    echo "✅ Flask instalado"
}

# Dependências ML
python3 -c "import sklearn; import xgboost; import pandas; import numpy" 2>/dev/null || {
    echo "⚠️  Dependências ML faltando, instalando..."
    cd "$BASE_DIR"
    pip install -r requirements.txt --quiet 2>/dev/null || pip install scikit-learn xgboost pandas numpy --quiet
    echo "✅ Dependências instaladas"
}

echo ""

# ════════════════════════════════════════════════════════════════════════════
# 2. LIMPAR PROCESSOS ANTIGOS
# ════════════════════════════════════════════════════════════════════════════

echo "🧹 Limpando processos antigos..."

pkill -9 -f "server_mt5_http" 2>/dev/null || true
pkill -9 -f "monitor_mt5_real" 2>/dev/null || true
sleep 1

rm -f /tmp/mt5_server.log /tmp/monitor_mt5.log 2>/dev/null || true

echo "✅ Limpo"
echo ""

# ════════════════════════════════════════════════════════════════════════════
# 3. VERIFICAR MT5
# ════════════════════════════════════════════════════════════════════════════

echo "🎮 Verificando MT5..."

if pgrep -f "terminal64.exe" > /dev/null; then
    echo "✅ MT5 já está rodando ($(pgrep -f 'terminal64.exe' | wc -l) processo(s))"
else
    echo "⚠️  MT5 não está rodando"
    echo ""
    echo "Para iniciar MT5, execute em outro terminal:"
    echo "  $ cd ~/.wine/drive_c/Program\\ Files/MetaTrader\\ 5/"
    echo "  $ DISPLAY=:99 wine terminal64.exe &"
    echo ""
    read -p "Pressione Enter para continuar sem MT5 (teste com test_client.py)..."
fi

echo ""

# ════════════════════════════════════════════════════════════════════════════
# 4. CARREGAR VARIÁVEIS DE AMBIENTE
# ════════════════════════════════════════════════════════════════════════════

echo "⚙️  Carregando configuração..."

if [ -f "$BASE_DIR/.env" ]; then
    set -a
    source "$BASE_DIR/.env"
    set +a
    echo "✅ .env carregado"
else
    echo "⚠️  .env não encontrado. Telegram pode não funcionar."
    echo "   Execute: cp .env.example .env && vi .env"
fi

echo ""

# ════════════════════════════════════════════════════════════════════════════
# 5. INICIAR SERVIDOR HTTP
# ════════════════════════════════════════════════════════════════════════════

echo "🌐 Iniciando Servidor HTTP (porta 8765)..."
cd "$PRODUCTION_DIR"

python3 server_mt5_http.py > /tmp/mt5_server.log 2>&1 &
SERVER_PID=$!

sleep 2

if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Servidor iniciado (PID $SERVER_PID)"
else
    echo "❌ Servidor falhou ao iniciar"
    echo "   Ver log: tail -f /tmp/mt5_server.log"
    exit 1
fi

echo ""

# ════════════════════════════════════════════════════════════════════════════
# 6. STATUS
# ════════════════════════════════════════════════════════════════════════════

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                          ✅ SISTEMA INICIADO                              ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 COMPONENTES ATIVOS:"
echo ""
echo "   ✅ MT5 HTTP Server"
echo "      - Porta: 8765"
echo "      - Endpoint: http://0.0.0.0:8765/mt5/candle"
echo "      - PID: $SERVER_PID"
echo ""
echo "   📨 Recebe candles M15 do MT5"
echo "   🤖 Calcula indicadores + modelo ML"
echo "   🎯 Gera sinais com threshold otimizado"
echo "   💬 Envia alertas Telegram"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📜 MONITORAR EM TEMPO REAL:"
echo ""
echo "   # Terminal 1: Ver logs do servidor"
echo "   $ tail -f /tmp/mt5_server.log"
echo ""
echo "   # Terminal 2: Ver sinais enviados"
echo "   $ grep -i 'sinal\\|telegram' /tmp/mt5_server.log"
echo ""
echo "   # Terminal 3: Status do servidor"
echo "   $ curl http://localhost:8765/mt5/status"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "🧪 TESTAR SEM MT5:"
echo ""
echo "   $ cd $BASE_DIR/production/websocket"
echo "   $ python3 test_client.py"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "🎮 INICIAR MT5 EM BACKGROUND:"
echo ""
echo "   $ DISPLAY=:99 wine ~/.wine/drive_c/Program\\ Files/MetaTrader\\ 5/terminal64.exe &"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "🛑 PARAR SISTEMA:"
echo ""
echo "   $ pkill -9 -f server_mt5_http"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# ════════════════════════════════════════════════════════════════════════════
# 7. MONITOR COM AUTO-RESTART
# ════════════════════════════════════════════════════════════════════════════

echo "✅ Servidor rodando. Pressione Ctrl+C para parar."
echo ""

while true; do
    if ! ps -p $SERVER_PID > /dev/null 2>&1; then
        echo ""
        echo "⚠️  SERVIDOR CAIU! $(date '+%Y-%m-%d %H:%M:%S')"
        echo "   Reiniciando..."
        
        python3 server_mt5_http.py > /tmp/mt5_server.log 2>&1 &
        SERVER_PID=$!
        
        echo "✅ Servidor reiniciado (PID $SERVER_PID)"
    fi
    
    sleep 10
done
