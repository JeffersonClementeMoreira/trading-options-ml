#!/usr/bin/env python3
"""
XGBoost Feature Selector
Identifica quais indicadores são mais preditivos para sinais vencedores
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import pickle
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════════════════

class FeatureEngineer:
    """Calcula indicadores técnicos para feature engineering"""
    
    @staticmethod
    def calculate_rsi(series, period=14):
        """Relative Strength Index"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-8)
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def calculate_macd(series, fast=12, slow=26, signal_period=9):
        """MACD - Moving Average Convergence Divergence"""
        ema_fast = series.ewm(span=fast).mean()
        ema_slow = series.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period).mean()
        histogram = macd - signal
        return macd, signal, histogram
    
    @staticmethod
    def calculate_bollinger_bands(series, period=20, num_std=2):
        """Bollinger Bands"""
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        bb_position = (series - lower) / (upper - lower + 1e-8)
        return upper, sma, lower, bb_position
    
    @staticmethod
    def calculate_atr_ratio(high, low, close, period=14):
        """ATR / Close ratio (volatility relative to price)"""
        tr = pd.concat([
            high - low,
            abs(high - close.shift(1)),
            abs(low - close.shift(1))
        ], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr / (close + 1e-8)
    
    @staticmethod
    def calculate_momentum(series, period=10):
        """Price momentum"""
        return series.pct_change(period)
    
    @staticmethod
    def calculate_ema(series, period):
        """Exponential Moving Average"""
        return series.ewm(span=period).mean()
    
    @staticmethod
    def calculate_sma(series, period):
        """Simple Moving Average"""
        return series.rolling(window=period).mean()
    
    @staticmethod
    def calculate_obv(close, volume):
        """On-Balance Volume"""
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv / (close * 100 + 1e-8)  # Normalize
    
    @staticmethod
    def calculate_roc(series, period=12):
        """Rate of Change"""
        return (series - series.shift(period)) / (series.shift(period) + 1e-8) * 100
    
    @staticmethod
    def calculate_stochastic(high, low, close, period=14):
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-8)
        d_percent = k_percent.rolling(window=3).mean()
        return k_percent, d_percent
    
    def engineer_features(self, df):
        """Calcular todos os indicadores"""
        df = df.copy()
        
        # Indicadores de tendência
        df['sma_20'] = self.calculate_sma(df['close'], 20)
        df['sma_50'] = self.calculate_sma(df['close'], 50)
        df['ema_12'] = self.calculate_ema(df['close'], 12)
        df['ema_26'] = self.calculate_ema(df['close'], 26)
        df['sma_trend'] = (df['sma_20'] - df['sma_50']) / df['close']
        
        # Momentum
        df['rsi'] = self.calculate_rsi(df['close'])
        df['momentum'] = self.calculate_momentum(df['close'])
        df['roc'] = self.calculate_roc(df['close'])
        
        # MACD
        macd, signal, histogram = self.calculate_macd(df['close'])
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_histogram'] = histogram
        
        # Bollinger Bands
        upper, middle, lower, bb_pos = self.calculate_bollinger_bands(df['close'])
        df['bb_position'] = bb_pos
        df['bb_width'] = (upper - lower) / (middle + 1e-8)
        
        # Volatilidade
        df['atr_ratio'] = self.calculate_atr_ratio(df['high'], df['low'], df['close'])
        df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        df['close_body_ratio'] = abs(df['close'] - df['open']) / (df['high'] - df['low'] + 1e-8)
        
        # Stochastic
        k_stoch, d_stoch = self.calculate_stochastic(df['high'], df['low'], df['close'])
        df['stoch_k'] = k_stoch
        df['stoch_d'] = d_stoch
        
        # Padrões de candle
        df['is_bullish'] = (df['close'] > df['open']).astype(int)
        df['upper_wick'] = (df['high'] - df[['open', 'close']].max(axis=1)) / (df['high'] - df['low'] + 1e-8)
        df['lower_wick'] = (df[['open', 'close']].min(axis=1) - df['low']) / (df['high'] - df['low'] + 1e-8)
        
        # Price position
        df['price_to_high_20'] = (df['close'] - df['close'].rolling(20).min()) / (df['close'].rolling(20).max() - df['close'].rolling(20).min() + 1e-8)
        
        return df


def train_xgboost_selector(csv_file, symbol='GBPUSD'):
    """Treinar XGBoost para selecionar melhores sinais"""
    
    print(f"\n{'='*100}")
    print(f"🤖 TREINANDO XGBOOST PARA {symbol}")
    print(f"{'='*100}\n")
    
    # Load data
    print(f"⏳ Carregando {csv_file}...")
    df = pd.read_csv(csv_file)
    print(f"✅ {len(df):,} candles carregados\n")
    
    # Engineer features
    print(f"🔧 Calculando indicadores técnicos...")
    engineer = FeatureEngineer()
    df = engineer.engineer_features(df)
    print(f"✅ {len([c for c in df.columns if c not in ['datetime', 'open', 'high', 'low', 'close']])} indicadores calculados\n")
    
    # Preparar data
    print(f"📊 Preparando dataset...")
    
    # Target: 1 se WIN, 0 se LOSS
    df['target'] = df['result'].str.contains('WIN', na=False).astype(int)
    
    # Filtrar apenas sinais (remover HOLD)
    df_signals = df[df['signal'] != 'HOLD'].copy()
    print(f"   Total de sinais: {len(df_signals)}")
    print(f"   ├─ WINs: {df_signals['target'].sum()}")
    print(f"   └─ LOSSes: {(1 - df_signals['target']).sum()}\n")
    
    # Features para treino
    exclude_cols = ['datetime', 'open', 'high', 'low', 'close', 'signal', 'entry_price', 
                    'exit_price', 'exit_time', 'movement_pct', 'result', 'target']
    feature_cols = [c for c in df_signals.columns if c not in exclude_cols]
    
    # Converter regime (string) para numérico
    regime_map = {'RANGE': 0, 'UP': 1, 'DOWN': -1}
    df_signals['regime'] = df_signals['regime'].map(regime_map).fillna(0)
    
    print(f"📋 Features ({len(feature_cols)}):")
    for i, col in enumerate(feature_cols, 1):
        print(f"   {i:2d}. {col}")
    print()
    
    # Remove NaN
    X = df_signals[feature_cols].fillna(0)
    y = df_signals['target']
    
    # Split: primeiros 80% treino, últimos 20% validação
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    print(f"📚 Split:")
    print(f"   Train: {len(X_train)} ({len(X_train)/len(X)*100:.1f}%)")
    print(f"   Test: {len(X_test)} ({len(X_test)/len(X)*100:.1f}%)\n")
    
    # Treinar XGBoost
    print(f"🚀 Treinando modelo...")
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train, verbose=False)
    
    # Avaliar
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"✅ Treinamento completo!\n")
    print(f"📈 Acurácia:")
    print(f"   Train: {train_score*100:.2f}%")
    print(f"   Test: {test_score*100:.2f}%\n")
    
    # Feature importance
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"⭐ TOP 15 FEATURES MAIS IMPORTANTES")
    print(f"{'─'*100}\n")
    for idx, row in importance.head(15).iterrows():
        bar = '█' * int(row['importance'] * 500)
        print(f"{row['feature']:20s} {row['importance']:8.6f} {bar}")
    
    print(f"\n{'─'*100}\n")
    
    # Predictions
    y_pred_proba = model.predict_proba(X)[:, 1]
    df_signals['win_probability'] = y_pred_proba
    
    print(f"🎯 ANÁLISE DE SINAIS")
    print(f"{'─'*100}\n")
    
    # Sinais de HIGH probability (>70%)
    high_prob = df_signals[df_signals['win_probability'] > 0.7]
    print(f"🟢 HIGH PROBABILITY (>70%): {len(high_prob)} sinais")
    if len(high_prob) > 0:
        actual_wr_high = high_prob['target'].sum() / len(high_prob) * 100
        print(f"   Actual Win Rate: {actual_wr_high:.2f}% ({int(high_prob['target'].sum())} wins)\n")
    
    # Sinais de MEDIUM probability (50-70%)
    med_prob = df_signals[(df_signals['win_probability'] > 0.5) & (df_signals['win_probability'] <= 0.7)]
    print(f"🟡 MEDIUM PROBABILITY (50-70%): {len(med_prob)} sinais")
    if len(med_prob) > 0:
        actual_wr_med = med_prob['target'].sum() / len(med_prob) * 100
        print(f"   Actual Win Rate: {actual_wr_med:.2f}% ({int(med_prob['target'].sum())} wins)\n")
    
    # Sinais de LOW probability (<50%)
    low_prob = df_signals[df_signals['win_probability'] <= 0.5]
    print(f"🔴 LOW PROBABILITY (<50%): {len(low_prob)} sinais")
    if len(low_prob) > 0:
        actual_wr_low = low_prob['target'].sum() / len(low_prob) * 100
        print(f"   Actual Win Rate: {actual_wr_low:.2f}% ({int(low_prob['target'].sum())} wins)\n")
    
    # Salvar modelo
    models_dir = Path('../models')
    models_dir.mkdir(exist_ok=True)
    model_path = models_dir / f'xgboost_{symbol.lower()}.pkl'
    pickle.dump(model, open(model_path, 'wb'))
    print(f"💾 Modelo salvo: {model_path}\n")
    
    # Salvar predictions
    output_df = df_signals[['datetime', 'signal', 'confluence', 'entry_price', 
                            'exit_price', 'exit_time', 'movement_pct', 'result', 'target', 
                            'win_probability']].copy()
    output_df['score_category'] = output_df['win_probability'].apply(
        lambda x: 'HIGH (>70%)' if x > 0.7 else ('MEDIUM (50-70%)' if x > 0.5 else 'LOW (<50%)')
    )
    
    output_path = Path('../output') / f'{symbol.lower()}_with_scores.csv'
    output_df.to_csv(output_path, index=False)
    print(f"📊 CSV com scores salvo: {output_path}\n")
    
    # Feature importance CSV
    importance_path = Path('../output') / f'{symbol.lower()}_feature_importance.csv'
    importance.to_csv(importance_path, index=False)
    print(f"📈 Feature importance salvo: {importance_path}\n")
    
    return model, importance, output_df


def main():
    """Main"""
    base_dir = Path('../output')
    
    # GBPUSD
    gbpusd_file = base_dir / 'gbpusd_signals_completo.csv'
    if gbpusd_file.exists():
        model_gb, importance_gb, output_gb = train_xgboost_selector(gbpusd_file, 'GBPUSD')
    
    # EURUSD
    eurusd_file = base_dir / 'eurusd_signals_completo.csv'
    if eurusd_file.exists():
        print("\n\n")
        model_eu, importance_eu, output_eu = train_xgboost_selector(eurusd_file, 'EURUSD')
    
    # XAUUSD (Gold)
    xauusd_file = base_dir / 'xauusd_signals_completo.csv'
    if xauusd_file.exists():
        print("\n\n")
        model_xau, importance_xau, output_xau = train_xgboost_selector(xauusd_file, 'XAUUSD')
    
    print(f"\n{'='*100}")
    print(f"✅ TODOS OS MODELOS TREINADOS E SALVOS")
    print(f"{'='*100}\n")


if __name__ == '__main__':
    main()
