#!/bin/bash

# SCRIPT FINAL - Treina v2 para todos os 6 ativos com otimizações

set -e

cd /home/ubuntu/pessoal/options

echo "🚀 PIPELINE DE CLASSIFICAÇÃO FINAL (v2) - 6 ATIVOS"
echo "=================================================="
echo ""
echo "⏳ Aguardando EURUSD terminar..."
echo ""

ATIVOS=("EURUSD" "GBPUSD" "EURAUD" "EURJPY" "NZDUSD" "GOLD")
TOTAL=${#ATIVOS[@]}

# Treinar o primeiro (EURUSD) se não estiver pronto
if [ ! -f results/backtest_EURUSD_DIRECTION_CLASSIFICATION.csv ]; then
    echo "📊 Treinando EURUSD..."
    timeout 600 python3 src/run_full_pipeline_v2_classification.py EURUSD || true
fi

# Treinar os 5 restantes
for ATIVO in "${ATIVOS[@]:1}"; do
    echo ""
    echo "📊 Treinando $ATIVO..."
    timeout 600 python3 src/run_full_pipeline_v2_classification.py "$ATIVO"
done

echo ""
echo "✅ TODOS OS TREINOS COMPLETADOS!"
echo ""
echo "📊 Comparando REGRESSÃO v1 vs CLASSIFICAÇÃO v2..."
echo ""

python3 compare_models_regression_vs_classification.py --all

echo ""
echo "=================================================="
echo "✅ ANÁLISE CONCLUÍDA!"
echo ""
echo "📁 Resultados salvos em:"
echo "   • results/backtest_*_DIRECTION_CLASSIFICATION.csv (6 arquivos)"
echo "   • results/comparison_regression_vs_classification.json"
echo "   • optimization_logs/turbo_*.csv (configs testadas)"
echo ""
echo "📈 RESUMO:"
cat results/comparison_regression_vs_classification.json | python3 -m json.tool | head -50
echo ""
