#!/bin/bash
# Real-time Status Monitor for Multi-Asset Backtest
# ==================================================

ASSETS=("EURUSD" "GBPUSD" "EURAUD" "EURJPY" "GOLD" "NZDUSD")
RESULTS_DIR="/home/ubuntu/pessoal/options/results"

while true; do
    clear
    echo ""
    echo "╔════════════════════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                                                    ║"
    echo "║                 📊 MULTI-ASSET BACKTEST - STATUS EM TEMPO REAL                                   ║"
    echo "║                                                                                                    ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    PROCESSED=0
    PENDING=0
    
    echo "📋 Status dos Ativos:"
    echo ""
    
    for asset in "${ASSETS[@]}"; do
        file="$RESULTS_DIR/backtest_${asset}_chronological.csv"
        
        if [ -f "$file" ]; then
            SIZE=$(du -h "$file" | cut -f1)
            LINES=$(wc -l < "$file" 2>/dev/null || echo "?")
            echo "   ✅ $asset - $(printf '%-6s' "$SIZE") - $LINES linhas"
            ((PROCESSED++))
        else
            # Verificar se está processando
            if ps aux | grep -q "backtest_chronological.py $asset"; then
                echo "   ⏳ $asset - 🔄 PROCESSANDO..."
            else
                echo "   ❌ $asset - Não processado"
            fi
            ((PENDING++))
        fi
    done
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║  Processados: ${PROCESSED}/6 | Aguardando: ${PENDING}/6                                                          ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Verificar processo
    ACTIVE=$(ps aux | grep "backtest_chronological.py" | grep -v grep | wc -l)
    if [ $ACTIVE -gt 0 ]; then
        echo "🔄 Processos ativos: $ACTIVE"
        ps aux | grep "backtest_chronological.py" | grep -v grep | awk '{printf "   └─ PID %d - CPU: %s%% - MEM: %s MB\n", $2, $3, int($6/1024)}'
        echo ""
        echo "⏸️  Próxima atualização em 10 segundos (Ctrl+C para sair)..."
        sleep 10
    else
        echo "✅ Nenhum processo ativo"
        echo ""
        break
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════════════════════════════════════════════"
echo "✅ BACKTEST MULTI-ASSET FINALIZADO"
echo "════════════════════════════════════════════════════════════════════════════════════════════════════"
echo ""
