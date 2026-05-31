╔════════════════════════════════════════════════════════════════════════════╗
║         🚀 GUIA COMPLETO: ATIVAR SISTEMA DE PRODUÇÃO COM TELEGRAM        ║
║                    Trading Signals em Tempo Real                          ║
╚════════════════════════════════════════════════════════════════════════════╝

# ✅ Status Atual

- ✅ Modelos ML: Treinados e validados
- ✅ Estratégia: 1 ordem/dia, sem visão do futuro
- ✅ WebSocket server: Pronto em `websocket/server.py`
- ✅ Arquivo de sinais: 5 arquivos de produção (`PRODUCAO_1ORDEM_POR_DIA_*.csv`)
- ⏳ Telegram: Aguardando suas credenciais

---

# 🔧 PASSO 1: Obter Credenciais Telegram

## 1.1 Criar Bot no Telegram

```
1. Abra Telegram
2. Procure por: @BotFather
3. Clique em /start
4. Digite: /newbot
5. Escolha um nome (ex: "OptionsTrader")
6. Escolha um username (ex: "optionstrader_bot")
7. BotFather responde com:
   
   "Done! Congratulations on your new bot. 
    You will find it at t.me/optionstrader_bot. 
    You can now add a description, about section and 
    commands. 
    
    Use this token to access the HTTP API:
    >>> 123456789:ABCDEfghIJKlmnoPQRstUVwxyz <<<
```

**COPIE ESTE TOKEN** (será usado como TELEGRAM_TOKEN)

## 1.2 Obter seu Chat ID

```
1. Envie uma mensagem para seu bot (qualquer coisa)
2. Cole este link no navegador:
   https://api.telegram.org/bot[SEU_TOKEN_AQUI]/getUpdates
   
   Exemplo:
   https://api.telegram.org/bot123456789:ABCDEfghIJKlmnoPQRstUVwxyz/getUpdates

3. Você verá um JSON com algo assim:
   {
     "ok": true,
     "result": [
       {
         "update_id": 123456,
         "message": {
           "message_id": 1,
           "date": 1234567890,
           "chat": {
             "id": 987654321,    ← ESTE É SEU CHAT_ID
             "is_bot": false,
             "type": "private",
             ...
```

**COPIE SEU CHAT ID** (será usado como TELEGRAM_CHAT_ID)

---

# 🖥️ PASSO 2: Configurar Variáveis de Ambiente

## Opção A: Terminal (Temporário - apenas sessão atual)

```bash
export TELEGRAM_TOKEN="123456789:ABCDEfghIJKlmnoPQRstUVwxyz"
export TELEGRAM_CHAT_ID="987654321"
```

## Opção B: Arquivo .env (Permanente)

Criar arquivo `/home/ubuntu/pessoal/options/production/websocket/.env`:

```
TELEGRAM_TOKEN=123456789:ABCDEfghIJKlmnoPQRstUVwxyz
TELEGRAM_CHAT_ID=987654321
```

## Opção C: Sistema (Linux/Mac - Permanente)

Adicionar ao `~/.bashrc` ou `~/.zshrc`:

```bash
export TELEGRAM_TOKEN="123456789:ABCDEfghIJKlmnoPQRstUVwxyz"
export TELEGRAM_CHAT_ID="987654321"
```

Depois executar:
```bash
source ~/.bashrc  # ou ~/.zshrc
```

---

# 🚀 PASSO 3: Iniciar Servidor de Produção

## 3.1 Verificar Dependências

```bash
# Instalar pacotes necessários (se não tiver)
pip3 install websockets pandas numpy requests
```

## 3.2 Testar Conexão Telegram

```bash
cd /home/ubuntu/pessoal/options/production/websocket

# Executar teste rápido
python3 << 'EOF'
import requests
import os

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TOKEN or not CHAT_ID:
    print("❌ Variáveis de ambiente não configuradas!")
    exit(1)

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
response = requests.post(url, json={
    'chat_id': CHAT_ID,
    'text': '✅ Bot funcionando! Pronto para sinais de trading.'
})

if response.status_code == 200:
    print("✅ Telegram conectado com sucesso!")
else:
    print(f"❌ Erro: {response.text}")
EOF
```

## 3.3 Iniciar o Servidor

```bash
python3 server.py
```

Você verá algo como:

```
2026-05-31 10:30:00 - INFO - ✅ Signal Monitor Initialized
2026-05-31 10:30:00 - INFO - ✅ Loaded 224 signals for EURUSD
2026-05-31 10:30:00 - INFO - ✅ Loaded 224 signals for GBPUSD
2026-05-31 10:30:00 - INFO - ✅ Loaded 225 signals for EURAUD
2026-05-31 10:30:00 - INFO - ✅ Loaded 225 signals for NZDUSD
2026-05-31 10:30:00 - INFO - ✅ Loaded 223 signals for EURJPY
2026-05-31 10:30:00 - INFO - WebSocket server started on ws://0.0.0.0:5000
```

✅ **Pronto!** Servidor escutando em `ws://localhost:5000`

---

# 📡 PASSO 4: Conectar MT5

## 4.1 EA em MQL5 (`mt5_client.mq5`)

O arquivo `mt5_client.mq5` já existe em `production/websocket/`

Ele faz:
- ✅ Conecta ao WebSocket todo tick
- ✅ Envia OHLC do candle M15
- ✅ Recebe resposta com sinal

## 4.2 Compilar EA em MT5

```
1. Abra MetaTrader 5
2. File → New → Expert Advisor
3. Copie conteúdo de `mt5_client.mq5`
4. Salve em: `C:\Program Files\MetaTrader 5\MQL5\Experts\`
5. F5 para compilar
6. Attachar ao gráfico EURUSD M15
```

---

# 📊 PASSO 5: Fluxo de Produção

## Timeline Exemplo

```
09/02/2025 00:00 UTC
├─ MT5 EA envia novo candle M15
├─ Servidor recebe via WebSocket
├─ Verifica: Há sinal para EURUSD hoje?
├─ SIM! Entrada: 1.16289, Alvo: 1.16598, BUY, 60% confiança
├─ ENVIA TELEGRAM ✉️
│  └─ "🎯 EURUSD BUY\nEntrada: 1.16289\nAlvo: 1.16598"
├─ Trader abre opção manualmente em MT5
├─ EA monitora até 14:00 UTC
│  (24 horas depois)
├─ Às 14:00 UTC: Verifica target
├─ Se atingiu: +11.9 pips ✅
│  Se não: -5.1 pips ❌
├─ REGISTRA RESULTADO
└─ Próximo dia: aguarda novo sinal

09/03/2025 00:00 UTC
├─ MT5 EA envia novo candle
├─ Verifica: Há sinal para hoje?
├─ SIM! Novo sinal GBPUSD
├─ ENVIA TELEGRAM ✉️
└─ ... (repete)
```

---

# 📈 O Que o Telegram Recebe

Cada sinal chegará assim no Telegram:

```
🎯 SINAL DE TRADING

📊 Par: EURUSD
🔼 Direção: BUY
💰 Entrada: 1.16289
🎯 Alvo: 1.16598
📏 Pips Esperados: +30.9
📊 Confiança: 60%
⏰ Horário: 2025-09-02 00:00:00

✅ Sistema de Produção Ativo
```

---

# ⚙️ Configurações Avançadas

## Arquivo `websocket/server.py`

Pode customizar:

```python
# Linha 318 - Tempo mínimo de confiança
MIN_CONFIDENCE = 0.50  # 50% - aumentar para 60+ para menos sinais

# Linha 317 - Janela de tempo para trigger
SIGNAL_WINDOW_MINUTES = 30  # 30 min ± do horário previsto

# Linha 320 - Porta WebSocket
PORT = 5000  # Mudar se porta estiver em uso
```

---

# 🔐 Segurança

## ⚠️ IMPORTANTE

1. **NUNCA compartilhe** seu TOKEN ou CHAT_ID
2. **Guarde em .env** (adicionar a .gitignore)
3. **Não commite** credenciais em Git
4. **Use .env.example** para documentar estrutura

---

# 📋 Checklist Final

Antes de ir para produção:

- [ ] Bot Telegram criado
- [ ] TOKEN copiado
- [ ] CHAT_ID copiado
- [ ] Variáveis de ambiente configuradas
- [ ] Teste Telegram bem-sucedido
- [ ] Servidor iniciado (`python3 server.py`)
- [ ] EA compilado em MT5
- [ ] WebSocket conectando (sem erros)
- [ ] Telegram recebendo testes

---

# 📞 Troubleshooting

## "Erro ao conectar Telegram"
```
→ Verificar TOKEN e CHAT_ID
→ Testar URL direto no navegador:
  https://api.telegram.org/bot[TOKEN]/getMe
→ Se retornar erro 401: TOKEN inválido
```

## "WebSocket não conectando"
```
→ Verificar se porta 5000 está em uso:
  lsof -i :5000
→ Se estiver, matar processo:
  kill -9 [PID]
→ Ou mudar porta em server.py
```

## "Servidor iniciado mas sem sinais"
```
→ Verificar se arquivos PRODUCAO_1ORDEM_POR_DIA_*.csv existem
→ Verificar se MT5 EA está enviando candles
→ Ver logs em terminal: tail -f server.log (se existir)
```

## "Telegram silencioso (não recebe mensagens)"
```
→ Verificar se CHAT_ID está correto:
  https://api.telegram.org/bot[TOKEN]/getUpdates
→ Testar envio manual de mensagem
→ Verificar se bot tem permissão para enviar
```

---

# 🎯 Próximas Etapas

1. ✅ Configurar Telegram (este guia)
2. ✅ Iniciar servidor de produção
3. ⏳ Monitorar por 1 semana em demo
4. ⏳ Validar resultados
5. ⏳ Escalar para conta real (com posição pequena)

---

# 📚 Referências

- WebSocket Server: `production/websocket/server.py`
- EA MT5: `production/websocket/mt5_client.mq5`
- Sinais: `production/PRODUCAO_1ORDEM_POR_DIA_*.csv`
- Backtests: `results/backtest_*CANDLE_A_CANDLE_TESTE.csv`

---

**✅ Pronto para começar? Siga os passos acima e bom trading!**
