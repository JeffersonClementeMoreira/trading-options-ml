#!/bin/bash

###############################################################################
# START MT5 - COM GUI VISÍVEL
# 
# Inicia MT5 em display :10 (RDP/XFCE)
# Visível via Desktop/RDP
###############################################################################

echo ""
echo "🎮 Iniciando MT5 Terminal..."
echo ""

# Parar anterior se existir
pkill -9 -f "terminal64" 2>/dev/null || true
pkill -9 -f "xvfb-run" 2>/dev/null || true
sleep 1

# Iniciar em display visível
DISPLAY=:10 wine ~/.wine/drive_c/Program\ Files/MetaTrader\ 5/terminal64.exe &

sleep 3

echo "✅ MT5 iniciado (PID $!)"
echo ""
echo "📊 Para ver na GUI:"
echo "   1. Conecte via RDP em :10"
echo "   2. Ou acesse via VNC (se configurado)"
echo ""

# Manter em background mas monitorável
tail -f /dev/null
