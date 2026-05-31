#!/bin/bash
# COMPLETE MULTI-ASSET FINAL REPORT GENERATOR
# ============================================
# Gera relatório completo assim que todos os 6 ativos estão prontos

RESULTS_DIR="/home/ubuntu/pessoal/options/results"
SRC_DIR="/home/ubuntu/pessoal/options/src"
EXPECTED=6

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                                    ║"
echo "║            🎯 GERADOR DE RELATÓRIO FINAL - AGUARDANDO TODOS OS 6 ATIVOS                           ║"
echo "║                                                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Aguardar todos os arquivos
while [ $(ls -1 "$RESULTS_DIR"/backtest_*chronological.csv 2>/dev/null | wc -l) -lt $EXPECTED ]; do
    CURRENT=$(ls -1 "$RESULTS_DIR"/backtest_*chronological.csv 2>/dev/null | wc -l)
    echo "[$(date +%H:%M:%S)] Aguardando... $CURRENT/$EXPECTED ativos prontos"
    sleep 10
done

echo ""
echo "✅ TODOS OS 6 ATIVOS ESTÃO PRONTOS!"
echo ""

# Gerar relatório final
echo "📊 Gerando RELATÓRIO FINAL COMPLETO..."
echo ""

python3 "$SRC_DIR/final_report.py"

echo ""
echo "════════════════════════════════════════════════════════════════════════════════════════════════════"
echo "✅ RELATÓRIO FINAL GERADO COM SUCESSO"
echo "════════════════════════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📁 Arquivos disponíveis:"
ls -lh "$RESULTS_DIR"/*.csv 2>/dev/null | tail -10
echo ""
