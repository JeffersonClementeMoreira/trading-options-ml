# 🚀 TESTE RÁPIDO DE DADOS MT5 - SEM ESPERAR 15 MINUTOS

## Problema
Você não quer esperar 15 minutos para saber se o último candle está sendo enviado corretamente.

## Solução
Usar scripts para testar e validar dados **imediatamente**.

---

## ⚡ TESTE RÁPIDO (2 minutos)

### Passo 1: Iniciar o sistema
```bash
bash /home/ubuntu/pessoal/options/bin/start_system.sh
```

Sistema fica rodando em background, monitorando por novos candles.

### Passo 2: Testar dados (em outro terminal)
```bash
bash /home/ubuntu/pessoal/options/bin/test_data.sh
```

Menu interativo aparece:
```
1) Extrair dados do MT5 (GetCandleData.mq5)
2) Testar EURUSD (~1.16)
3) Testar XAUUSD (~2500)
4) Testar GBPUSD (~1.27)
5) Enviar JSON customizado
6) Ver logs do servidor
7) Ver logs do monitor
```

---

## 📋 FLUXO PARA VALIDAR DADOS REAIS

### Opção A: Testar com dados reais do MT5 (melhor)

1. **Abra MetaEditor no MT5:**
   ```
   MT5 → Tools → MetaEditor (F4)
   ```

2. **Abra o script GetCandleData.mq5:**
   ```
   File → Open
   /home/ubuntu/pessoal/options/GetCandleData.mq5
   ```

3. **Compile:**
   ```
   Ctrl+Shift+F9 (ou Compile)
   0 errors
   ```

4. **Anexe a um gráfico M15:**
   - Abra gráfico EURUSD M15 (qualquer par)
   - Arraste GetCandleData.mq5 até o gráfico
   - Clique OK

5. **Verifique Experts (Ctrl+Shift+3):**
   ```
   [OK] Last M15 candle:
   {"symbol":"EURUSD","datetime":"2026-05-27T12:30:00","open":1.1598,"high":1.1602,"low":1.1595,"close":1.1599,"volume":5000}
   ```

6. **Copie o JSON:**
   ```
   Selecione todo o JSON
   Ctrl+C
   ```

7. **Teste no Linux:**
   ```bash
   bash /home/ubuntu/pessoal/options/bin/test_data.sh
   # Escolha opção 5
   # Cole o JSON
   ```

8. **Verifique resultado:**
   - Escolha opção 6 para ver logs do servidor
   - Deve mostrar: `[OK] EURUSD @ 1.1599` (seu preço real)
   - Se diferente de ~1.16, há algo errado!

---

### Opção B: Testar com dados de teste (rápido)

Sem tocar no MT5:

```bash
bash /home/ubuntu/pessoal/options/bin/test_data.sh

# Escolha opção 2 (EURUSD)
# Vê resposta [OK]
# Escolha opção 6 para ver logs
```

Logs mostram:
```
[OK] EURUSD @ 1.1599
[Processing] Calculated 25 indicators...
[WebSocket] Broadcasting to monitor...
```

---

## ✅ O QUE ESPERAR

### Se dados REAIS do MT5:
```
Server log:
  [OK] EURUSD @ 1.1598  ← Preço real do MT5

Monitor log:
  [NEW_CANDLE] EURUSD
  RSI: 45.23
  SMA20: 1.1580
  ... outros 25 indicadores
  [TELEGRAM] Sent alert
```

### Se dados FAKE:
```
Server log:
  [OK] EURUSD @ 1.0851  ← ❌ Muito fora do real!

Monitor log:
  [ERROR] Cannot calculate indicators on fake data
```

---

## 🔍 VERIFICAÇÃO RÁPIDA

Antes de começar a tradear, valide:

```bash
# 1. Sistema rodando?
ps aux | grep server_mt5_http

# 2. Servidor respondendo?
curl -X POST http://127.0.0.1:8765/mt5/candle \
  -H "Content-Type: application/json" \
  -d '{"symbol":"EURUSD","datetime":"2026-05-27T12:30:00","open":1.1598,"high":1.1602,"low":1.1595,"close":1.1599,"volume":5000}'

# 3. Deve responder: {"ok": true}

# 4. Último dado recebido?
tail -f /tmp/server_real.log
```

---

## 📝 CHECKLIST DE VALIDAÇÃO

- [ ] Sistema inicia: `bash /home/ubuntu/pessoal/options/bin/start_system.sh`
- [ ] Porta 8765 está listening: `lsof -i :8765`
- [ ] Teste com dados reais do MT5 funciona
- [ ] Preço EURUSD está em ~1.16 (não 1.0851)
- [ ] Preço XAUUSD está em ~2500 (não 2485)
- [ ] Preço GBPUSD está em ~1.27
- [ ] Logs mostram dados sendo processados
- [ ] Telegram recebe alertas com preços corretos

---

## 🎯 PRÓXIMO PASSO

Quando validado:

```bash
# Rodar com screen para deixar em background
screen -S mt5system bash /home/ubuntu/pessoal/options/bin/start_system.sh

# Para voltar:
screen -r mt5system

# Para sair do screen:
Ctrl+A + D
```

---

## ❓ TROUBLESHOOTING

### "Conexão recusada"
```bash
# Sistema não rodando?
bash /home/ubuntu/pessoal/options/bin/start_system.sh
```

### "Dados muito fora do real"
```bash
# Verificar se MT5 está anexado
# GetCandleData.mq5 → deve mostrar dados do gráfico
```

### "Nenhum dado no log"
```bash
# Monitor não conectado?
ps aux | grep monitor_mt5_real
# Se não tiver, sistema foi reiniciado

# Verificar erro:
tail -50 /tmp/monitor_real.log
```

---

**Próximo:** Use `bash /home/ubuntu/pessoal/options/bin/test_data.sh` para validar seus dados! 🚀
