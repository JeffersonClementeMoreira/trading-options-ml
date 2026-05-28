# 📊 ANÁLISE RÁPIDA - COMO USAR OS ARQUIVOS ENHANCED

## 🎯 Novo Arquivo Criado

Para cada ativo, agora temos um arquivo **ANALYSIS_ASSET_ENHANCED.csv** com colunas de análise rápida:

```
✅ ANALYSIS_EURUSD_ENHANCED.csv
✅ ANALYSIS_GBPUSD_ENHANCED.csv  
✅ ANALYSIS_EURAUD_ENHANCED.csv
✅ ANALYSIS_EURJPY_ENHANCED.csv
✅ ANALYSIS_NZDUSD_ENHANCED.csv
✅ ANALYSIS_GOLD_ENHANCED.csv
```

---

## 📋 Colunas Principais (em ordem de análise)

### 1. **timestamp** - Quando o sinal foi gerado
```
Exemplo: 2025-09-03 03:45:00
Significa: 03:45 UTC no dia 3 de setembro
```

### 2. **close** - Preço de fechamento quando gerou o sinal
```
Exemplo: 1.16231
Preço do candle M15 que gerou o sinal
```

### 3. **ensemble_direction** - Direção do modelo ensemble
```
Valores: UP ou DOWN
Votação de XGBoost + RandomForest
```

### 4. **refined_direction** - Direção refinada pela Decision Tree
```
Valores: UP ou DOWN
Após processamento pela árvore de decisão
```

### 5. **confidence_pct** - Confiança da predição (0-100%)
```
Exemplo: 87.88%
Quanto o modelo tem certeza do sinal
🟢 ≥ 90%: Muito bom
🟡 80-90%: Bom
🔴 < 80%: Fraco
```

### 6. **quality_score** - Score de qualidade (1-5)
```
5.0 = Sinal perfeito
4.0 = Excelente
3.0 = Bom
2.0 = OK
1.0 = Fraco

Baseado em:
- confidence_pct
- refinement_score
- confluence de indicadores
```

### 7. **decision** - Decisão de Ação
```
ENTER  = Bom sinal, entrar na operação
HOLD   = Possível, mas aguardar melhor setup
SKIP   = Sinal fraco, não operar

Lógica:
- ENTER: confidence ≥ 90% E confluence ≥ 3
- HOLD: confidence ≥ 85% E confluence ≥ 2
- SKIP: Resto
```

### 8. **actual_pips** - Ganho/Perda Real
```
Exemplo: +24.40 = 24.4 pips de ganho
Exemplo: -15.20 = 15.2 pips de perda
Exemplo: 0.00 = Breakeven (entrou no preço exato)
```

### 9. **result** - Resultado Final
```
WIN        = actual_pips > 0 (ganhou!)
LOSS       = actual_pips < 0 (perdeu)
BREAKEVEN  = actual_pips = 0 (empatou)
```

### 10. **reasons** - Motivos do Sinal
```
Exemplos:
- "HighConf | GoodRef | 3Confluent"
- "VeryHighConf | ExcelRef | OrderBlock | FVG"
- "GoodConf | ModRef | DirChange-UP"

Componentes:
✓ HighConf / GoodConf / VeryHighConf = Nível de confiança
✓ ExcelRef / GoodRef / ModRef = Qualidade do refinement
✓ 4Confluent / 3Confluent = Indicadores concordam
✓ OrderBlock / FVG = Padrões Smart Money
✓ DirChange-UP/DOWN = Mudança de direção
```

---

## 🎯 Como Usar para Análise Rápida

### Opção 1: Excel/Libreoffice Calc

```bash
libreoffice ~/pessoal/options/results/ANALYSIS_EURUSD_ENHANCED.csv
```

**Filtros úteis em Excel:**
1. Coluna **decision** = "ENTER" (ver só sinais de entrada)
2. Coluna **result** = "WIN" (ver só ganhos)
3. Coluna **quality_score** ≥ 3.0 (sinais bons)

**Cálculos úteis:**
- WIN rate = COUNTIF(result,"WIN") / COUNTA(result)
- Pips totais = SUM(actual_pips)
- Pips médios = AVERAGE(actual_pips)

---

### Opção 2: Python - Análise Rápida

```python
import pandas as pd

# Carregar arquivo
df = pd.read_csv('results/ANALYSIS_EURUSD_ENHANCED.csv')

# Sinais de ENTRADA
enters = df[df['decision'] == 'ENTER']
print(f"Sinais ENTER: {len(enters)}")

# Win rate dos ENTERs
wins = len(enters[enters['result'] == 'WIN'])
win_rate = wins / len(enters) * 100
print(f"Win Rate (ENTER): {win_rate:.1f}%")

# Pips totais
total_pips = enters['actual_pips'].sum()
print(f"Pips Totais: {total_pips:.0f}")

# Qualidade média
avg_quality = enters['quality_score'].mean()
print(f"Qualidade Média: {avg_quality:.2f}/5")

# Confiança média
avg_confidence = enters['confidence_pct'].mean()
print(f"Confiança Média: {avg_confidence:.1f}%")
```

---

### Opção 3: Filtrar Sinais Bons

```python
# Sinais com alta qualidade
good_signals = df[(df['decision'] == 'ENTER') & 
                  (df['quality_score'] >= 3.0) &
                  (df['confidence_pct'] >= 90)]

print(f"Sinais BONS: {len(good_signals)}")
print(f"Win Rate: {(good_signals['result']=='WIN').sum() / len(good_signals) * 100:.1f}%")
print(f"Pips: {good_signals['actual_pips'].sum():.0f}")
```

---

## 📊 Exemplo: Análise Completa de um Ativo

```python
import pandas as pd

def analisa_ativo(asset_name):
    df = pd.read_csv(f'results/ANALYSIS_{asset_name}_ENHANCED.csv')
    
    print(f"\n{'='*60}")
    print(f"  ANÁLISE: {asset_name}")
    print(f"{'='*60}\n")
    
    # Total de sinais
    print(f"Total de sinais: {len(df)}")
    
    # Por decision
    enters = len(df[df['decision'] == 'ENTER'])
    holds = len(df[df['decision'] == 'HOLD'])
    skips = len(df[df['decision'] == 'SKIP'])
    print(f"  ENTER: {enters} ({enters/len(df)*100:.1f}%)")
    print(f"  HOLD:  {holds} ({holds/len(df)*100:.1f}%)")
    print(f"  SKIP:  {skips} ({skips/len(df)*100:.1f}%)\n")
    
    # Se houver ENTERs
    if enters > 0:
        enter_df = df[df['decision'] == 'ENTER']
        wins = len(enter_df[enter_df['result'] == 'WIN'])
        losses = len(enter_df[enter_df['result'] == 'LOSS'])
        be = len(enter_df[enter_df['result'] == 'BREAKEVEN'])
        
        print(f"Sinais ENTER:")
        print(f"  Ganhos (WIN):    {wins}")
        print(f"  Perdidos (LOSS): {losses}")
        print(f"  Empatados (BE):  {be}")
        print(f"  Win Rate:        {wins/(wins+losses)*100:.1f}%\n" if (wins+losses) > 0 else "")
        
        print(f"Performance:")
        print(f"  Total Pips:      {enter_df['actual_pips'].sum():.0f}")
        print(f"  Pips/Sinal:      {enter_df['actual_pips'].mean():.2f}")
        print(f"  Qualidade Média: {enter_df['quality_score'].mean():.2f}/5")
        print(f"  Confiança Média: {enter_df['confidence_pct'].mean():.1f}%\n")
        
        # Melhores sinais
        best = enter_df.nlargest(3, 'actual_pips')
        print(f"Top 3 Ganhos:")
        for idx, row in best.iterrows():
            print(f"  {row['timestamp']}: +{row['actual_pips']:.1f} pips ({row['reasons']})")

# Analisar EURUSD
analisa_ativo('EURUSD')
```

---

## 🔍 Interpretando "Reasons"

### Componentes de Confiança
```
VeryHighConf (≥95%)  🟢 Muito bom, operar
HighConf (90-95%)    🟢 Bom, operar
GoodConf (85-90%)    🟡 OK, com cuidado
```

### Componentes de Refinement
```
ExcelRef (≥0.8)      🟢 Árvore mudou muito para melhor
GoodRef (0.5-0.8)    🟡 Árvore ajustou bem
ModRef (<0.5)        🔴 Pouca mudança
```

### Componentes de Confluência
```
4Confluent  🟢 4+ indicadores concordam (forte!)
3Confluent  🟡 3 indicadores concordam
```

### Componentes de Padrões
```
OrderBlock  💡 Smart Money order block detectado
FVG         💡 Fair Value Gap (gap de preço)
DirChange   ↔️  Direção foi refinada
```

---

## 📈 Estratégia de Filtragem

### Apenas Sinais ENTER com Qualidade

```python
df_quality = df[(df['decision'] == 'ENTER') & 
                (df['quality_score'] >= 3.5) &
                (df['confidence_pct'] >= 90) &
                (df['result'].isin(['WIN']))]

print(f"Sinais Premium: {len(df_quality)}")
win_rate = len(df_quality[df_quality['result']=='WIN']) / len(df_quality) * 100
print(f"Win Rate Premium: {win_rate:.1f}%")
```

### Consolidar por Dia

```python
df['date'] = pd.to_datetime(df['timestamp']).dt.date
daily = df.groupby('date').agg({
    'decision': lambda x: (x == 'ENTER').sum(),
    'actual_pips': 'sum',
    'result': lambda x: (x == 'WIN').sum()
})
daily.columns = ['enters', 'pips', 'wins']
print(daily)
```

---

## 📋 Checklist de Uso

- [ ] Gerou arquivos ANALYSIS_*_ENHANCED.csv? ✅
- [ ] Abriu em Excel/Calc para visualizar?
- [ ] Rodou `enhance_backtest_results.py` após novo pipeline?
- [ ] Filtrou por `decision == ENTER`?
- [ ] Analisou `quality_score` e `confidence_pct`?
- [ ] Validou `result` (WIN/LOSS)?
- [ ] Verificou `reasons` para entender sinais?

---

## 🎯 Script Automático

Para rodar automaticamente após o pipeline:

```bash
cd /home/ubuntu/pessoal/options

# Rodar pipeline
python3 src/run_full_pipeline.py --all

# Gerar análise enhanced
python3 enhance_backtest_results.py

# Abrir primeiro arquivo
libreoffice results/ANALYSIS_EURUSD_ENHANCED.csv
```

---

## 🚀 Próximo Passo

Agora você tem tudo o que pediu:
1. ✅ Arquivo com colunas de análise (Decision, Reasons, Result, Quality)
2. ✅ Script `enhance_backtest_results.py` que gera esses arquivos
3. ✅ Fácil de abrir em Excel/Calc
4. ✅ Pronto para tomar decisões rápidas

**Rotina recomendada:**
```
1. python3 src/run_full_pipeline.py --all
2. python3 enhance_backtest_results.py
3. Abrir ANALYSIS_*_ENHANCED.csv em Excel
4. Analisar sinais + tomar decisões
```

---

*Última atualização: 2026-05-28*
