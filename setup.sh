#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║              🚀 SETUP AUTOMÁTICO - Trading Options ML                    ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# 1. Verificar Python
echo "1️⃣  Verificando Python..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   ✅ Python $python_version instalado"
echo ""

# 2. Criar virtual env
echo "2️⃣  Criando virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ venv criado"
else
    echo "   ℹ️  venv já existe"
fi
echo ""

# 3. Ativar venv
echo "3️⃣  Ativando venv..."
source venv/bin/activate
echo "   ✅ venv ativado"
echo ""

# 4. Instalar dependências
echo "4️⃣  Instalando dependências..."
pip install -q -r requirements.txt
echo "   ✅ Dependências instaladas"
echo ""

# 5. Verificar .env
echo "5️⃣  Verificando configuração..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "   ✅ .env criado (editar com suas credenciais)"
    echo ""
    echo "   ⚠️  IMPORTANTE: Editar .env com suas credenciais Telegram"
    echo "      nano .env"
    echo ""
else
    echo "   ✅ .env já existe"
fi
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETO!"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "🚀 Para iniciar o servidor:"
echo "   cd production/websocket"
echo "   python3 server.py"
echo ""
echo "🧪 Para testar em outro terminal:"
echo "   source venv/bin/activate"
echo "   cd production/websocket"
echo "   python3 test_client.py"
echo ""
