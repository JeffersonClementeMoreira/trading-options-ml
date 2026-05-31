#!/bin/bash
# Multi-Asset Backtest Executor (Paralelo com controle)
# ======================================================

cd /home/ubuntu/pessoal/options

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                                    ║"
echo "║                      🚀 MULTI-ASSET BACKTEST - MODO EXECUTOR                                      ║"
echo "║                                                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Configurações
ASSETS=("EURUSD" "GBPUSD" "EURAUD" "EURJPY" "GOLD" "NZDUSD")
PARALLEL_JOBS=${1:-2}  # Default: 2 jobs paralelos (pode passar como argumento)
TOTAL=${#ASSETS[@]}

echo "⚙️  Configuração:"
echo "   Total de ativos: ${TOTAL}"
echo "   Jobs paralelos: ${PARALLEL_JOBS}"
echo "   Modo: Sequencial com fila (${PARALLEL_JOBS} por vez)"
echo ""

# Função para processar um ativo
process_asset() {
    local asset=$1
    local idx=$2
    local total=$3
    
    echo "[${idx}/${total}] 🚀 Iniciando ${asset}..."
    python3 src/backtest_chronological.py "$asset" 2>&1 | sed "s/^/[${asset}] /" | tail -30
}

export -f process_asset

# Executar com GNU Parallel ou com xargs
if command -v parallel &> /dev/null; then
    echo "📌 Usando GNU Parallel para processamento..."
    echo ""
    
    START_TIME=$(date +%s)
    
    # Usar parallel com delay
    printf '%s\n' "${ASSETS[@]}" | \
        parallel --joblog /tmp/backtest_parallel.log -j $PARALLEL_JOBS \
        'cd /home/ubuntu/pessoal/options && python3 src/backtest_chronological.py {} 2>&1'
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo ""
    echo "📊 Resumo de Processamento (GNU Parallel):"
    tail -20 /tmp/backtest_parallel.log
    
else
    echo "📌 GNU Parallel não disponível. Usando xargs..."
    echo ""
    
    START_TIME=$(date +%s)
    
    printf '%s\n' "${ASSETS[@]}" | \
        xargs -I {} -P $PARALLEL_JOBS bash -c \
        'cd /home/ubuntu/pessoal/options && python3 src/backtest_chronological.py {}'
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
fi

# Verificar arquivos gerados
echo ""
echo "════════════════════════════════════════════════════════════════════════════════════════════════════"
echo "📊 ARQUIVOS GERADOS"
echo "════════════════════════════════════════════════════════════════════════════════════════════════════"
echo ""

ls -lh results/backtest_*_chronological.csv 2>/dev/null || echo "❌ Nenhum arquivo encontrado"

echo ""
echo "════════════════════════════════════════════════════════════════════════════════════════════════════"
echo "✅ BACKTEST MULTI-ASSET CONCLUÍDO"
echo "════════════════════════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Tempo total: ${DURATION} segundos (~$((DURATION / 60)) minutos, ~$((DURATION / 60 / 60)) horas)"
echo ""
echo "💡 Próximos passos:"
echo "   1. Consolidar resultados: python3 src/consolidate_results.py"
echo "   2. Gerar relatório final: python3 src/generate_performance_report.py"
echo ""
