#!/usr/bin/env python3
"""
BACKTEST CHRONOLOGICAL - Mantém ordem cronológica, treina 70% inicial, prediz 30% final
Usa módulo indicators.py para cálculo de indicadores técnicos
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Importar módulo de indicadores
from indicators import calculate_all_indicators, get_model_features

def load_and_process_data(csv_file, symbol):
    """Carrega dados e calcula indicadores"""
    print(f"\n{'='*80}")
    print(f"📁 Processando {symbol}")
    print(f"{'='*80}")
    
    print(f"\n📥 Carregando {csv_file}...")
    # Arquivo tem formato: <DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>
    df = pd.read_csv(csv_file, sep='\t', skiprows=1)
    
    # Renomear colunas
    df.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'tickvol', 'vol', 'spread']
    
    # Criar timestamp
    df['timestamp'] = df['date'].astype(str) + ' ' + df['time'].astype(str)
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y.%m.%d %H:%M:%S')
    
    # Extrair data (sem hora)
    df['date_only'] = df['timestamp'].dt.date
    
    # Deixar apenas as colunas necessárias
    df = df[['timestamp', 'date_only', 'open', 'high', 'low', 'close', 'vol', 'spread']].copy()
    df.reset_index(drop=True, inplace=True)
    
    print(f"✅ {len(df)} linhas carregadas")
    print(f"   Primeira: {df.iloc[0]['timestamp']}")
    print(f"   Última: {df.iloc[-1]['timestamp']}")
    
    # Calcular indicadores
    print(f"\n📊 Calculando indicadores técnicos (módulo indicators.py)...")
    df = calculate_all_indicators(df)
    print(f"✅ Indicadores calculados")
    
    # Criar target_price: preço às 14:00 do PRÓXIMO dia
    print(f"\n⏰ Calculando target_price (preço às 14:00 do dia seguinte)...")
    
    # Próxima data para cada linha
    df['next_date'] = df['date_only'] + pd.Timedelta(days=1)
    
    # Criar índice por data para acesso rápido
    date_price_map = {}  # {date: price_at_14h}
    
    for date in df['date_only'].unique():
        # Todos os candles daquele dia
        day_data = df[df['date_only'] == date]
        
        # Encontrar próximo dia disponível
        next_date = date + pd.Timedelta(days=1)
        next_day_data = df[df['date_only'] == next_date]
        
        if len(next_day_data) > 0:
            # Encontrar timestamp mais próximo de 14:00 do próximo dia
            target_time = pd.Timestamp(next_date) + pd.Timedelta(hours=14)
            next_day_data_copy = next_day_data.copy()
            next_day_data_copy['time_diff'] = abs((next_day_data_copy['timestamp'] - target_time).dt.total_seconds())
            closest_idx = next_day_data_copy['time_diff'].idxmin()
            price_at_14h = df.loc[closest_idx, 'close']
        else:
            # Se não houver próximo dia, usar último close do dia atual
            price_at_14h = day_data['close'].iloc[-1]
        
        date_price_map[date] = price_at_14h
    
    # Aplicar target_price usando o mapa
    df['target_price'] = df['date_only'].map(date_price_map)
    
    # Remover colunas temporárias
    df.drop(['date_only', 'next_date'], axis=1, inplace=True)
    
    print(f"✅ Target_price calculado")
    print(f"   Validação: Todas as linhas do mesmo dia têm target igual? ", end="")
    # Teste rápido
    test_date = df.iloc[0]['timestamp'].date()
    same_date_rows = df[df['timestamp'].dt.date == test_date]
    all_same = (same_date_rows['target_price'] == same_date_rows['target_price'].iloc[0]).all()
    print(f"{'✅ SIM' if all_same else '❌ NÃO'}")
    
    return df

def train_models(df_train):
    """Treina XGBoost e RandomForest"""
    print(f"\n{'─'*80}")
    print(f"🤖 Treinando modelos com {len(df_train)} linhas (70% histórico)")
    print(f"{'─'*80}")
    
    # ✅ USAR FEATURES DO MÓDULO
    feature_names = get_model_features()
    
    print(f"\n📊 Features utilizadas ({len(feature_names)}):")
    print(f"   {', '.join(feature_names[:5])}...")
    
    X_train = df_train[feature_names].values
    y_train = df_train['target_price'].values
    
    # Normalizar features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Treinar XGBoost
    print("\n🔹 Treinando XGBoost...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=200, learning_rate=0.05, max_depth=7,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
        objective='reg:squarederror', verbosity=0
    )
    xgb_model.fit(X_train_scaled, y_train)
    
    y_pred_xgb = xgb_model.predict(X_train_scaled)
    mae_xgb = mean_absolute_error(y_train, y_pred_xgb)
    r2_xgb = r2_score(y_train, y_pred_xgb)
    print(f"   ✅ MAE: {mae_xgb*10000:.2f} pips, R²: {r2_xgb:.4f}")
    
    # Treinar RandomForest
    print("\n🔹 Treinando RandomForest...")
    rf_model = RandomForestRegressor(
        n_estimators=200, max_depth=15, min_samples_split=5,
        random_state=42, n_jobs=-1, verbose=0
    )
    rf_model.fit(X_train_scaled, y_train)
    
    y_pred_rf = rf_model.predict(X_train_scaled)
    mae_rf = mean_absolute_error(y_train, y_pred_rf)
    r2_rf = r2_score(y_train, y_pred_rf)
    print(f"   ✅ MAE: {mae_rf*10000:.2f} pips, R²: {r2_rf:.4f}")
    
    return xgb_model, rf_model, scaler, feature_names

def predict_on_test(df_test, xgb_model, rf_model, scaler, feature_names, symbol):
    """Faz predições no conjunto de teste (30% final)"""
    print(f"\n{'─'*80}")
    print(f"🔮 Fazendo predições nos últimos {len(df_test)} linhas (30% recente)")
    print(f"{'─'*80}")
    
    X_test = df_test[feature_names].values
    X_test_scaled = scaler.transform(X_test)
    
    # Predições individuais
    pred_xgb = xgb_model.predict(X_test_scaled)
    pred_rf = rf_model.predict(X_test_scaled)
    
    # Ensemble (média)
    pred_ensemble = (pred_xgb + pred_rf) / 2
    
    # Confiança baseada em concordância
    model_diff = np.abs(pred_xgb - pred_rf)
    max_diff = np.max(model_diff)
    confidence = 1.0 - (model_diff / (max_diff + 1e-6))
    
    # Calcular pips
    entry_prices = df_test['close'].values
    actual_prices = df_test['target_price'].values
    
    pred_pips_xgb = (pred_xgb - entry_prices) * 10000
    pred_pips_rf = (pred_rf - entry_prices) * 10000
    pred_pips_ensemble = (pred_ensemble - entry_prices) * 10000
    actual_pips = (actual_prices - entry_prices) * 10000
    error_pips = np.abs(actual_pips - pred_pips_ensemble)
    
    # Calcular métricas
    mae = mean_absolute_error(actual_prices, pred_ensemble)
    r2 = r2_score(actual_prices, pred_ensemble)
    total_pips = np.sum(actual_pips)
    wins = (actual_pips > 0).sum()
    
    print(f"\n📊 Métricas no conjunto de teste:")
    print(f"   ✅ MAE: {mae*10000:.2f} pips")
    print(f"   ✅ R²: {r2:.4f}")
    print(f"   ✅ Total Pips: {total_pips:.2f}")
    print(f"   ✅ Win Rate: {wins}/{len(df_test)} = {wins/len(df_test)*100:.2f}%")
    print(f"   ✅ Confiança Média: {np.mean(confidence)*100:.2f}%")
    
    return {
        'pred_xgb': pred_xgb,
        'pred_rf': pred_rf,
        'pred_ensemble': pred_ensemble,
        'confidence': confidence,
        'pips_xgb': pred_pips_xgb,
        'pips_rf': pred_pips_rf,
        'pips_ensemble': pred_pips_ensemble,
        'actual_pips': actual_pips,
        'error_pips': error_pips
    }

def create_output_csv(df_full, df_train_idx, predictions, output_file, symbol):
    """Cria arquivo de saída com ordem cronológica mantida e predições apenas nos 30% finais"""
    print(f"\n💾 Gerando arquivo de saída...")
    
    df_output = df_full.copy()
    
    # Inicializar colunas com NaN (vão ser preenchidas apenas nas linhas de teste)
    df_output['predicted_price_xgb'] = np.nan
    df_output['predicted_price_rf'] = np.nan
    df_output['predicted_price_ensemble'] = np.nan
    df_output['confidence'] = np.nan
    df_output['confidence_pct'] = np.nan
    df_output['predicted_pips_ensemble'] = np.nan
    df_output['actual_pips'] = np.nan
    df_output['error_pips'] = np.nan
    
    # Obter índices de teste (últimos 30%)
    test_start_idx = len(df_train_idx)
    test_indices = np.arange(test_start_idx, len(df_output))
    
    # Preencher predições nas linhas de teste
    df_output.loc[test_indices, 'predicted_price_xgb'] = predictions['pred_xgb']
    df_output.loc[test_indices, 'predicted_price_rf'] = predictions['pred_rf']
    df_output.loc[test_indices, 'predicted_price_ensemble'] = predictions['pred_ensemble']
    df_output.loc[test_indices, 'confidence'] = predictions['confidence']
    df_output.loc[test_indices, 'confidence_pct'] = predictions['confidence'] * 100
    df_output.loc[test_indices, 'predicted_pips_ensemble'] = predictions['pips_ensemble']
    df_output.loc[test_indices, 'actual_pips'] = predictions['actual_pips']
    df_output.loc[test_indices, 'error_pips'] = predictions['error_pips']
    
    # Coluna de preço real (target)
    df_output['actual_price'] = df_output['target_price']
    
    # Selecionar colunas para saída
    output_cols = [
        'timestamp',
        'close',  # Entry price
        # Indicadores básicos
        'rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum',
        # SD e Bollinger Bands
        'sd', 'bb_upper', 'bb_lower', 'bb_width',
        # SMC - Smart Money Concepts
        'smc_support', 'smc_resistance',
        # Indicadores binários clássicos
        'price_above_sma20', 'price_above_sma50', 'rsi_oversold', 'rsi_overbought',
        'macd_positive', 'momentum_positive',
        # Indicadores binários novos (Bollinger + SMC)
        'price_above_bb_upper', 'price_below_bb_lower', 'smc_order_block', 'smc_fvg',
        # Predições
        'predicted_price_xgb',
        'predicted_price_rf',
        'predicted_price_ensemble',
        # Confiança
        'confidence',
        'confidence_pct',
        # Resultado
        'actual_price',
        'predicted_pips_ensemble',
        'actual_pips',
        'error_pips'
    ]
    
    # Manter apenas colunas que existem no dataframe
    output_cols = [col for col in output_cols if col in df_output.columns]
    
    df_output = df_output[output_cols].copy()
    df_output.to_csv(output_file, index=False)
    
    # Contar linhas com e sem predições
    with_pred = df_output['predicted_price_ensemble'].notna().sum()
    without_pred = df_output['predicted_price_ensemble'].isna().sum()
    
    print(f"✅ {output_file}")
    print(f"   Total linhas: {len(df_output)}")
    print(f"   Com predições: {with_pred} (30% - teste)")
    print(f"   Sem predições: {without_pred} (70% - treino)")
    print(f"   Tamanho: {df_output.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
    
    return df_output

def main():
    print("\n" + "="*80)
    print("🚀 BACKTEST CHRONOLOGICAL - Mantém Ordem + Predições")
    print("="*80)
    
    # Processar EURUSD
    print("\n\n" + "="*80)
    print("EURUSD")
    print("="*80)
    
    df_eurusd = load_and_process_data(
        '/home/ubuntu/pessoal/options/data/EURUSD_M15_202401012200_202605222015.csv',
        'EURUSD'
    )
    
    # Split temporal 70/30
    split_idx = int(len(df_eurusd) * 0.70)
    df_eurusd_train = df_eurusd.iloc[:split_idx].copy()
    df_eurusd_test = df_eurusd.iloc[split_idx:].copy()
    
    print(f"\n✅ Split temporal:")
    print(f"   Treino: {len(df_eurusd_train)} linhas (70%)")
    print(f"   Teste: {len(df_eurusd_test)} linhas (30%)")
    
    xgb_eurusd, rf_eurusd, scaler_eurusd, features = train_models(df_eurusd_train)
    pred_eurusd = predict_on_test(df_eurusd_test, xgb_eurusd, rf_eurusd, scaler_eurusd, features, 'EURUSD')
    
    # Manter índices de treino para criar output completo
    train_indices_eurusd = np.arange(split_idx)
    
    df_eurusd_output = create_output_csv(
        df_eurusd,
        train_indices_eurusd,
        pred_eurusd,
        '/home/ubuntu/pessoal/options/results/backtest_EURUSD_chronological.csv',
        'EURUSD'
    )
    
    # Processar GBPUSD
    print("\n\n" + "="*80)
    print("GBPUSD")
    print("="*80)
    
    df_gbpusd = load_and_process_data(
        '/home/ubuntu/pessoal/options/data/GBPUSD_M15_202401012200_202605222015.csv',
        'GBPUSD'
    )
    
    # Split temporal 70/30
    split_idx = int(len(df_gbpusd) * 0.70)
    df_gbpusd_train = df_gbpusd.iloc[:split_idx].copy()
    df_gbpusd_test = df_gbpusd.iloc[split_idx:].copy()
    
    print(f"\n✅ Split temporal:")
    print(f"   Treino: {len(df_gbpusd_train)} linhas (70%)")
    print(f"   Teste: {len(df_gbpusd_test)} linhas (30%)")
    
    xgb_gbpusd, rf_gbpusd, scaler_gbpusd, features = train_models(df_gbpusd_train)
    pred_gbpusd = predict_on_test(df_gbpusd_test, xgb_gbpusd, rf_gbpusd, scaler_gbpusd, features, 'GBPUSD')
    
    # Manter índices de treino para criar output completo
    train_indices_gbpusd = np.arange(split_idx)
    
    df_gbpusd_output = create_output_csv(
        df_gbpusd,
        train_indices_gbpusd,
        pred_gbpusd,
        '/home/ubuntu/pessoal/options/results/backtest_GBPUSD_chronological.csv',
        'GBPUSD'
    )
    
    print("\n\n" + "="*80)
    print("✅ BACKTEST CHRONOLOGICAL COMPLETO")
    print("="*80)
    print(f"""
Arquivos gerados:
  📊 /home/ubuntu/pessoal/options/results/backtest_EURUSD_chronological.csv
  📊 /home/ubuntu/pessoal/options/results/backtest_GBPUSD_chronological.csv

Colunas de saída (22 total):
  1. timestamp
  2-13. Indicadores (rsi, sma20, sma50, macd, atr, momentum + binários)
  14. predicted_price_xgb
  15. predicted_price_rf
  16. predicted_price_ensemble
  17. confidence
  18. confidence_pct
  19. actual_price (D+1 14:00)
  20. predicted_pips_ensemble
  21. actual_pips
  22. error_pips

⚠️ IMPORTANTE: Apenas últimas 30% de cada arquivo contêm predições (conjunto de teste)
    """)

if __name__ == '__main__':
    main()
