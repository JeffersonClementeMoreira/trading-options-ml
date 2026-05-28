#!/usr/bin/env python3
"""
BACKTEST CHRONOLOGICAL - Mantém ordem cronológica, treina 70% inicial, prediz 30% final
Usa módulo indicators.py para cálculo de indicadores técnicos
ENHANCED: Decision Tree Refiner para melhorar acerto de direção
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Importar módulos
from indicators import calculate_all_indicators, get_model_features
from decision_tree_refiner import DirectionRefinementTree, build_direction_features

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

def refine_predictions_with_decision_tree(df_test, predictions):
    """
    Refina predições de direção usando Decision Tree.
    
    XGBoost/RF prediz preço → Árvore refina DIREÇÃO com indicadores técnicos
    """
    print(f"\n{'─'*80}")
    print(f"🌳 Refinando predições com Árvore de Decisão")
    print(f"{'─'*80}")
    
    try:
        # Criar refiner
        tree_refiner = DirectionRefinementTree(max_depth=7, min_samples_leaf=50)
        
        # Labels: direção real (1 = up, 0 = down)
        direction_labels = (df_test['target_price'] > df_test['close']).astype(int)
        
        # Confiança do ensemble (usar como feature)
        confidence_scores = predictions['confidence']
        
        # Treinar árvore
        print(f"\n   Treinando árvore com {len(df_test)} samples...")
        importance = tree_refiner.train(df_test, direction_labels, confidence_scores)
        
        # Refinar predições
        refined_directions, refinement_scores = tree_refiner.predict_refined_direction(
            df_test,
            predictions['pred_ensemble'],
            confidence_scores
        )
        
        # Calcular direção bruta do ensemble
        ensemble_direction = (predictions['pred_ensemble'] > df_test['close'].values).astype(int)
        
        # Contar mudanças
        changes = (refined_directions != ensemble_direction).sum()
        
        print(f"   ✅ Árvore refinada!")
        print(f"   📊 Direções alteradas: {changes}/{len(refined_directions)} ({changes/len(refined_directions)*100:.1f}%)")
        
        # Calcular novo win rate com direções refinadas
        refined_pips = np.where(
            refined_directions == 1,
            predictions['actual_pips'],
            -predictions['actual_pips']
        )
        refined_wins = (refined_pips > 0).sum()
        refined_win_rate = refined_wins / len(refined_directions) * 100
        
        print(f"   📈 Win rate refinado: {refined_wins}/{len(refined_directions)} = {refined_win_rate:.2f}%")
        
        original_wins = (predictions['actual_pips'] > 0).sum()
        improvement = refined_win_rate - (original_wins / len(refined_directions) * 100)
        print(f"   ⬆️  Melhoria: {improvement:+.2f}%")
        
        return {
            'refined_directions': refined_directions,
            'refinement_scores': refinement_scores,
            'tree_refiner': tree_refiner,
            'importance': importance
        }
    
    except Exception as e:
        print(f"   ⚠️  Erro ao refinar: {e}")
        return {
            'refined_directions': (predictions['pred_ensemble'] > df_test['close'].values).astype(int),
            'refinement_scores': predictions['confidence'],
            'tree_refiner': None,
            'importance': pd.DataFrame()
        }

def calculate_confluence_score(df, window=5):
    """Calcula confluence score (0-5) para cada linha usando histórico de predições"""
    confluence_scores = []
    
    for i in range(len(df)):
        if i < window - 1 or pd.isna(df.iloc[i]['predicted_pips_ensemble']):
            confluence_scores.append(0)
        else:
            # Ver últimos N candles (inclusive este)
            window_start = i - window + 1
            window_end = i + 1
            window_data = df.iloc[window_start:window_end]
            
            # Contar concordâncias na direção
            directions = []
            for idx, row in window_data.iterrows():
                if pd.notna(row['predicted_pips_ensemble']):
                    # 1 se bullish (pips > 0), -1 se bearish
                    directions.append(1 if row['predicted_pips_ensemble'] > 0 else -1)
            
            if len(directions) > 0:
                consensus = abs(sum(directions))  # Quantos concordam (0-5)
                confluence_scores.append(int(consensus))
            else:
                confluence_scores.append(0)
    
    return confluence_scores


def apply_signal_filters(df):
    """Aplica os 3 filtros e marca signal_status"""
    
    # Inicializar colunas
    df['confluence_score'] = calculate_confluence_score(df)
    df['confluence_bonus_pct'] = 0.0
    df['confidence_base'] = df['confidence_pct'].copy()
    df['confidence_with_bonus_pct'] = df['confidence_pct'].copy()
    df['signal_status'] = 'NO_PREDICTION'
    
    # Para linhas com predição
    has_pred = df['predicted_pips_ensemble'].notna()
    
    # Filtro 1: Confidence >= 90%
    f1 = (df['confidence_pct'] >= 90) & has_pred
    
    # Filtro 2: Confluence >= 3
    f2 = (df['confluence_score'] >= 3) & has_pred
    
    # Aplicar bonus se ambos os filtros passam
    both_filters = f1 & f2
    df.loc[both_filters, 'confluence_bonus_pct'] = 15.0
    df.loc[both_filters, 'confidence_with_bonus_pct'] = df.loc[both_filters, 'confidence_pct'] * (1 + 0.15)
    
    # Marcar como FILTERED se passou nos filtros
    df.loc[both_filters, 'signal_status'] = 'FILTERED'
    
    # Marcar como SEND apenas o primeiro de cada dia que passou nos filtros
    df['date'] = df['timestamp'].dt.date
    
    for date in df['date'].unique():
        day_data_idx = df[df['date'] == date].index
        day_filtered = df.loc[day_data_idx][df.loc[day_data_idx, 'signal_status'] == 'FILTERED']
        
        if len(day_filtered) > 0:
            # Marcar apenas o PRIMEIRO
            first_idx = day_filtered.index[0]
            df.loc[first_idx, 'signal_status'] = 'SEND'
    
    df.drop('date', axis=1, inplace=True)
    
    return df


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
    
    # ========================================================================
    # APLICAR FILTROS DE SINAL
    # ========================================================================
    df_output = apply_signal_filters(df_output)
    
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
        # Confiança (base e com bonus)
        'confidence',
        'confidence_pct',
        'confidence_base',
        'confluence_score',
        'confluence_bonus_pct',
        'confidence_with_bonus_pct',
        # Resultado
        'actual_price',
        'predicted_pips_ensemble',
        'actual_pips',
        'error_pips',
        # Status do sinal
        'signal_status'
    ]
    
    # Manter apenas colunas que existem no dataframe
    output_cols = [col for col in output_cols if col in df_output.columns]
    
    df_output = df_output[output_cols].copy()
    df_output.to_csv(output_file, index=False)
    
    # Contar linhas com e sem predições
    with_pred = df_output['predicted_price_ensemble'].notna().sum()
    without_pred = df_output['predicted_price_ensemble'].isna().sum()
    
    # Contar sinais SEND e FILTERED
    sends = (df_output['signal_status'] == 'SEND').sum()
    filtered = (df_output['signal_status'] == 'FILTERED').sum()
    no_pred = (df_output['signal_status'] == 'NO_PREDICTION').sum()
    
    print(f"✅ {output_file}")
    print(f"   Total linhas: {len(df_output)}")
    print(f"   Com predições: {with_pred} (30% - teste)")
    print(f"   Sem predições: {without_pred} (70% - treino)")
    print(f"\n   📊 Status de Sinais (nas linhas com predição):")
    print(f"   - SEND: {sends} sinais (será enviado para Telegram)")
    print(f"   - FILTERED: {filtered} sinais (passou nos filtros, mas não é o primeiro do dia)")
    print(f"   - NO_PREDICTION: {no_pred} (sem predição)")
    print(f"\n   Tamanho: {df_output.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
    
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
    
    # ========================================================================
    # 🌳 REFINAR COM DECISION TREE
    # ========================================================================
    refinement_eurusd = refine_predictions_with_decision_tree(df_eurusd_test, pred_eurusd)
    pred_eurusd['refined_directions'] = refinement_eurusd['refined_directions']
    pred_eurusd['refinement_scores'] = refinement_eurusd['refinement_scores']
    
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

✨ Novas colunas com filtros de sinal:
  1. confidence_base - Confiança sem bonus
  2. confluence_score - Score de confluência (0-5)
  3. confluence_bonus_pct - Bonus de 15% se confluence >= 3
  4. confidence_with_bonus_pct - Confiança final com bonus
  5. signal_status - SEND / FILTERED / NO_PREDICTION

📊 Colunas completas:
  Indicadores: timestamp, close, rsi, sma20, sma50, macd, atr, momentum, sd, bb_*, smc_*
  Predições: predicted_price_xgb, predicted_price_rf, predicted_price_ensemble
  Confiança: confidence_pct, confidence_base, confluence_score, confluence_bonus_pct, confidence_with_bonus_pct
  Resultado: actual_price, predicted_pips_ensemble, actual_pips, error_pips
  Status: signal_status

⚠️ IMPORTANTE: 
  • Últimas 30% contêm predições e status de sinal
  • Primeiras 70% têm signal_status = NO_PREDICTION
  • Apenas 1 SEND por dia (primeiro que passa nos filtros)
  • SEND = enviado para Telegram | FILTERED = passou filtros mas não é o primeiro
    """)

if __name__ == '__main__':
    main()
