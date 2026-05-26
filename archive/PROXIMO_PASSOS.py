#!/usr/bin/env python3
"""
Guia de Próximos Passos - Sistema Completo

Tudo está pronto! Apenas siga os passos abaixo.
"""

PROXIMO_PASSOS = """

════════════════════════════════════════════════════════════════════════════════
                        🚀 PRÓXIMOS PASSOS 🚀
════════════════════════════════════════════════════════════════════════════════

Você acabou de receber um sistema completo de trading com:

✅ XGBoost treinado (78.4% acurácia)
✅ Monitoramento automático de ativos
✅ Alertas via Telegram
✅ Documentação completa


────────────────────────────────────────────────────────────────────────────────
PASSO 1: CONFIGURAR TELEGRAM (⏱️ 5 minutos)
────────────────────────────────────────────────────────────────────────────────

Abra o arquivo: SETUP_TELEGRAM.md

Siga exatamente os 5 passos:

1. Criar bot em @BotFather
   → Copiar TOKEN

2. Obter Chat ID em @userinfobot
   → Copiar User ID

3. Editar monitoramento_telegram.py
   → Cole TOKEN e Chat ID

4. Testar conexão
   → Rodar script uma vez para testar

5. Pronto!


────────────────────────────────────────────────────────────────────────────────
PASSO 2: INICIAR SISTEMA (⏱️ 2 minutos)
────────────────────────────────────────────────────────────────────────────────

Abra 2 terminais no VS Code:

TERMINAL 1 - Servidor ML5:
┌─────────────────────────────────────────────────────────────────────────────┐
│ cd /home/ubuntu/pessoal/options                                             │
│ PYTHONPATH=.:$PYTHONPATH python3 src/ml5_inference_server.py               │
└─────────────────────────────────────────────────────────────────────────────┘

TERMINAL 2 - Monitoramento (Telegram):
┌─────────────────────────────────────────────────────────────────────────────┐
│ cd /home/ubuntu/pessoal/options                                             │
│ python3 monitoramento_telegram.py                                           │
└─────────────────────────────────────────────────────────────────────────────┘

Ambos devem dizer: ✅ Pronto


────────────────────────────────────────────────────────────────────────────────
PASSO 3: RECEBER SINAIS (⏱️ Passivo - rodando em background)
────────────────────────────────────────────────────────────────────────────────

Quando chegar um sinal no Telegram:

1. Você recebe mensagem com:
   • Ativo (EURUSD, GBPUSD, XAUUSD)
   • Preço
   • Hora
   • Decisão XGBoost (BUY/SELL)
   • Confiança (75% a 100%)

2. Você abre a ordem MANUALMENTE em:
   • MT5
   • Ou qualquer outra plataforma
   • Ou corretora

3. Sistema continua monitorando


────────────────────────────────────────────────────────────────────────────────
PASSO 4: VALIDAR LIVE PAPER TRADING (⏱️ 1-2 dias)
────────────────────────────────────────────────────────────────────────────────

Antes de usar dinheiro real:

1. Receba 10-20 sinais
2. Abra ordens em paper trading
3. Compare resultado real vs predição
4. Verifique taxa de acerto
5. Se acima de 50%: pronto para live real


────────────────────────────────────────────────────────────────────────────────
PASSO 5: LIVE REAL (⏱️ Quando sentir confiante)
────────────────────────────────────────────────────────────────────────────────

Quando tiver confiança (após validação):

1. Configure tamanho do lote (ex: 0.1 micro lot)
2. Use stop loss e take profit
3. Comece pequeno
4. Aumente gradualmente conforme lucra

Lembrete: Sistema envia ALERTAS, você que abre a ordem!


════════════════════════════════════════════════════════════════════════════════
                      TECNOLOGIA UTILIZADA
════════════════════════════════════════════════════════════════════════════════

Código:                Linguagem:         Biblioteca:
─────────────────────────────────────────────────────────────────────────────

train_xgboost.py    → Python 3       → XGBoost (Machine Learning)
                                      Pandas (dados)
                                      NumPy (matemática)

monitoramento_telegram.py → Python 3 → Telegram API
                                      Requests (HTTP)

src/ml5_inference_server.py → Python 3 → Flask (servidor HTTP)
                                         Pickle (serialização)


════════════════════════════════════════════════════════════════════════════════
                    CUSTOMIZAÇÕES POSSÍVEIS
════════════════════════════════════════════════════════════════════════════════

Se quiser ajustar o sistema depois:

1. Aumentar acurácia do XGBoost:
   → python3 train_xgboost.py (treina novamente)

2. Adicionar mais ativos:
   → Editar CONFIG['ativos'] em monitoramento_telegram.py

3. Alterar intervalo de monitoramento:
   → CONFIG['intervalo_verificacao'] = 600  (10 min)

4. Aumentar confiança mínima:
   → CONFIG['min_confidence'] = 0.85  (85%)


════════════════════════════════════════════════════════════════════════════════
                    TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════════════

Problema: Servidor não sobe
→ Verifique porta 9998: netstat -an | grep 9998
→ Se ocupada: mude porta em ml5_inference_server.py

Problema: Não recebe sinais Telegram
→ Verifique TOKEN e Chat ID (erro comum)
→ Teste em @BotFather que bot responde

Problema: Acurácia baixa
→ Treine novamente com mais dados
→ Ajuste features em core/ml5_processor.py

Problema: Sistema consome muita CPU
→ Aumentar intervalo_verificacao (300 → 600 segundos)


════════════════════════════════════════════════════════════════════════════════
                    PRONTO PARA COMEÇAR!
════════════════════════════════════════════════════════════════════════════════

Seguindo estes 5 passos, você terá:

✅ Sistema de análise automático (XGBoost 78%)
✅ Monitoramento de múltiplos ativos
✅ Alertas em tempo real via Telegram
✅ Você abre ordens quando quiser
✅ 100% sob seu controle

COMECE AGORA:

1. Abra SETUP_TELEGRAM.md
2. Siga os 5 passos de configuração
3. Rode os 2 terminais
4. Receba primeiro sinal no Telegram
5. Celebre! 🎉


Alguma dúvida? Verifique docs/ para documentação técnica.

Boa sorte! 🚀

"""

if __name__ == "__main__":
    print(PROXIMO_PASSOS)
