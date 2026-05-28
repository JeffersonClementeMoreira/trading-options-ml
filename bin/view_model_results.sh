#!/bin/bash
#
# Ver Resultados dos Modelos Treinados
# Mostra análise e testes automaticamente
#

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║         📊 ANÁLISE DOS MODELOS XGBOOST TREINADOS                      ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Verificar se os modelos existem
if ! ls /home/ubuntu/pessoal/options/src/xgboost_*.pkl >/dev/null 2>&1; then
    echo "❌ Nenhum modelo encontrado!"
    echo ""
    echo "Você precisa treinar os modelos primeiro:"
    echo "  bash /home/ubuntu/pessoal/options/bin/train_quick_start.sh"
    echo ""
    exit 1
fi

echo "✅ Modelos encontrados!"
echo ""

# 1. Análise detalhada
echo "═════════════════════════════════════════════════════════════════════════"
echo "1️⃣  ANÁLISE DETALHADA DOS MODELOS"
echo "═════════════════════════════════════════════════════════════════════════"
echo ""

cd /home/ubuntu/pessoal/options/src
python3 analyze_models.py

# 2. Testes
echo ""
echo "═════════════════════════════════════════════════════════════════════════"
echo "2️⃣  TESTE DOS MODELOS COM CENÁRIOS SIMULADOS"
echo "═════════════════════════════════════════════════════════════════════════"
echo ""

python3 test_models.py

# 3. Próximos passos
echo ""
echo "═════════════════════════════════════════════════════════════════════════"
echo "3️⃣  PRÓXIMOS PASSOS"
echo "═════════════════════════════════════════════════════════════════════════"
echo ""

echo "✅ Modelos analisados e testados com sucesso!"
echo ""

echo "Para usar os modelos em produção:"
echo ""
echo "Passo 1: Reiniciar sistema"
echo "─────────────────────────"
echo "bash /home/ubuntu/pessoal/options/bin/start_system.sh"
echo ""

echo "Passo 2: Reanexar EA no MT5"
echo "──────────────────────────"
echo "1. Abra MT5"
echo "2. Vá para qualquer gráfico M15 (ex: EURUSD)"
echo "3. Tools → Expert Advisors → SendCandlesToServer"
echo ""

echo "Passo 3: Monitorar Telegram"
echo "──────────────────────────"
echo "Receberá 1 alerta a cada 15 minutos com:"
echo "  • Símbolo"
echo "  • Hora"
echo "  • Direção (ALTA/QUEDA)"
echo "  • Score XGBoost (0-100%)"
echo ""

echo "Dica: Ver logs em tempo real"
echo "────────────────────────────"
echo "tail -f /tmp/server_real.log     # HTTP POST do MT5"
echo "tail -f /tmp/monitor_real.log    # Alertas e Telegram"
echo ""

echo "═════════════════════════════════════════════════════════════════════════"
echo ""
