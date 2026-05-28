#!/usr/bin/env python3
"""
SIGNAL GENERATOR - Gera sinais de trading baseado em 5 últimas previsões
Regra: Se as últimas 5 previsões forem TODAS alta ou TODAS baixa = SINAL
Limite: Máximo 1 sinal por dia
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


def generate_directional_signals(df, min_consecutive=5, max_signals_per_day=1):
    """
    Gera sinais baseado em direção de previsões
    
    Parâmetros:
    - min_consecutive: Número de previsões consecutivas necessárias (padrão: 5)
    - max_signals_per_day: Máximo de sinais por dia (padrão: 1)
    
    Lógica:
    1. Calcular direção de cada previsão vs close (HIGH se pred > close, LOW se pred < close)
    2. Procurar min_consecutive previsões com mesma direção
    3. Se encontrar, gerar sinal
    4. Garantir máximo max_signals_per_day por dia
    
    Retorna DataFrame com colunas adicionais:
    - prediction_direction: HIGH (+1) ou LOW (-1)
    - consecutive_direction: Número de consecutivas com mesma direção
    - signal_generated: True/False
    - signal_strength: 0-1 (baseado em confidence médio dos últimos 5)
    - signal_type: 'BUY' ou 'SELL'
    """
    print("\n📊 Gerando sinais de trading...")
    
    df_signals = df.copy()
    
    # Filtrar apenas linhas com predições
    df_signals = df_signals[df_signals['predicted_price_ensemble'].notna()].copy()
    df_signals = df_signals.reset_index(drop=True)
    
    if len(df_signals) == 0:
        print("❌ Sem dados de teste para gerar sinais")
        return None
    
    # ─── 1. CALCULAR DIREÇÃO DE CADA PREVISÃO ───
    df_signals['prediction_direction'] = np.where(
        df_signals['predicted_price_ensemble'] > df_signals['close'],
        1,  # HIGH
        -1  # LOW
    )
    df_signals['prediction_direction'] = np.where(
        df_signals['predicted_price_ensemble'] == df_signals['close'],
        0,  # NEUTRO
        df_signals['prediction_direction']
    )
    
    df_signals['prediction_pips'] = (
        (df_signals['predicted_price_ensemble'] - df_signals['close']) * 10000
    )
    
    # ─── 2. ENCONTRAR CONSECUTIVAS ───
    df_signals['consecutive_direction'] = 0
    df_signals['consecutive_confidence_avg'] = 0.0
    df_signals['consecutive_direction_str'] = 'NEUTRO'
    
    for idx in range(min_consecutive - 1, len(df_signals)):
        # Olhar para os últimos min_consecutive candles
        window = df_signals.iloc[idx - min_consecutive + 1:idx + 1]
        directions = window['prediction_direction'].values
        
        # Se todos têm mesma direção (não NEUTRO)
        if len(set(directions)) == 1 and directions[0] != 0:
            df_signals.loc[idx, 'consecutive_direction'] = min_consecutive
            df_signals.loc[idx, 'consecutive_confidence_avg'] = window['confidence'].mean()
            df_signals.loc[idx, 'consecutive_direction_str'] = (
                'HIGH' if directions[0] == 1 else 'LOW'
            )
        else:
            # Calcular quantas consecutivas temos
            current_dir = directions[-1]
            count = 1
            for i in range(len(directions) - 2, -1, -1):
                if directions[i] == current_dir and current_dir != 0:
                    count += 1
                else:
                    break
            df_signals.loc[idx, 'consecutive_direction'] = count
            df_signals.loc[idx, 'consecutive_confidence_avg'] = window['confidence'].mean()
    
    # ─── 3. MARCAR SINAIS ───
    df_signals['signal_generated'] = False
    df_signals['signal_type'] = ''
    df_signals['signal_strength'] = 0.0
    
    # Extrair data de cada timestamp
    df_signals['signal_date'] = pd.to_datetime(df_signals['timestamp']).dt.date
    
    # Rastrear sinais por dia
    signals_today = {}
    
    for idx in range(len(df_signals)):
        if df_signals.loc[idx, 'consecutive_direction'] >= min_consecutive:
            signal_date = df_signals.loc[idx, 'signal_date']
            
            # Verificar se já temos sinal neste dia
            if signal_date not in signals_today:
                signals_today[signal_date] = 0
            
            if signals_today[signal_date] < max_signals_per_day:
                df_signals.loc[idx, 'signal_generated'] = True
                
                direction = df_signals.loc[idx, 'prediction_direction']
                signal_type = 'BUY' if direction == 1 else 'SELL'
                df_signals.loc[idx, 'signal_type'] = signal_type
                df_signals.loc[idx, 'signal_strength'] = (
                    df_signals.loc[idx, 'consecutive_confidence_avg']
                )
                
                signals_today[signal_date] += 1
    
    print(f"✅ Sinais gerados")
    print(f"   • Total de sinais: {df_signals['signal_generated'].sum()}")
    print(f"   • Sinais BUY: {(df_signals['signal_type'] == 'BUY').sum()}")
    print(f"   • Sinais SELL: {(df_signals['signal_type'] == 'SELL').sum()}")
    
    return df_signals


def analyze_signal_performance(df_signals):
    """Analisa performance dos sinais gerados"""
    print("\n📈 Analisando performance dos sinais...")
    
    # Calcular signal_is_correct para TODOS os sinais
    df_signals['signal_is_correct'] = False
    signal_mask = df_signals['signal_generated'] == True
    df_signals.loc[signal_mask, 'signal_is_correct'] = (
        ((df_signals.loc[signal_mask, 'signal_type'] == 'BUY') & (df_signals.loc[signal_mask, 'actual_pips'] > 0)) |
        ((df_signals.loc[signal_mask, 'signal_type'] == 'SELL') & (df_signals.loc[signal_mask, 'actual_pips'] < 0))
    )
    
    df_signals_only = df_signals[df_signals['signal_generated']].copy()
    
    if len(df_signals_only) == 0:
        print("⚠️ Nenhum sinal gerado para análise")
        return None
    
    win_rate = df_signals_only['signal_is_correct'].mean() * 100
    total_pips = df_signals_only['actual_pips'].sum()
    avg_pips = df_signals_only['actual_pips'].mean()
    max_profit = df_signals_only['actual_pips'].max()
    max_loss = df_signals_only['actual_pips'].min()
    
    print(f"\n🎯 Performance dos Sinais:")
    print(f"   • Total de sinais: {len(df_signals_only)}")
    print(f"   • Win Rate: {win_rate:.2f}%")
    print(f"   • Total Pips: {total_pips:+.2f}")
    print(f"   • Pips Médios: {avg_pips:+.2f}")
    print(f"   • Maior Ganho: {max_profit:+.2f} pips")
    print(f"   • Maior Perda: {max_loss:+.2f} pips")
    
    # Performance por força do sinal
    print(f"\n📊 Performance por força do sinal:")
    strength_bins = [0, 0.5, 0.7, 0.8, 0.9, 1.0]
    strength_labels = ['0-50%', '50-70%', '70-80%', '80-90%', '90-100%']
    
    df_signals_only['strength_bin'] = pd.cut(
        df_signals_only['signal_strength'],
        bins=strength_bins,
        labels=strength_labels
    )
    
    for label in strength_labels:
        group = df_signals_only[df_signals_only['strength_bin'] == label]
        if len(group) > 0:
            wr = group['signal_is_correct'].mean() * 100
            total_p = group['actual_pips'].sum()
            avg_p = group['actual_pips'].mean()
            print(f"\n   {label}:")
            print(f"      • Sinais: {len(group)}")
            print(f"      • Win Rate: {wr:.2f}%")
            print(f"      • Pips Total: {total_p:+.2f}")
            print(f"      • Pips Médio: {avg_p:+.2f}")
    
    # Performance por tipo
    print(f"\n📊 Performance por tipo:")
    for signal_type in ['BUY', 'SELL']:
        group = df_signals_only[df_signals_only['signal_type'] == signal_type]
        if len(group) > 0:
            wr = group['signal_is_correct'].mean() * 100
            total_p = group['actual_pips'].sum()
            avg_p = group['actual_pips'].mean()
            print(f"\n   {signal_type}:")
            print(f"      • Sinais: {len(group)}")
            print(f"      • Win Rate: {wr:.2f}%")
            print(f"      • Pips Total: {total_p:+.2f}")
            print(f"      • Pips Médio: {avg_p:+.2f}")
    
    return df_signals  # Retorna completo, com signal_is_correct para todos


def create_signals_output(df_signals, output_file):
    """Cria arquivo com todos os sinais"""
    print(f"\n💾 Salvando arquivo de sinais...")
    
    df_signals_only = df_signals[df_signals['signal_generated']].copy()
    
    output_cols = [
        'timestamp', 'close',
        'predicted_price_ensemble', 'prediction_pips',
        'confidence', 'signal_type', 'signal_strength',
        'consecutive_direction', 'consecutive_direction_str',
        'actual_pips', 'signal_is_correct',
        'rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum',
        'ob_distance_pct', 'sd_distance_pct'
    ]
    
    output_cols = [col for col in output_cols if col in df_signals_only.columns]
    df_output = df_signals_only[output_cols].copy()
    
    df_output.to_csv(output_file, index=False)
    print(f"✅ {output_file}")
    print(f"   • Sinais: {len(df_output)}")


def create_signals_log(df_signals, output_file):
    """Cria log formatado de sinais"""
    print(f"\n📝 Criando log de sinais...")
    
    df_signals_only = df_signals[df_signals['signal_generated']].copy()
    
    with open(output_file, 'w') as f:
        f.write("="*120 + "\n")
        f.write("📊 LOG DE SINAIS DE TRADING\n")
        f.write("="*120 + "\n\n")
        
        for idx, row in df_signals_only.iterrows():
            f.write(f"🔔 SINAL #{idx + 1}\n")
            f.write(f"{'─'*120}\n")
            f.write(f"Data/Hora: {row['timestamp']}\n")
            f.write(f"Tipo:      {row['signal_type']:6s} | Força: {row['signal_strength']:.2%}\n")
            f.write(f"Preço:     {row['close']:.5f} → Predição: {row['predicted_price_ensemble']:.5f} ({row['prediction_pips']:+.2f} pips)\n")
            f.write(f"Confiança: {row['confidence']:.2%} | Consecutivas: {int(row['consecutive_direction'])} {row['consecutive_direction_str']}\n")
            f.write(f"Resultado: {row['actual_pips']:+.2f} pips {'✅ WIN' if row['signal_is_correct'] else '❌ LOSS'}\n")
            f.write(f"RSI: {row['rsi']:.2f} | SMA20: {row['sma20']:.5f} | MACD: {row['macd']:.6f}\n")
            f.write("\n")
    
    print(f"✅ {output_file}")


def main():
    """Gera sinais para backtest"""
    
    print("\n" + "="*100)
    print("🚀 SIGNAL GENERATOR - Gera sinais de trading")
    print("="*100)
    
    # Processar EURUSD
    print("\n📥 Carregando backtest EURUSD...")
    df_eurusd = pd.read_csv('/home/ubuntu/pessoal/options/results/backtest_EURUSD_chronological.csv')
    
    print(f"✅ {len(df_eurusd)} candles carregados")
    
    # Gerar sinais
    df_eurusd_signals = generate_directional_signals(df_eurusd, min_consecutive=5, max_signals_per_day=1)
    
    # Analisar performance
    analyze_signal_performance(df_eurusd_signals)
    
    # Salvar outputs
    create_signals_output(
        df_eurusd_signals,
        '/home/ubuntu/pessoal/options/results/signals_EURUSD.csv'
    )
    create_signals_log(
        df_eurusd_signals,
        '/home/ubuntu/pessoal/options/results/signals_EURUSD_log.txt'
    )
    
    # Processar GBPUSD
    print("\n\n" + "="*100)
    print("GBPUSD")
    print("="*100)
    
    print("\n📥 Carregando backtest GBPUSD...")
    df_gbpusd = pd.read_csv('/home/ubuntu/pessoal/options/results/backtest_GBPUSD_chronological.csv')
    
    print(f"✅ {len(df_gbpusd)} candles carregados")
    
    df_gbpusd_signals = generate_directional_signals(df_gbpusd, min_consecutive=5, max_signals_per_day=1)
    analyze_signal_performance(df_gbpusd_signals)
    
    create_signals_output(
        df_gbpusd_signals,
        '/home/ubuntu/pessoal/options/results/signals_GBPUSD.csv'
    )
    create_signals_log(
        df_gbpusd_signals,
        '/home/ubuntu/pessoal/options/results/signals_GBPUSD_log.txt'
    )
    
    print("\n\n" + "="*100)
    print("✅ SIGNAL GENERATOR COMPLETO")
    print("="*100)
    print("\n📊 Arquivos gerados:")
    print("   • signals_EURUSD.csv")
    print("   • signals_EURUSD_log.txt")
    print("   • signals_GBPUSD.csv")
    print("   • signals_GBPUSD_log.txt")


if __name__ == '__main__':
    main()
