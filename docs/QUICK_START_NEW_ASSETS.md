# ⚡ Quick Start: Adicionar Novo Ativo em 5 Minutos

## 🎯 Objetivo
Adicionar um novo ativo (GOLD, SP500, DAX, etc) e começar a gerar sinais.

---

## ✅ CHECKLIST PRÉ-INÍCIO

- [ ] Tenho acesso a dados M15 do ativo? (MT5, TradingView, broker)
- [ ] Sei o horário de fechamento do ativo em UTC?
- [ ] Tenho pelo menos 50.000 candles de dados?
- [ ] Arquivo CSV está em `data/` folder?

**Se respondeu SIM a tudo:** Continua! ⬇️

---

## 🚀 PASSO 1: Coletar Informações (2 min)

### Opção A: Do MetaTrader 5 (RECOMENDADO)

```
1. Abrir MT5
2. Procurar símbolo (GOLD, SP500, DAX, etc)
3. Clicar direita → Propriedades
4. Anotar:
   ✓ Spread típico: Ex: 0.3
   ✓ Ponto (Point): Ex: 0.01
   ✓ Horários: Ex: 00:00-23:59
   ✓ Timezone: Ex: UTC
   ✓ Horário de fechamento: Ex: 17:00
```

**Exemplo prático - GOLD:**
```
Símbolo: GOLD
Spread: 0.3
Ponto: 0.01
Horário de fechamento: 17:00
```

### Opção B: Do TradingView

```
1. Abrir gráfico em TradingView
2. Clique no nome do ativo no topo
3. Ver: Symbol info → Type, Exchange, Hours
4. Procurar: Spread, Point size na descrição
```

### Opção C: Do site do Broker ou CME

```
GOLD:    https://www.cmegroup.com/
SP500:   https://www.cme.com/ ou https://nyse.com
DAX:     https://www.eurex.com/
FTSE:    https://www.lseg.com/
```

---

## 📋 PASSO 2: Preparar Arquivo de Dados (1 min)

### Exportar dados MT5

```
1. MT5 → Menu → Janela de Navegação
2. Histórico
3. Procurar SEUATIVO
4. Clicar direita → Exportar
5. Salvar em: /home/ubuntu/pessoal/options/data/SEUATIVO_M15.csv
```

### Formato esperado (tab-separated):

```
date        time        open    high    low     close   tickvol vol spread
2025-01-01  00:00:00    1.0500  1.0510  1.0495  1.0505  100     10000   1
2025-01-01  00:15:00    1.0505  1.0520  1.0500  1.0515  150     15000   1
...
```

**Deve ter NO MÍNIMO 50.000 linhas!**

```bash
# Verificar:
wc -l data/GOLD_M15.csv
# Saída: 51000 data/GOLD_M15.csv ✅
```

---

## 🔧 PASSO 3: Atualizar config.json (1 min)

Abrir `/home/ubuntu/pessoal/options/config.json`

### Encontrar seu ativo na seção "assets"

```json
// Se GOLD já existe (Ready for setup):
"GOLD": {
  "enabled": false,           // ← Mudar para TRUE
  "asset_type": "commodity",
  "description": "Gold (COMEX)",
  "base": "GOLD",
  "quote": "USD",
  "pip_value": 0.01,         // ← Conferir com MT5
  "spread_typical": 0.30,
  "timezone": "UTC",
  "closing_time": "17:00",   // ← EM UTC!
  "notes": "Ready for setup"
}

// Se seu ativo NÃO existe, adicionar:
"SEUATIVO": {
  "enabled": true,
  "asset_type": "forex_pair",  // ou "commodity" ou "index"
  "description": "Your Asset",
  "base": "XXX",
  "quote": "YYY",              // null se for índice
  "pip_value": 0.0001,         // ← CRÍTICO! Conferir MT5
  "spread_typical": 1.0,
  "timezone": "UTC",           // ou seu timezone
  "closing_time": "14:00",     // ← EM UTC! Conferir MT5
  "notes": "New asset"
}
```

### ⚠️ PONTOS CRÍTICOS

```
1. "enabled": true
   └─ Sem isso, pipeline ignora o ativo

2. "pip_value"
   └─ EURUSD: 0.0001
   └─ GOLD: 0.01
   └─ SP500: 1.0
   └─ ERRADO: quebra tudo!

3. "closing_time"
   └─ SEMPRE em UTC (não em horário local!)
   └─ SP500: 4:00 PM ET = 20:00 UTC (verão)
   └─ GOLD: 17:00 UTC = 17:00 UTC
   └─ ERRADO: modela price wrong

4. "quote": null (apenas para índices!)
   └─ EURUSD: "quote": "USD" ✅
   └─ SP500: "quote": null ✅
   └─ GOLD: "quote": "USD" ✅
```

**Salvar arquivo!**

---

## ▶️ PASSO 4: Rodar Pipeline (1 min)

```bash
cd /home/ubuntu/pessoal/options

# Testar seu ativo:
python3 src/run_full_pipeline.py GOLD

# Ou se criou novo ativo:
python3 src/run_full_pipeline.py SEUATIVO

# Ou rodar TODOS os habilitados:
python3 src/run_full_pipeline.py --all
```

**Saída esperada:**
```
Loading config.json...
Processing GOLD...
  ✓ Loading data from data/GOLD_M15.csv
  ✓ Calculating indicators...
  ✓ Training models...
  ✓ Generating signals...
  ✓ Output: results/UNIFIED_SIGNALS_GOLD.csv

Processing complete!
```

---

## 📊 PASSO 5: Verificar Resultados (1 min)

```bash
# Ver resultados:
head -5 results/UNIFIED_SIGNALS_GOLD.csv

# Saída esperada:
Nº,Signal Time (ENTRY),Entry Price,Direction,Confidence %,...
1,2025-09-04 00:15:00,2050.50,DOWN,99.33,...
2,2025-09-10 04:45:00,2045.25,UP,94.51,...
...

# Contar sinais:
wc -l results/UNIFIED_SIGNALS_GOLD.csv

# Exemplo: 102 sinais = 101 signals + 1 header ✅

# Ver performance em Python:
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('results/UNIFIED_SIGNALS_GOLD.csv')

# Win rate
wins = (df['Result'] == 'WIN').sum()
total = len(df)
wr = wins / total * 100
print(f"Win Rate: {wins}/{total} ({wr:.1f}%)")

# Total pips
pips = df['Actual Pips'].sum()
print(f"Total Pips: {pips:+.2f}")

# Average confidence
conf = df['Confidence %'].mean()
print(f"Avg Confidence: {conf:.1f}%")
EOF
```

---

## 🎯 SE FUNCIONOU

✅ Sucesso! Seu ativo agora está gerando sinais!

**O que fazer agora:**

1. **Analisar performance**
   ```bash
   python3 << 'EOF'
   import pandas as pd
   df = pd.read_csv('results/UNIFIED_SIGNALS_GOLD.csv')
   print(df.describe())
   EOF
   ```

2. **Comparar com outros ativos**
   ```bash
   python3 src/run_full_pipeline.py --all
   # Compara todos os habilitados
   ```

3. **Otimizar closing_time** (se quiser)
   ```
   Testar múltiplos horários:
   1. Copiar config.json para config-17h.json, config-18h.json
   2. Mudar closing_time em cada cópia
   3. python3 src/run_full_pipeline.py GOLD --config config-17h.json
   4. Comparar resultados
   ```

4. **Ativar para trading** (quando satisfeito)
   ```
   1. Deixar "enabled": true em config.json
   2. Rodar regularmente: python3 src/run_full_pipeline.py --all
   3. Usar sinais gerados para trading real
   ```

---

## ⚠️ SE NÃO FUNCIONOU

### Erro 1: "File not found data/GOLD_M15.csv"

**Solução:**
```bash
# Verificar arquivo existe:
ls -la data/GOLD_M15.csv

# Se não existe:
1. Exportar de MT5 novamente
2. Salvar em: /home/ubuntu/pessoal/options/data/
3. Nome deve ser: SIMBOLO_M15.csv

# Conferir:
ls data/ | grep GOLD
```

### Erro 2: "Invalid pip_value in config.json"

**Solução:**
```
1. Abrir config.json
2. Procurar seu ativo
3. Conferir pip_value com MT5:
   - MT5 Propriedades → "Point" (ex: 0.01)
4. Mudar em config.json
5. Testar novamente
```

### Erro 3: "closing_time not in UTC"

**Solução:**
```
1. Conferir fuso horário do ativo (MT5)
2. Converter para UTC:
   Ex: 4:00 PM ET (EDT) = 20:00 UTC
3. Atualizar em config.json
4. Testar novamente

Tabela rápida:
   14:30 ET → 18:30 UTC (EDT)
   16:00 ET → 20:00 UTC (EDT)  ← SP500!
   17:00 UTC → 17:00 UTC        ← GOLD!
```

### Erro 4: "Menos de 50 sinais gerados"

**Pode ser normal!** Ativos menos voláteis geram menos sinais.

**Verificar:**
```bash
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('results/UNIFIED_SIGNALS_GOLD.csv')

# Ver distribuição de sinais
print(f"Total sinais: {len(df)}")
print(f"Confiança média: {df['Confidence %'].mean():.1f}%")
print(f"Confluência média: {df['Confluence Score'].mean():.1f}")

# Se muitos sinais com confiança < 90%:
low_conf = (df['Confidence %'] < 90).sum()
print(f"Sinais filtrados (conf < 90%): {low_conf}")
EOF
```

---

## 📞 REFERÊNCIA RÁPIDA

### Comando mais comum:
```bash
cd /home/ubuntu/pessoal/options && python3 src/run_full_pipeline.py GOLD
```

### Verificar todos os ativos habilitados:
```bash
python3 << 'EOF'
import json
with open('config.json') as f:
    cfg = json.load(f)
enabled = [s for s, d in cfg['assets'].items() if d['enabled']]
print(f"Ativos habilitados: {', '.join(enabled)}")
EOF
```

### Listar todos os arquivos de resultado:
```bash
ls -lh results/UNIFIED_SIGNALS_*.csv
```

### Editar config manualmente:
```bash
nano config.json
# ou
vi config.json
```

---

## 🎓 PRÓXIMOS PASSOS

1. **Entender melhor?** Leia `docs/FAQ_ASSETS.md`
2. **Profundo?** Leia `docs/CONFIG_JSON_GUIDE.md`
3. **Mais ativos?** Repita este guia para cada um
4. **Otimizar?** Use `docs/SETUP_NEW_ASSET.md`
5. **Problema?** Volte à seção "Se não funcionou"

---

## ✨ DICAS PROFISSIONAIS

### Dica 1: Automatizar múltiplos ativos
```bash
# Script para testar todos:
for asset in GOLD SP500 DAX EURUSD GBPUSD; do
  python3 src/run_full_pipeline.py $asset 2>&1 | tail -3
done
```

### Dica 2: Comparar performance
```python
import pandas as pd
import glob

results = {}
for csv in glob.glob('results/UNIFIED_SIGNALS_*.csv'):
    asset = csv.split('_')[-1].replace('.csv', '')
    df = pd.read_csv(csv)
    wr = (df['Result'] == 'WIN').sum() / len(df) * 100
    pips = df['Actual Pips'].sum()
    results[asset] = {'WR': f"{wr:.1f}%", 'Pips': f"{pips:+.0f}"}

pd.DataFrame(results).T.sort_values('WR', ascending=False)
```

### Dica 3: Detectar problemas de dados
```bash
# Se preços parecem estranhos:
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data/GOLD_M15.csv', sep='\t')
print(f"Primeiras 5 linhas:")
print(df.head())
print(f"\nEstatísticas:")
print(df[['open', 'close', 'high', 'low']].describe())
EOF
```

---

## 📝 TEMPLATE COMPLETO PARA NOVO ATIVO

Se seu ativo não existe em config.json, use este template:

```json
"SIMBOLO": {
  "enabled": false,
  "asset_type": "forex_pair",
  "description": "Your Asset Description (M15)",
  "base": "XXX",
  "quote": "YYY",
  "pip_value": 0.0001,
  "spread_typical": 1.0,
  "timezone": "UTC",
  "closing_time": "14:00",
  "active_hours": "00:00-23:59",
  "notes": "Ready for setup"
}
```

Preencher com seus dados e adicionar em config.json.

---

## 🏁 RESUMO EXECUTIVO

| Passo | Tempo | O quê |
|-------|-------|--------|
| 1 | 2 min | Coletar info do MT5/TradingView |
| 2 | 1 min | Exportar dados CSV |
| 3 | 1 min | Atualizar config.json |
| 4 | 1 min | Rodar: `python3 src/run_full_pipeline.py GOLD` |
| 5 | 1 min | Verificar resultados em `results/` |
| **Total** | **5-10 min** | **Novo ativo ativo!** ✅ |

---

**Pronto? Vamos começar!** 🚀

```bash
cd /home/ubuntu/pessoal/options
python3 src/run_full_pipeline.py GOLD
```
