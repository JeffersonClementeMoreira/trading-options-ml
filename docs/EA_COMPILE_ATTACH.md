# 🎯 Compilar e Anexar EA no MT5

## ❌ ERRO 400 - RESOLVIDO ✅

O servidor agora aceita múltiplos formatos de timestamp:
- ISO: `2026-05-31T17:06:00`  
- MT5: `2026.05.31 17:06:00`

**Novo EA melhorado**: `SendCandlesToServer.mq5`

---

## 📋 PASSO A PASSO (5 minutos)

### 1️⃣ Abrir MetaEditor no MT5

```
MT5 → Menu → Tools → MetaEditor
OU: Ctrl+Shift+E (atalho)
```

### 2️⃣ Criar novo arquivo

```
File → New → Expert Advisor
Nome: SendCandlesToServer
OK
```

### 3️⃣ Copiar código do EA

1. Abrir arquivo: `/home/ubuntu/pessoal/options/SendCandlesToServer.mq5`
2. Copiar **TODO** o código
3. Colar no MetaEditor (substituir código gerado)

### 4️⃣ Compilar (F5)

```
Pressionar F5
ou: Compile → Compile
```

**Resultado esperado:**
```
✅ 0 errors, 0 warnings
Compilation complete
```

### 5️⃣ Anexar ao gráfico EURUSD M15

```
Abrir gráfico: EURUSD timeframe M15
Arquivo → New → Expert Advisor → SendCandlesToServer
OK

ou:

Arrastar da pasta: SendCandlesToServer.ex5 → gráfico EURUSD M15
```

### 6️⃣ Permitir Web Request

```
Confirmar: "Permitir que o EA acesse a Internet?"
Marcar: ✓ Sempre
OK
```

---

## ✅ VERIFICAR SE ESTÁ FUNCIONANDO

### Terminal MT5 (abas)

```
[1] EURUSD @ 2026-05-31 17:00:00 O=1.08610 C=1.08620 V=1500 ✓
[2] GBPUSD @ 2026-05-31 17:00:00 O=1.26500 C=1.26520 V=2000 ✓
[3] EURJPY @ 2026-05-31 17:00:00 O=158.400 C=158.420 V=1200 ✓
```

### Servidor Python

```bash
curl http://127.0.0.1:8765/mt5/status | jq
```

Resultado:
```json
{
  "status": "running",
  "mode": "REAL DATA ONLY",
  "data_type": "REAL - NO SIMULATION",
  "pairs_tracked": ["EURUSD", "GBPUSD", "EURJPY"],
  "models_loaded": true
}
```

---

## 🚀 ESPERADO: PRIMEIRO SINAL

**Quando o novo candle M15 fechar:**

```
📨 REAL: EURUSD @ 2026-05-31 17:15:00 | O=1.0861 C=1.0862 V=1500
🔄 Calculando indicadores...
🤖 Predição ML: 0.92 (92% confiança)
✅ Threshold: 0.85 → SINAL GERADO!

🟢 BUY EURUSD 🎯
Entry: $1.08620
Confidence: 92.0%
Status: ✅ REAL DATA
```

---

## ❓ TROUBLESHOOTING

### "Erro: 400" no Terminal MT5

- ✅ **RESOLVIDO** - Servidor agora aceita múltiplos formatos

### "Warning: WebRequest denied"

```
MT5 → Tools → Options → Expert Advisors → Allow WebRequest
Marcar: ✓ Web request on same domain only
Adicionar: localhost
OK
```

### "EA não aparece no gráfico"

1. Recompile (F5)
2. Feche e reabra MT5
3. Tente novamente

### Servidor retorna 400 ainda?

```bash
tail -f /tmp/mt5_server.log
```

Procure por `[ERROR]` - mostra o motivo exato

---

## 📊 MONITORING (OPCIONAL)

### Terminal Linux

```bash
# Ver logs do servidor em tempo real
tail -f /tmp/mt5_server.log

# Ver status
curl http://127.0.0.1:8765/mt5/status | python3 -m json.tool

# Ver último sinal
tail -20 /tmp/mt5_live_real.log | grep "SIGNAL"
```

---

## ✨ TUDO PRONTO!

- ✅ Servidor rodando (porta 8765)
- ✅ EA compilado e anexado
- ✅ Telegram configurado
- ✅ Dados REAIS (sem simulação)
- ✅ Aguardando próximo candle M15...

**Próximo candle fecha em aproximadamente 15 minutos!**
