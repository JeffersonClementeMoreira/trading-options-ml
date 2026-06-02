#!/bin/bash
# watchdog.sh - Mantém servidor mt5_live_real_server sempre rodando

LOG="/tmp/watchdog.log"
SERVER_LOG="/tmp/mt5_server.log"
DIR="/home/ubuntu/pessoal/options"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG"
}

log "🐕 Watchdog iniciado"

while true; do
    if ! pgrep -f "mt5_live_real_server" > /dev/null; then
        log "⚠️  Servidor morto! Reiniciando..."
        cd "$DIR" && python3 production/mt5_live_real_server.py >> "$SERVER_LOG" 2>&1 &
        sleep 5
        if pgrep -f "mt5_live_real_server" > /dev/null; then
            log "✅ Servidor reiniciado com sucesso"
        else
            log "❌ Falha ao reiniciar servidor"
        fi
    fi
    sleep 30
done
