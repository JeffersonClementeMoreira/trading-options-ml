#!/bin/bash

echo "=========================================================================="
echo "              START SYSTEM - REAL MT5 DATA              "
echo "=========================================================================="
echo ""

cd /home/ubuntu/pessoal/options/src

echo "Stopping old processes..."
pkill -9 -f "server_mt5_http" 2>/dev/null
pkill -9 -f "monitor_mt5_real" 2>/dev/null
sleep 2
echo "[OK] Cleaned"
echo ""

echo "Removing old logs..."
rm -f /tmp/server_real.log /tmp/monitor_real.log
echo "[OK] Cleaned"
echo ""

echo "STARTING SYSTEM:"
echo ""

echo "[1] HTTP Server (port 8765)..."
python3 server_mt5_http.py > /tmp/server_real.log 2>&1 &
SERVER_PID=$!
sleep 2
echo "    [OK] PID: $SERVER_PID"
echo ""

echo "[2] WebSocket Monitor..."
python3 monitor_mt5_real.py > /tmp/monitor_real.log 2>&1 &
MONITOR_PID=$!
sleep 2
echo "    [OK] PID: $MONITOR_PID"
echo ""

echo "=========================================================================="
echo "[OK] SYSTEM READY!"
echo "=========================================================================="
echo ""
echo "Running processes:"
echo "   * server_mt5_http.py (PID $SERVER_PID)"
echo "   * monitor_mt5_real.py (PID $MONITOR_PID)"
echo ""
echo "Monitor in real-time:"
echo ""
echo "   SERVER LOG:"
echo "   tail -f /tmp/server_real.log"
echo ""
echo "   MONITOR LOG:"
echo "   tail -f /tmp/monitor_real.log"
echo ""
echo "=========================================================================="
echo "Waiting for first real M15 candle from MT5..."
echo ""
echo "TIP: Run 'tail -f /tmp/server_real.log' in another terminal to monitor"
echo "     real-time data from MT5."
echo ""
echo "=========================================================================="
echo ""

# Monitor processes and restart if they crash
while true; do
    # Check if server is running
    if ! ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "[WARNING] Server died at $(date '+%Y-%m-%d %H:%M:%S'), restarting..."
        python3 server_mt5_http.py > /tmp/server_real.log 2>&1 &
        SERVER_PID=$!
        echo "[OK] Server restarted (PID $SERVER_PID)"
        sleep 2
    fi
    
    # Check if monitor is running
    if ! ps -p $MONITOR_PID > /dev/null 2>&1; then
        echo "[WARNING] Monitor died at $(date '+%Y-%m-%d %H:%M:%S'), restarting..."
        python3 monitor_mt5_real.py > /tmp/monitor_real.log 2>&1 &
        MONITOR_PID=$!
        echo "[OK] Monitor restarted (PID $MONITOR_PID)"
        sleep 2
    fi
    
    sleep 10
done
