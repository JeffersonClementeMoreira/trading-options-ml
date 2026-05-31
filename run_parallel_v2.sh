#!/bin/bash

# SCRIPT PARALELO - Roda todos os 6 ativos ao mesmo tempo

set -e

cd /home/ubuntu/pessoal/options

echo "🚀 PIPELINE PARALELO - Classificação v2 (6 ATIVOS)"
echo "=================================================="
echo ""

ATIVOS=("EURUSD" "GBPUSD" "EURAUD" "EURJPY" "NZDUSD" "GOLD")

# Verificar qual já está pronto
for ATIVO in "${ATIVOS[@]}"; do
    if [ -f "results/backtest_${ATIVO}_DIRECTION_CLASSIFICATION.csv" ]; then
        echo "✅ $ATIVO já está pronto (pulando)"
    else
        echo "⏳ $ATIVO será treinado"
    fi
done

echo ""
echo "🚀 Iniciando treinos em paralelo..."
echo ""

# Treinar cada ativo em background
for ATIVO in "${ATIVOS[@]}"; do
    if [ ! -f "results/backtest_${ATIVO}_DIRECTION_CLASSIFICATION.csv" ]; then
        echo "📊 Iniciando $ATIVO... (PID: $$)"
        (
            timeout 600 python3 src/run_full_pipeline_v2_classification.py "$ATIVO" 2>&1 | sed "s/^/[$ATIVO] /"
        ) &
        sleep 10  # Pequeno delay para não sobrecarregar
    fi
done

# Aguardar todos
echo ""
echo "⏳ Aguardando conclusão de todos os treinos..."
wait

echo ""
echo "✅ TODOS OS TREINOS COMPLETADOS!"
echo ""

# Contar resultados
COUNT=$(ls results/backtest_*_DIRECTION_CLASSIFICATION.csv 2>/dev/null | wc -l)
echo "📊 Resultados gerados: $COUNT/6 arquivos"

# Se todos estão prontos, fazer a comparação
if [ $COUNT -eq 6 ]; then
    echo ""
    echo "📈 Comparando REGRESSÃO v1 vs CLASSIFICAÇÃO v2..."
    python3 compare_models_regression_vs_classification.py --all 2>&1 | tail -50
fi

echo ""
echo "✅ PIPELINE PARALELO CONCLUÍDO!"
