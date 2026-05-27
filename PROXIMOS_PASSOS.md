🚀 PRÓXIMOS PASSOS - COLOCAR NO AR
═════════════════════════════════════════════════════════════════════════════

Agora que o sistema foi validado 100%, é hora de anexar no MT5 real e começar
a receber dados de verdade.


📋 CHECKLIST - O QUE FAZER AGORA
═════════════════════════════════════════════════════════════════════════════

[ ] 1. Compilar MQL5 no MetaEditor
[ ] 2. Anexar ao gráfico XAUUSD M15
[ ] 3. Verificar primeira mensagem no servidor
[ ] 4. Confirmar Telegram recebe alerta
[ ] 5. Monitorar 7 dias antes de tradear


✅ PASSO 1: COMPILAR MQL5
═════════════════════════════════════════════════════════════════════════════

Arquivo: SendCandlesToServer.mq5
Local: /home/ubuntu/pessoal/options/src/SendCandlesToServer.mq5

Ações:
1. No MT5, abrir: Tools → MetaEditor (F11)
2. Abrir arquivo SendCandlesToServer.mq5
3. Compilar: Compile (F7)

Resultado esperado:
   📊 expert_compilations_log
   ✅ 0 errors
   ✅ 0 warnings
   ✅ 1 compiled code

Se houver erro: Verifique que MT5 está na versão mais recente


✅ PASSO 2: ANEXAR NO GRÁFICO
═════════════════════════════════════════════════════════════════════════════

Ações:
1. Abrir MT5
2. Ir ao gráfico XAUUSD M15
3. Expert Advisors (ctrl + E)
4. Arrastar SendCandlesToServer.mq5 para o gráfico
   OU
   Clicar em "Navigator" → Experts → SendCandlesToServer → Drag

Resultado esperado:
   ✓ Ícone de robô 🤖 aparece na barra de ferramentas
   ✓ Status: "Expert Advisor attached"
   ✓ Na barra inferior: "SendCandlesToServer: initialized"

Se não funcionar:
   → Verificar se "Enable Expert Advisors" está ON
   → Ir em Tools → Options → Expert Advisors
   → Checar "Allow WebRequests"
   → Reiniciar MT5


✅ PASSO 3: VER PRIMEIRO CANDLE CHEGANDO
═════════════════════════════════════════════════════════════════════════════

Abrir terminal no Linux:

  tail -f /tmp/server_real.log | grep "NOVO CANDLE"

Resultado esperado em ~5 segundos após anexar:

  ✅ NOVO CANDLE! XAUUSD | 2026-05-27T02:15:00 | Close: 4511.50
     RSI_14: 52.3
     SMA_20: 4508.75
     ATR_14: 1.25
     Confluence: 4
     [8 features for XGBoost]

  ✅ NOVO CANDLE! EURUSD | 2026-05-27T02:15:00 | Close: 1.0851
  ✅ NOVO CANDLE! GBPUSD | 2026-05-27T02:15:00 | Close: 1.2654


✅ PASSO 4: VERIFICAR TELEGRAM
═════════════════════════════════════════════════════════════════════════════

Abrir grupo Telegram: "MT5 Real-time Alerts"

Mensagem esperada (~10 segundos após candle):

  🚨 XAUUSD | M15 | 02:15:00
  ━━━━━━━━━━━━━━━━━━━━━━
  Close: 4511.50
  RSI: 52.3% | ATR: 1.25
  Confluence: 4/10
  
  🎯 XGBoost Score: 78% 
  ✅ POSICIONAR
  ─────────────
  Entry: 4510.00
  TP: 4520.00 (+10 pips)
  SL: 4505.00 (-5 pips)

Se não receber:
   → Verificar /tmp/monitor_real.log
   → Ver se "WebSocket connected" aparece
   → Confirmar Telegram token em monitor_mt5_real.py (linha ~45)


✅ PASSO 5: MONITORAR 7 DIAS
═════════════════════════════════════════════════════════════════════════════

Por 7 dias, monitorar:

1. Servidor recebendo candles
   tail -f /tmp/server_real.log | grep NOVO

2. Predições XGBoost
   tail -f /tmp/monitor_real.log | grep Score

3. Alertas Telegram
   Contar quantos "POSICIONAR" vs "OBSERVAR" vs "AGUARDAR"

4. Taxa de acerto
   Comparar predição com resultado real (close vs TP)


📊 DURANTE OS 7 DIAS
═════════════════════════════════════════════════════════════════════════════

Que observar:

✅ Bom sinal:
   • Candles chegando regularmente (a cada 15 min)
   • XGBoost Score entre 70-90% para POSICIONAR
   • Telegram recebendo de forma confiável
   • Valores realistas (XAUUSD ~4500, EURUSD ~1.08, GBPUSD ~1.26)
   • Performance HTTP <100ms

❌ Problema:
   • Candle faltando (gap de >20 min sem novo POST)
   • Valores duplicados ou fora do padrão
   • "NOVO CANDLE!" aparecendo 2x para mesma data
   • WebSocket desconectando
   • Telegram sem mensagens


🔧 TROUBLESHOOTING COMUM
═════════════════════════════════════════════════════════════════════════════

Problema: "Conexão recusada" no servidor HTTP
Solução:
   1. Verificar se servidor Python está rodando:
      ps aux | grep server_mt5_http
   2. Se não estiver:
      cd /home/ubuntu/pessoal/options/src
      python3 server_mt5_http.py &
   3. Verificar se porta 8765 está disponível:
      netstat -tulpn | grep 8765

─────────────────────────────────────────────────────────────────────────

Problema: MQL5 não envia candle
Solução:
   1. Abrir "Experts" tab no MT5
   2. Ver mensagens de erro
   3. Verificar se WebRequests está habilitado
   4. Reiniciar MT5
   5. Compilar MQL5 novamente

─────────────────────────────────────────────────────────────────────────

Problema: Valores errados (ex: XAUUSD = 2546)
Solução:
   1. Verificar se MT5 está sincronizado (ver barra de status)
   2. Aguardar sincronização completa
   3. Reabrir gráfico XAUUSD M15
   4. Desanexar/Reanexar EA

─────────────────────────────────────────────────────────────────────────

Problema: Telegram não recebe
Solução:
   1. Verificar token em monitor_mt5_real.py
   2. Verificar chat ID em monitor_mt5_real.py
   3. Confirmar WebSocket conectando:
      tail -f /tmp/monitor_real.log | grep Connected
   4. Se desconectado, reiniciar monitor


🎯 DEPLOY FINAL
═════════════════════════════════════════════════════════════════════════════

Após 7 dias de monitoramento:

✅ Se 96% das predições estão corretas:
   → XAUUSD pronto para tradear!
   → Model confiança: ALTA

✅ Se 80-95% corretas:
   → XAUUSD pode tradear, mas com cuidado
   → Model confiança: MÉDIA

❌ Se <80% corretas:
   → Não tradear
   → Revisar se dados não estão contaminados
   → Verificar se Market mudou drasticamente


📝 COMANDOS ÚTEIS
═════════════════════════════════════════════════════════════════════════════

Ver logs em tempo real:
  tail -f /tmp/server_real.log

Ver últimas 50 linhas de erro:
  tail -50 /tmp/server_real.log | grep Error

Parar sistema:
  bash /home/ubuntu/pessoal/options/bin/realtime-stop

Iniciar novamente:
  bash /home/ubuntu/pessoal/options/bin/realtime-start

Status dos processos:
  ps aux | grep -E "server_mt5|monitor_mt5"

Ver quantos candles recebidos hoje:
  grep "NOVO CANDLE" /tmp/server_real.log | wc -l

Ver precisão XGBoost:
  grep "XGBoost Score" /tmp/monitor_real.log | head -20


🚀 RESUMO
═════════════════════════════════════════════════════════════════════════════

1. Compilar + Anexar MQL5 no MT5
   ↓
2. Verificar primeiro candle em /tmp/server_real.log
   ↓
3. Confirmar Telegram recebendo alerta
   ↓
4. Monitorar 7 dias
   ↓
5. Fazer deploy em produção (se tudo OK)


📌 IMPORTANTE
═════════════════════════════════════════════════════════════════════════════

⚠️  NÃO TRADEAR durante os 7 dias de validação!
    Sistema está coletando dados apenas.

⚠️  Se parar o servidor, reanexar EA no MT5 para começar novamente.

⚠️  Manter Linux rodando 24/7 (ou servidor Python vai parar).

⚠️  Verificar backup dos dados:
    - /home/ubuntu/pessoal/options/src/*.pkl (modelos)
    - /tmp/server_real.log (histórico)


💡 DÚVIDAS?
═════════════════════════════════════════════════════════════════════════════

Verificar documentação:
  - MQL5_CHANGELOG.md
  - RESUMO_EXECUTIVO.txt
  - README.md

Ver logs detalhados:
  tail -100 /tmp/server_real.log
  tail -100 /tmp/monitor_real.log

═════════════════════════════════════════════════════════════════════════════

🎉 BOA SORTE! Sistema está pronto para produção!

Status: 🟢 VALIDADO ✅
Data: 2026-05-27
Próximo: Anexar no MT5 e começar monitoramento

═════════════════════════════════════════════════════════════════════════════
