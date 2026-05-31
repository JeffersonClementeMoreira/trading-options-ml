#!/bin/bash
# Multi-Asset Backtest Loop
# ==========================
# Roda backtest_chronological.py para TODOS os 6 ativos

cd /home/ubuntu/pessoal/options

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                                    ║"
echo "║                     🚀 MULTI-ASSET BACKTEST EXPANSION - INICIANDO                                 ║"
echo "║                                                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════════════════════════════╝"
echo ""

ASSETS=("EURUSD" "GBPUSD" "EURAUD" "EURJPY" "GOLD" "NZDUSD")
TOTAL=${#ASSETS[@]}
CURRENT=1

START_TIME=$(date +%s)

for asset in "${ASSETS[@]}"; do
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════════════════════════"
    echo "[${CURRENT}/${TOTAL}] 📊 Backtest para ${asset}"
    echo "════════════════════════════════════════════════════════════════════════════════════════════════════"
    
    ASSET_START=$(date +%s)
    
    # Rodar backtest
    python3 src/backtest_chronological.py "$asset"
    
    ASSET_END=$(date +%s)
    ASSET_DURATION=$((ASSET_END - ASSET_START))
    
    echo ""
    echo "✅ [${asset}] Concluído em ${ASSET_DURATION} segundos"
    echo ""
    
    CURRENT=$((CURRENT + 1))
    
    # Pequeno delay entre execuções
    if [ $CURRENT -le $TOTAL ]; then
        sleep 5
    fi
done

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                                    ║"
echo "║                          ✅ BACKTEST MULTI-ASSET CONCLUÍDO!                                       ║"
echo "║                                                                                                    ║"
echo "║  Tempo total: ${TOTAL_DURATION} segundos (~$((TOTAL_DURATION / 60)) minutos)                                   ║"
echo "║                                                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 Arquivos gerados em: results/"
ls -lh results/backtest_*_chronological.csv 2>/dev/null || echo "  (nenhum arquivo encontrado)"
echo ""
