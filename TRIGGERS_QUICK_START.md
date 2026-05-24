# ⚡ QUICK START - Sistema de Triggers Flexível

## 3 Passos para Começar (5 minutos)

### 1️⃣ Rodar o Pipeline (1 minuto)
```bash
cd /home/ubuntu/pessoal/options
python3 options_v3.py --file dados/EURUSD_M15_202301012200_202605222015.csv
```

**O que esperar:**
- Output normal do pipeline
- **NOVA SEÇÃO:** "AVALIAÇÃO DE TRIGGERS"
- Mostra score de 0-100% + recomendação

---

### 2️⃣ Analisar Backtest de Triggers (2 minutos)
```bash
python3 analysis/analyze_triggers.py --file dados/EURUSD_M15_202301012200_202605222015.csv
```

**O que esperar:**
- Tabela com scores de todos os dias
- Estatísticas (média, máx, mín)
- Distribuição por nível (FORTE/MÉDIA/FRACA/EVITAR)

---

### 3️⃣ Filtrar Apenas Bons Setups (1 minuto)
```bash
python3 analysis/analyze_triggers.py --file dados/EURUSD_M15_202301012200_202605222015.csv --min-quality 70
```

**O que esperar:**
- Apenas setups com score ≥70% (FORTE + melhores MÉDIA)
- Valida que scores altos = melhor qualidade

---

## O Score Explicado em 30 segundos

```
Score = (sd_score × 0.5) + (confluence_score × 0.3) + (regime × 0.2)

Exemplo:
  • SD está a 0.2% = 75%
  • 2 confluências = 40%
  • Regime TREND = 50%
  
  Score final = (75 × 0.5) + (40 × 0.3) + (50 × 0.2)
              = 37.5 + 12 + 10
              = 59% → MÉDIA ✅
```

---

## Tabela de Decisão Rápida

| Score | Recomendação | Ação |
|-------|--------------|------|
| 75-100% | 🟢 FORTE | Entre 100% |
| 50-74% | 🟡 MÉDIA | Entre 70% |
| 25-49% | 🟠 FRACA | Espere ou entre 30% |
| 0-24% | 🔴 EVITAR | NÃO entre |

---

## Exemplo Real de Output

```
════════════════════════════════════════════════════════════════════════════════
AVALIAÇÃO DE TRIGGERS (FLEXÍVEL - Não é imposição)
════════════════════════════════════════════════════════════════════════════════

📊 QUALIDADE GERAL DA ENTRADA: █████░░░░░ 59%
   Recomendação: MÉDIA

   • Supply/Demand Score: 75% (Distância: 0.2000%)
   • Confluências Score: 40% (2 confluência(s))

   Summary: 🟢 BOM: Apenas 0.2% de distância da SD (muito próximo) | 2 confluências extras

════════════════════════════════════════════════════════════════════════════════

👉 O que significa:
   • SD está MUITO perto (75/100)
   • 2 confirmações extras (40/100)
   • Mercado em TREND (bom para venda de opções)
   
   CONCLUSÃO: Setup BÔEM, recomendação MÉDIA
   AÇÃO: Entrar com posição reduzida (70% do normal)
```

---

## Documentação Completa

### Entender o Sistema (10 min)
📖 [docs/TRIGGER_EVALUATION_FLEXIBLE_SCORING.md](docs/TRIGGER_EVALUATION_FLEXIBLE_SCORING.md)

### Detalhes Técnicos (5 min)
📖 [docs/TECHNICAL_CHANGES_SUMMARY.md](docs/TECHNICAL_CHANGES_SUMMARY.md)

### Ver o Código
🐍 [options_v3.py](options_v3.py) (linhas 220-360)

---

## Comandos Úteis

```bash
# Básico (vê tudo)
python3 options_v3.py --file dados.csv

# Apenas triggers (tabela compacta)
python3 analysis/analyze_triggers.py --file dados.csv

# Filtrar por qualidade
python3 analysis/analyze_triggers.py --file dados.csv --min-quality 70

# Salvar para análise em Excel/Python
python3 analysis/analyze_triggers.py --file dados.csv --save-json resultado.json

# Ver ajuda
python3 analysis/analyze_triggers.py --help
```

---

## FAQ Rápido

**P: O sistema ainda usa 0.5%?**  
R: Não! Agora é contínuo (0.2%, 0.6%, 1.5%, etc). Cada valor tem um score diferente.

**P: Como uso isso no meu EA?**  
R: Veja o score no contexto e ajuste position_size baseado em nível (75%→100%, 50%→70%, etc).

**P: Posso mudar os pesos (0.5, 0.3, 0.2)?**  
R: Sim! Edite em options_v3.py linha ~323 e execute novamente.

**P: Score alto garante lucro?**  
R: Não é garantia, mas tende a ter melhor hit rate. Backtest para validar!

---

## Próximas Semanas

1. **Validação:** Confirme que scores altos = melhor resultado
2. **Otimização:** Ajuste pesos e limiares conforme aprenda
3. **Produção:** Use scores para position sizing automático
4. **EA:** Integre com MT5 para sinais em tempo real

---

## Suporte

Qualquer dúvida:
1. Leia [TRIGGER_EVALUATION_FLEXIBLE_SCORING.md](docs/TRIGGER_EVALUATION_FLEXIBLE_SCORING.md)
2. Veja exemplo em [TECHNICAL_CHANGES_SUMMARY.md](docs/TECHNICAL_CHANGES_SUMMARY.md)
3. Teste com diferentes `--min-quality` valores

---

## Status

✅ **Pronto para usar**  
✅ **Testado**  
✅ **Documentado**  
✅ **Backward compatible**  

**COMECE AGORA!** 🚀
