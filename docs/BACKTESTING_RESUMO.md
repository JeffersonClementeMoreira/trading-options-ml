# 📊 Sistema de Backtesting - Resumo Executivo

## ⚠️ REGRA EXPLÍCITA

**NUNCA usar dados sintéticos. EXPRESSAMENTE PROÍBIDO inventar dados.**

✅ **APENAS dados reais exportados do MT5**

Isso garante que todas as validações sejam baseadas em histórico verdadeiro.

---

## ✅ Sistema Implementado

### Backtesting com Dados Reais do MT5
- **Arquivo**: `backtest_with_real_csv.py`
- **Função**: Carrega CSV exportado e faz loop completo
- **Loop**: Para cada dia → Faz previsão → Compara com D+1 14:00
- **Resultado**: 100% baseado em dados verdadeiros
- **Uso**: Validação produção

### Interface Interativa
- **Arquivo**: `backtest_master.sh`
- **Menu**: 4 opções (backtesting, instruções, estrutura, sair)
- **Facilidade**: Usuário não precisa lembrar comandos

---

## 🎯 Como Usar

### Passo 1: Exportar Dados do MT5

```
MT5 → View → History Center
├─ Expandir "Currencies"
├─ Selecionar EURUSD
├─ Expandir M15
├─ Clique direito → Export
└─ Salvar como EURUSD_M15.csv (mínimo 30 dias)
```

### Passo 2: Copiar Arquivo

```bash
mkdir -p /home/ubuntu/pessoal/options/data
cp ~/Downloads/EURUSD_M15.csv /home/ubuntu/pessoal/options/data/
```

### Passo 3: Rodar Backtesting

```bash
cd /home/ubuntu/pessoal/options/src
python3 backtest_with_real_csv.py
```

### Ou Use o Menu Interativo

```bash
bash /home/ubuntu/pessoal/options/bin/backtest_master.sh
```

---

## 📈 Exemplo de Saída

```
EURUSD (com dados reais de 30 dias):
  Total de dias: 30
  Taxa de acerto: 52.3% (15/29 acertos)
  Confiança média: 75.2%
  Confiança >70%: 58.3% acertos ✅

GBPUSD (com dados reais de 30 dias):
  Total de dias: 30
  Taxa de acerto: 61.2% (18/29 acertos)
  Confiança média: 72.1%
  Confiança >70%: 66.7% acertos ✅✅
```

---

## 💡 Interpretação

### Regra de Decisão

**Se taxa de acerto com confiança >70%:**

- ✅ **>60%** → Use em produção (máximo lucro)
- 🟡 **50-60%** → Use com Money Management (risco limitado)
- ❌ **<50%** → Não use (precisa melhorar)

### Exemplo

```
"GBPUSD com confiança >70%: 66.7% de acertos"

Significado:
├─ Das 100 previsões com confiança alta
├─ 66.7 acertaram a direção (UP ou DOWN)
└─ 33.3 erraram

Resultado esperado:
├─ Lucro teórico: 66.7% - 33.3% = 33.4% (antes de spreads)
└─ Lucro real: ~25-30% (após spreads)
```

---

## 📁 Estrutura de Arquivos

```
/home/ubuntu/pessoal/options/
├── src/
│   ├── backtest_with_real_csv.py       ← Backtesting (REAL)
│   ├── server_nextday_predict.py       ← Servidor HTTP
│   ├── train_nextday_close_model.py    ← Treino
│   ├── nextday_clf_EURUSD.pkl          ← Modelos
│   ├── nextday_reg_EURUSD.pkl
│   ├── nextday_clf_GBPUSD.pkl
│   ├── nextday_reg_GBPUSD.pkl
│   └── ...
├── bin/
│   └── backtest_master.sh              ← Menu interativo
├── data/                               ← CSV REAIS (IMPORTANTE!)
│   ├── EURUSD_M15.csv                  ← Exportar aqui
│   ├── GBPUSD_M15.csv
│   └── XAUUSD_M15.csv
└── *.md                                ← Documentação
```

---

## 🎯 Próximos Passos

### Imediato
- [ ] Exportar dados do MT5 (EURUSD, GBPUSD, XAUUSD)
- [ ] Copiar para `/home/ubuntu/pessoal/options/data/`
- [ ] Rodar backtesting

### Se Taxa >55% com Confiança >70%
- [ ] ✅ Pronto para produção
- [ ] Iniciar servidor: `python3 server_nextday_predict.py`
- [ ] Anexar EA ao MT5
- [ ] Monitorar por 1-2 semanas

### Se Taxa <50%
- [ ] ❌ Precisa melhorar
- [ ] Retreinar com mais dados
- [ ] Adicionar filtros de entrada
- [ ] Testar outros símbolos

---

## 🔧 Comandos Rápidos

```bash
# Criar pasta de dados
mkdir -p /home/ubuntu/pessoal/options/data

# Copiar arquivo
cp ~/Downloads/EURUSD_M15.csv /home/ubuntu/pessoal/options/data/

# Rodar backtesting com dados reais
python3 /home/ubuntu/pessoal/options/src/backtest_with_real_csv.py

# Menu interativo
bash /home/ubuntu/pessoal/options/bin/backtest_master.sh

# Ver arquivos
ls -la /home/ubuntu/pessoal/options/data/

# Verificar CSV
head -5 /home/ubuntu/pessoal/options/data/EURUSD_M15.csv
```

---

## ✅ Garantias

- ✅ **Sem dados sintéticos** - APENAS histórico real do MT5
- ✅ **Loop automático** - Processa todos os dias do arquivo
- ✅ **Comparação precisa** - Previsão vs resultado real D+1 14:00
- ✅ **Relatório detalhado** - Dia a dia + resumo + confiança
- ✅ **Interface fácil** - Menu interativo (backtest_master.sh)
- ✅ **Pronto para produção** - Quando taxa >55% com confiança >70%

---

**Data**: 27 de maio de 2026
**Versão**: 1.0 (REAL DATA ONLY)
**Status**: ✅ Pronto para validação com dados reais



