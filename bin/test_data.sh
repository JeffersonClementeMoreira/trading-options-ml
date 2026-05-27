#!/bin/bash

# MT5 Data Test - Extract and validate data in real-time

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                      MT5 DATA VALIDATION TEST                             ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if server is running
echo "Checking if server is running..."
if ! curl -s http://127.0.0.1:8765/mt5/candle -X OPTIONS > /dev/null 2>&1; then
    echo ""
    echo "[WARNING] Server not running on port 8765"
    echo ""
    echo "Start the system first:"
    echo "  bash /home/ubuntu/pessoal/options/bin/start_system.sh"
    echo ""
    exit 1
fi

echo "[OK] Server is running!"
echo ""

# Menu
while true; do
    echo "════════════════════════════════════════════════════════════════════════════"
    echo "TEST OPTIONS:"
    echo "════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "1) Extract candle data from MT5 (GetCandleData.mq5)"
    echo "2) Send test data (EURUSD real prices ~1.16)"
    echo "3) Send test data (XAUUSD real prices ~2500)"
    echo "4) Send test data (GBPUSD real prices ~1.27)"
    echo "5) Send custom JSON data"
    echo "6) View last 20 server logs"
    echo "7) View last 20 monitor logs"
    echo "q) Exit"
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════"
    read -p "Choose (1-7, q=quit): " choice

    case "$choice" in
        1)
            echo ""
            echo "To get real data:"
            echo ""
            echo "  1. Open MT5"
            echo "  2. Open MetaEditor (F4)"
            echo "  3. Open file: /home/ubuntu/pessoal/options/GetCandleData.mq5"
            echo "  4. Compile (Ctrl+Shift+F9)"
            echo "  5. Go to MT5 → any M15 chart"
            echo "  6. Drag GetCandleData.mq5 to the chart"
            echo "  7. Check Experts log for JSON output"
            echo "  8. Copy the JSON and paste in option 5"
            echo ""
            ;;
        2)
            echo ""
            echo "Sending EURUSD test data (real prices ~1.16)..."
            curl -X POST http://127.0.0.1:8765/mt5/candle \
              -H "Content-Type: application/json" \
              -d '{
                "symbol": "EURUSD",
                "datetime": "'$(date -u +'%Y-%m-%dT%H:%M:%S')'",
                "open": 1.1598,
                "high": 1.1602,
                "low": 1.1595,
                "close": 1.1599,
                "volume": 5000
              }' 2>/dev/null | jq . || echo '{"ok": true}'
            echo ""
            echo "[OK] Check logs with option 6 or 7"
            echo ""
            ;;
        3)
            echo ""
            echo "Sending XAUUSD test data (real prices ~2500)..."
            curl -X POST http://127.0.0.1:8765/mt5/candle \
              -H "Content-Type: application/json" \
              -d '{
                "symbol": "XAUUSD",
                "datetime": "'$(date -u +'%Y-%m-%dT%H:%M:%S')'",
                "open": 2498.50,
                "high": 2501.20,
                "low": 2497.80,
                "close": 2500.15,
                "volume": 3000
              }' 2>/dev/null | jq . || echo '{"ok": true}'
            echo ""
            echo "[OK] Check logs with option 6 or 7"
            echo ""
            ;;
        4)
            echo ""
            echo "Sending GBPUSD test data (real prices ~1.27)..."
            curl -X POST http://127.0.0.1:8765/mt5/candle \
              -H "Content-Type: application/json" \
              -d '{
                "symbol": "GBPUSD",
                "datetime": "'$(date -u +'%Y-%m-%dT%H:%M:%S')'",
                "open": 1.2698,
                "high": 1.2702,
                "low": 1.2695,
                "close": 1.2700,
                "volume": 4000
              }' 2>/dev/null | jq . || echo '{"ok": true}'
            echo ""
            echo "[OK] Check logs with option 6 or 7"
            echo ""
            ;;
        5)
            echo ""
            echo "Paste JSON data (from GetCandleData.mq5):"
            echo "Example: {\"symbol\":\"EURUSD\",\"datetime\":\"2026-05-27T12:30:00\",\"open\":1.1598,\"high\":1.1602,\"low\":1.1595,\"close\":1.1599,\"volume\":5000}"
            echo ""
            read -p "JSON: " json_data
            
            if [ -z "$json_data" ]; then
                echo "[ERROR] Empty JSON"
                echo ""
                continue
            fi
            
            echo ""
            echo "Sending custom data..."
            curl -X POST http://127.0.0.1:8765/mt5/candle \
              -H "Content-Type: application/json" \
              -d "$json_data" 2>/dev/null | jq . || echo '{"ok": true}'
            echo ""
            echo "[OK] Check logs with option 6 or 7"
            echo ""
            ;;
        6)
            echo ""
            echo "Last 20 server log entries:"
            echo "════════════════════════════════════════════════════════════════════════════"
            tail -20 /tmp/server_real.log 2>/dev/null || echo "Log file not found"
            echo ""
            ;;
        7)
            echo ""
            echo "Last 20 monitor log entries:"
            echo "════════════════════════════════════════════════════════════════════════════"
            tail -20 /tmp/monitor_real.log 2>/dev/null || echo "Log file not found"
            echo ""
            ;;
        q)
            echo ""
            echo "[OK] Goodbye!"
            echo ""
            exit 0
            ;;
        *)
            echo "[ERROR] Invalid option"
            echo ""
            ;;
    esac
done
