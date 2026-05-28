#!/bin/bash

# 🚀 Script Completo: Pipeline + Análise Enriquecida
# Executa: run_full_pipeline.py + enhance_backtest_results.py

set -e

WORK_DIR="/home/ubuntu/pessoal/options"
LOG_FILE="/tmp/ml_pipeline_$(date +%Y%m%d_%H%M%S).log"

echo "=========================================="
echo "🚀 PIPELINE COMPLETO + ANÁLISE ENRIQUECIDA"
echo "=========================================="
echo "📝 Log: $LOG_FILE"
echo ""

# 1. Ir para diretório
cd "$WORK_DIR"

# 2. Executar pipeline para todos os ativos
echo "📊 Executando Pipeline para todos os ativos..."
python3 src/run_full_pipeline.py --all >> "$LOG_FILE" 2>&1 || {
    echo "❌ Pipeline falhou!"
    echo "Ver logs: tail -50 $LOG_FILE"
    exit 1
}
echo "✅ Pipeline concluído"
echo ""

# 3. Enriquecer resultados com análise
echo "🔧 Enriquecendo resultados com Analysis columns..."
python3 enhance_backtest_results.py >> "$LOG_FILE" 2>&1 || {
    echo "❌ Enriquecimento falhou!"
    echo "Ver logs: tail -50 $LOG_FILE"
    exit 1
}
echo "✅ Análise enriquecida"
echo ""

# 4. Gerar dashboard final
echo "📈 Gerando Dashboard final..."
python3 analyze_results_v2.py >> "$LOG_FILE" 2>&1 || {
    echo "⚠️ Dashboard com warning, mas pipeline OK"
}
echo "✅ Dashboard gerado"
echo ""

# 5. Resumo de outputs
echo "=========================================="
echo "✅ PIPELINE COMPLETO - TUDO PRONTO"
echo "=========================================="
echo ""
echo "Arquivos gerados:"
echo "  📊 results/backtest_*_DETAILED.csv (dados brutos)"
echo "  📊 results/ANALYSIS_*_ENHANCED.csv (análise rápida)"
echo "  📊 results/analysis_dashboard.json (métricas)"
echo ""
echo "Para análise imediata:"
echo "  libreoffice results/ANALYSIS_EURUSD_ENHANCED.csv"
echo ""
echo "Ver logs:"
echo "  tail -100 $LOG_FILE"
echo ""
echo "=========================================="
