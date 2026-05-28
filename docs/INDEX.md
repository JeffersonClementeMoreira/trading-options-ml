# 📚 Índice de Documentação - Suporte para Novos Ativos

## 🎯 Encontre o que você precisa

### ⚡ Preciso começar AGORA (5 minutos)?
→ **[QUICK_START_NEW_ASSETS.md](QUICK_START_NEW_ASSETS.md)**
- 5 passos práticos
- Adicionar GOLD, SP500, ou outro ativo
- Checklist, troubleshooting, dicas

### ❓ Tenho uma dúvida específica?
→ **[FAQ_ASSETS.md](FAQ_ASSETS.md)**
- 10 perguntas mais frequentes
- Como descrever GOLD/SP500?
- O que é "Ready for setup"?
- Como mudar closing_time?
- Validação em Python

### 📖 Quero entender tudo em detalhes?
→ **[CONFIG_JSON_GUIDE.md](CONFIG_JSON_GUIDE.md)**
- Explicação completa de cada campo
- Passo-a-passo: GOLD, SP500, SILVER
- Onde descobrir informações (MT5, TradingView, CME, etc)
- Tabelas de referência para 15+ ativos
- Troubleshooting profundo

### 🔧 Quero adicionar múltiplos forex?
→ **[SETUP_NEW_ASSET.md](SETUP_NEW_ASSET.md)**
- AUDUSD, NZDUSD, USDCAD
- Validação de dados
- Verificações de qualidade

### 📝 Preciso recordar comandos?
→ **Scroll para baixo neste arquivo** (Referência Rápida)

---

## 🗺️ Mapa de Aprendizado Recomendado

### Para Iniciante (30 min)
```
1. Ler FAQ_ASSETS.md (10 min)
2. Ler QUICK_START_NEW_ASSETS.md (10 min)
3. Fazer: Adicionar GOLD (10 min)
```

### Para Intermediário (1 hora)
```
1. Ler QUICK_START_NEW_ASSETS.md (10 min)
2. Ler FAQ_ASSETS.md (10 min)
3. Fazer: Adicionar um ativo novo (20 min)
4. Comparar com outro ativo (20 min)
```

### Para Avançado (2 horas)
```
1. Ler CONFIG_JSON_GUIDE.md (30 min)
2. Fazer: Adicionar 2-3 ativos diferentes (30 min)
3. Otimizar: Testar múltiplos closing_time (30 min)
4. Documentar: Criar automação pessoal (30 min)
```

---

## 📚 Estrutura Completa de Documentação

```
docs/
├─ README.md ......................... Visão geral do projeto
├─ CHANGELOG.md ...................... Histórico de versões (v1.0.0+)
├─ SETUP_NEW_ASSET.md ................ Adicionar AUDUSD, NZDUSD, USDCAD
│
├─ 🆕 QUICK_START_NEW_ASSETS.md ....... 5 passos em 5 minutos ⭐
│                                      Para começar AGORA
│
├─ 🆕 FAQ_ASSETS.md .................. 10 perguntas respondidas ⭐
│                                      Para entender conceitos
│
├─ 🆕 CONFIG_JSON_GUIDE.md ........... Guia completo do config.json ⭐
│                                      Para dominar tudo
│
└─ INDEX.md .......................... Este arquivo!
```

---

## 🔑 Campos Críticos (Memo)

| Campo | Exemplo EURUSD | Exemplo GOLD | Exemplo SP500 | Crítico? |
|-------|---------|---------|---------|----------|
| `asset_type` | "forex_pair" | "commodity" | "index" | ⭐⭐ |
| `base` | "EUR" | "GOLD" | "SPX" | ⭐⭐ |
| `quote` | "USD" | "USD" | null | ⭐⭐ |
| `pip_value` | 0.0001 | 0.01 | 1.0 | ⭐⭐⭐ CRÍTICO |
| `closing_time` | "14:00" | "17:00" | "20:00" | ⭐⭐⭐ CRÍTICO |
| `timezone` | "UTC" | "UTC" | "US/Eastern" | ⭐ |
| `enabled` | true | false | false | ⭐ |

> **Errar em `pip_value` ou `closing_time` = Resultados incorretos!**

---

## 🚀 Referência Rápida de Comandos

### Rodar Pipeline
```bash
# Um ativo específico
cd /home/ubuntu/pessoal/options
python3 src/run_full_pipeline.py GOLD

# Todos os habilitados
python3 src/run_full_pipeline.py --all

# Ativo customizado
python3 src/run_full_pipeline.py EURUSD --config config-custom.json
```

### Verificar Config
```bash
# Listar ativos habilitados
python3 << 'EOF'
import json
with open('config.json') as f:
    cfg = json.load(f)
enabled = [s for s, d in cfg['assets'].items() if d.get('enabled')]
print(f"Habilitados: {', '.join(enabled)}")
EOF

# Ver detalhes de um ativo
python3 << 'EOF'
import json
with open('config.json') as f:
    cfg = json.load(f)
import pprint
pprint.pprint(cfg['assets']['GOLD'])
EOF

# Listar todos (com status)
python3 << 'EOF'
import json
with open('config.json') as f:
    cfg = json.load(f)
for symbol, data in cfg['assets'].items():
    status = "✅" if data['enabled'] else "⏸️"
    print(f"{status} {symbol:10} | {data['asset_type']:12} | closing: {data.get('closing_time')}")
EOF
```

### Analisar Resultados
```bash
# Ver sinais gerados
head -3 results/UNIFIED_SIGNALS_GOLD.csv

# Contar sinais
wc -l results/UNIFIED_SIGNALS_GOLD.csv

# Estatísticas básicas
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('results/UNIFIED_SIGNALS_GOLD.csv')
wr = (df['Result'] == 'WIN').sum() / len(df) * 100
pips = df['Actual Pips'].sum()
print(f"Win Rate: {wr:.1f}%")
print(f"Total Pips: {pips:+.1f}")
print(f"Média Confidence: {df['Confidence %'].mean():.1f}%")
EOF

# Comparar múltiplos ativos
python3 << 'EOF'
import pandas as pd
import glob
for f in sorted(glob.glob('results/UNIFIED_SIGNALS_*.csv')):
    df = pd.read_csv(f)
    asset = f.split('_')[-1].replace('.csv', '')
    wr = (df['Result'] == 'WIN').sum() / len(df) * 100
    print(f"{asset:10} | {wr:5.1f}% WR | {len(df):3} signals | {df['Actual Pips'].sum():+7.1f} pips")
EOF
```

### Editar Config
```bash
# Nano (mais fácil)
nano config.json

# Vi/Vim (mais poderoso)
vi config.json

# Apenas visualizar
cat config.json | head -50
```

### Validar Dados
```bash
# Verificar arquivo CSV
head -5 data/GOLD_M15.csv
wc -l data/GOLD_M15.csv

# Mostrar estatísticas
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data/GOLD_M15.csv', sep='\t')
print(f"Linhas: {len(df)}")
print(f"Datas: {df['date'].min()} a {df['date'].max()}")
print(f"Preços: {df['open'].min():.2f} - {df['open'].max():.2f}")
EOF
```

---

## ⚙️ Estrutura Técnica

### Fluxo de Dados
```
Dados (data/SEUATIVO_M15.csv)
    ↓
run_full_pipeline.py (maestro)
    ├─ indicators.py (23 features)
    ├─ generate_detailed_csvs.py (backtest)
    ├─ decision_tree_refiner.py (classificação)
    └─ generate_*_signals.py (filtragem)
    ↓
Resultados (results/UNIFIED_SIGNALS_SEUATIVO.csv)
```

### Arquivos Principais
- `config.json` → Configuração de todos os ativos
- `src/run_full_pipeline.py` → Script maestro
- `data/` → Dados de entrada (M15 candles)
- `results/` → Sinais gerados

---

## ❓ FAQ Rápida

**P: Qual é a diferença entre FAQ_ASSETS.md e CONFIG_JSON_GUIDE.md?**
R: FAQ é para perguntas específicas (10 perguntas + respostas rápidas). CONFIG_JSON_GUIDE é profundo (linha-por-linha do arquivo).

**P: Onde começo se sou iniciante?**
R: QUICK_START_NEW_ASSETS.md → 5 passos → pronto!

**P: Como mudo closing_time?**
R: Editar config.json, campo `closing_time`. Ver FAQ_ASSETS.md pergunta 4.

**P: Posso testar múltiplos closing_time?**
R: Sim! Criar config-14h.json, config-16h.json, etc. Ver QUICK_START_NEW_ASSETS.md seção "Dica 2".

**P: Onde acho informações de um novo ativo?**
R: MT5 (propriedades), TradingView (info), ou CME/NYSE (sites oficiais). Ver CONFIG_JSON_GUIDE.md.

**P: E se algo não funcionar?**
R: Ver QUICK_START_NEW_ASSETS.md seção "Se não funcionou" OU FAQ_ASSETS.md pergunta 9.

---

## 📊 Ativos Já Definidos em config.json

### ✅ Habilitados (Pronto para Use)
- EURUSD (forex_pair)
- GBPUSD (forex_pair)

### 🟡 Desabilitados mas Prontos (Ready for setup)
- AUDUSD (forex_pair)
- NZDUSD (forex_pair)
- USDCAD (forex_pair)
- GOLD (commodity)
- SILVER (commodity)
- OIL (commodity)
- SP500 (index)
- DAX (index)
- FTSE (index)
- NASDAQ (index)

### 📝 Como Ativar
1. Abrir config.json
2. Procurar o ativo
3. Mudar `"enabled": false` → `"enabled": true`
4. Salvar
5. Rodar `python3 src/run_full_pipeline.py SEUATIVO`

---

## 🎓 Próximas Melhorias (Roadmap)

- [ ] Validação automática de closing_time em UTC
- [ ] Conversão automática de timezone
- [ ] Dashboard visual comparando ativos
- [ ] Backtester para otimizar closing_time
- [ ] Integração com MT5 em tempo real
- [ ] API REST para query de sinais

---

## 📞 Suporte

Precisa de ajuda?

1. **Procurar em:** FAQ_ASSETS.md
2. **Procurar em:** CONFIG_JSON_GUIDE.md
3. **Procurar em:** QUICK_START_NEW_ASSETS.md seção "Se não funcionou"
4. **Validar:** Rodar scripts Python de validação em QUICK_START_NEW_ASSETS.md

---

**Última atualização:** v1.0.1  
**Status:** ✅ Produção Pronta  
**Suporte:** Completo (4 documentos MD)
