#!/bin/bash
#
# Backtesting Master - APENAS DADOS REAIS
#

clear

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║    🎯 BACKTESTING - APENAS DADOS REAIS DO MT5 (SEM SINTÉTICOS)           ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝


⚠️  REGRA EXPLÍCITA:
════════════════════════════════════════════════════════════════════════════

  ❌ NUNCA usar dados sintéticos
  ❌ EXPRESSAMENTE PROÍBIDO inventar dados
  ✅ APENAS dados reais exportados do MT5

Isso garante que todas as validações sejam baseadas em histórico real.


🎯 OPÇÃO DISPONÍVEL
════════════════════════════════════════════════════════════════════════════

  1️⃣  Rodar Backtesting com Dados Reais CSV
  2️⃣  Ver Instruções: Como Exportar do MT5
  3️⃣  Analisar Resultados de Backtesting
  4️⃣  Ver Estrutura de Pastas e Arquivos
  5️⃣  Sair


🔧 COMO EXPORTAR DADOS REAIS DO MT5
════════════════════════════════════════════════════════════════════════════

PASSO 1: Abrir History Center
  MT5 → View → History Center

PASSO 2: Selecionar Símbolo
  Expandir "Currencies"
  Clicar em EURUSD, GBPUSD, etc.

PASSO 3: Exportar
  Clique direito no símbolo
  → Export
  → Escolher período (últimos 30-60 dias)
  → Salvar como EURUSD_M15.csv

PASSO 4: Salvar no Local Correto
  Guardar em: /home/ubuntu/pessoal/options/data/
  Criar pasta se não existir:
    mkdir -p /home/ubuntu/pessoal/options/data
  
  Arquivos esperados:
    ├─ EURUSD_M15.csv
    ├─ GBPUSD_M15.csv
    └─ XAUUSD_M15.csv

PASSO 5: Rodar backtesting
  python3 /home/ubuntu/pessoal/options/src/backtest_with_real_csv.py


📈 EXEMPLO DE RESULTADO ESPERADO
════════════════════════════════════════════════════════════════════════════

Com dados reais:

EURUSD:
  Total de dias: 30
  Taxa de acerto: 52.3% (15/29 acertos)
  Confiança média: 75.2%
  Confiança >70%: 58.3% acertos ✅ (BOM!)

GBPUSD:
  Total de dias: 30
  Taxa de acerto: 61.2% (18/29 acertos)
  Confiança média: 72.1%
  Confiança >70%: 66.7% acertos ✅✅ (ÓTIMO!)


🎯 INTERPRETAÇÃO
════════════════════════════════════════════════════════════════════════════

Se Taxa de Acerto com Confiança >70%:

  ✅ >60%  → Use em produção! (BOM)
  🟡 50-60% → Use com Money Management (ACEITÁVEL)
  ❌ <50%  → Não use, ou treinar mais (RUIM)


📋 PRÓXIMOS PASSOS APÓS BACKTESTING
════════════════════════════════════════════════════════════════════════════

Se resultado ✅ (>55% com confiança >70%):

  1. Ir para produção
  2. Usar servidor em tempo real:
     python3 server_nextday_predict.py

  3. Anexar EA ao MT5:
     SendCandleForNextDayPrediction.mq5

  4. Monitorar resultados
     Esperar 1-2 semanas de dados reais


═════════════════════════════════════════════════════════════════════════════

                        Escolha uma opção abaixo:

═════════════════════════════════════════════════════════════════════════════

EOF

echo ""
while true; do
    echo "1) 🔄 Rodar Backtesting com Dados Reais CSV"
    echo "2) 📋 Ver Instruções: Como Exportar do MT5"
    echo "3) � Analisar Resultados de Backtesting"
    echo "4) 📁 Ver Estrutura de Pastas"
    echo "5) ❌ Sair"
    echo ""
    read -p "Escolha (1-5): " choice
    
    case $choice in
        1)
            echo ""
            echo "▶️  Rodando backtesting com dados CSV reais..."
            echo ""
            python3 /home/ubuntu/pessoal/options/src/backtest_with_real_csv.py
            ;;
        2)
            clear
            cat << 'INSTRUÇÕES'

╔════════════════════════════════════════════════════════════════════════════╗
║                 📥 COMO EXPORTAR DADOS REAIS DO MT5                       ║
╚════════════════════════════════════════════════════════════════════════════╝

⚠️  IMPORTANTE: Apenas dados reais - sem sintéticos!

PASSO 1: ABRIR HISTORY CENTER
─────────────────────────────────────────────────────────────────────────────
  MT5 → View → History Center

PASSO 2: SELECIONAR SÍMBOLO
─────────────────────────────────────────────────────────────────────────────
  Na janela History Center:
  
  ├─ Expandir "Currencies"
  ├─ Procurar EURUSD
  ├─ Expandir para ver timeframes
  └─ Clicar em M15 (15 minutos)

PASSO 3: DEFINIR PERÍODO
─────────────────────────────────────────────────────────────────────────────
  Selecione intervalo de datas reais:
  
  Para 30 dias: 30 dias atrás → Hoje
  Para 60 dias: 60 dias atrás → Hoje
  
  ⚠️  Mínimo: 21 dias (2 semanas)

PASSO 4: DOWNLOAD DE DADOS
─────────────────────────────────────────────────────────────────────────────
  Se dados não carregarem automaticamente:
  → Clique "Download" para buscar dados históricos
  → Aguarde carregamento completo

PASSO 5: EXPORTAR
─────────────────────────────────────────────────────────────────────────────
  Clique direito no símbolo M15
  → Export
  → Escolher pasta: Downloads
  → Nome: EURUSD_M15.csv
  → Formato: CSV

PASSO 6: MOVER PARA LOCAL CORRETO
─────────────────────────────────────────────────────────────────────────────
  mkdir -p /home/ubuntu/pessoal/options/data
  cp ~/Downloads/EURUSD_M15.csv /home/ubuntu/pessoal/options/data/
  
  Verificar:
  ls -lh /home/ubuntu/pessoal/options/data/

PASSO 7: REPETIR PARA OUTROS SÍMBOLOS
─────────────────────────────────────────────────────────────────────────────
  Repita para:
  ├─ GBPUSD_M15.csv
  ├─ XAUUSD_M15.csv
  └─ Outros símbolos (conforme necessário)

PASSO 8: RODAR BACKTESTING
─────────────────────────────────────────────────────────────────────────────
  Volta ao menu (opção 1) e escolha "Rodar Backtesting com Dados Reais CSV"

📝 FORMATO ESPERADO DO CSV
─────────────────────────────────────────────────────────────────────────────
  Date,Time,Open,High,Low,Close,Volume
  2026.05.01,00:00,1.0850,1.0860,1.0840,1.0855,100000
  2026.05.01,00:15,1.0855,1.0865,1.0845,1.0860,95000

  Verificar com:
  head -5 /home/ubuntu/pessoal/options/data/EURUSD_M15.csv


⚠️  REGRA IMPORTANTE
─────────────────────────────────────────────────────────────────────────────
  ❌ NUNCA use dados sintéticos ou inventados
  ✅ SEMPRE exporte dados reais do MT5
  ✅ SEMPRE verifique o arquivo antes de usar

Isso garante que todas as validações sejam baseadas em histórico verdadeiro!

════════════════════════════════════════════════════════════════════════════

INSTRUÇÕES
            read -p "Pressione ENTER para voltar ao menu..."
            clear
            exec "$0"
            ;;
        3)
            echo ""
            echo "▶️  Analisando resultados de backtesting..."
            echo ""
            python3 /home/ubuntu/pessoal/options/src/analyze_backtest_results.py
            ;;
        4)
            clear
            echo ""
            echo "📂 ESTRUTURA DE PASTAS E ARQUIVOS"
            echo ""
            echo "/home/ubuntu/pessoal/options/"
            echo "├── src/                                 (Scripts)"
            echo "│   ├── backtest_with_real_csv.py       ← Backtesting (REAL)"
            echo "│   ├── analyze_backtest_results.py     ← Análise de resultados"
            echo "│   ├── server_nextday_predict.py       ← Servidor"
            echo "│   ├── nextday_clf_EURUSD.pkl          ← Modelos"
            echo "│   ├── nextday_reg_EURUSD.pkl"
            echo "│   ├── nextday_clf_GBPUSD.pkl"
            echo "│   ├── nextday_reg_GBPUSD.pkl"
            echo "│   └── ..."
            echo "├── bin/"
            echo "│   └── backtest_master.sh              ← Este menu"
            echo "└── data/                               ← CSV REAIS (IMPORTANTE!)"
            echo "    ├── EURUSD_M15.csv                  ← Exportar aqui"
            echo "    ├── GBPUSD_M15.csv"
            echo "    └── XAUUSD_M15.csv"
            echo ""
            echo "✅ ARQUIVOS PRESENTES:"
            echo ""
            ls -lh /home/ubuntu/pessoal/options/src/*.pkl 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
            echo ""
            echo "📊 ARQUIVOS CSV DE DADOS (deve estar vazio no início):"
            echo ""
            ls -lh /home/ubuntu/pessoal/options/data/ 2>/dev/null | tail -n +2 | awk '{print "   " $9 " (" $5 ")"}' || echo "   (nenhum - criar com: mkdir -p /home/ubuntu/pessoal/options/data)"
            echo ""
            read -p "Pressione ENTER para voltar ao menu..."
            clear
            exec "$0"
            ;;
        5)
            echo ""
            echo "❌ Saindo... (apenas dados reais)"
            echo ""
            exit 0
            ;;
        *)
            echo "Opção inválida!"
            ;;
    esac
    
    echo ""
    echo "Pressione ENTER para continuar..."
    read
done

echo "✅ Sistema encerrado (regra: apenas dados reais)"
