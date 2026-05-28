#!/bin/bash
#
# Treinar modelos XGBoost a partir de dados do MT5
# 

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  TREINAR MODELOS XGBOOST A PARTIR DO MT5                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Parar servidor antigo (se estiver rodando)
pkill -f "train_models_from_mt5" || true
sleep 1

# Iniciar servidor de treinamento
echo "1️⃣  Iniciando servidor de treinamento (porta 9999)..."
cd /home/ubuntu/pessoal/options/src
python3 train_models_from_mt5.py &
SERVER_PID=$!
sleep 2

echo ""
echo "2️⃣  PRÓXIMOS PASSOS NO MT5:"
echo "   ├─ Abra o MT5"
echo "   ├─ Menu: Tools → Scripts → ExportHistoricalDataForTraining"
echo "   └─ OU: Clique duplo em ExportHistoricalDataForTraining na aba Scripts"
echo ""
echo "   ⚠️  IMPORTANTE:"
echo "   ├─ Tenha gráficos M15 abertos para EURUSD, GBPUSD, GOLD"
echo "   ├─ O script vai coletar últimos 500 candles de cada"
echo "   └─ Enviará para este servidor treinar os modelos"
echo ""
echo "3️⃣  MONITORAR TREINAMENTO:"
echo "   └─ Este terminal mostrará o progresso abaixo:"
echo ""

# Aguardar treinamento
echo "⏳ Aguardando dados do MT5..."
echo ""

# Aguardar por 3 minutos máximo
for i in {1..180}; do
    if [[ -f "/home/ubuntu/pessoal/options/src/xgboost_EURUSD.pkl" ]] && \
       [[ -f "/home/ubuntu/pessoal/options/src/xgboost_GBPUSD.pkl" ]] && \
       [[ -f "/home/ubuntu/pessoal/options/src/xgboost_XAUUSD.pkl" ]]; then
        echo ""
        echo "✅ TODOS OS MODELOS TREINADOS COM SUCESSO!"
        echo ""
        ls -lh /home/ubuntu/pessoal/options/src/xgboost_*.pkl
        echo ""
        kill $SERVER_PID 2>/dev/null || true
        exit 0
    fi
    
    if (( i % 10 == 0 )); then
        echo "   [$i/180s] Ainda aguardando..."
    fi
    
    sleep 1
done

echo ""
echo "⚠️  TIMEOUT: Não foi possível treinar os modelos em 3 minutos"
echo ""
echo "Possíveis causas:"
echo "  1. Script não foi executado no MT5"
echo "  2. Gráficos M15 não estão abertos"
echo "  3. Erro de conexão entre MT5 e Python"
echo ""
echo "Verifique os logs do MT5 (View → Logs) para erros"
echo ""
kill $SERVER_PID 2>/dev/null || true
exit 1
