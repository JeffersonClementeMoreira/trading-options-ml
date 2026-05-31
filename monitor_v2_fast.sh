#!/bin/bash

# Monitor v2 FAST - Aguarda EURUSD, depois lança 5 ativos paralelos
# Versão otimizada: sem SVM, 5 modelos apenas

echo "📊 MONITORAMENTO PIPELINE v2 FAST - EURUSD"
echo "======================================"

MAX_WAIT=600
INTERVAL=5

start_time=$(date +%s)
elapsed=0

# Aguarda EURUSD com timeout de 10 minutos
while [ $elapsed -lt $MAX_WAIT ]; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    # Pega CPU/MEM do processo
    CPU=$(ps aux | grep "run_full_pipeline_v2_fast.py EURUSD" | grep -v grep | awk '{print $3}' | head -1)
    MEM=$(ps aux | grep "run_full_pipeline_v2_fast.py EURUSD" | grep -v grep | awk '{print int($6/1024)}' | head -1)
    
    # Se não encontrou processo, pode ter terminado
    if [ -z "$CPU" ]; then
        CPU="0"
        MEM="0"
    fi
    
    echo "⏳ Processando... [$elapsed/$MAX_WAIT s] CPU: ${CPU}% | Mem: ${MEM}MB"
    
    # Verifica se arquivo foi criado
    if [ -f "results/backtest_EURUSD_DIRECTION_CLASSIFICATION.csv" ]; then
        echo ""
        echo "✅ EURUSD CONCLUÍDO!"
        wc -l results/backtest_EURUSD_DIRECTION_CLASSIFICATION.csv
        break
    fi
    
    sleep $INTERVAL
done

# Verifica timeout
if [ $elapsed -ge $MAX_WAIT ]; then
    echo "❌ Timeout! Processo demorou mais de 10 minutos"
    exit 1
fi

# EURUSD completou, lança 5 ativos em paralelo
echo ""
echo "🚀 Lançando 5 ativos em paralelo..."
echo ""

ATIVOS=("GBPUSD" "EURAUD" "EURJPY" "NZDUSD" "GOLD")

for ATIVO in "${ATIVOS[@]}"; do
    echo "  → Iniciando $ATIVO..."
    nohup python3 src/run_full_pipeline_v2_fast.py $ATIVO > logs/v2_fast_${ATIVO}.log 2>&1 &
    sleep 2
done

echo ""
echo "✅ Todos os 5 ativos foram lançados em background!"
echo "📊 Monitorar com: tail -f logs/v2_fast_*.log"
echo ""
