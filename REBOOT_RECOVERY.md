# 🔄 GUIA DE REBOOT E RECUPERAÇÃO MT5

## 📌 Status Pré-Reboot (28-05-2026)

✅ **Pipeline Completo**:
- 6 ativos processados
- 6 CSV backtest gerados
- Toda documentação criada
- Git commitado localmente

⚠️ **AÇÃO NECESSÁRIA**: Push para GitHub (remoto)

---

## 📤 ANTES DO REBOOT - Push para GitHub

```bash
cd /home/ubuntu/pessoal/options

# 1. Verificar remoto
git remote -v

# 2. Se NÃO houver remoto (ou estiver vazio):
# Adicione seu repositório GitHub
git remote add origin https://github.com/SEU_USER/ml-trading.git
# OU se já tem remoto:
git remote set-url origin https://github.com/SEU_USER/ml-trading.git

# 3. Fazer push
git push -u origin main
# OU se branch diferente:
git branch -M main
git push -u origin main

# 4. Verificar se funcionou
git log --oneline -n 5 --all
```

**Esperado**: Commits aparecem no GitHub.com

---

## 🔄 APÓS REBOOT - Recuperar Estado

```bash
# 1. Ligar computador e logon

# 2. Voltar para projeto
cd /home/ubuntu/pessoal/options

# 3. Trazer últimas mudanças do GitHub
git pull origin main

# 4. Verificar se tudo está lá
ls -la results/*.csv       # Deve mostrar 6 arquivos
ls -la src/               # Scripts
cat config.json | head -20 # Config
```

---

## 🎮 REATIVAR MT5 APÓS REBOOT

### Opção 1: Via Terminal (Recomendado)

```bash
# 1. Navegar para MT5
cd ~/mt5

# 2. Executar MT5 via box64 (emulador x86)
box64 ./MetaTrader5

# 3. Abrir MT5
# Vai demorar 20-30 segundos na primeira vez
# Vai pedir login (se não estiver salvo)
# Usar credenciais da conta (broker dados)
```

### Opção 2: Via Script (se existir)

```bash
cd ~/pessoal/options

# Se houver script mt5.sh
./mt5.sh

# OU se shell script em ~/bin/
~/bin/realtime-start
```

### Opção 3: Via Desktop Icon

1. Abrir Desktop
2. Clicar em "MetaTrader 5.desktop"
3. Ou "MetaEditor 5.desktop" (se quiser editor)

---

## ✅ Checklist Pós-Reboot

- [ ] **Sistema iniciou** → OK
- [ ] **Logado como ubuntu** → OK
- [ ] **Git pull funcionou** → `git pull origin main` sem erros
- [ ] **Arquivos recuperados** → `ls results/backtest_*.csv` mostra 6 arquivos
- [ ] **MT5 iniciou** → `box64 ./MetaTrader5` abre a janela
- [ ] **MT5 conectado** → Login automático (ou manual se necessário)
- [ ] **Terminal MT5 rodando** → Pode rodar pipeline novamente

---

## 🚨 SE ALGO FALHAR

### Git: "repository not found"
```bash
# Verificar remote
git remote -v

# Se vazio, adicionar:
git remote add origin https://github.com/SEU_USER/repo.git

# Testar conexão
git fetch origin
```

### MT5: "box64 not found"
```bash
# Reinstalar box64
sudo apt update
sudo apt install box64

# OU usar Wine direto (mais lento)
wine ~/mt5/MetaTrader5
```

### Arquivos não recuperados
```bash
# Git pull pode ter falhado
git status
git log

# Fazer merge manual se necessário
git pull origin main --rebase
```

### Permissões
```bash
# Se falhar permissão
chmod +x ~/mt5/MetaTrader5
chmod +x ~/pessoal/options/mt5.sh
chmod +x ~/bin/*
```

---

## 📊 Reproduzir Pipeline Após Reboot

```bash
cd /home/ubuntu/pessoal/options

# 1. Verificar config
python3 -c "import json; print(json.load(open('config.json'))['assets'].keys())"

# 2. Rodar análise (rápido)
python3 analyze_results_v2.py

# 3. Rodar novo pipeline (se quiser retreinar)
python3 src/run_full_pipeline.py EURUSD
python3 src/run_full_pipeline.py --all  # Todos 6

# 4. Ver resultados
tail -100 /tmp/ml_trading.log
```

---

## 🔐 Proteger Dados Críticos

Antes do reboot, backup adicional:

```bash
# Backup da pasta completa
cp -r ~/pessoal/options ~/pessoal/options.backup.$(date +%Y%m%d)

# Backup só dos resultados
zip -r ~/pessoal/results_backup.zip ~/pessoal/options/results/

# Backup só dos modelos treinados (se houver)
find ~/pessoal/options -name "*.pkl" -o -name "*.model" | xargs zip -r ~/models.zip

# Verificar backup
ls -lah ~/pessoal/*.zip ~/pessoal/*.backup*
```

---

## 📞 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| Git: arquivo não sincronizou | `git pull origin main` |
| MT5 não abre | `box64 ~/mt5/MetaTrader5` ou `wine` |
| Sem internet | Usar backup local, `git remote` pode precisar auth SSH |
| Terminal travou | `Ctrl+C` para interromper, `clear` para limpar |
| Python erro | `python3 -c "import pandas"` testar libs |

---

## 📋 Resumo Simples

**Antes Reboot**:
1. `cd /home/ubuntu/pessoal/options`
2. `git push origin main` ← CRÍTICO
3. Reboot

**Depois Reboot**:
1. Login
2. `cd /home/ubuntu/pessoal/options`
3. `git pull origin main`
4. `box64 ~/mt5/MetaTrader5` ← MT5 volta
5. `python3 analyze_results_v2.py` ← Pipeline continua

---

## 🎯 Pronto?

✅ Fazer push para GitHub (veja seção "ANTES DO REBOOT")  
✅ Depois reboot com segurança  
✅ Após reboot: git pull + MT5 reinicia  
✅ Pipeline continua normalmente  

**Status**: 🟢 TUDO PRONTO PARA REBOOT
