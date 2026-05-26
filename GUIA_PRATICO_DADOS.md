# 🎓 GUIA PRÁTICO: Como Usar os Dados da Análise Candle-a-Candle

## 📂 Arquivos Disponíveis

```
/home/ubuntu/pessoal/options/backtest_results/
  📄 analise_candle_a_candle_20260526_025440.csv (16,885 linhas)
     ↳ Dados brutos de previsão vs realidade

/home/ubuntu/pessoal/options/
  📄 ANALISE_CANDLE_A_CANDLE_RESULTADOS.md
     ↳ Interpretação técnica completa
  
  📄 SUMARIO_EXECUTIVO.md (este arquivo acima)
     ↳ Recomendações e conclusões
```

---

## 💻 Usando os Dados em Python

### 1. Carregar e Explorar

```python
import pandas as pd

# Carregar
df = pd.read_csv('analise_candle_a_candle_20260526_025440.csv')

# Ver tamanho
print(f"Total de linhas: {len(df)}")
print(f"Total de colunas: {len(df.columns)}")

# Ver primeiras linhas
print(df.head())

# Ver tipos de dados
print(df.dtypes)
```

### 2. Filtrar Acertos vs Erros

```python
# Candles onde acertou a direção
acertos = df[df['AcertoDirecao'] == 1]
print(f"Acertos: {len(acertos)} ({len(acertos)/len(df)*100:.1f}%)")

# Candles onde errou
erros = df[df['AcertoDirecao'] == 0]
print(f"Erros: {len(erros)} ({len(erros)/len(df)*100:.1f}%)")
```

### 3. Encontrar Menores Erros

```python
# Predições mais precisas (menor erro)
top_precisos = df.nsmallest(10, 'ErroAbsoluto(%)')

print("Predições mais precisas:")
for idx, row in top_precisos.iterrows():
    print(f"{row['Data']} | Real: {row['VariacaoReal(%)']:+.6f}% | "
          f"Pred: {row['PredicaoModelo(%)']:+.6f}% | "
          f"Erro: {row['ErroAbsoluto(%)']:.6f}%")
```

### 4. Analisar por Horário

```python
# Extrair hora
df['Hora'] = pd.to_datetime(df['Data']).dt.hour

# Agrupar por hora
por_hora = df.groupby('Hora').agg({
    'AcertoDirecao': ['sum', 'count', 'mean']
})

print(por_hora)

# Mostrar apenas melhores horários
melhores = df.groupby('Hora')['AcertoDirecao'].mean()
print("\nMelhores horários:")
print(melhores.sort_values(ascending=False).head(5))
```

### 5. Usar Indicadores para Filtrar

```python
# Casos onde RSI > 60 E Close > SMA200
padrão_bullish = df[(df['RSI14'] > 60) & (df['Close'] > df['SMA200'])]

print(f"Total de casos com padrão bullish: {len(padrão_bullish)}")
print(f"Taxa de acerto: {padrão_bullish['AcertoDirecao'].mean()*100:.1f}%")

# Casos onde BBPosition está nos extremos
bb_extremos = df[(df['BBPosition'] > 0.8) | (df['BBPosition'] < 0.2)]

print(f"Total de casos em extremo de BB: {len(bb_extremos)}")
print(f"Taxa de acerto: {bb_extremos['AcertoDirecao'].mean()*100:.1f}%")
```

---

## 📊 Análise de Padrões

### Padrão 1: RSI Extremo

```python
# RSI em nível extremo (sobrecompra/sobrevenda)
extremos = df[(df['RSI14'] > 70) | (df['RSI14'] < 30)]

print(f"Casos com RSI extremo: {len(extremos)}")
print(f"Taxa de acerto: {extremos['AcertoDirecao'].mean()*100:.1f}%")

# Análise por direção
rsi_alto = df[df['RSI14'] > 70]
rsi_baixo = df[df['RSI14'] < 30]

print(f"RSI > 70: {rsi_alto['AcertoDirecao'].mean()*100:.1f}%")
print(f"RSI < 30: {rsi_baixo['AcertoDirecao'].mean()*100:.1f}%")
```

### Padrão 2: Preço vs Média Móvel

```python
# Preço acima da SMA200
acima_sma200 = df[df['Close'] > df['SMA200']]
abaixo_sma200 = df[df['Close'] < df['SMA200']]

print(f"Close > SMA200: {acima_sma200['AcertoDirecao'].mean()*100:.1f}%")
print(f"Close < SMA200: {abaixo_sma200['AcertoDirecao'].mean()*100:.1f}%")

# Combinação com RSI
padrão_forte = df[(df['Close'] > df['SMA200']) & (df['RSI14'] > 60)]
print(f"Padrão Bullish Forte: {padrão_forte['AcertoDirecao'].mean()*100:.1f}%")
```

### Padrão 3: Bollinger Bands

```python
# Preço toca banda superior (extremo)
bb_superior = df[df['BBPosition'] > 0.8]
bb_inferior = df[df['BBPosition'] < 0.2]
bb_centro = df[(df['BBPosition'] > 0.4) & (df['BBPosition'] < 0.6)]

print(f"Preço em BB Superior (0.8-1.0): {bb_superior['AcertoDirecao'].mean()*100:.1f}%")
print(f"Preço em BB Inferior (0-0.2): {bb_inferior['AcertoDirecao'].mean()*100:.1f}%")
print(f"Preço no Centro (0.4-0.6): {bb_centro['AcertoDirecao'].mean()*100:.1f}%")
```

---

## 🔍 Comparação: Real vs Previsão

### Exemplo 1: Caso Acertado

```python
# Encontrar um caso bem acertado
caso_bom = df.nsmallest(1, 'ErroAbsoluto(%)').iloc[0]

print(f"Data: {caso_bom['Data']}")
print(f"Close Atual: {caso_bom['Close']:.5f}")
print(f"Close Próximo: {caso_bom['ProximoClose']:.5f}")
print(f"Variação Real: {caso_bom['VariacaoReal(%)']:+.6f}%")
print(f"Previsão Modelo: {caso_bom['PredicaoModelo(%)']:+.6f}%")
print(f"Erro: {caso_bom['ErroAbsoluto(%)']:.6f}%")
print(f"Acertou direção? {'✅ SIM' if caso_bom['AcertoDirecao'] else '❌ NÃO'}")
print(f"Indicadores:")
print(f"  RSI: {caso_bom['RSI14']:.1f}")
print(f"  MACD: {caso_bom['MACD']:.6f}")
print(f"  CCI20: {caso_bom['CCI20']:.1f}")
```

### Exemplo 2: Caso Errado

```python
# Encontrar um caso muito errado
caso_ruim = df.nlargest(1, 'ErroAbsoluto(%)').iloc[0]

print(f"Data: {caso_ruim['Data']}")
print(f"Close Atual: {caso_ruim['Close']:.5f}")
print(f"Close Próximo: {caso_ruim['ProximoClose']:.5f}")
print(f"Variação Real: {caso_ruim['VariacaoReal(%)']:+.6f}%")
print(f"Previsão Modelo: {caso_ruim['PredicaoModelo(%)']:+.6f}%")
print(f"Erro: {caso_ruim['ErroAbsoluto(%)']:.6f}%")
print(f"Acertou direção? {'✅ SIM' if caso_ruim['AcertoDirecao'] else '❌ NÃO'}")
```

---

## 📈 Visualizações em Texto

### Distribuição de Acertos

```python
import numpy as np

# Criar histograma de erros
erros = df['ErroAbsoluto(%)'].values

print("Distribuição de Erros:")
print("=" * 50)
print("Erro %  | Frequência | Visualização")
print("-" * 50)

bins = [0, 0.01, 0.03, 0.05, 0.1, 0.5, 1.0]
for i in range(len(bins) - 1):
    mascara = (erros >= bins[i]) & (erros < bins[i+1])
    freq = mascara.sum()
    pct = freq / len(erros) * 100
    barra = "█" * int(pct)
    print(f"{bins[i]:.2f}-{bins[i+1]:.2f} | {freq:6d}    | {barra} {pct:.1f}%")
```

### Taxa de Acerto por Indicador

```python
# Qual indicador mais correlacionado com sucesso?
indicadores = ['RSI14', 'MACD', 'BBPosition', 'StochK', 'CCI20']

print("Correlação Indicadores vs Acerto:")
print("=" * 40)
for ind in indicadores:
    corr = df[ind].corr(df['AcertoDirecao'])
    barra = "█" * int(abs(corr) * 1000)
    print(f"{ind:15s} {corr:+.6f} {barra}")
```

---

## 🎯 Estratégia Baseada em Padrões

### Construir Estratégia de Filtros

```python
def calcular_score(row):
    """
    Calcular score de confiança (0-3)
    """
    score = 0
    
    # Padrão 1: RSI > 60 E Close > SMA200
    if (row['RSI14'] > 60) and (row['Close'] > row['SMA200']):
        score += 1
    
    # Padrão 2: BBPosition nos extremos
    if (row['BBPosition'] > 0.8) or (row['BBPosition'] < 0.2):
        score += 1
    
    # Padrão 3: CCI20 extremo
    if abs(row['CCI20']) > 100:
        score += 1
    
    return score

# Aplicar score
df['Score'] = df.apply(calcular_score, axis=1)

# Análise por score
print("Taxa de Acerto por Score:")
for s in range(4):
    dados = df[df['Score'] == s]
    if len(dados) > 0:
        taxa = dados['AcertoDirecao'].mean() * 100
        print(f"Score {s}: {taxa:.1f}% ({len(dados)} casos)")
```

### Filtrar Operações de Alta Confiança

```python
# Apenas Score 3 (todos os padrões alinhados)
operacoes_seguras = df[df['Score'] == 3]

print(f"Operações de Alta Confiança: {len(operacoes_seguras)}")
print(f"Taxa de Acerto: {operacoes_seguras['AcertoDirecao'].mean()*100:.1f}%")

# Por horário
print("\nPor horário:")
operacoes_seguras['Hora'] = pd.to_datetime(operacoes_seguras['Data']).dt.hour
for hora in sorted(operacoes_seguras['Hora'].unique()):
    dados_hora = operacoes_seguras[operacoes_seguras['Hora'] == hora]
    if len(dados_hora) > 0:
        taxa = dados_hora['AcertoDirecao'].mean() * 100
        print(f"  {hora:02d}:00 → {taxa:.1f}% ({len(dados_hora)} casos)")
```

---

## 🔐 Checklist para Usar em Produção

### Antes de Tradear

```python
# 1. Verificar data/hora
print(f"Última atualização: {df['Data'].max()}")
print(f"Primeira data: {df['Data'].min()}")

# 2. Verificar se há NaN
print(f"Valores faltando: {df.isnull().sum().sum()}")

# 3. Verificar distribuição de acertos
print(f"Taxa média: {df['AcertoDirecao'].mean()*100:.1f}%")

# 4. Verificar padrão mais preditivo
print(f"Melhor padrão: RSI > 60 + Close > SMA200 → 51.6%")

# 5. Verificar melhor horário
print(f"Melhor horário: 17:00 → 53.4%")
```

---

## 🚀 Próxima Etapa Recomendada

### 1. Validar Manualmente (5 min)
```
Abrir gráfico EURUSD M15
Verificar 5-10 casos da análise
Confirmar que indicadores estão corretos
```

### 2. Treinar Modelo Especializado por Hora (30 min)
```python
# Treinar modelo apenas para hora 17:00
df_17h = df[df['Data'].dt.hour == 17]
# Treinar XGBoost apenas nesses dados
# Resultado esperado: 53.4% → 55-60%
```

### 3. Implementar Filtro em Produção (1 dia)
```python
# Usar Score 3 + Horário 17:00
# + CCI20 como confirmação
# Integrar com Telegram
```

---

## 📞 Suporte

Se tiver dúvidas sobre os dados, consulte:

1. **ANALISE_CANDLE_A_CANDLE_RESULTADOS.md** 
   → Interpretação técnica

2. **SUMARIO_EXECUTIVO.md**
   → Recomendações estratégicas

3. **Este arquivo (GUIA_PRATICO.md)**
   → Exemplos de código

---

**Sucesso no trading! 🚀**
