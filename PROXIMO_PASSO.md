# ⚙️ GUIA DE PRODUÇÃO - PRÓXIMAS AÇÕES

## 🎯 AÇÃO IMEDIATA (Agora)

### 1️⃣ Gerar Dashboard de Performance
```bash
cd /home/ubuntu/pessoal/options
python3 analyze_results.py
```

**O que faz**: Analisa todos 6 backtest CSVs e gera:
- Tabela de Win Rates, Pips, Confiança
- Recomendação de produção (🚀 ou ⚠️)
- Dashboard em `results/dashboard.json`

**Esperado**: 
```
ATIVO       STATUS  SINAIS  GANHOS  PERDAS  WR%   PIPS   CONF%  CONF_SCORE  RATING
EURUSD      ✅      X       Y       Z      AA%   +BBB  CC%     3.5         🟢 GOOD
GBPUSD      ✅      X       Y       Z      AA%   +BBB  CC%     3.2         🟢 GOOD
EURAUD      ✅      X       Y       Z      AA%   +BBB  CC%     3.4         🟡 OK
EURJPY      ✅      X       Y       Z      AA%   +BBB  CC%     3.1         🔴 POOR
NZDUSD      ✅      X       Y       Z      AA%   +BBB  CC%     3.6         🟢 GOOD
GOLD        ✅      X       Y       Z      AA%   +BBB  CC%     2.9         🟡 OK
```

---

## 📊 ANÁLISE MANUAL (Se analyze_results.py tiver problemas)

### Contar Sinais por Ativo
```bash
cd /home/ubuntu/pessoal/options/results

# EURUSD
grep "SEND" backtest_EURUSD_DETAILED.csv | wc -l
grep "FILTERED" backtest_EURUSD_DETAILED.csv | wc -l

# GBPUSD
grep "SEND" backtest_GBPUSD_DETAILED.csv | wc -l

# ... etc para outros ativos
```

### Calcular Win Rate Rápido
```bash
cd /home/ubuntu/pessoal/options

# Para EURUSD
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('results/backtest_EURUSD_DETAILED.csv')
# Filtrar apenas sinais SEND
sends = df[df['ensemble_direction'] == 'SEND']
if len(sends) > 0:
    wins = (sends['actual_pips'] > 0).sum()
    wr = (wins / len(sends)) * 100
    avg_conf = sends['confidence_pct'].mean()
    total_pips = sends['actual_pips'].sum()
    print(f"EURUSD: {len(sends)} SEND signals | WR: {wr:.1f}% | Pips: {total_pips:.0f} | Conf: {avg_conf:.1f}%")
EOF
```

---

## 🚀 CONFIGURAÇÃO DE PRODUÇÃO (Quando WR ≥ 50%)

### Opção 1: Cron (Mais Simples) ✅ RECOMENDADO

**1. Criar script de execução diária**:
```bash
cat > /home/ubuntu/pessoal/options/run_daily_pipeline.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/pessoal/options
DATE=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="/tmp/ml_trading_$(date +%Y%m%d).log"

echo "[$DATE] Iniciando pipeline..." >> $LOG_FILE

# Executar apenas ativos com WR ≥ 50%
# Exemplo (ajuste conforme análise):
python3 src/run_full_pipeline.py EURUSD >> $LOG_FILE 2>&1
python3 src/run_full_pipeline.py GBPUSD >> $LOG_FILE 2>&1
python3 src/run_full_pipeline.py NZDUSD >> $LOG_FILE 2>&1

# Gerar dashboard
python3 analyze_results.py >> $LOG_FILE 2>&1

# Enviar alerta
# python3 src/telegram_alerts.py >> $LOG_FILE 2>&1

DATE_END=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$DATE_END] Pipeline completo" >> $LOG_FILE
EOF

chmod +x /home/ubuntu/pessoal/options/run_daily_pipeline.sh
```

**2. Adicionar ao Crontab**:
```bash
crontab -e

# Adicionar esta linha (executar 22:00 UTC)
0 22 * * * /home/ubuntu/pessoal/options/run_daily_pipeline.sh
```

**3. Verificar Crontab**:
```bash
crontab -l
```

---

### Opção 2: Systemd (Mais Profissional)

**1. Criar arquivo de serviço**:
```bash
sudo tee /etc/systemd/system/ml-trading.service > /dev/null << 'EOF'
[Unit]
Description=ML Trading Pipeline
After=network.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/pessoal/options
ExecStart=/usr/bin/python3 /home/ubuntu/pessoal/options/src/run_full_pipeline.py --all
StandardOutput=append:/tmp/ml_trading.log
StandardError=append:/tmp/ml_trading.log

[Install]
WantedBy=multi-user.target
EOF
```

**2. Criar arquivo de timer (scheduler)**:
```bash
sudo tee /etc/systemd/system/ml-trading.timer > /dev/null << 'EOF'
[Unit]
Description=ML Trading Pipeline Timer
Requires=ml-trading.service

[Timer]
OnCalendar=*-*-* 22:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
```

**3. Ativar**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ml-trading.timer
sudo systemctl start ml-trading.timer
sudo systemctl status ml-trading.timer
```

---

## 📱 ALERTAS (Telegram ou Email)

### Setup Telegram (Recomendado)

**1. Criar bot no Telegram**:
   - Falar com @BotFather
   - `/newbot`
   - Nome: "ML Trading Bot"
   - Username: "ml_trading_bot_XXX"
   - Copiar TOKEN

**2. Pegar seu Chat ID**:
   - Falar com bot: `/start`
   - Executar: `curl https://api.telegram.org/botTOKEN/getUpdates`
   - Copiar `chat_id` da resposta

**3. Configurar em config.json**:
```json
{
  "alerts": {
    "enabled": true,
    "type": "telegram",
    "telegram_token": "COLOQUE_TOKEN_AQUI",
    "telegram_chat_id": "COLOQUE_CHAT_ID_AQUI",
    "send_on_error": true,
    "send_summary": true
  }
}
```

**4. Script de alerta**:
```bash
python3 src/telegram_alerts.py
```

---

## 📈 MONITORAMENTO EM PRODUÇÃO

### Verificar Logs Diários
```bash
tail -50 /tmp/ml_trading_*.log
tail -50 /tmp/ml_trading.log
```

### Ver Dashboard
```bash
cat results/dashboard.json | python3 -m json.tool
```

### Verificar se Cron está Rodando
```bash
# Ver execuções da cron
grep CRON /var/log/syslog | tail -20

# Em systemd
sudo journalctl -u ml-trading.service -n 50
sudo journalctl -u ml-trading.timer -n 50
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

Antes de ativar produção:

- [ ] `python3 analyze_results.py` rodou sem erros
- [ ] Pelo menos 1 ativo com WR ≥ 60% (idealmente 3+)
- [ ] Confiança média ≥ 85% nos bons ativos
- [ ] Pips totais ≥ 0 (positivo)
- [ ] 1 sinal/dia mantido na filtragem
- [ ] CSV outputs criados e têm dados (não vazios)
- [ ] Cron/Systemd configurado e testado
- [ ] Telegram/Email alerts funcionando
- [ ] Backup do config.json feito: `cp config.json config.json.backup`
- [ ] Documentação de troubleshooting revisada

---

## 🛑 PAUSAR PRODUÇÃO (Se Necessário)

```bash
# Cron
crontab -e
# Comentar a linha ou remover

# Systemd
sudo systemctl stop ml-trading.timer
sudo systemctl disable ml-trading.timer
```

---

## 📞 TROUBLESHOOTING PRODUÇÃO

### Pipeline Não Rodou
```bash
# Verificar cron log
grep CRON /var/log/syslog | grep ml_trading
sudo journalctl -u ml-trading.timer -n 50

# Testar manualmente
/home/ubuntu/pessoal/options/run_daily_pipeline.sh
```

### Erro "No space left on device"
```bash
# Limpar cache
rm -rf /home/ubuntu/pessoal/options/.cache
du -sh /tmp/*
df -h
```

### Win Rate Caiu
```bash
# Verificar se dados mudaram
wc -l data/ASSET_*.csv

# Re-treinar ativo específico
python3 src/run_full_pipeline.py ASSET_NAME --retrain
```

### Alertas Não Chegam
```bash
# Testar Telegram
curl -X POST https://api.telegram.org/botTOKEN/sendMessage \
  -d chat_id=CHAT_ID -d text="teste"

# Verificar config.json
grep -A5 '"alerts"' config.json
```

---

## 🎓 REFERENCE - Comandos Principais

```bash
# Análise
python3 analyze_results.py

# Pipeline manual
python3 src/run_full_pipeline.py EURUSD
python3 src/run_full_pipeline.py --all

# Verificar outputs
ls -lh results/backtest_*.csv

# Buscar sinais
grep "SEND" results/backtest_EURUSD_DETAILED.csv | head

# Ver config
cat config.json | python3 -m json.tool

# Logs
tail -100 /tmp/ml_trading.log
```

---

## 📝 STATUS ATUAL

✅ **Pipeline**: Todos 6 ativos completados  
⏳ **Análise**: Aguardando `python3 analyze_results.py`  
⏳ **Produção**: Pronto para deploy após validação KPIs  
⏳ **Alertas**: Pronto para ativar após deploy  

**Próxima ação**: Rode `analyze_results.py` para ver resultados detalhados

---

*Última atualização: 2026-05-22*  
*Versão: 1.1.0*
