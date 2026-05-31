#!/bin/bash

# Script para treinar v2 (classificação) e comparar com v1 (regressão)

set -e

echo "🚀 EXECUTANDO PIPELINE DE CLASSIFICAÇÃO v2 (6 ATIVOS)"
echo "======================================================"
echo ""

ATIVOS=("EURUSD" "GBPUSD" "EURAUD" "EURJPY" "NZDUSD" "GOLD")
TOTAL=${#ATIVOS[@]}
CURRENT=0

for ATIVO in "${ATIVOS[@]}"; do
    CURRENT=$((CURRENT + 1))
    echo ""
    echo "📊 [$CURRENT/$TOTAL] Treinando $ATIVO..."
    echo "---"
    
    python3 src/run_full_pipeline_v2_classification.py "$ATIVO" 2>&1 | tail -20
    
    echo ""
done

echo ""
echo "✅ TREINOS COMPLETADOS!"
echo "=================================================="
echo ""
echo "📈 Comparando resultados (Regressão v1 vs Classificação v2)..."
echo ""

python3 compare_models_regression_vs_classification.py --all

echo ""
echo "✅ COMPARAÇÃO CONCLUÍDA!"
echo ""
echo "📁 Arquivos gerados:"
echo "   • results/comparison_regression_vs_classification.json"
echo "   • 6x backtest_*_DIRECTION_CLASSIFICATION.csv"
echo ""
