# ⚡ QUICK START - 2 Minutos

## Status Agora

```
✅ Servidor HTTP: Rodando (recebe MT5)
✅ Monitor Telegram: Rodando (envia sinais)
✅ Testado: 6 sinais enviados com sucesso
```

## Para Conectar MT5 Real

### 1️⃣ No MT5 (Windows/Wine)

Abra MetaEditor (F11):
```
Copiar código de:
/home/ubuntu/pessoal/options/SendCandlesToServer.mq5

Colar em: Novo Script > Scripts > SendCandlesToServer.mq5
Compilar (F5)
```

Depois no MT5:
```
Tools → Options → Expert Advisors
✅ Allow WebRequest for listed URLs
✅ Adicionar: http://127.0.0.1:8765
```

Rodar no chart:
```
Navigator → Scripts → SendCandlesToServer
Clicar direito → Attach to chart
```

### 2️⃣ No Linux (Verificar)

```bash
# Confirmar que servidores estão rodando:
ps aux | grep -E 'server_mt5_http|monitor_mt5_real' | grep -v grep

# Se sim: Está tudo OK!
# Se não, rodar:
cd /home/ubuntu/pessoal/options/src
python3 server_mt5_http.py > /tmp/server.log 2>&1 &
python3 monitor_mt5_real.py > /tmp/monitor.log 2>&1 &
```

### 3️⃣ Verificar Telegram

Você deve receber:
- 📊 Novo candle a cada M15 (15 minutos)
- 📈 Com OHLC + Indicadores + Score XGBoost
- 🎯 Ação: POSICIONAR/OBSERVAR/AGUARDAR

## Arquivos Importantes

| Arquivo | Função |
|---------|--------|
| `SendCandlesToServer.mq5` | Script MQL5 para MT5 |
| `server_mt5_http.py` | Recebe dados MT5 |
| `monitor_mt5_real.py` | Envia Telegram |
| `test_mt5_http.py` | Teste (sem MT5) |
| `FINAL_SUMMARY.md` | Documentação completa |

## Teste Sem MT5

```bash
cd /home/ubuntu/pessoal/options/src
python3 test_mt5_http.py
# Verá 6+ mensagens Telegram em ~30s
```

---

**Tudo pronto! Sistema operacional 24/7 🚀**
