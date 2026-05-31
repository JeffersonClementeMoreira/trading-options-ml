# 🎮 REATIVAR MT5 APÓS REBOOT

## 📌 Situação
Você vai fazer reboot do sistema. MT5 funcionava antes. Aqui está como voltar.

---

## ⚡ Opção 1: Rápida (5 segundos)

```bash
cd ~/mt5
box64 ./MetaTrader5 &
```

**Esperado**: Janela MT5 abre em ~20 segundos

---

## 🎯 Opção 2: Via Script (se existir)

```bash
# Verificar se existe script
ls ~/pessoal/options/mt5.sh
ls ~/bin/realtime-*

# Executar
./mt5.sh
# OU
~/bin/realtime-start
```

---

## 🖱️ Opção 3: Via Desktop (GUI)

1. Clicar no Desktop (se tiver ícones)
2. Procurar "MetaTrader 5" ou "MT5"
3. Double-click para abrir

---

## 🔍 Opção 4: Diagnóstico & Fix (Se Não Abrir)

### Passo 1: Verificar Instalação

```bash
# MT5 instalado?
ls -la ~/mt5/MetaTrader5
ls -la ~/.wine/drive_c/Program\ Files/MetaTrader\ 5/

# Se um deles existe, está OK
# Se vazio/não existe, precisa reinstalar
```

### Passo 2: Verificar Box64

```bash
# Box64 instalado?
which box64
box64 --version

# Se não tem:
sudo apt update
sudo apt install box64 -y
```

### Passo 3: Permissões

```bash
# Dar permissão de execução
chmod +x ~/mt5/MetaTrader5

# Tentar novamente
box64 ~/mt5/MetaTrader5
```

### Passo 4: Wine (Alternativa, mais lento)

```bash
# Se box64 não funcionar, usar Wine direto
wine ~/mt5/MetaTrader5

# OU
wine ~/.wine/drive_c/Program\ Files/MetaTrader\ 5/terminal.exe
```

---

## 🚀 Iniciar Completamente (Primeiro Boot)

```bash
#!/bin/bash
# mt5-start.sh

echo "🚀 Iniciando MT5..."

# 1. Ir para pasta
cd ~/mt5

# 2. Limpar cache (opcional, se houver problemas)
# rm -rf ~/.wine/drive_c/users/*/Local\ Settings/cache
# rm -rf ~/.wine/drive_c/users/*/Temp

# 3. Iniciar
echo "⏳ Aguardando MT5 abrir (pode levar 20-30 segundos)..."
box64 ./MetaTrader5 &

# 4. Esperar abertura
sleep 30

# 5. Verificar se process está rodando
if pgrep -f MetaTrader5 > /dev/null; then
    echo "✅ MT5 iniciado com sucesso"
else
    echo "❌ MT5 não iniciou, tentando diagnóstico..."
    box64 ./MetaTrader5
fi
```

---

## 📊 Verificar Estado do MT5

```bash
# Ver se MT5 está rodando
ps aux | grep -i metatrader

# Ver logs
tail -50 ~/.wine/drive_c/users/*/Local\ Settings/Application\ Data/*/logs/*

# Matar processo (se travar)
killall MetaTrader5
killall -9 MetaTrader5

# Status das portas
netstat -tlnp | grep 5.* || echo "MT5 não rodando"
```

---

## 🔧 Troubleshooting Completo

### Erro: "command not found: box64"

```bash
# Instalar box64
sudo apt update
sudo apt install box64 -y

# Tentar novamente
cd ~/mt5
box64 ./MetaTrader5
```

### Erro: "Cannot open shared object file"

```bash
# Instalar dependências
sudo apt install libgl1 libx11-6 libxext6 -y

# Tentar novamente
box64 ~/mt5/MetaTrader5
```

### Erro: "Permission denied"

```bash
# Dar permissões
chmod +x ~/mt5/MetaTrader5
chmod +x ~/mt5/*.so* 2>/dev/null || true

# Tentar novamente
box64 ~/mt5/MetaTrader5
```

### MT5 Abre mas Não Conecta

```bash
# 1. Verificar internet
ping google.com

# 2. Verificar credenciais
# MT5 → Settings → Account → Check

# 3. Reiniciar
killall -9 MetaTrader5
sleep 5
box64 ~/mt5/MetaTrader5

# 4. Fazer login novamente se pedir
# (usuário/senha da conta de broker)
```

### MT5 Muito Lento

```bash
# Opção 1: Atualizar box64
sudo apt update && sudo apt upgrade box64 -y

# Opção 2: Usar Wine em vez de box64 (mais estável)
cd ~/mt5
wine ./MetaTrader5

# Opção 3: Aumentar heap size
BOX64_DYNAREC=1 box64 ~/mt5/MetaTrader5
```

---

## 💾 Dados MT5 Persistem?

**Sim!** Todos os dados persistem após reboot:

```bash
# Contas continuam logadas
# Histórico de operações: ~\.wine\drive_c\users\*\AppData\Roaming\MetaQuotes\Terminal

# Verificar se dados estão lá
ls -la ~/.wine/drive_c/users/*/AppData/Roaming/MetaQuotes/Terminal/

# Backup dos dados (segurança)
cp -r ~/.wine/drive_c/users/*/AppData/Roaming/MetaQuotes ~/mt5_backup_$(date +%Y%m%d)
```

---

## 🔄 Ciclo Completo: Reboot → MT5

```bash
# 1. PRÉ-REBOOT (agora)
cd /home/ubuntu/pessoal/options
git push -u origin main  # Enviar para GitHub
# ... fazer reboot ...

# 2. PÓS-REBOOT (após reiniciar)
# Logon no Ubuntu

# 3. Recuperar código
cd /home/ubuntu/pessoal/options
git pull origin main

# 4. Iniciar MT5
box64 ~/mt5/MetaTrader5 &

# 5. Verificar se tudo OK
sleep 30
ps aux | grep MetaTrader
# Deve mostrar processo rodando

# 6. Continuar pipeline
python3 analyze_results_v2.py
python3 src/run_full_pipeline.py EURUSD  # ou outro
```

---

## ⏱️ Timeline Esperado

| Tempo | Ação |
|-------|------|
| T+0s | Pressiona reboot |
| T+30s | Sistema reinicia |
| T+60s | Logon completo |
| T+70s | `cd /home/ubuntu/pessoal/options` |
| T+75s | `git pull origin main` |
| T+80s | `box64 ~/mt5/MetaTrader5 &` |
| T+110s | MT5 abre (20-30s de delay) |
| T+120s | MT5 conectado + dados carregados |
| T+125s | Pronto para pipeline/trades |

---

## 📋 Checklist Reboot

### Antes
- [ ] `git push -u origin main` (enviado para GitHub)
- [ ] Todos arquivos commitados
- [ ] Reboot iniciado

### Depois (Imediatamente)
- [ ] Sistema online
- [ ] `git pull origin main` (código recuperado)
- [ ] `box64 ~/mt5/MetaTrader5` (MT5 abrindo)
- [ ] MT5 conectado (ver status na tela)
- [ ] `ps aux | grep MetaTrader` (verificar processo)

### Pipeline
- [ ] `python3 analyze_results_v2.py` (análise roda)
- [ ] Novo pipeline pode iniciar
- [ ] Continuar operações normais

---

## 🎯 Se Tudo Falhar

```bash
# Nuclear option: limpar e recomeçar
cd ~/mt5
rm -rf ~/.wine/  # Remove Wine (vai perder dados!)

# Reinstalar
box64 ./MetaTrader5  # Vai reconstruir Wine automaticamente
# Vai pedir login novamente
```

⚠️ **CUIDADO**: Isso perde dados salvos!

---

## ✅ Status Pós-Reboot

Tudo deve funcionar:
- ✅ Git sincronizado
- ✅ ML Pipeline funcional
- ✅ MT5 conectado
- ✅ Pronto para continuar trading

**Tempo estimado para ficar 100% operacional: ~5 minutos**

---

*Última atualização: 2026-05-28*
