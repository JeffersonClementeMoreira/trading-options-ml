#!/bin/bash
#
# QUICK START: Treinar modelos em 3 passos
#

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  TREINAR MODELOS XGBOOST - QUICK START                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "⚠️  ANTES DE COMEÇAR, CERTIFIQUE-SE DE:"
echo "   ✓ MT5 aberto"
echo "   ✓ Gráficos M15 carregados para: EURUSD, GBPUSD, GOLD"
echo ""
read -p "Pressione ENTER para continuar..."

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PASSO 1: Iniciando servidor de treinamento..."
echo "═══════════════════════════════════════════════════════════════"
echo ""

bash /home/ubuntu/pessoal/options/bin/train_from_mt5.sh &
TRAIN_PID=$!

sleep 2

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PASSO 2: Executar script no MT5"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  AGORA VOCÊ PRECISA FAZER ISSO NO MT5:"
echo ""
echo "   1. Abra o MT5 (se não estiver aberto)"
echo "   2. Vá para: Tools → Scripts"
echo "   3. Procure por: ExportHistoricalDataForTraining"
echo "   4. Duplo-clique para executar"
echo ""
echo "   OU:"
echo ""
echo "   1. Clique na aba 'Scripts' à esquerda"
echo "   2. Duplo-clique em 'ExportHistoricalDataForTraining'"
echo ""

read -p "Pressione ENTER depois de executar o script no MT5..."

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "PASSO 3: Aguardando conclusão do treinamento..."
echo "═══════════════════════════════════════════════════════════════"
echo ""

wait $TRAIN_PID
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ SUCESSO! Modelos criados:"
    echo ""
    ls -lh /home/ubuntu/pessoal/options/src/xgboost_*.pkl
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "PRÓXIMOS PASSOS:"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "1. Reiniciar o sistema:"
    echo "   bash /home/ubuntu/pessoal/options/bin/start_system.sh"
    echo ""
    echo "2. Reanexar EA no MT5:"
    echo "   Tools → Expert Advisors → SendCandlesToServer"
    echo ""
    echo "3. Monitorar:"
    echo "   tail -f /tmp/monitor_real.log"
    echo ""
else
    echo ""
    echo "❌ Erro no treinamento"
    echo ""
    echo "Possíveis causas:"
    echo "  • Script não foi executado no MT5"
    echo "  • Gráficos M15 não estão carregados"
    echo "  • Erro de conexão entre MT5 e Python"
    echo ""
    echo "Verifique os logs no MT5: View → Logs → Experts"
    echo ""
    exit 1
fi
