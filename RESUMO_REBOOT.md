# 🚀 REBOOT: TUDO O QUE VOCÊ PRECISA SABER

## 🎯 Situação Atual (28-05-2026, 20:30 UTC)

✅ **Pipeline ML**: 100% completo (6 ativos processados)  
✅ **Código**: Commitado localmente  
⏳ **GitHub**: Pronto para push  
🎮 **MT5**: Funcionando (vai desligar com reboot)  

---

## 📋 RESUMO: 3 Etapas

### ETAPA 1️⃣: ANTES DO REBOOT (Fazer AGORA)

```bash
cd /home/ubuntu/pessoal/options

# Fazer backup & push para GitHub
./backup_and_push.sh https://github.com/SEU_USER/ml-trading.git
```

**Se não tiver GitHub ainda:**
1. Ir para https://github.com/new
2. Criar repo: "ml-trading"
3. Copiar URL (tipo: https://github.com/seu_user/ml-trading.git)
4. Rodar comando acima com essa URL

**Esperado**: Mensagem "✅ BACKUP & PUSH COMPLETO"

---

### ETAPA 2️⃣: FAZER REBOOT

```bash
# Reboot seguro
sudo reboot

# Ou desligar completo
sudo shutdown -h now
```

**⏱️ Tempo**: ~30-60 segundos para reiniciar

---

### ETAPA 3️⃣: APÓS REBOOT (Login novamente)

```bash
# 1. Recuperar código do GitHub
cd /home/ubuntu/pessoal/options
git pull origin main

# 2. Iniciar MT5
box64 ~/mt5/MetaTrader5 &

# 3. Esperar ~20 segundos, depois verificar
ps aux | grep MetaTrader
# Deve mostrar "MetaTrader5" na lista

# 4. Continuar com pipeline
python3 analyze_results_v2.py
```

**✅ Pronto!** Tudo volta à normalidade em ~5 minutos

---

## 📚 Documentação Disponível

| Documento | Uso | Quando Ler |
|-----------|-----|-----------|
| **PUSH_GITHUB.md** | Como fazer push em detalhes | Agora |
| **REBOOT_RECOVERY.md** | Checklist completo pre/post-reboot | Agora |
| **MT5_REBOOT.md** | Como reativar MT5 | Depois do reboot |
| **AGORA_MESMO.md** | Pipeline quick-start | Depois do reboot |
| **backup_and_push.sh** | Script automático | Agora: ./backup_and_push.sh |

---

## ✅ Checklist PRÉ-REBOOT

Faça AGORA antes de desligar:

```
☐ 1. Abri PUSH_GITHUB.md?
☐ 2. Tenho URL do GitHub?
☐ 3. Rodei: ./backup_and_push.sh https://github.com/SEU_USER/ml-trading.git?
☐ 4. Vi mensagem "✅ BACKUP & PUSH COMPLETO"?
☐ 5. Verifiquei em GitHub.com que os arquivos estão lá?
☐ 6. Pronto para reboot!
```

Se algum passo falhar: leia **PUSH_GITHUB.md** com detalhes

---

## ✅ Checklist PÓS-REBOOT

Faça logo após reiniciar e fazer login:

```
☐ 1. Logado no Ubuntu?
☐ 2. Rodei: cd /home/ubuntu/pessoal/options?
☐ 3. Rodei: git pull origin main?
☐ 4. Rodei: box64 ~/mt5/MetaTrader5 &?
☐ 5. MT5 abriu (aguarde 20 segundos)?
☐ 6. Rodei: python3 analyze_results_v2.py?
☐ 7. Tudo funcionando!
```

Se algo falhar: leia **MT5_REBOOT.md** ou **REBOOT_RECOVERY.md**

---

## 🔑 Comandos Críticos

### PRÉ-REBOOT (AGORA)
```bash
./backup_and_push.sh https://github.com/SEU_USER/ml-trading.git
```

### PÓS-REBOOT (DEPOIS)
```bash
cd /home/ubuntu/pessoal/options
git pull origin main
box64 ~/mt5/MetaTrader5 &
python3 analyze_results_v2.py
```

---

## 🚨 Problemas & Soluções Rápidas

### Push para GitHub não funciona?
→ Leia **PUSH_GITHUB.md** (seção "Erros Comuns")

### MT5 não abre?
→ Leia **MT5_REBOOT.md** (seção "Troubleshooting")

### Git pull traz erro?
→ Leia **REBOOT_RECOVERY.md** (seção "Git: arquivo não sincronizou")

### Perdeu dados?
→ Backup está em `/home/ubuntu/pessoal/backup_TIMESTAMP/`

---

## 📊 O Que Vai Acontecer

### ANTES DE REBOOT (Setup 5 min)
```
✅ Backup local criado
✅ Código enviado para GitHub  
✅ Tudo versionado e seguro
```

### REBOOT (30-60 segundos)
```
Sistema desliga → Sistema liga → Login
```

### DEPOIS DE REBOOT (5 minutos)
```
✅ Código recuperado do GitHub
✅ MT5 iniciado
✅ Pipeline funcional novamente
```

---

## 💡 Dicas Importantes

1. **SEMPRE fazer push ANTES de reboot**
   - Se não fizer, trabalho local pode perder (improvável, mas possível)

2. **Box64 leva 20-30 segundos na primeira vez**
   - É normal! Aguarde pacientemente

3. **GitHub URLs**
   - HTTPS: `https://github.com/seu_user/repo.git` (pede token)
   - SSH: `git@github.com:seu_user/repo.git` (mais seguro)

4. **Se MT5 não conecta após reboot**
   - Aguarde 10 segundos (está carregando contas)
   - Se persistir, reinicie: `killall -9 MetaTrader5`

5. **Fazer backup extra se quiser**
   ```bash
   cp -r ~/pessoal/options ~/pessoal/options.backup.$(date +%Y%m%d)
   ```

---

## 🎯 Fluxo Recomendado

**AGORA (próximos 10 min):**
1. Ler este documento (você já está lendo ✅)
2. Ir para **PUSH_GITHUB.md**
3. Executar: `./backup_and_push.sh https://github.com/SEU_USER/ml-trading.git`
4. Verificar no GitHub.com
5. Fazer reboot

**APÓS REBOOT (depois que ligar novamente):**
1. Fazer login
2. `cd /home/ubuntu/pessoal/options && git pull origin main`
3. `box64 ~/mt5/MetaTrader5 &`
4. `python3 analyze_results_v2.py`
5. Continuar normalmente

---

## 📞 Resumo Ejecutivo

| Item | Situação | Ação |
|------|----------|------|
| Código | 100% completo | ✅ Commitado |
| Backup | Local OK | ✅ Em backup/ |
| GitHub | Pronto | 📤 Fazer push AGORA |
| MT5 | Funcionando | 🎮 Vai reiniciar com reboot |
| Reboot | Seguro | ✅ OK fazer agora |

---

## ✅ STATUS FINAL

🟢 **Pronto para Reboot!**

**Próxima Ação**: 
```bash
./backup_and_push.sh https://github.com/SEU_USER/ml-trading.git
```

**Depois**: 
```
sudo reboot
```

**E Depois de Reiniciar**:
```bash
cd /home/ubuntu/pessoal/options
git pull origin main && box64 ~/mt5/MetaTrader5 &
```

---

*Documento: RESUMO REBOOT*  
*Data: 2026-05-28*  
*Status: ✅ TUDO PRONTO*
