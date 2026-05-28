#!/bin/bash

# Checklist para validação de 15 minutos

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              📋 CHECKLIST DE VALIDAÇÃO - 15 MINUTOS                       ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝


⏱️  ACOMPANHAMENTO DURANTE OS 15 MINUTOS
════════════════════════════════════════════════════════════════════════════

Terminal 1: Monitorar servidor
─────────────────────────────────────────────────────────────────────────────
$ tail -f /tmp/server_real.log

O que procurar:
  ✅ Deve aparecer IMEDIATAMENTE (quando anexar o EA):
     [OK] EURUSD @ 1.1598
     [OK] GBPUSD @ 1.2700
     [OK] XAUUSD @ 4504.06
     
  ✅ Se aparecer entre agora e 15 minutos:
     [OK] EURUSD @ novo_preço (novo candle fechou!)


Terminal 2: Monitorar monitor
─────────────────────────────────────────────────────────────────────────────
$ tail -f /tmp/monitor_real.log

O que procurar:
  ✅ Deve aparecer IMEDIATAMENTE:
     [NEW_CANDLE] EURUSD
     [Processing] Calculando indicadores...
     RSI_14: ...
     SMA_20: ...
     [SCORE] EURUSD: 0.73
     [Telegram] Enviado alerta
     
  ✅ Se aparecer entre agora e 15 minutos:
     Mesmo padrão com novo candle


Terminal 3: Verificar MT5
─────────────────────────────────────────────────────────────────────────────
No MT5:
  - Abra Experts (Ctrl+Shift+3)
  - Procure por linhas do SendCandlesToServer
  
O que procurar:
  ✅ DEVE APARECER:
     [OK] EURUSD → EURUSD 2026-05-27T02:00:00 1.1598
     [OK] GBPUSD → GBPUSD 2026-05-27T02:00:00 1.2700
     [OK] GOLD → XAUUSD 2026-05-27T02:00:00 4504.06
     
  ❌ NÃO DEVE APARECER:
     [ERROR] ... code=500
     [ERROR] ... code=400


Telegram
─────────────────────────────────────────────────────────────────────────────
  ✅ Deve receber mensagem com:
     Symbol
     Preço (Close)
     Score (%)
     Indicadores


════════════════════════════════════════════════════════════════════════════

📊 CRONOGRAMA

Agora (T=0):
  └─ Anexar EA ao gráfico M15
  └─ Verificar se logs mostram dados IMEDIATAMENTE

Próximos 15 minutos (T=0-15):
  └─ Monitorar logs
  └─ Verificar se há erros
  └─ Checar Telegram

Aos 15 minutos (T=15):
  └─ Novo candle M15 fecha
  └─ Sistema deve enviar novo candle automaticamente
  └─ Telegram deve receber novo alerta


════════════════════════════════════════════════════════════════════════════

✅ SE TUDO ESTIVER OK (esperado):

1. Logo que anexar:
   - Logs mostram 3 candles (EUR, GBP, GOLD)
   - Telegram recebe 3 mensagens iniciais

2. Aos 15 minutos:
   - 3 novos candles aparecem nos logs
   - 3 novos alertas no Telegram
   - Sem erros em nenhum lugar


❌ SE HOUVER PROBLEMA:

1. Nada aparece nos logs?
   - EA não foi anexado
   - EA foi anexado mas não está rodando
   - Verificar: Gráfico está ativo? EA está visível?

2. Logs mostram [ERROR]?
   - SendCandlesToServer não foi recompilado
   - Recompilar e reanexar

3. Telegram não recebe?
   - Verificar se token Telegram está correto
   - Monitor não conectou ao servidor
   - Checar logs do monitor


════════════════════════════════════════════════════════════════════════════

O QUE RELATAR QUANDO VOLTAR

Importante: Tirar screenshots ou copiar os logs completos de:
  1. Experts (MT5) - últimas 20 linhas
  2. /tmp/server_real.log - últimas 30 linhas
  3. /tmp/monitor_real.log - últimas 30 linhas


════════════════════════════════════════════════════════════════════════════

EOF
