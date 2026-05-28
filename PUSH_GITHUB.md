# 📤 PUSH PARA GITHUB - PASSO A PASSO

## 🎯 Objetivo
Enviar todo o código ML pipeline para GitHub antes de fazer reboot

---

## ⚡ Opção 1: Rápido (Script Automático)

```bash
cd /home/ubuntu/pessoal/options

# Se já tem remote GitHub configurado:
./backup_and_push.sh

# Se NÃO tem remote:
./backup_and_push.sh https://github.com/SEU_USER/ml-trading.git
```

**Esperado**: Mensagem "✅ BACKUP & PUSH COMPLETO"

---

## 🔧 Opção 2: Manual (Passo a Passo)

### Passo 1: Verificar Remote

```bash
cd /home/ubuntu/pessoal/options
git remote -v
```

**Se tiver saída** (tipo `origin  https://github.com/...`):
→ Já tem remote, vá para **Passo 3**

**Se VAZIO** (sem saída):
→ Vá para **Passo 2**

---

### Passo 2: Adicionar Remote GitHub

**A. Criar repositório no GitHub:**

1. Ir para https://github.com/new
2. Nome: `ml-trading` (ou outro)
3. Descrição: "ML Trading Pipeline - XGBoost + RandomForest + Decision Tree"
4. **NÃO** inicializar com README (já temos)
5. Clicar "Create repository"
6. Copiar URL (algo como `https://github.com/seu_user/ml-trading.git`)

**B. Configurar em local:**

```bash
cd /home/ubuntu/pessoal/options

# Adicionar remote (substitua URL)
git remote add origin https://github.com/SEU_USER/ml-trading.git

# Verificar
git remote -v
```

---

### Passo 3: Fazer Push

```bash
cd /home/ubuntu/pessoal/options

# Enviar para GitHub
git push -u origin main
```

**Esperado**:
```
Enumerating objects: 150, done.
Counting objects: 100% (150/150), done.
Delta compression using up to 4 threads
Compressing objects: 100% done.
Writing objects: 100% done.
Total 150 (delta 50), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (50/50), done.
To https://github.com/seu_user/ml-trading.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

## 🔑 Autenticação GitHub

Se pedir **username e password**:

### Opção A: Personal Access Token (Recomendado)

1. GitHub.com → Settings → Developer settings → Personal access tokens
2. Gerar novo token com permissões: `repo` (full control)
3. Copiar token (vai aparecer só uma vez)
4. Quando git pedir password, colar o token

### Opção B: SSH (Mais Seguro)

```bash
# 1. Gerar chave SSH
ssh-keygen -t ed25519 -C "seu_email@gmail.com"
# Pressione Enter 3x (usa valores defaults)

# 2. Copiar chave pública
cat ~/.ssh/id_ed25519.pub

# 3. GitHub.com → Settings → SSH Keys → New SSH Key
# Colar conteúdo (inteiro, começando com "ssh-ed25519")

# 4. Testar conexão
ssh -T git@github.com

# 5. Atualizar remote (mude HTTPS → SSH)
git remote set-url origin git@github.com:SEU_USER/ml-trading.git

# 6. Fazer push
git push -u origin main
```

---

## ✅ Verificar Push

### No Terminal

```bash
# Ver se ficou no remote
git branch -a

# Esperado:
#  main
#  remotes/origin/main
```

### No GitHub.com

1. Ir para https://github.com/SEU_USER/ml-trading
2. Deve mostrar:
   - Branch: `main`
   - Último commit: "🎬 FINAL: Pipeline 6 ativos..."
   - Arquivos: config.json, src/, results/, docs, etc.

---

## 🚨 Erros Comuns & Soluções

### Erro: "fatal: 'origin' does not appear to be a 'git' repository"

```bash
# Verificar remote
git remote -v

# Se vazio, adicionar:
git remote add origin https://github.com/seu_user/ml-trading.git
```

### Erro: "Permission denied (publickey)"

- SSH não configurado corretamente
- **Solução**: Usar HTTPS em vez de SSH
- `git remote set-url origin https://github.com/seu_user/ml-trading.git`

### Erro: "fatal: The remote end hung up unexpectedly"

- Problema de conexão/rede
- **Solução**: Tentar novamente em alguns segundos
- `git push -u origin main --verbose` (para mais detalhes)

### Erro: "Repository not found"

- URL incorreta
- Repositório privado (sem permissão)
- **Solução**:
```bash
git remote -v  # Verificar URL
# Se errada, corrigir:
git remote set-url origin https://github.com/seu_user/ml-trading.git
```

---

## 📊 O Que Será Enviado

```
✅ Código:
  ✅ src/run_full_pipeline.py
  ✅ src/indicators.py
  ✅ src/decision_tree_refiner.py
  ✅ src/telegram_alerts.py
  ✅ analyze_results_v2.py
  ✅ config.json

✅ Dados (Results):
  ✅ backtest_EURUSD_DETAILED.csv
  ✅ backtest_GBPUSD_DETAILED.csv
  ✅ backtest_EURAUD_DETAILED.csv
  ✅ backtest_EURJPY_DETAILED.csv
  ✅ backtest_NZDUSD_DETAILED.csv
  ✅ backtest_GOLD_DETAILED.csv

✅ Documentação:
  ✅ README.md (ou criar novo)
  ✅ PRODUCAO.md
  ✅ AGORA_MESMO.md
  ✅ RESUMO_EXECUTIVO.md
  ✅ REBOOT_RECOVERY.md
  ✅ etc.

❌ NÃO será enviado:
  ❌ data/ (raw data, muito grande)
  ❌ .cache/ (temporário)
  ❌ .env (credenciais, se houver)
```

---

## 📋 Checklist Final

- [ ] Git remote verificado: `git remote -v`
- [ ] GitHub repo criado: https://github.com/SEU_USER/ml-trading
- [ ] Autenticação funcionando: token/SSH gerado
- [ ] Push executado: `git push -u origin main`
- [ ] GitHub mostra commits: verificou em GitHub.com? 
- [ ] Todos arquivos lá: config.json, src/, results/
- [ ] Pronto para reboot ✅

---

## 🎯 Próximo Passo (Após Push com Sucesso)

```bash
# Fazer reboot com confiança
sudo reboot

# Após reboot:
cd /home/ubuntu/pessoal/options
git pull origin main
# Tudo volta automaticamente!
```

---

**Status**: 📤 Pronto para Push
