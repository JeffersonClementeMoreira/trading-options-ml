#!/bin/bash
#
# Nova Estratégia: Prever fechamento D+1 às 14:00
#

clear

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║               🎯 NOVA ESTRATÉGIA - FECHAMENTO D+1 ÀS 14:00               ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝


📊 O QUE MUDOU
════════════════════════════════════════════════════════════════════════════

❌ ESTRATÉGIA ANTIGA:
   └─ Prever próximo candle M15
   └─ Alvo: 10-25 pips no candle seguinte
   └─ Resultado: Previsões ruins (<50%)

✅ ESTRATÉGIA NOVA:
   └─ Prever fechamento D+1 às 14:00
   └─ Entrada: Em qualquer momento (a cada 15min)
   └─ Saída: Fixa em D+1 14:00
   └─ Tipo: Swing trade (24h+)


🎯 COMO FUNCIONA
════════════════════════════════════════════════════════════════════════════

1️⃣  ENTRADA (A qualquer momento):
    ├─ Recebe candle M15 atual
    ├─ Analisa todos os indicadores
    ├─ Prevê: Que preço estará em D+1 às 14:00?
    └─ Armazena previsão com confiança

2️⃣  SAÍDA (D+1 às 14:00):
    ├─ Compara previsão com preço real
    ├─ Calcula se acertou a direção (UP/DOWN)
    ├─ Registra pips reais
    └─ Atualiza taxa de acerto

3️⃣  VALIDAÇÃO CONTÍNUA:
    ├─ Monitora performance em tempo real
    ├─ Segmenta por confiança (>70%, 50-70%, <50%)
    ├─ Mostra pips esperados vs reais
    └─ Recomenda otimizações


📈 MODELOS TREINADOS
════════════════════════════════════════════════════════════════════════════

✅ EURUSD:
   └─ Classificador: 96.6% acurácia
   └─ Regressor: 0.03% MAPE (erro)
   └─ Pronto para usar

✅ GBPUSD:
   └─ Classificador: 96.0% acurácia
   └─ Regressor: 0.03% MAPE (erro)
   └─ Pronto para usar

❌ XAUUSD:
   └─ Tem dados com problemas
   └─ Será corrigido em breve


🚀 COMO USAR AGORA
════════════════════════════════════════════════════════════════════════════

1. Ver previsões de demo:
   
   python3 /home/ubuntu/pessoal/options/src/monitor_nextday_close.py

2. Validar resultados (simular D+1):
   
   python3 /home/ubuntu/pessoal/options/src/validate_nextday_close.py

3. Ver relatório de performance:
   
   python3 /home/ubuntu/pessoal/options/src/validate_nextday_close.py


📋 PRÓXIMOS PASSOS
════════════════════════════════════════════════════════════════════════════

1️⃣  INTEGRAR COM MT5:
   
   ├─ Criar EA que exporta candles em tempo real
   ├─ Fazer previsão a cada 15 minutos
   ├─ Armazenar em banco de dados
   └─ Validar no D+1 às 14:00

2️⃣  VALIDAR EM PRODUÇÃO:
   
   ├─ Rodar 5-7 dias de testes
   ├─ Recolher 30-50 previsões
   ├─ Medir taxa de acerto real
   └─ Se >55% com confiança >70% → usar em trading

3️⃣  OTIMIZAÇÕES:
   
   ├─ Filtros de entrada (BOS, CHOC, SMC levels)
   ├─ Money management por confiança
   ├─ Ajustar tamanho de posição
   └─ Adicionar proteção de stops


💡 DIFERENÇAS IMPORTANTES
════════════════════════════════════════════════════════════════════════════

ANTIGA ESTRATÉGIA:
  └─ Intraday (15 min candles)
  └─ Precisa acertar 10+ pips AGORA
  └─ High frequency (muitos trades/dia)
  └─ Difícil com ruído de mercado

NOVA ESTRATÉGIA:
  └─ Swing trade (24h+)
  └─ Prevê direção geral do dia
  └─ Lower frequency (1 trade/dia)
  └─ Mais tempo para movimento

RESULTADO:
  └─ Menos pressão do modelo
  └─ Maior taxa de acerto esperada
  └─ Menos ruído/spread impact


📊 EXEMPLO DE PREVISÃO
════════════════════════════════════════════════════════════════════════════

Hoje às 10:30:

  📈 EURUSD
     Preço: 1.0851
     Modelo diz: D+1 às 14:00 → 1.0865 (UP)
     Confiança: 57.9%
     Pips esperados: 14p

  ✅ Resultado (Amanhã às 14:00):
     Preço real: 1.0868
     Resultado: HIT (acertou direção)
     Pips: 17p (mais do que esperava!)


🎯 GATILHOS DE ENTRADA (Trabalhar em próximas etapas)
════════════════════════════════════════════════════════════════════════════

1️⃣  TOQUE EM SMC (Support/Resistance):
    └─ Esperar preço tocar nível importante
    └─ Depois fazer previsão

2️⃣  CHOC (Break of Structure):
    └─ Quando preço quebra estrutura recente
    └─ Fazer previsão na reversão

3️⃣  DESVIO PADRÃO:
    └─ Quando preço está X desvios do SMA
    └─ Entrada em extremo

4️⃣  CONVERGÊNCIA DE INDICADORES:
    └─ Quando RSI + MACD + Volume concordam
    └─ Sinal mais forte


════════════════════════════════════════════════════════════════════════════

Próximo passo: Conectar com MT5 para coletar dados em tempo real!

════════════════════════════════════════════════════════════════════════════

EOF

echo ""
echo "Pressione ENTER para continuar..."
read

# Menu
while true; do
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "1) Ver previsões de DEMO"
    echo "2) Validar resultados (simular D+1)"
    echo "3) Treinar modelos novamente"
    echo "4) Ver performance (relatório)"
    echo "5) Retornar ao menu"
    echo ""
    read -p "Escolha uma opção (1-5): " choice
    
    case $choice in
        1)
            echo ""
            python3 /home/ubuntu/pessoal/options/src/monitor_nextday_close.py
            ;;
        2)
            echo ""
            python3 /home/ubuntu/pessoal/options/src/validate_nextday_close.py
            ;;
        3)
            echo ""
            python3 /home/ubuntu/pessoal/options/src/train_nextday_close_model.py
            ;;
        4)
            echo ""
            python3 /home/ubuntu/pessoal/options/src/validate_nextday_close.py
            ;;
        5)
            break
            ;;
        *)
            echo "Opção inválida!"
            ;;
    esac
done

echo "Saindo..."
