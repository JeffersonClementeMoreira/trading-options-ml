# 🚀 Setup Telegram - Guia Rápido

## Passo 1: Criar Bot no Telegram

1. Abra o Telegram
2. Procure por: **@BotFather**
3. Envie: `/newbot`
4. BotFather vai pedir:
   - Nome do bot (ex: MeuBot)
   - Nome de usuário (ex: meubot_trading_bot)
5. Copie o **TOKEN** (algo como: `123456:ABCdefGHIjklmnoPQRstUVwxyz`)

**Salve este token com segurança!**

---

## Passo 2: Obter seu Chat ID

1. Abra o Telegram
2. Procure por: **@userinfobot**
3. Envie: `/start`
4. Bot vai retornar seu **User ID** (número grande tipo: `987654321`)

**Salve este ID também!**

---

## Passo 3: Configurar no Python

Abra: `monitoramento_telegram.py`

Procure pela seção `CONFIG`:

```python
CONFIG = {
    "ativos": ["EURUSD", "GBPUSD", "XAUUSD"],
    "intervalo_verificacao": 300,  # 5 minutos
    "min_confidence": 0.75,  # 75%
    "telegram_token": "SEU_TOKEN_AQUI",  # ← COLE AQUI
    "telegram_chat_id": "SEU_CHAT_ID_AQUI",  # ← COLE AQUI
}
```

Exemplo preenchido:

```python
CONFIG = {
    "ativos": ["EURUSD", "GBPUSD", "XAUUSD"],
    "intervalo_verificacao": 300,
    "min_confidence": 0.75,
    "telegram_token": "123456:ABCdefGHIjklmnoPQRstUVwxyz",
    "telegram_chat_id": "987654321",
}
```

**Pronto! Salve o arquivo.**

---

## Passo 4: Testar Conexão

```bash
cd /home/ubuntu/pessoal/options
python3 monitoramento_telegram.py
```

Se ver um alerta formatado no seu Telegram: ✅ **FUNCIONANDO!**

Se não receber: Verifique token e chat_id

---

## Passo 5: Iniciar em Background

```bash
# Terminal 1 - Servidor ML5:
PYTHONPATH=.:$PYTHONPATH python3 src/ml5_inference_server.py

# Terminal 2 - Monitoramento:
python3 monitoramento_telegram.py > monitor.log 2>&1 &

# Terminal 3 - Verificar logs:
tail -f monitor.log
```

---

## 📱 Formato do Alerta Telegram

Quando sinal aparecer, você receberá:

```
🚨 SINAL DE TRADING

📊 EURUSD
💰 Preço: 1.08915
⏰ Hora: 23:38:30

🤖 XGBoost Decision
→ BUY
✅ Confiança: 95%

📝 Análise: XGBoost: BUY com 95% de confiança

💡 Abra a ordem manualmente em sua plataforma
```

---

## ⚙️ Customizações Possíveis

### Alterar confiança mínima:
```python
"min_confidence": 0.80,  # Aumentar para 80%
```

### Adicionar mais ativos:
```python
"ativos": ["EURUSD", "GBPUSD", "XAUUSD", "USDJPY"],
```

### Alterar intervalo:
```python
"intervalo_verificacao": 900,  # 15 minutos
```

---

## 🐛 Troubleshooting

**Erro: "Telegram token inválido"**
- Verifique se copiou todo o token (incluindo o número e `:`)
- Teste em @BotFather novamente

**Erro: "Chat ID inválido"**
- Confirme que é número (não texto)
- Teste em @userinfobot novamente

**Não recebe mensagens?**
- Verifique se você é membro do bot (envie `/start` para o bot)
- Confirme confiança mínima sendo atingida
- Verifique `monitor.log` para erros

---

## 🎊 Pronto!

Sistema está configurado e pronto para enviar alertas via Telegram!

**Próximo passo**: Deixar rodando e receber sinais de trading.

