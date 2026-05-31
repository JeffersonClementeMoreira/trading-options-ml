#!/bin/bash
# Auto-consolidate and Report Generator
# =====================================
# Aguarda conclusão e gera relatório automaticamente

RESULTS_DIR="/home/ubuntu/pessoal/options/results"
EXPECTED_ASSETS=6
PYTHON_SCRIPT="/home/ubuntu/pessoal/options/src/final_report.py"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                                    ║"
echo "║                  🚀 AUTO-CONSOLIDATION MONITOR - Aguardando todos os ativos                       ║"
echo "║                                                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════════════════════════════╝"
echo ""

START_TIME=$(date +%s)

while true; do
    PROCESSED=$(ls -1 "$RESULTS_DIR"/backtest_*chronological.csv 2>/dev/null | wc -l)
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [ $PROCESSED -eq $EXPECTED_ASSETS ]; then
        echo ""
        echo "✅ TODOS OS 6 ATIVOS PROCESSADOS!"
        echo ""
        echo "Tempo total: ${ELAPSED} segundos (~$((ELAPSED/60)) minutos)"
        echo ""
        
        # Gerar relatório
        echo "📊 Gerando relatório final..."
        python3 "$PYTHON_SCRIPT"
        
        echo ""
        echo "════════════════════════════════════════════════════════════════════════════════════════════════════"
        echo "✅ CONSOLIDAÇÃO CONCLUÍDA"
        echo "════════════════════════════════════════════════════════════════════════════════════════════════════"
        echo ""
        echo "Arquivos disponíveis em: $RESULTS_DIR/"
        ls -lh "$RESULTS_DIR"/backtest_*chronological.csv
        
        break
    else
        echo "[$(date +%H:%M:%S)] Processados: $PROCESSED/$EXPECTED_ASSETS (${ELAPSED}s)"
        sleep 30
    fi
done
