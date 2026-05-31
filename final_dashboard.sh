#!/bin/bash
# Final Dashboard - Real-time monitoring until completion
# =========================================================

RESULTS_DIR="/home/ubuntu/pessoal/options/results"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                                    ║"
echo "║              🚀 FINAL DASHBOARD - BACKTEST MULTI-ASSET (Aguardando conclusão)                     ║"
echo "║                                                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════════════════════════════╝"
echo ""

while true; do
    COMPLETED=$(ls -1 "$RESULTS_DIR"/backtest_*chronological.csv 2>/dev/null | wc -l)
    
    echo "[$(date +%H:%M:%S)] Status: $COMPLETED/6 ativos processados"
    
    ls -1 "$RESULTS_DIR"/backtest_*chronological.csv 2>/dev/null | sed 's|.*/||;s|_chronological.csv||' | while read asset; do
        SIZE=$(du -h "$RESULTS_DIR/backtest_${asset}_chronological.csv" | cut -f1)
        LINES=$(wc -l < "$RESULTS_DIR/backtest_${asset}_chronological.csv" 2>/dev/null)
        printf "  ✅ %-10s %5s  %s linhas\n" "$asset" "$SIZE" "$LINES"
    done
    
    # Verificar se há processo ativo
    ACTIVE=$(ps aux | grep "backtest_chronological.py" | grep -v grep | wc -l)
    if [ $ACTIVE -gt 0 ]; then
        echo ""
        echo "🔄 Processos ativos:"
        ps aux | grep "backtest_chronological.py" | grep -v grep | awk '{
            asset=$NF
            cpu=$3
            mem=int($6/1024)
            printf "  └─ %-10s  CPU: %5.1f%%  MEM: %4d MB\n", asset, cpu, mem
        }'
        echo ""
        sleep 15
    else
        echo ""
        if [ $COMPLETED -eq 6 ]; then
            echo "✅ TODOS OS 6 ATIVOS FORAM PROCESSADOS COM SUCESSO!"
        else
            echo "⏳ Nenhum processo ativo, mas apenas $COMPLETED/6 ativos processados"
        fi
        break
    fi
done

echo ""
