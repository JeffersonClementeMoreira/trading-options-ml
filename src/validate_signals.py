#!/usr/bin/env python3
"""
VALIDADOR DE SINAIS - Backtest Validator
=========================================

Valida se o filtro está funcionando:
1. Apenas 1 SEND por dia (não múltiplos)
2. Condições reais: confidence >= 90% AND consecutive_confluence >= 3
3. Mostra estatísticas de cobertura
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


def calculate_consecutive_confluence(df, window=5, direction_threshold=0.5):
    """
    Calcula consecutive confluence para cada linha.
    
    Confluence: Se últimos 5 candles predizem HIGH (target > close),
    consideramos como "bullish streak" para sinal UP.
    
    Returns: Lista com score (0-5) para cada linha
    """
    confluence_scores = []
    
    for i in range(len(df)):
        if i < window - 1:
            # Não temos histórico suficiente
            confluence_scores.append(0)
        else:
            # Ver últimos N candles (inclusive este)
            window_start = i - window + 1
            window_end = i + 1
            
            window_data = df.iloc[window_start:window_end]
            
            # Calcular direção de cada candle
            directions = []
            for idx, row in window_data.iterrows():
                if pd.notna(row['predicted_pips_ensemble']):
                    # Use predicted pips para saber direção
                    directions.append(1 if row['predicted_pips_ensemble'] > 0 else -1)
            
            # Score = quantos concordam
            if len(directions) > 0:
                consensus = abs(sum(directions)) / len(directions)
                confluence_scores.append(int(abs(sum(directions))))  # 0-5
            else:
                confluence_scores.append(0)
    
    return confluence_scores


def validate_signals(backtest_csv, pair, output_signal_csv=None):
    """
    Valida sinais de um backtest CSV.
    
    Filtros:
    1. confidence >= 90%
    2. consecutive_confluence >= 3 (mínimo 3 dos últimos 5 candles na mesma direção)
    3. Apenas 1 SEND por dia
    
    Returns: DataFrame com sinais válidos
    """
    print(f"\n{'='*80}")
    print(f"🔍 VALIDANDO SINAIS - {pair}")
    print(f"{'='*80}")
    
    # Carregar backtest
    df = pd.read_csv(backtest_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    print(f"\n📥 Carregado: {len(df)} linhas")
    
    # Filtrar apenas linhas com predição
    df_pred = df[df['predicted_price_ensemble'].notna()].copy()
    print(f"   Com predição: {len(df_pred)} linhas")
    
    if len(df_pred) == 0:
        print("   ⚠️  Nenhuma predição encontrada!")
        return pd.DataFrame()
    
    # ============================================================================
    # 1. CALCULAR CONFLUENCE (últimos 5 candles)
    # ============================================================================
    print(f"\n📊 Calculando confluence (últimos 5 candles)...")
    df_pred['confluence_score'] = calculate_consecutive_confluence(df_pred, window=5)
    
    # Aplicar bonus de confiança se confluence >= 3
    df_pred['confluence_bonus'] = df_pred['confluence_score'].apply(
        lambda x: 0.15 if x >= 3 else 0.0
    )
    df_pred['confidence_with_bonus'] = df_pred['confidence'] * (1 + df_pred['confluence_bonus'])
    df_pred['confidence_with_bonus_pct'] = df_pred['confidence_with_bonus'] * 100
    
    print(f"   ✅ Confluence calculado")
    
    # ============================================================================
    # 2. APLICAR FILTROS
    # ============================================================================
    print(f"\n🎯 Aplicando filtros...")
    
    # Filtro 1: Confiança >= 90%
    f1 = df_pred['confidence_with_bonus_pct'] >= 90
    print(f"   Filtro 1 (confidence >= 90%): {f1.sum()}/{len(df_pred)} = {f1.sum()/len(df_pred)*100:.1f}%")
    
    # Filtro 2: Confluence >= 3 (3+ dos últimos 5 candles concordam)
    f2 = df_pred['confluence_score'] >= 3
    print(f"   Filtro 2 (confluence >= 3): {f2.sum()}/{len(df_pred)} = {f2.sum()/len(df_pred)*100:.1f}%")
    
    # Ambos os filtros
    f_both = f1 & f2
    print(f"   Ambos os filtros: {f_both.sum()}/{len(df_pred)} = {f_both.sum()/len(df_pred)*100:.1f}%")
    
    df_pred['filter_passed'] = f_both
    
    # ============================================================================
    # 3. SELECIONAR APENAS 1 SEND POR DIA
    # ============================================================================
    print(f"\n📅 Garantindo 1 SEND por dia...")
    
    signals = []
    for date in df_pred['date'].unique():
        day_data = df_pred[df_pred['date'] == date].sort_values('timestamp')
        
        # Filtrar apenas os que passaram nos filtros
        day_signals = day_data[day_data['filter_passed']].copy()
        
        if len(day_signals) > 0:
            # Pegar o PRIMEIRO (em ordem cronológica)
            signal = day_signals.iloc[0].copy()
            signal['signal_status'] = 'SEND'
            signals.append(signal)
    
    df_signals = pd.DataFrame(signals)
    
    if len(df_signals) > 0:
        print(f"   ✅ {len(df_signals)} sinais válidos (1 por dia)")
        print(f"   Cobertura: {len(df_signals)}/{df_pred['date'].nunique()} dias = {len(df_signals)/df_pred['date'].nunique()*100:.1f}%")
    else:
        print(f"   ⚠️  Nenhum sinal válido encontrado!")
        return pd.DataFrame()
    
    # ============================================================================
    # 4. VALIDAR QUALIDADE DOS SINAIS
    # ============================================================================
    print(f"\n📈 Estatísticas dos sinais SEND:")
    
    if len(df_signals) > 0:
        print(f"   Confiança média (com bonus): {df_signals['confidence_with_bonus_pct'].mean():.2f}%")
        print(f"   Confiança mínima: {df_signals['confidence_with_bonus_pct'].min():.2f}%")
        print(f"   Confiança máxima: {df_signals['confidence_with_bonus_pct'].max():.2f}%")
        
        print(f"\n   Confluence score dos sinais:")
        print(f"   - com 3 de concordância: {(df_signals['confluence_score'] == 3).sum()}")
        print(f"   - com 4 de concordância: {(df_signals['confluence_score'] == 4).sum()}")
        print(f"   - com 5 de concordância: {(df_signals['confluence_score'] == 5).sum()}")
        
        print(f"\n   Resultado dos pips (rentabilidade real):")
        win_signals = df_signals[df_signals['actual_pips'] > 0]
        print(f"   - Ganhadores: {len(win_signals)}/{len(df_signals)} = {len(win_signals)/len(df_signals)*100:.1f}%")
        print(f"   - Total pips: {df_signals['actual_pips'].sum():.2f}")
        print(f"   - Pips médios: {df_signals['actual_pips'].mean():.2f}")
        print(f"   - Pips máximo: {df_signals['actual_pips'].max():.2f}")
        print(f"   - Pips mínimo: {df_signals['actual_pips'].min():.2f}")
    
    # ============================================================================
    # 5. SALVAR SINAIS (se solicitado)
    # ============================================================================
    if output_signal_csv:
        output_cols = [
            'timestamp', 'close', 'confidence', 'confidence_with_bonus_pct',
            'confluence_score', 'predicted_pips_ensemble', 'actual_pips',
            'actual_price', 'predicted_price_ensemble', 'signal_status'
        ]
        output_cols = [col for col in output_cols if col in df_signals.columns]
        
        df_signals[output_cols].to_csv(output_signal_csv, index=False)
        print(f"\n💾 Sinais salvos em: {output_signal_csv}")
    
    return df_signals


def compare_pairs():
    """Compara resultados entre EURUSD e GBPUSD."""
    print("\n" + "="*80)
    print("📊 COMPARAÇÃO DE PARES")
    print("="*80)
    
    results = {}
    
    for pair in ['EURUSD', 'GBPUSD']:
        backtest_csv = f'/home/ubuntu/pessoal/options/results/backtest_{pair}_chronological.csv'
        signal_csv = f'/home/ubuntu/pessoal/options/production/validated_signals_{pair}.csv'
        
        if Path(backtest_csv).exists():
            df_signals = validate_signals(backtest_csv, pair, signal_csv)
            results[pair] = df_signals
        else:
            print(f"\n⚠️  Arquivo não encontrado: {backtest_csv}")
    
    # Resumo geral
    print("\n" + "="*80)
    print("📋 RESUMO GERAL")
    print("="*80)
    
    total_sends = sum(len(df) for df in results.values())
    print(f"\n✅ Total de sinais SEND: {total_sends}")
    
    for pair, df_signals in results.items():
        if len(df_signals) > 0:
            print(f"\n{pair}:")
            print(f"  - {len(df_signals)} sinais")
            print(f"  - Confiança média: {df_signals['confidence_with_bonus_pct'].mean():.2f}%")
            print(f"  - Win rate: {(df_signals['actual_pips'] > 0).sum()}/{len(df_signals)} = {(df_signals['actual_pips'] > 0).sum()/len(df_signals)*100:.1f}%")
            print(f"  - Pips totais: {df_signals['actual_pips'].sum():.2f}")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 VALIDADOR DE SINAIS - Backtest Signal Validator")
    print("="*80)
    
    # Comparar pares
    compare_pairs()
    
    print("\n" + "="*80)
    print("✅ Validação completa!")
    print("="*80)
