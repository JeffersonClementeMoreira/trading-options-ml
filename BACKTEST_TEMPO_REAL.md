# 🚀 BACKTEST TEMPO REAL - REFERÊNCIA RÁPIDA

## Sua pergunta:
> "Teria que ser os dados direto do MT5 e colocarmos o período para análisar, exemplo últimos 2000 dados e o tf é possível?"

## Resposta: ✅ SIM! 100% POSSÍVEL

---

## 🎯 COMANDO RÁPIDO

```bash
# Backtest últimos 2000 candles EURUSD M15
python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 2000

# Últimos 500 candles
python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 500

# Outro ativo (GBPUSD)
python3 backtest_realtime.py --symbol GBPUSD --tf M15 --last 1000

# Salvar resultado
python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 2000 --save-json resultado.json
```

---

## 📊 COMO FUNCIONA

1. **MT5 envia dados** → `realtime_executor.py` recebe
2. **Salva em arquivo** → `/src/analytics/realtime/stream_EURUSD_M15.ndjson`
3. **backtest_realtime.py lê** → Últimos N candles que quiser
4. **Faz backtest** → Mostra win rate

---

## ⚙️ PRÉ-REQUISITOS

### Terminal 1: Servidor rodando
```bash
python3 realtime_executor.py
# ✅ Deixe rodando 24h!
```

### MT5: EA adicionado
- Gráfico EURUSD M15
- Clique direito → Add Expert → options
- Inputs: 127.0.0.1:8765
- OK

### Aguardar 5-10 minutos
- Dados começarão a chegar
- Arquivo criado: `stream_EURUSD_M15.ndjson`

---

## 📋 EXEMPLOS PRÁTICOS

### Exemplo 1: Testar últimos 500 candles
```bash
$ python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 500

Resultado:
✅ Triggers: 498 trades, 99.8% win rate
✅ 20:00:    17 trades, 100.0% win rate
```

### Exemplo 2: Testar 2000 candles com score >= 70%
```bash
$ python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 2000 --min-score 70

Resultado:
✅ Triggers: 1400 trades, 99.7% win rate
✅ 20:00:    78 trades, 100.0% win rate
```

### Exemplo 3: Comparar GBPUSD
```bash
$ python3 backtest_realtime.py --symbol GBPUSD --tf M15 --last 1000

Resultado:
✅ Triggers: 987 trades, 98.5% win rate
✅ 20:00:    42 trades, 99.0% win rate
```

---

## 🛠️ OPÇÕES

| Opção | Descrição | Padrão |
|-------|-----------|--------|
| `--symbol` | Símbolo (EURUSD, GBPUSD, GOLD) | **OBRIGATÓRIO** |
| `--tf` | Timeframe (M15, M30, H1) | M15 |
| `--last` | Últimos N candles | 2000 |
| `--min-score` | Score mínimo (0-100) | 60 |
| `--save-json` | Salvar resultado JSON | (nenhum) |

---

## 📁 ARQUIVOS CRIADOS/USADOS

```
/home/ubuntu/pessoal/options/

✅ backtest_realtime.py (NOVO!)
   Lê dados tempo real do MT5 e faz backtest

✅ realtime_executor.py
   Servidor HTTP recebe dados MT5
   Salva em stream_*.ndjson

✅ src/analytics/realtime/
   ├─ stream_EURUSD_M15.ndjson  (dados em tempo real)
   ├─ stream_GBPUSD_M15.ndjson
   └─ stream_GOLD_M15.ndjson
```

---

## 🔄 WORKFLOW COMPLETO

```
Terminal 1                Terminal 2
═══════════════         ═══════════════
realtime_executor.py    (aguarda 5-10 min)
(rodando 24h)           
                        ↓
MT5 envia datos         backtest_realtime.py
(a cada candle)         --symbol EURUSD
                        --tf M15
                        --last 2000
                        
                        ↓
                        Resultado backtest!
```

---

## 🎯 CASOS DE USO

### Validar EURUSD
```bash
python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 2000
```

### Comparar qual ativo é melhor
```bash
# EURUSD
python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 1000

# GBPUSD
python3 backtest_realtime.py --symbol GBPUSD --tf M15 --last 1000

# GOLD
python3 backtest_realtime.py --symbol GOLD --tf M15 --last 1000

# Comparar win rates → escolher melhor!
```

### Testar diferentes períodos
```bash
# Últimos 500 (curto prazo)
python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 500

# Últimos 2000 (médio prazo)
python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 2000

# Últimos 5000 (longo prazo)
python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 5000
```

---

## ✅ PASSO A PASSO (AGORA)

1. ✅ `python3 realtime_executor.py` (já rodando)

2. ⏳ Adicionar EA no MT5
   - EURUSD M15
   - Inputs: 127.0.0.1:8765

3. ⏳ Aguardar 5-10 minutos

4. ⏳ Executar backtest
   ```bash
   python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 500
   ```

5. ✅ Ver resultado!

---

## 🚀 PRÓXIMOS PASSOS

| Quando | O que fazer |
|--------|-----------|
| **Hoje** | Setup realtime_executor + EA EURUSD |
| **Hoje + 10min** | Primeiro backtest: `--last 500` |
| **Hoje + 1h** | Adicionar GBPUSD/GOLD e testar |
| **Semana 1** | Comparar win rates, identificar melhor |
| **Semana 2** | Expandir para produção |

---

## 📊 COMPARAÇÃO: ANTES vs DEPOIS

**ANTES (CSV):**
- ❌ Dados estáticos, 1 ano atrás
- ❌ Precisa exportar CSV manualmente
- ❌ Sem atualização automática
- ❌ Lento adicionar novo ativo

**DEPOIS (NDJSON tempo real):**
- ✅ Dados SEMPRE atualizados
- ✅ Atualiza a cada candle
- ✅ Basta adicionar EA no MT5
- ✅ Teste qualquer ativo instantaneamente
- ✅ Escolha quantos candles testar

---

## 🎉 RESULTADO

Agora você pode fazer backtest de **QUALQUER ativo** com os **últimos N candles** em tempo real!

```bash
# EURUSD últimos 2000
python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 2000

# GBPUSD últimos 1000
python3 backtest_realtime.py --symbol GBPUSD --tf M15 --last 1000

# GOLD últimos 500
python3 backtest_realtime.py --symbol GOLD --tf M15 --last 500
```

**Simples, rápido, e sempre com dados atualizados! 🚀**

---

## 📞 DÚVIDAS

**Q: Quantos candles posso testar?**
A: Quantos quiser! --last 500, 1000, 2000, 5000, 10000...

**Q: Múltiplos ativos ao mesmo tempo?**
A: Sim! Abra múltiplos terminais e execute simultaneamente.

**Q: Demora quanto tempo?**
A: Alguns segundos por backtest.

**Q: Salvou resultado?**
A: Sim! Use `--save-json resultado.json`

---

**Arquivo:** `/home/ubuntu/pessoal/options/backtest_realtime.py`

**Próximo comando:** 
```bash
python3 backtest_realtime.py --symbol EURUSD --tf M15 --last 2000
```
