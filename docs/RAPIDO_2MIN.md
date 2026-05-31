# ⚡ RÁPIDO: Compilar e Anexar EA (2 minutos)

## ✅ EA já está na pasta MT5!

Arquivo: `~/.wine/drive_c/Program Files/MetaTrader 5/MQL5/Experts/SendCandlesToServer.mq5`

---

## 🚀 Faça isso agora:

### 1️⃣ Abrir MetaEditor no MT5 (30 segundos)

```
MT5 → Tools → MetaEditor
Ou: Ctrl+Shift+E
```

### 2️⃣ Abrir o EA (30 segundos)

```
File → Open
Procurar: SendCandlesToServer.mq5
Abrir
```

### 3️⃣ Compilar (15 segundos)

```
Pressionar F5
ou: Compile

Resultado esperado:
✓ 0 errors, 0 warnings
```

### 4️⃣ Anexar ao gráfico (30 segundos)

```
1. Abrir gráfico: EURUSD M15
2. Arrastar SendCandlesToServer do MetaEditor para o gráfico
ou
   File → New → Expert Advisor → SendCandlesToServer

3. Confirmar: "Permitir Internet?" → ✓ Sempre
```

### 5️⃣ Pronto! 🎉

```
Aguardar próximo candle M15 (falta ~14 minutos)
EA enviará dados automaticamente
Servidor processará
Telegram enviará sinal (se houver)
```

---

## 📊 Verificar se funcionou

**Terminal MT5 (aba "Experts"):**
```
[OK] EURUSD ✓ 2026.05.31 17:15:00 O=1.08610 C=1.08620 V=1500
```

**Servidor Python:**
```bash
curl http://127.0.0.1:8765/mt5/status
```

Pronto! 🚀
