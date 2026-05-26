#!/usr/bin/env python3
"""
Análise Candle-a-Candle: Prever movimento do dia seguinte com ML
Objetivo: Entender qual indicador impacta mais na previsão
Output: Para cada candle mostrar: variação esperada, previsão, resultado real
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# =====================================================================
# 1. CARREGAR DADOS
# =====================================================================
print("=" * 80)
print("1️⃣ CARREGANDO DADOS HISTÓRICOS")
print("=" * 80)

df = pd.read_csv('/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015_processed.csv')
df['datetime'] = pd.to_datetime(df['datetime'])
df = df.sort_values('datetime').reset_index(drop=True)

print(f"✅ Carregados {len(df)} candles")
print(f"   Período: {df['datetime'].min()} → {df['datetime'].max()}")
print()

# =====================================================================
# 2. CALCULAR INDICADORES PARA CADA CANDLE
# =====================================================================
print("=" * 80)
print("2️⃣ CALCULANDO INDICADORES")
print("=" * 80)

def calcular_sma(df, col, window):
    """Calcula SMA"""
    return df[col].rolling(window=window, min_periods=1).mean()

def calcular_rsi(df, col, period=14):
    """Calcula RSI"""
    delta = df[col].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
    rs = gain / loss.replace(0, 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calcular_macd(df, col, fast=12, slow=26, signal=9):
    """Calcula MACD"""
    ema_fast = df[col].ewm(span=fast, adjust=False).mean()
    ema_slow = df[col].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calcular_atr(df, period=14):
    """Calcula ATR (Average True Range)"""
    df_copy = df.copy()
    df_copy['tr'] = np.maximum(
        df_copy['high'] - df_copy['low'],
        np.maximum(
            abs(df_copy['high'] - df_copy['close'].shift()),
            abs(df_copy['low'] - df_copy['close'].shift())
        )
    )
    atr = df_copy['tr'].rolling(window=period, min_periods=1).mean()
    return atr

def calcular_bollinger_bands(df, col, period=20, std_dev=2):
    """Calcula Bandas de Bollinger"""
    sma = df[col].rolling(window=period, min_periods=1).mean()
    std = df[col].rolling(window=period, min_periods=1).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    bb_width = upper - lower
    bb_position = (df[col] - lower) / (upper - lower)
    return upper, lower, bb_width, bb_position

def calcular_stochastic(df, period=14):
    """Calcula Stochastic Oscillator"""
    low_min = df['low'].rolling(window=period, min_periods=1).min()
    high_max = df['high'].rolling(window=period, min_periods=1).max()
    k_percent = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-9)
    d_percent = k_percent.rolling(window=3, min_periods=1).mean()
    return k_percent, d_percent

def calcular_cci(df, period=20):
    """Calcula CCI (Commodity Channel Index)"""
    tp = (df['high'] + df['low'] + df['close']) / 3
    sma_tp = tp.rolling(window=period, min_periods=1).mean()
    mad = (tp - sma_tp).abs().rolling(window=period, min_periods=1).mean()
    cci = (tp - sma_tp) / (0.015 * mad + 1e-9)
    return cci

def calcular_momentum(df, col, period=10):
    """Calcula Momentum"""
    return df[col] - df[col].shift(period)

# Calcular indicadores
print("Calculando SMA...")
df['sma_20'] = calcular_sma(df, 'close', 20)
df['sma_50'] = calcular_sma(df, 'close', 50)
df['sma_200'] = calcular_sma(df, 'close', 200)

print("Calculando RSI...")
df['rsi_14'] = calcular_rsi(df, 'close', 14)

print("Calculando MACD...")
df['macd'], df['macd_signal'], df['macd_hist'] = calcular_macd(df, 'close')

print("Calculando ATR...")
df['atr_14'] = calcular_atr(df, 14)

print("Calculando Bollinger Bands...")
df['bb_upper'], df['bb_lower'], df['bb_width'], df['bb_position'] = calcular_bollinger_bands(df, 'close', 20, 2)

print("Calculando Stochastic...")
df['stoch_k'], df['stoch_d'] = calcular_stochastic(df, 14)

print("Calculando CCI...")
df['cci_20'] = calcular_cci(df, 20)

print("Calculando Momentum...")
df['momentum_10'] = calcular_momentum(df, 'close', 10)

# Volatilidade (%) na hora
df['volatility_pct'] = ((df['high'] - df['low']) / df['close'] * 100).rolling(window=14, min_periods=1).mean()

# Relações de preço
df['price_vs_sma20'] = ((df['close'] - df['sma_20']) / df['close'] * 100)
df['price_vs_sma50'] = ((df['close'] - df['sma_50']) / df['close'] * 100)
df['price_vs_sma200'] = ((df['close'] - df['sma_200']) / df['close'] * 100)

# Close/Open range
df['co_range'] = ((df['close'] - df['open']) / df['open'] * 100)

# High/Low range
df['hl_range'] = ((df['high'] - df['low']) / df['open'] * 100)

print("✅ Indicadores calculados!")
print()

# =====================================================================
# 3. PREPARAR DADOS PARA PREVISÃO
# =====================================================================
print("=" * 80)
print("3️⃣ PREPARANDO DADOS PARA PREVISÃO")
print("=" * 80)

# Calcular próximo close (dia seguinte)
df['next_close'] = df['close'].shift(-1)
df['next_day_change'] = ((df['next_close'] - df['close']) / df['close'] * 100)

# Extrair hora do candle
df['hour'] = df['datetime'].dt.hour
df['day_of_week'] = df['datetime'].dt.dayofweek
df['month'] = df['datetime'].dt.month

# Criar dataset de features
features_cols = [
    'open', 'high', 'low', 'close',
    'sma_20', 'sma_50', 'sma_200',
    'rsi_14', 'macd', 'macd_signal', 'macd_hist',
    'atr_14', 'bb_upper', 'bb_lower', 'bb_width', 'bb_position',
    'stoch_k', 'stoch_d', 'cci_20', 'momentum_10',
    'volatility_pct', 'price_vs_sma20', 'price_vs_sma50', 'price_vs_sma200',
    'co_range', 'hl_range', 'hour', 'day_of_week', 'month'
]

# Remover linhas com NaN
df_clean = df[features_cols + ['next_day_change', 'datetime', 'next_close']].dropna().reset_index(drop=True)

print(f"✅ Dataset preparado: {len(df_clean)} candles com dados completos")
print(f"   Features: {len(features_cols)}")
print(f"   Target (next_day_change): média={df_clean['next_day_change'].mean():.4f}%, std={df_clean['next_day_change'].std():.4f}%")
print()

# =====================================================================
# 4. DIVIDIR DADOS (80/20) - MANTER ORDEM TEMPORAL
# =====================================================================
print("=" * 80)
print("4️⃣ DIVIDINDO DADOS (Treino 80% / Teste 20%)")
print("=" * 80)

split_idx = int(len(df_clean) * 0.8)
df_train = df_clean[:split_idx].copy()
df_test = df_clean[split_idx:].copy()

X_train = df_train[features_cols]
y_train = df_train['next_day_change']

X_test = df_test[features_cols]
y_test = df_test['next_day_change']

print(f"✅ Treino: {len(df_train)} candles ({split_idx} até {split_idx})")
print(f"   Teste: {len(df_test)} candles")
print()

# =====================================================================
# 5. NORMALIZAR FEATURES
# =====================================================================
print("=" * 80)
print("5️⃣ NORMALIZANDO FEATURES")
print("=" * 80)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("✅ Features normalizadas")
print()

# =====================================================================
# 6. TREINAR MODELO XGBOOST
# =====================================================================
print("=" * 80)
print("6️⃣ TREINANDO MODELO XGBOOST")
print("=" * 80)

model = xgb.XGBRegressor(
    n_estimators=200,
    max_depth=7,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    verbosity=0
)

print("Treinando...")
model.fit(X_train_scaled, y_train, verbose=False)

# Previsões
y_train_pred = model.predict(X_train_scaled)
y_test_pred = model.predict(X_test_scaled)

# Métricas
train_mae = mean_absolute_error(y_train, y_train_pred)
test_mae = mean_absolute_error(y_test, y_test_pred)
train_r2 = r2_score(y_train, y_train_pred)
test_r2 = r2_score(y_test, y_test_pred)

print(f"✅ Modelo treinado!")
print(f"   Treino:")
print(f"      MAE: {train_mae:.6f}%")
print(f"      R² Score: {train_r2:.4f}")
print(f"   Teste:")
print(f"      MAE: {test_mae:.6f}%")
print(f"      R² Score: {test_r2:.4f}")
print()

# =====================================================================
# 7. FEATURE IMPORTANCE
# =====================================================================
print("=" * 80)
print("7️⃣ IMPORTÂNCIA DOS INDICADORES")
print("=" * 80)

feature_importance = pd.DataFrame({
    'feature': features_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("Top 15 indicadores mais importantes:")
print()
for idx, row in feature_importance.head(15).iterrows():
    importance_pct = row['importance'] * 100
    bar_length = int(importance_pct / 0.5)
    bar = "█" * min(bar_length, 50)
    print(f"{row['feature']:20s} {importance_pct:6.2f}% {bar}")
print()

# =====================================================================
# 8. ANÁLISE DETALHADA DE TESTE
# =====================================================================
print("=" * 80)
print("8️⃣ ANÁLISE DETALHADA (Últimos 50 candles do teste)")
print("=" * 80)

df_resultado = df_test.copy()
df_resultado['previsao'] = y_test_pred
df_resultado['real'] = y_test.values
df_resultado['erro'] = abs(df_resultado['previsao'] - df_resultado['real'])
df_resultado['acerto'] = (np.sign(df_resultado['previsao']) == np.sign(df_resultado['real'])).astype(int)

# Resumo
print()
print("RESUMO DO TESTE:")
print("-" * 80)
print(f"Total de candles testados: {len(df_resultado)}")
print(f"Acertos de direção: {df_resultado['acerto'].sum()} ({df_resultado['acerto'].mean() * 100:.1f}%)")
print(f"Erro médio (MAE): {df_resultado['erro'].mean():.6f}%")
print(f"Erro máximo: {df_resultado['erro'].max():.6f}%")
print(f"Erro mínimo: {df_resultado['erro'].min():.6f}%")
print()

# Análise por hora
print("ACERTO POR HORA DO DIA:")
print("-" * 80)
acerto_por_hora = df_resultado.groupby('hour').agg({
    'acerto': ['sum', 'count', 'mean'],
    'real': ['mean', 'std'],
    'previsao': 'mean'
}).round(4)

for hora in sorted(df_resultado['hour'].unique()):
    dados = df_resultado[df_resultado['hour'] == hora]
    acertos = dados['acerto'].sum()
    total = len(dados)
    pct = acertos / total * 100 if total > 0 else 0
    real_media = dados['real'].mean()
    prev_media = dados['previsao'].mean()
    print(f"Hora {int(hora):02d}:00 - Acertos: {acertos}/{total} ({pct:5.1f}%) | Real: {real_media:+.4f}% | Previsão: {prev_media:+.4f}%")
print()

# =====================================================================
# 9. GERAR CSV DE SAÍDA
# =====================================================================
print("=" * 80)
print("9️⃣ GERANDO ARQUIVO DE SAÍDA")
print("=" * 80)

output_df = df_resultado[[
    'datetime', 'open', 'high', 'low', 'close', 'next_close',
    'real', 'previsao', 'erro', 'acerto',
    'sma_20', 'sma_50', 'sma_200',
    'rsi_14', 'macd', 'bb_position', 'stoch_k', 'cci_20'
]].copy()

output_df.columns = [
    'Data', 'Open', 'High', 'Low', 'Close', 'ProximoClose',
    'VariacaoReal(%)', 'PredicaoModelo(%)', 'ErroAbsoluto(%)', 'AcertoDirecao',
    'SMA20', 'SMA50', 'SMA200',
    'RSI14', 'MACD', 'BBPosition', 'StochK', 'CCI20'
]

# Salvar
timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
output_file = f'/home/ubuntu/pessoal/options/backtest_results/analise_candle_a_candle_{timestamp}.csv'
output_df.to_csv(output_file, index=False)

print(f"✅ Arquivo salvo: {output_file}")
print(f"   Linhas: {len(output_df)}")
print(f"   Colunas: {len(output_df.columns)}")
print()

# =====================================================================
# 10. MOSTRAR EXEMPLOS
# =====================================================================
print("=" * 80)
print("🔟 EXEMPLOS DE PREDIÇÕES (Últimos 10)")
print("=" * 80)
print()

for idx in range(max(0, len(output_df) - 10), len(output_df)):
    row = output_df.iloc[idx]
    status = "✅" if row['AcertoDirecao'] == 1 else "❌"
    print(f"{status} {row['Data']}")
    print(f"   Close: {row['Close']:.5f}")
    print(f"   Próximo Close: {row['ProximoClose']:.5f}")
    print(f"   Variação Real: {row['VariacaoReal(%)']:+.6f}%")
    print(f"   Predição Modelo: {row['PredicaoModelo(%)']:+.6f}%")
    print(f"   Erro: {row['ErroAbsoluto(%)']:.6f}%")
    print(f"   Indicadores: SMA200={row['SMA200']:.5f}, RSI14={row['RSI14']:.1f}, StochK={row['StochK']:.1f}")
    print()

print("=" * 80)
print("✨ ANÁLISE CONCLUÍDA!")
print("=" * 80)
