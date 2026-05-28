#!/bin/bash
#
# Treinar + Analisar (Automatizado)
# Treina os modelos e mostra resultados automaticamente
#

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║     🚀 TREINAR MODELOS E VISUALIZAR RESULTADOS AUTOMATICAMENTE       ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# 1. Treinar
echo "═════════════════════════════════════════════════════════════════════════"
echo "1️⃣  INICIANDO TREINAMENTO"
echo "═════════════════════════════════════════════════════════════════════════"
echo ""

bash /home/ubuntu/pessoal/options/bin/train_from_mt5.sh

TRAIN_EXIT=$?

if [ $TRAIN_EXIT -ne 0 ]; then
    echo ""
    echo "❌ Treinamento falhou!"
    exit 1
fi

echo ""
echo "✅ Treinamento concluído!"
echo ""

# 2. Analisar
echo "═════════════════════════════════════════════════════════════════════════"
echo "2️⃣  VISUALIZANDO RESULTADOS"
echo "═════════════════════════════════════════════════════════════════════════"
echo ""

sleep 2

bash /home/ubuntu/pessoal/options/bin/view_model_results.sh

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  ✨ Processo completo! Modelos treinados e analisados.              ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
