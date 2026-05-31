#!/bin/bash

# Monitoramento em tempo real do pipeline v2

cd /home/ubuntu/pessoal/options

echo "📊 MONITORAMENTO PIPELINE v2 - EURUSD"
echo "======================================"
echo ""

MAX_WAIT=600  # 10 minutos
ELAPSED=0
CHECK_INTERVAL=5

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if [ -f results/backtest_EURUSD_DIRECTION_CLASSIFICATION.csv ]; then
        echo ""
        echo "✅ EURUSD COMPLETOU! ✅"
        echo ""
        echo "📁 Arquivo gerado:"
        ls -lh results/backtest_EURUSD_DIRECTION_CLASSIFICATION.csv
        echo ""
        echo "📊 Estatísticas:"
        wc -l results/backtest_EURUSD_DIRECTION_CLASSIFICATION.csv
        head -3 results/backtest_EURUSD_DIRECTION_CLASSIFICATION.csv | tail -2
        echo ""
        echo "✅ Iniciando os 5 restantes..."
        echo ""
        
        # Lançar os 5 em paralelo
        for ATIVO in GBPUSD EURAUD EURJPY NZDUSD GOLD; do
            echo "📊 Lançando $ATIVO..."
            nohup python3 src/run_full_pipeline_v2_classification.py "$ATIVO" > "logs/v2_${ATIVO}.log" 2>&1 &
            sleep 1
        done
        
        echo ""
        echo "✅ Todos os 5 em paralelo!"
        echo "⏳ Aguardando conclusão..."
        
        exit 0
    fi
    
    # Status
    PS_OUTPUT=$(ps aux | grep "run_full_pipeline_v2_classification" | grep -v grep)
    if [ ! -z "$PS_OUTPUT" ]; then
        CPU=$(echo "$PS_OUTPUT" | awk '{print $3}')
        MEM=$(echo "$PS_OUTPUT" | awk '{print $6}')
        echo "⏳ Processando... [$ELAPSED/$MAX_WAIT s] CPU: $CPU% | Mem: $((MEM/1024))MB"
    else
        echo "❌ Processo não encontrado!"
        break
    fi
    
    ELAPSED=$((ELAPSED + CHECK_INTERVAL))
    sleep $CHECK_INTERVAL
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "❌ Timeout! Processo demorou mais de 10 minutos"
    ps aux | grep "run_full_pipeline_v2_classification" | grep -v grep
fi
