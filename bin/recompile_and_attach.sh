#!/bin/bash
#
# Script para recompilar SendCandlesToServer.mq5 e reanexar ao MT5
#

set -e

echo "================================================================"
echo "  RECOMPILAR E REANEXAR SendCandlesToServer.mq5"
echo "================================================================"
echo ""

# Caminho dos arquivos
MQL5_SOURCE="$HOME/.wine/drive_c/Program Files/MetaTrader 5/MQL5/Experts/SendCandlesToServer.mq5"
MQL5_COMPILED="$HOME/.wine/drive_c/Program Files/MetaTrader 5/MQL5/Experts/SendCandlesToServer.ex5"
METAEDITOR="$HOME/.wine/drive_c/Program Files/MetaTrader 5/MetaEditor64.exe"

echo "1️⃣  Compilando MQL5..."
DISPLAY=:1 wine "$METAEDITOR" "$MQL5_SOURCE" /compile 2>&1 | grep -E "errors|warnings" || true
sleep 2

if [[ -f "$MQL5_COMPILED" ]]; then
    echo "✅ Compilação bem-sucedida!"
    echo "   Arquivo: $(ls -lh "$MQL5_COMPILED" | awk '{print $9, $5}')"
    echo ""
else
    echo "❌ Erro: Arquivo compilado não encontrado!"
    exit 1
fi

echo "2️⃣  PRÓXIMOS PASSOS:"
echo "   ⚠️  O EA precisa ser REANEXADO manualmente no MT5"
echo ""
echo "   Instruções:"
echo "   1. Abra o MT5"
echo "   2. Vá para qualquer gráfico (ex: EURUSD M15)"
echo "   3. Menu → File → Open → Experts"
echo "   4. Selecione: SendCandlesToServer"
echo "   5. Clique OK (aceite os parâmetros padrão)"
echo ""
echo "   OU:"
echo "   - Clique na aba 'Experts' na esquerda"
echo "   - Arraste SendCandlesToServer para um gráfico M15 (ex: EURUSD)"
echo ""
echo "3️⃣  VALIDAÇÃO:"
echo "   - Veja o Experts log para confirmar que está enviando dados"
echo "   - Use: tail -f /tmp/server_real.log"
echo "   - Use: tail -f /tmp/monitor_real.log"
echo ""
echo "================================================================"
