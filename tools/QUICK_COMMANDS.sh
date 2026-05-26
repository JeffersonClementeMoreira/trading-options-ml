#!/bin/bash

# QUICK COMMANDS - Sistema em Teste (1-2 semanas)

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║              ⚡ COMANDOS RÁPIDOS - MONITOR WEBSOCKET DEBUG ⚡                 ║
║                                                                                ║
║              (Fase de Teste: 1-2 semanas - Enviando TODOS os candles)         ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

📋 COMANDOS PRINCIPAIS
════════════════════════════════════════════════════════════════════════════════

1️⃣  VER STATUS (Mostrar se tudo está OK)
─────────────────────────────────────────────────────────────────────────────────
  $ cd /home/ubuntu/pessoal/options/src && ./diagnostic.sh

  ✅ Procure por:
     ✓ Servidor Bridge: ✅ ATIVO
     ✓ Monitor Debug: ✅ ATIVO  
     ✓ Porta WebSocket 9001: ✅ ABERTA
     ✓ Servidor respondendo: ✅ OK

════════════════════════════════════════════════════════════════════════════════

2️⃣  VER PROCESSOS EM EXECUÇÃO
─────────────────────────────────────────────────────────────────────────────────
  $ ps aux | grep -E 'mt5_websocket|live_websocket_monitor_debug' | grep -v grep

  ✅ Deve mostrar 2 linhas:
     - python3 mt5_websocket_server_demo.py
     - python3 live_websocket_monitor_debug.py

════════════════════════════════════════════════════════════════════════════════

3️⃣  PARAR SISTEMA
─────────────────────────────────────────────────────────────────────────────────
  $ pkill -9 -f 'mt5_websocket_server_demo|live_websocket_monitor_debug'

════════════════════════════════════════════════════════════════════════════════

4️⃣  REINICIAR SISTEMA
─────────────────────────────────────────────────────────────────────────────────
  $ cd /home/ubuntu/pessoal/options/src
  $ python3 mt5_websocket_server_demo.py &
  $ sleep 2
  $ python3 live_websocket_monitor_debug.py &

════════════════════════════════════════════════════════════════════════════════

5️⃣  LER DOCUMENTAÇÃO COMPLETA
─────────────────────────────────────────────────────────────────────────────────
  $ cat /home/ubuntu/pessoal/options/src/DEBUG_GUIDE.md

════════════════════════════════════════════════════════════════════════════════

📱 VERIFICAR TELEGRAM
════════════════════════════════════════════════════════════════════════════════

Abra seu Telegram e vá para:
  Channel ID: -1001735082183

Procure por:
  ✅ Mensagem inicial: "🚀 MONITOR DEBUG INICIADO"
  ✅ Mensagens regulares: "📡 MONITOR WEBSOCKET EM ANDAMENTO"
  
Cada M15 (15 minutos) uma nova mensagem deve chegar com:
  - Data/Hora do candle
  - Close price
  - Indicadores (RSI, MACD, EMA, etc)
  - XGBoost Score
  - Ação recomendada (HIGH/MEDIUM/LOW)

════════════════════════════════════════════════════════════════════════════════

🔍 VALIDAR QUE ESTÁ FUNCIONANDO
════════════════════════════════════════════════════════════════════════════════

✅ Checklist Rápido:

[ ] Processos rodando?
    $ ps aux | grep -E 'mt5_websocket|live_websocket_monitor_debug' | grep -v grep

[ ] Telegram recebendo mensagens?
    Abra seu Telegram → Canal -1001735082183

[ ] Sistema reconectando ao servidor?
    $ ./diagnostic.sh

[ ] Tudo OK?
    🟢 SISTEMA ESTÁ FUNCIONANDO!

════════════════════════════════════════════════════════════════════════════════

🚀 MODO DE FUNCIONAMENTO (1-2 SEMANAS)
════════════════════════════════════════════════════════════════════════════════

Nessa fase de teste:

  ✅ Servidor está ATIVO
  ✅ Monitor está ENVIANDO TODOS os candles ao Telegram
  ✅ CADA novo candle M15 = UMA mensagem no Telegram
  ✅ Você recebe: DateTime + OHLC + Indicadores + XGBoost Score + Ação

Objetivo: Validar que o sistema está funcionando corretamente

Duração: 1-2 semanas (como você especificou)

Depois: Voltar ao modo normal (enviar apenas sinais HIGH > 70%)

════════════════════════════════════════════════════════════════════════════════

❓ DÚVIDAS FREQUENTES
════════════════════════════════════════════════════════════════════════════════

P: Não está enviando mensagens no Telegram
R: Rode ./diagnostic.sh para verificar se está tudo OK

P: Quer voltar ao modo normal (só sinais > 70%)?
R: 
   $ pkill -9 -f 'live_websocket_monitor_debug'
   $ cd /home/ubuntu/pessoal/options/src
   $ python3 live_websocket_monitor.py &

P: Como saber que está processando candles?
R: Use ./diagnostic.sh - vai mostrar que os processos estão ativos

P: Porta 9001 já está em uso?
R:
   $ lsof -i :9001 | grep -v COMMAND | awk '{print $2}' | xargs kill -9
   $ ./diagnostic.sh (depois)

════════════════════════════════════════════════════════════════════════════════

📚 ARQUIVOS IMPORTANTES
════════════════════════════════════════════════════════════════════════════════

/home/ubuntu/pessoal/options/src/
├─ diagnostic.sh                      (Comando de diagnóstico)
├─ DEBUG_GUIDE.md                     (Documentação completa)
├─ mt5_websocket_server_demo.py       (Servidor Bridge)
├─ live_websocket_monitor_debug.py    (Monitor em DEBUG)
├─ live_websocket_monitor.py          (Monitor normal)
└─ models/
   ├─ xgboost_gbpusd.pkl
   ├─ xgboost_eurusd.pkl
   └─ xgboost_xauusd.pkl

════════════════════════════════════════════════════════════════════════════════

Status: 🟢 ATIVO E TESTANDO
Modo: 🔍 DEBUG (Todos os candles)
Duração: 1-2 semanas
Próximo: Voltar ao modo de produção (apenas sinais > 70%)

════════════════════════════════════════════════════════════════════════════════

EOF

