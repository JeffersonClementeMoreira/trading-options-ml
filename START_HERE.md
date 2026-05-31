#!/bin/bash

# QUICK START - Trading Options ML
# Este arquivo contém todos os comandos para iniciar o sistema

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║              🚀 TRADING OPTIONS ML - QUICK START GUIDE                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Passo 1: Clone (executar uma única vez)
echo "PASSO 1: Clonar repositório (executar uma única vez)"
echo "────────────────────────────────────────────────────────────────────────────"
echo "git clone git@github.com:JeffersonClementeMoreira/trading-options-ml.git"
echo "cd trading-options-ml"
echo ""

# Passo 2: Setup (executar uma única vez)
echo "PASSO 2: Setup automático (executar uma única vez)"
echo "────────────────────────────────────────────────────────────────────────────"
echo "bash setup.sh"
echo ""
echo "Ou manualmente:"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  cp .env.example .env"
echo "  nano .env  # Editar com credenciais Telegram"
echo ""

# Passo 3: Rodar servidor
echo "PASSO 3: Iniciar servidor (em cada sessão)"
echo "────────────────────────────────────────────────────────────────────────────"
echo "source venv/bin/activate"
echo "cd production/websocket"
echo "python3 server.py"
echo ""
echo "Esperado:"
echo "  🚀 WebSocket server iniciado em ws://0.0.0.0:5000"
echo "  📁 Sinais carregados para 5 pares"
echo "  ✅ Servidor aguardando conexões MT5..."
echo ""

# Passo 4: Testar (em outro terminal)
echo "PASSO 4: Testar em outro terminal"
echo "────────────────────────────────────────────────────────────────────────────"
echo "source venv/bin/activate"
echo "cd production/websocket"
echo "python3 test_client.py"
echo ""
echo "Se receber:"
echo "  ✅ Conectado ao servidor"
echo "  📊 Signal: 1 | Confidence: 0.67"
echo "  💬 Telegram enviado!"
echo "→ Tudo funcionando! 🎉"
echo ""

# Passo 5: Conectar MT5
echo "PASSO 5: Conectar MetaTrader 5 (opcional)"
echo "────────────────────────────────────────────────────────────────────────────"
echo "1. Abrir MT5"
echo "2. File → New → Expert Advisor"
echo "3. Copiar code de: production/websocket/mt5_client.mq5"
echo "4. F5 para compilar"
echo "5. Attach ao gráfico EURUSD M15"
echo "6. Ver sinais chegando em tempo real"
echo ""

# Monitoramento
echo "MONITORAMENTO"
echo "────────────────────────────────────────────────────────────────────────────"
echo "Ver logs em tempo real:"
echo "  tail -f production.log"
echo ""
echo "Com debug (verbose):"
echo "  LOG_LEVEL=DEBUG python3 production/websocket/server.py"
echo ""
echo "Verificar conexões:"
echo "  lsof -i :5000"
echo ""

# Troubleshooting
echo "TROUBLESHOOTING"
echo "────────────────────────────────────────────────────────────────────────────"
echo "❓ Port 5000 em uso?"
echo "   lsof -i :5000 | grep LISTEN | awk '{print $2}' | xargs kill -9"
echo ""
echo "❓ Dependências faltando?"
echo "   pip install -r requirements.txt"
echo ""
echo "❓ Telegram não envia?"
echo "   Verificar .env com TELEGRAM_TOKEN e TELEGRAM_CHAT_ID corretos"
echo ""

# Estrutura
echo "ESTRUTURA DO PROJETO"
echo "────────────────────────────────────────────────────────────────────────────"
echo "production/websocket/"
echo "├── server.py                 ← WebSocket + Telegram"
echo "├── mt5_client.mq5            ← EA para MT5"
echo "└── test_client.py            ← Cliente de teste"
echo ""
echo "src/"
echo "├── indicators.py             ← 23 indicadores técnicos"
echo "└── backtest_classification_optimized.py"
echo ""
echo "production/PRODUCAO_1ORDEM_POR_DIA_*.csv"
echo "└── 5 pares × 224 trades (sinais pré-calculados)"
echo ""

# Recursos
echo "RECURSOS"
echo "────────────────────────────────────────────────────────────────────────────"
echo "📖 Quick start:      cat docs/QUICK_START.md"
echo "📚 Arquitetura:      cat docs/ARCHITECTURE.md"
echo "🆘 Principal:        cat README.md"
echo "🔐 Setup Telegram:   cat production/SETUP_TELEGRAM.md"
echo ""

# Links
echo "LINKS IMPORTANTES"
echo "────────────────────────────────────────────────────────────────────────────"
echo "🌐 GitHub:           https://github.com/JeffersonClementeMoreira/trading-options-ml"
echo "📊 Performance:      48-54% win rate (validado em 30% test set)"
echo "🎯 Estratégia:       1 ordem/dia, tempo real, sem futuro"
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo "✅ PRONTO PARA COMEÇAR!"
echo "════════════════════════════════════════════════════════════════════════════"
