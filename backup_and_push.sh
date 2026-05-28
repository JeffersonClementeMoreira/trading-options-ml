#!/bin/bash

# 🚀 SCRIPT: Backup & Push para GitHub
# Uso: ./backup_and_push.sh [github_url]
# Ex: ./backup_and_push.sh https://github.com/seu_user/ml-trading.git

set -e

REPO_URL="${1:-}"
BACKUP_DIR="/home/ubuntu/pessoal/backup_$(date +%Y%m%d_%H%M%S)"
WORK_DIR="/home/ubuntu/pessoal/options"

echo "========================================="
echo "🚀 BACKUP & PUSH PARA GITHUB"
echo "========================================="
echo ""

# 1. Criar backup local
echo "📦 Criando backup local..."
mkdir -p "$BACKUP_DIR"
cp -r "$WORK_DIR"/* "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ Backup criado em: $BACKUP_DIR"
echo ""

# 2. Ver status do git
echo "📊 Status do Git:"
cd "$WORK_DIR"
git status --short | head -20 || echo "  ✅ Limpo"
echo ""

# 3. Ver remote
echo "🔗 Remote Configurado:"
CURRENT_REMOTE=$(git remote -v | head -1 || echo "")
if [ -z "$CURRENT_REMOTE" ]; then
    echo "  ⚠️ Nenhum remote configurado"
    if [ -n "$REPO_URL" ]; then
        echo "  📝 Configurando: $REPO_URL"
        git remote add origin "$REPO_URL"
        echo "  ✅ Remote adicionado"
    else
        echo "  💡 Use: ./backup_and_push.sh https://github.com/seu_user/repo.git"
        exit 0
    fi
else
    echo "  ✅ $CURRENT_REMOTE"
fi
echo ""

# 4. Fazer commit final se houver mudanças
echo "💾 Verificando mudanças não commitadas..."
if git status --porcelain | grep -q .; then
    echo "  📝 Encontradas mudanças, commitando..."
    git add -A
    git commit -m "🔄 Pre-reboot backup: $(date +%Y-%m-%d_%H:%M:%S)" || true
    echo "  ✅ Committed"
else
    echo "  ✅ Nada pendente"
fi
echo ""

# 5. Fazer push
echo "🚀 Fazendo push para GitHub..."
REMOTE_URL=$(git remote -v | grep "origin" | grep "push" | awk '{print $2}' || echo "")

if [ -z "$REMOTE_URL" ]; then
    echo "  ⚠️ Nenhum remote 'origin' encontrado"
    echo "  📝 Configure com: git remote add origin https://github.com/seu_user/repo.git"
    exit 1
fi

git push -u origin main 2>&1 || {
    echo "  ⚠️ Erro no push, tentando verificar..."
    echo "  Remote: $REMOTE_URL"
    echo ""
    echo "  💡 Possíveis soluções:"
    echo "     1. Verificar credenciais GitHub"
    echo "     2. Usar SSH em vez de HTTPS: git@github.com:user/repo.git"
    echo "     3. Gerar personal access token em GitHub"
    exit 1
}

echo "  ✅ Push realizado com sucesso"
echo ""

# 6. Verificar logs
echo "📝 Últimos commits:"
git log --oneline -n 5
echo ""

# 7. Status final
echo "========================================="
echo "✅ BACKUP & PUSH COMPLETO"
echo "========================================="
echo "📍 Backup local: $BACKUP_DIR"
echo "📤 Push: OK"
echo "🎯 Pronto para reboot!"
echo "========================================="
