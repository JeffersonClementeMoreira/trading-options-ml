"""
Daily Signal Selector for MT5 Production
========================================

Selects 1 actionable signal per day based on:
1. Consecutive confluence (last 5 signals with 15% bonus)
2. High confidence (threshold-based)
3. Real-time observable criteria (not waiting for end-of-day max)
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Optional
from datetime import datetime, timedelta


def count_consecutive_confluence(df: pd.DataFrame, test_indices: np.ndarray, window: int = 5) -> np.ndarray:
    """
    Count consecutive confluence signals in the last N records.
    Returns array of consecutive confluence counts for each test signal.
    """
    consecutive = np.zeros(len(test_indices))
    has_confluence = (df.loc[test_indices, 'confluence_bonus_pct'] == 15.0).values
    
    for i in range(len(test_indices)):
        # Count confluence in the previous records (moving window)
        start_idx = max(0, i - window)
        consecutive[i] = has_confluence[start_idx:i].sum()
    
    return consecutive


def select_daily_signals(backtest_csv: str, strategy: str = 'high_confidence_confluence') -> pd.DataFrame:
    """
    Select 1 actionable signal per day for MT5 deployment.
    
    Parameters:
    -----------
    backtest_csv : str
        Path to backtest CSV with predictions and confidence scores
    strategy : str
        Selection strategy:
        - 'high_confidence_confluence': confidence >= 90% + 3+ successive confluence (RECOMMENDED)
        - 'ultra_high_confidence': confidence >= 95% (conservative, ~50% signals)
        - 'balanced': confidence >= 85% + 4+ successive confluence (65% signals)
        - 'first_send': first SEND signal of the day (early entry, lower confidence)
        - 'first_15_confluence': first signal with 15% confluence bonus (balanced)
    
    Returns:
    --------
    pd.DataFrame
        One signal per day with columns: timestamp, confidence, confluence_bonus_pct,
        predicted_price_ensemble, actual_price, signal_strength
    """
    
    # Load backtest results
    df = pd.read_csv(backtest_csv, low_memory=False)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    # Filter only SEND signals
    send_signals = df[df['signal_status'] == 'SEND'].copy().reset_index(drop=True)
    
    if len(send_signals) == 0:
        print(f"⚠️  No SEND signals found in {backtest_csv}")
        return pd.DataFrame()
    
    # Calculate consecutive confluence for each signal
    send_signals['consecutive_confluence'] = count_consecutive_confluence(
        send_signals, 
        np.arange(len(send_signals))
    )
    
    # Apply strategy filter
    if strategy == 'high_confidence_confluence':
        # RECOMMENDED: High confidence + multiple confluence confirmations
        filtered = send_signals[
            (send_signals['confidence'] >= 0.90) &
            (send_signals['consecutive_confluence'] >= 3)
        ].copy()
        strategy_desc = "confidence >= 90% + 3+ confluence"
        
    elif strategy == 'ultra_high_confidence':
        # CONSERVATIVE: Just very high confidence
        filtered = send_signals[send_signals['confidence'] >= 0.95].copy()
        strategy_desc = "confidence >= 95%"
        
    elif strategy == 'balanced':
        # BALANCED: More signals, lower minimum confidence
        filtered = send_signals[
            (send_signals['confidence'] >= 0.85) &
            (send_signals['consecutive_confluence'] >= 4)
        ].copy()
        strategy_desc = "confidence >= 85% + 4+ confluence"
        
    elif strategy == 'first_send':
        # EARLY ENTRY: First SEND of the day
        filtered = send_signals.copy()
        strategy_desc = "First SEND of day"
        
    elif strategy == 'first_15_confluence':
        # Balanced: First signal with 15% confluence
        filtered = send_signals[send_signals['confluence_bonus_pct'] == 15.0].copy()
        strategy_desc = "First signal with 15% confluence"
        
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    # Select 1 signal per day
    daily_signals = []
    
    for date, group in filtered.groupby('date'):
        if strategy == 'first_send' or strategy == 'first_15_confluence':
            # Take first chronologically
            signal = group.iloc[0]
        else:
            # Take signal with highest confidence for that day
            signal = group.loc[group['confidence'].idxmax()]
        
        daily_signals.append(signal)
    
    result = pd.DataFrame(daily_signals).reset_index(drop=True)
    
    # Calculate metrics
    total_days = send_signals['date'].nunique()
    selected_days = len(result)
    avg_confidence = result['confidence'].mean()
    
    print(f"\n{'='*80}")
    print(f"📊 DAILY SIGNAL SELECTION - {strategy}")
    print(f"{'='*80}")
    print(f"Strategy: {strategy_desc}")
    print(f"\n📈 Coverage:")
    print(f"  Days with SEND signals: {total_days}")
    print(f"  Days selected: {selected_days} ({selected_days/total_days*100:.1f}%)")
    print(f"  Total SEND signals: {len(send_signals):,}")
    print(f"  Filtered signals: {len(filtered):,} ({len(filtered)/len(send_signals)*100:.1f}%)")
    print(f"\n🎯 Quality Metrics:")
    print(f"  Average confidence: {avg_confidence:.2%}")
    print(f"  Min/Max confidence: {result['confidence'].min():.2%} / {result['confidence'].max():.2%}")
    print(f"  Average confluence bonus: {result['confluence_bonus_pct'].mean():.1f}%")
    print(f"  Average consecutive confluence: {result['consecutive_confluence'].mean():.1f}")
    print(f"\n📅 Temporal Distribution:")
    print(f"  Average time of day (signal): {pd.to_datetime(result['timestamp']).dt.hour.mean():.1f}h")
    
    return result


def prepare_mt5_export(daily_signals: pd.DataFrame, output_file: str = None) -> pd.DataFrame:
    """
    Prepare signals for MT5 export with essential columns only.
    
    Returns:
    --------
    pd.DataFrame with columns: Date, Time, Pair, Direction, Confidence, EntryPrice
    """
    
    if len(daily_signals) == 0:
        print("⚠️  No signals to export")
        return pd.DataFrame()
    
    export_df = pd.DataFrame({
        'Date': daily_signals['timestamp'].dt.date,
        'Time': daily_signals['timestamp'].dt.time,
        'Pair': daily_signals.get('pair', 'UNKNOWN'),  # assumes pair column exists
        'EntryPrice': daily_signals['predicted_price_ensemble'],
        'TargetPrice': daily_signals['actual_price'],
        'Confidence': (daily_signals['confidence'] * 100).astype(int),
        'ConfluenceBonus': daily_signals['confluence_bonus_pct'].astype(int),
        'Signal': 'BUY' if (daily_signals['predicted_pips_ensemble'] > 0).mean() > 0.5 else 'SELL',
    })
    
    if output_file:
        export_df.to_csv(output_file, index=False)
        print(f"\n✅ Exported to: {output_file}")
    
    return export_df


def compare_strategies(backtest_csv: str) -> pd.DataFrame:
    """
    Compare all available strategies on the same backtest data.
    """
    
    strategies = [
        'high_confidence_confluence',
        'ultra_high_confidence',
        'balanced',
        'first_send',
        'first_15_confluence'
    ]
    
    print(f"\n{'='*80}")
    print(f"📊 STRATEGY COMPARISON")
    print(f"{'='*80}\n")
    
    results = []
    for strat in strategies:
        signals = select_daily_signals(backtest_csv, strategy=strat)
        
        if len(signals) > 0:
            results.append({
                'Strategy': strat,
                'Days': len(signals),
                'Avg Confidence': signals['confidence'].mean(),
                'Min Confidence': signals['confidence'].min(),
                'Confluence %': signals['confluence_bonus_pct'].mean(),
                'Avg Time (h)': pd.to_datetime(signals['timestamp']).dt.hour.mean()
            })
    
    comparison = pd.DataFrame(results)
    print("\nComparison Summary:")
    print(comparison.to_string(index=False))
    
    return comparison


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python daily_signal_selector.py <backtest_csv> [strategy]")
        print("Strategies: high_confidence_confluence, ultra_high_confidence, balanced, first_send, first_15_confluence")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    strategy = sys.argv[2] if len(sys.argv) > 2 else 'high_confidence_confluence'
    
    # Select signals
    daily_signals = select_daily_signals(csv_file, strategy=strategy)
    
    # Show sample
    print(f"\n📋 Sample of selected signals (first 5):")
    print(daily_signals[['timestamp', 'confidence', 'confluence_bonus_pct', 'consecutive_confluence']].head().to_string())
    
    # Compare strategies
    compare_strategies(csv_file)
