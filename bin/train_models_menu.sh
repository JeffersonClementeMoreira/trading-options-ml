#!/bin/bash
#
# Menu unificado para treinar modelos
# Opções: Teste simulado ou Treinamento real do MT5
#

show_menu() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  TREINAR MODELOS XGBOOST                                       ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Escolha uma opção:"
    echo ""
    echo "  1) 🧪 TESTE SIMULADO (demonstração)"
    echo "     Simula dados fictícios para testar o sistema"
    echo ""
    echo "  2) 🔴 TREINAMENTO REAL (dados do MT5)"
    echo "     Coleta dados reais do MT5 e treina os modelos"
    echo ""
    echo "  3) ℹ️  VER DOCUMENTAÇÃO"
    echo "     Mostrar documentação completa"
    echo ""
    echo "  0) ❌ SAIR"
    echo ""
}

test_simulation() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  TESTE SIMULADO - Validar Sistema"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    
    # Parar servidor antigo
    pkill -f "train_models_from_mt5" 2>/dev/null || true
    sleep 1
    
    # Iniciar servidor
    echo "1️⃣  Iniciando servidor de treinamento..."
    cd /home/ubuntu/pessoal/options/src
    python3 train_models_from_mt5.py > /tmp/training_server.log 2>&1 &
    SERVER_PID=$!
    sleep 2
    
    # Rodar teste
    echo "2️⃣  Enviando dados simulados..."
    python3 test_training_simulation.py
    
    # Aguardar conclusão
    echo ""
    echo "3️⃣  Aguardando conclusão (máximo 30 segundos)..."
    for i in {1..30}; do
        if [[ -f "/home/ubuntu/pessoal/options/src/xgboost_EURUSD.pkl" ]] && \
           [[ -f "/home/ubuntu/pessoal/options/src/xgboost_GBPUSD.pkl" ]] && \
           [[ -f "/home/ubuntu/pessoal/options/src/xgboost_XAUUSD.pkl" ]]; then
            
            echo ""
            echo "✅ TESTE BEM-SUCEDIDO!"
            echo ""
            echo "Modelos criados:"
            ls -lh /home/ubuntu/pessoal/options/src/xgboost_*.pkl
            echo ""
            echo "⚠️  Nota: Estes são modelos de TESTE (dados fictícios)"
            echo "         Para modelos reais, use a opção 2 (Treinamento Real)"
            echo ""
            
            kill $SERVER_PID 2>/dev/null || true
            return 0
        fi
        
        if (( i % 5 == 0 )); then
            echo "   [$i/30s] Ainda treinando..."
        fi
        
        sleep 1
    done
    
    echo "❌ Timeout: Treinamento não concluído"
    kill $SERVER_PID 2>/dev/null || true
    return 1
}

real_training() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  TREINAMENTO REAL - Dados do MT5"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    bash /home/ubuntu/pessoal/options/bin/train_from_mt5.sh
}

show_docs() {
    echo ""
    less /home/ubuntu/pessoal/options/TREINAR_MODELOS_DO_MT5.md
}

main() {
    while true; do
        show_menu
        read -p "Opção: " choice
        
        case $choice in
            1)
                test_simulation
                read -p "Pressione ENTER para continuar..."
                clear
                ;;
            2)
                real_training
                read -p "Pressione ENTER para continuar..."
                clear
                ;;
            3)
                show_docs
                clear
                ;;
            0)
                echo "Saindo..."
                exit 0
                ;;
            *)
                echo "❌ Opção inválida"
                read -p "Pressione ENTER para continuar..."
                clear
                ;;
        esac
    done
}

main
