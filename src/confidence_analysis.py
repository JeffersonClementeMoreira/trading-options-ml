#!/usr/bin/env python3
"""
ANÁLISE DE CONFIANÇA - Correlaciona confidence score com acurácia
Calcula distância em % para indicadores técnicos (Order Block, FVG, SD, etc.)
"""

import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
import warnings
warnings.filterwarnings('ignore')


def calculate_distance_metrics(df):
    """
    Calcula distância em % do preço até os indicadores técnicos
    
    Métricas:
    - order_block_distance_pct: % do preço até o support/resistance do order block
    - fvg_distance_pct: % do preço até o fair value gap
    - sd_distance_pct: % do preço até o standard deviation
    - bb_distance_pct: % do preço até as bandas de Bollinger
    - smc_distance_pct: % do preço até os níveis SMC
    """
    print("\n📐 Calculando distâncias em % dos indicadores...")
    
    df_metrics = df.copy()
    
    # ─── ORDER BLOCK DISTANCE ───
    # Distance = |close - smc_support ou smc_resistance| / close
    df_metrics['ob_support_distance_pct'] = np.abs(
        (df['close'] - df['smc_support']) / df['close'] * 100
    )
    df_metrics['ob_resistance_distance_pct'] = np.abs(
        (df['close'] - df['smc_resistance']) / df['close'] * 100
    )
    df_metrics['ob_distance_pct'] = df_metrics[['ob_support_distance_pct', 'ob_resistance_distance_pct']].min(axis=1)
    
    # ─── FVG DISTANCE ───
    # FVG pode ser gap_up (low > high_prev) ou gap_down (high < low_prev)
    # Calcular distância até o gap midpoint
    df_metrics['fvg_distance_pct'] = np.where(
        df['smc_fvg'] > 0,  # Se há FVG ativo
        (np.abs(df['close'] - (df['smc_support'] + df['smc_resistance']) / 2) / df['close'] * 100),
        0
    )
    
    # ─── STANDARD DEVIATION DISTANCE ───
    # Distance = sd / close (em percentual)
    df_metrics['sd_distance_pct'] = (df['sd'] / df['close'] * 100)
    
    # ─── BOLLINGER BANDS DISTANCE ───
    df_metrics['bb_upper_distance_pct'] = np.abs(
        (df['close'] - df['bb_upper']) / df['close'] * 100
    )
    df_metrics['bb_lower_distance_pct'] = np.abs(
        (df['close'] - df['bb_lower']) / df['close'] * 100
    )
    df_metrics['bb_distance_pct'] = df_metrics[['bb_upper_distance_pct', 'bb_lower_distance_pct']].min(axis=1)
    
    # ─── SMC SUPPORT/RESISTANCE DISTANCE ───
    df_metrics['smc_distance_pct'] = np.minimum(
        df_metrics['ob_support_distance_pct'],
        df_metrics['ob_resistance_distance_pct']
    )
    
    # ─── MOMENTUM DISTANCE ───
    # Momentum normalizado pela volatilidade (SD)
    df_metrics['momentum_normalized_pct'] = np.abs(
        (df['momentum'] / (df['sd'] + 1e-6)) * 100
    )
    
    print("✅ Distâncias calculadas")
    return df_metrics


def analyze_confidence_vs_accuracy(df):
    """
    Correlaciona confidence score com acurácia das predições
    
    Retorna:
    - Correlação Pearson e Spearman
    - Grupos de confiança com estatísticas
    """
    print("\n📊 Analisando correlação Confiança x Acurácia...")
    
    # Filtrar apenas linhas com predições (test set)
    df_test = df[df['predicted_price_ensemble'].notna()].copy()
    
    if len(df_test) == 0:
        print("❌ Sem dados de teste para análise")
        return None
    
    # Calcular acurácia (inverso do erro normalizado)
    # Acurácia = 1 - (|erro_pips| / média_movimento_diário_em_pips)
    df_test['accuracy'] = 1 - (df_test['error_pips'] / (df_test['error_pips'].max() + 1e-6))
    df_test['accuracy'] = df_test['accuracy'].clip(0, 1)  # Entre 0-1
    
    # Correlação
    pearson_corr, pearson_pval = pearsonr(df_test['confidence'], df_test['accuracy'])
    spearman_corr, spearman_pval = spearmanr(df_test['confidence'], df_test['accuracy'])
    
    print(f"\n🔗 Correlação Confiança vs Acurácia:")
    print(f"   Pearson:  {pearson_corr:+.4f} (p-value: {pearson_pval:.6f})")
    print(f"   Spearman: {spearman_corr:+.4f} (p-value: {spearman_pval:.6f})")
    
    # Análise por faixas de confiança
    print(f"\n📈 Performance por nível de confiança:")
    conf_bins = [0, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
    conf_labels = ['0-50%', '50-70%', '70-80%', '80-90%', '90-95%', '95-100%']
    
    df_test['confidence_bin'] = pd.cut(df_test['confidence'], bins=conf_bins, labels=conf_labels)
    
    for label in conf_labels:
        group = df_test[df_test['confidence_bin'] == label]
        if len(group) > 0:
            accuracy_mean = group['accuracy'].mean()
            win_rate = (group['actual_pips'] > 0).sum() / len(group) * 100
            avg_pips = group['actual_pips'].mean()
            print(f"\n   {label}:")
            print(f"      • Quantos: {len(group)}")
            print(f"      • Acurácia média: {accuracy_mean:.2%}")
            print(f"      • Win rate: {win_rate:.2f}%")
            print(f"      • Pips médios: {avg_pips:.2f}")
    
    return {
        'pearson': pearson_corr,
        'spearman': spearman_corr,
        'pearson_pval': pearson_pval,
        'spearman_pval': spearman_pval,
        'df_test': df_test
    }


def analyze_indicator_distance_vs_accuracy(df):
    """
    Correlaciona distância dos indicadores com acurácia das predições
    """
    print("\n\n📏 Analisando impacto de distâncias dos indicadores...")
    
    df_test = df[df['predicted_price_ensemble'].notna()].copy()
    
    if len(df_test) == 0:
        return None
    
    # Calcular acurácia
    df_test['accuracy'] = 1 - (df_test['error_pips'] / (df_test['error_pips'].max() + 1e-6))
    df_test['accuracy'] = df_test['accuracy'].clip(0, 1)
    
    distance_indicators = [
        'ob_distance_pct',
        'fvg_distance_pct', 
        'sd_distance_pct',
        'bb_distance_pct',
        'smc_distance_pct',
        'momentum_normalized_pct'
    ]
    
    print("\n🔗 Correlação de distâncias com Acurácia:")
    correlations = {}
    
    for indicator in distance_indicators:
        if indicator in df_test.columns:
            # Remove NaN e infinitos
            mask = (df_test[indicator].notna()) & np.isfinite(df_test[indicator])
            
            if mask.sum() > 0:
                corr, pval = pearsonr(
                    df_test.loc[mask, indicator],
                    df_test.loc[mask, 'accuracy']
                )
                correlations[indicator] = {'corr': corr, 'pval': pval}
                
                significance = "✅" if pval < 0.05 else "⚠️"
                print(f"   {significance} {indicator:30s}: {corr:+.4f} (p={pval:.6f})")
    
    return correlations


def analyze_indicator_distance_vs_win_rate(df):
    """
    Analisa impacto de distâncias no win rate
    """
    print("\n\n📈 Analisando impacto de distâncias no Win Rate...")
    
    df_test = df[df['predicted_price_ensemble'].notna()].copy()
    df_test['is_win'] = (df_test['actual_pips'] > 0).astype(int)
    
    distance_indicators = [
        'ob_distance_pct',
        'fvg_distance_pct',
        'sd_distance_pct',
        'bb_distance_pct',
        'smc_distance_pct'
    ]
    
    print("\n🎯 Win Rate por proximidade de indicadores:")
    
    for indicator in distance_indicators:
        if indicator in df_test.columns:
            mask = (df_test[indicator].notna()) & np.isfinite(df_test[indicator])
            
            if mask.sum() > 0:
                dist_data = df_test.loc[mask, indicator]
                q1, q2, q3 = dist_data.quantile([0.25, 0.5, 0.75])
                
                print(f"\n   {indicator}:")
                
                # Grupo 1: Muito próximo (0-Q1)
                close_mask = mask & (df_test[indicator] <= q1)
                if close_mask.sum() > 0:
                    wr = df_test.loc[close_mask, 'is_win'].mean() * 100
                    print(f"      • Muito próximo (0-Q1): {wr:.2f}% ({close_mask.sum()} trades)")
                
                # Grupo 2: Médio (Q1-Q3)
                mid_mask = mask & (df_test[indicator] > q1) & (df_test[indicator] <= q3)
                if mid_mask.sum() > 0:
                    wr = df_test.loc[mid_mask, 'is_win'].mean() * 100
                    print(f"      • Médio (Q1-Q3): {wr:.2f}% ({mid_mask.sum()} trades)")
                
                # Grupo 3: Longe (>Q3)
                far_mask = mask & (df_test[indicator] > q3)
                if far_mask.sum() > 0:
                    wr = df_test.loc[far_mask, 'is_win'].mean() * 100
                    print(f"      • Longe (>Q3): {wr:.2f}% ({far_mask.sum()} trades)")


def create_analysis_output(df, output_file):
    """Cria arquivo com análise completa"""
    print(f"\n💾 Salvando análise detalhada...")
    
    df_test = df[df['predicted_price_ensemble'].notna()].copy()
    df_test['accuracy'] = 1 - (df_test['error_pips'] / (df_test['error_pips'].max() + 1e-6))
    df_test['accuracy'] = df_test['accuracy'].clip(0, 1)
    
    # Selecionar colunas para análise
    output_cols = [
        'timestamp', 'close',
        # Predições
        'predicted_price_xgb', 'predicted_price_rf', 'predicted_price_ensemble',
        'confidence', 'confidence_pct', 'accuracy',
        # Resultado
        'actual_price', 'actual_pips', 'predicted_pips_ensemble', 'error_pips',
        # Distâncias
        'ob_distance_pct', 'fvg_distance_pct', 'sd_distance_pct',
        'bb_distance_pct', 'smc_distance_pct', 'momentum_normalized_pct',
        # Indicadores base
        'rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum', 'sd',
        'bb_width', 'smc_support', 'smc_resistance'
    ]
    
    output_cols = [col for col in output_cols if col in df_test.columns]
    df_output = df_test[output_cols].copy()
    
    df_output.to_csv(output_file, index=False)
    print(f"✅ {output_file}")
    print(f"   • Linhas: {len(df_output)}")
    print(f"   • Colunas: {len(output_cols)}")


def main():
    """Análise completa de confiança e indicadores"""
    
    print("\n" + "="*100)
    print("🔍 ANÁLISE DE CONFIANÇA E INDICADORES TÉCNICOS")
    print("="*100)
    
    # Carregar backtest EURUSD
    print("\n📥 Carregando backtest EURUSD...")
    df_eurusd = pd.read_csv('/home/ubuntu/pessoal/options/results/backtest_EURUSD_chronological.csv')
    
    # Calcular distâncias
    df_eurusd = calculate_distance_metrics(df_eurusd)
    
    # Análise de confiança
    conf_analysis = analyze_confidence_vs_accuracy(df_eurusd)
    
    # Análise de distâncias vs acurácia
    analyze_indicator_distance_vs_accuracy(df_eurusd)
    
    # Análise de distâncias vs win rate
    analyze_indicator_distance_vs_win_rate(df_eurusd)
    
    # Salvar análise completa
    create_analysis_output(
        df_eurusd,
        '/home/ubuntu/pessoal/options/results/analysis_confidence_EURUSD.csv'
    )
    
    # Carregar e analisar GBPUSD
    print("\n\n" + "="*100)
    print("GBPUSD")
    print("="*100)
    
    print("\n📥 Carregando backtest GBPUSD...")
    df_gbpusd = pd.read_csv('/home/ubuntu/pessoal/options/results/backtest_GBPUSD_chronological.csv')
    
    df_gbpusd = calculate_distance_metrics(df_gbpusd)
    conf_analysis = analyze_confidence_vs_accuracy(df_gbpusd)
    analyze_indicator_distance_vs_accuracy(df_gbpusd)
    analyze_indicator_distance_vs_win_rate(df_gbpusd)
    
    create_analysis_output(
        df_gbpusd,
        '/home/ubuntu/pessoal/options/results/analysis_confidence_GBPUSD.csv'
    )
    
    print("\n\n" + "="*100)
    print("✅ ANÁLISE COMPLETA")
    print("="*100)
    print("\n📊 Arquivos gerados:")
    print("   • analysis_confidence_EURUSD.csv")
    print("   • analysis_confidence_GBPUSD.csv")


if __name__ == '__main__':
    main()
