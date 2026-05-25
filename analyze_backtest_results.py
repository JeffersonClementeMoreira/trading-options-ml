#!/usr/bin/env python3
"""
Analisador de Resultados do Daily Backtest

Analisa CSV gerado pelo backtest e cria visualizações/sumários
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
import argparse


def analyze_backtest_csv(csv_path: str):
    """Analisa arquivo CSV do backtest."""
    
    if not Path(csv_path).exists():
        print(f"❌ Arquivo não encontrado: {csv_path}")
        return
    
    print(f"\n📊 Carregando: {csv_path}\n")
    
    df = pd.read_csv(csv_path)
    
    # Filtrar trades válidos (com resultado)
    df_valid = df[df['was_correct'].isin(['✅', '❌'])].copy()
    
    print(f"Total de linhas: {len(df)}")
    print(f"Trades com resultado: {len(df_valid)}")
    print()
    
    if len(df_valid) == 0:
        print("⚠️ Sem dados válidos")
        return
    
    # === ESTATÍSTICAS GERAIS ===
    total_trades = len(df_valid)
    wins = len(df_valid[df_valid['was_correct'] == '✅'])
    losses = len(df_valid[df_valid['was_correct'] == '❌'])
    win_rate = wins / total_trades
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║              📊 RESULTADO GERAL                           ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print(f"║ Total de Trades:        {total_trades:<8} ({win_rate:>6.1%})                 ║")
    print(f"║ Acertos (✅):           {wins:<8} ({wins/total_trades:>6.1%})                 ║")
    print(f"║ Erros (❌):             {losses:<8} ({losses/total_trades:>6.1%})                 ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # === IMPACTO DA CONFLUÊNCIA ===
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║          🎯 IMPACTO DA CONFLUÊNCIA MULTI-TF               ║")
    print("╠════════════════════════════════════════════════════════════╣")
    
    # Com confluência (M15 = H4)
    df_aligned = df_valid[df_valid['is_aligned'] == '✅']
    aligned_wins = len(df_aligned[df_aligned['was_correct'] == '✅'])
    aligned_total = len(df_aligned)
    aligned_wr = aligned_wins / aligned_total if aligned_total > 0 else 0
    
    # Sem confluência (divergência)
    df_divergent = df_valid[df_valid['is_aligned'] == '❌']
    divergent_wins = len(df_divergent[df_divergent['was_correct'] == '✅'])
    divergent_total = len(df_divergent)
    divergent_wr = divergent_wins / divergent_total if divergent_total > 0 else 0
    
    improvement = aligned_wr - divergent_wr
    
    print(f"║                                                            ║")
    print(f"║ COM CONFLUÊNCIA (M15 = H4):                              ║")
    print(f"║   Trades: {aligned_total:<3} | Acertos: {aligned_wins:<3} ({aligned_wr:>6.1%})           ║")
    print(f"║                                                            ║")
    print(f"║ SEM CONFLUÊNCIA (M15 ≠ H4):                              ║")
    print(f"║   Trades: {divergent_total:<3} | Acertos: {divergent_wins:<3} ({divergent_wr:>6.1%})           ║")
    print(f"║                                                            ║")
    print(f"║ 📈 MELHORIA: {improvement:+.1%}                              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # === ANÁLISE POR DIA DA SEMANA ===
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║              📅 ANÁLISE POR DIA DA SEMANA                 ║")
    print("╠════════════════════════════════════════════════════════════╣")
    
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day in days_order:
        df_day = df_valid[df_valid['day_of_week'] == day]
        if len(df_day) > 0:
            day_wins = len(df_day[df_day['was_correct'] == '✅'])
            day_wr = day_wins / len(df_day)
            print(f"║ {day:<10s}: {len(df_day):>2} trades | {day_wins:>2} acertos ({day_wr:>6.1%})        ║")
    
    print("╚════════════════════════════════════════════════════════════╝")
    
    # === ANÁLISE DE MUDANÇAS ===
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║              📈 ANÁLISE DE MUDANÇAS                       ║")
    print("╠════════════════════════════════════════════════════════════╣")
    
    # Converter % para float
    df_valid_pct = df_valid.copy()
    df_valid_pct['change_pct_float'] = df_valid_pct['change_pct'].str.rstrip('%').astype(float)
    
    avg_change = df_valid_pct['change_pct_float'].mean()
    max_change = df_valid_pct['change_pct_float'].max()
    min_change = df_valid_pct['change_pct_float'].min()
    std_change = df_valid_pct['change_pct_float'].std()
    
    print(f"║ Mudança Média:           {avg_change:>+8.3f}%                    ║")
    print(f"║ Mudança Máxima (UP):     {max_change:>+8.3f}%                    ║")
    print(f"║ Mudança Mínima (DOWN):   {min_change:>+8.3f}%                    ║")
    print(f"║ Volatilidade (std):      {std_change:>8.3f}%                    ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # === TOP 10 MELHORES E PIORES ===
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║         🏆 TOP 5 MELHORES PREVISÕES                       ║")
    print("╠════════════════════════════════════════════════════════════╣")
    
    df_valid_pct_sorted = df_valid_pct.sort_values('change_pct_float', ascending=False)
    
    for idx, (_, row) in enumerate(df_valid_pct_sorted.head(5).iterrows(), 1):
        status = '✅' if row['was_correct'] == '✅' else '❌'
        print(f"║ {idx}. {row['date']} | {row['final_pred']:>3s} ({row['final_prob']:>6s}) | "
              f"{row['change_pct']:>+8s} | {status}       ║")
    
    print("║                                                            ║")
    print("║         ⚠️ TOP 5 PIORES PREVISÕES                         ║")
    print("╠════════════════════════════════════════════════════════════╣")
    
    for idx, (_, row) in enumerate(df_valid_pct_sorted.tail(5).iterrows(), 1):
        status = '✅' if row['was_correct'] == '✅' else '❌'
        print(f"║ {idx}. {row['date']} | {row['final_pred']:>3s} ({row['final_prob']:>6s}) | "
              f"{row['change_pct']:>+8s} | {status}       ║")
    
    print("╚════════════════════════════════════════════════════════════╝")
    
    # === PADRÕES DE CONFLUÊNCIA ===
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║         🎯 PADRÕES DE CONFLUÊNCIA MAIS FREQUENTES         ║")
    print("╠════════════════════════════════════════════════════════════╣")
    
    # Padrões M15/H4
    patterns = df_valid.groupby(['m15_trend', 'h4_trend']).size().sort_values(ascending=False)
    for (m15, h4), count in patterns.head(5).items():
        aligned = '✅' if m15 == h4 else '❌'
        df_pattern = df_valid[(df_valid['m15_trend'] == m15) & (df_valid['h4_trend'] == h4)]
        pattern_wins = len(df_pattern[df_pattern['was_correct'] == '✅'])
        pattern_wr = pattern_wins / count if count > 0 else 0
        
        print(f"║ M15: {m15:<8s} + H4: {h4:<8s} {aligned} | {count:>3d}x ({pattern_wr:>6.1%})    ║")
    
    print("╚════════════════════════════════════════════════════════════╝")
    
    # === EXPORT PARA CSV SIMPLIFICADO ===
    print("\n💾 Criando versão simplificada para análise rápida...")
    
    df_simple = df_valid[[
        'date', 'day_of_week', 
        'xgb_pred', 'xgb_prob',
        'm15_trend', 'h4_trend', 'is_aligned', 'alignment_score',
        'final_pred', 'final_prob',
        'result', 'change_pct', 'was_correct'
    ]].copy()
    
    simple_path = csv_path.replace('.csv', '_simplified.csv')
    df_simple.to_csv(simple_path, index=False)
    print(f"✅ Salvo: {simple_path}")
    
    # === RECOMENDAÇÕES ===
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║              💡 RECOMENDAÇÕES                             ║")
    print("╠════════════════════════════════════════════════════════════╣")
    
    if improvement > 0.1:
        print(f"║ ✅ Confluência tem ALTO impacto (+{improvement:.1%})     ║")
        print("║    Priorizar trades com M15 = H4                         ║")
    elif improvement > 0.02:
        print(f"║ ✓ Confluência tem impacto moderado (+{improvement:.1%})   ║")
        print("║    Considerar confluência no screening                   ║")
    else:
        print(f"║ ⚠️ Confluência tem baixo impacto ({improvement:+.1%})      ║")
        print("║    Revisar estratégia de confluence                      ║")
    
    if aligned_wr > 0.60:
        print(f"║ ✅ Trades alinhados com >60% acerto ({aligned_wr:.1%})  ║")
    elif aligned_wr > 0.55:
        print(f"║ ✓ Trades alinhados próximos a 55% acerto ({aligned_wr:.1%}) ║")
    else:
        print(f"║ ⚠️ Trades alinhados abaixo de 55% ({aligned_wr:.1%})    ║")
    
    print("╚════════════════════════════════════════════════════════════╝")
    
    print(f"\n✅ Análise completa!")
    print(f"\n📊 Arquivos gerados:")
    print(f"   • Original: {csv_path}")
    print(f"   • Simplificado: {simple_path}")


def main():
    parser = argparse.ArgumentParser(description='Analisar resultados do Daily Backtest')
    parser.add_argument('csv_file', nargs='?', help='Arquivo CSV do backtest')
    parser.add_argument('--latest', action='store_true', help='Usar arquivo mais recente')
    
    args = parser.parse_args()
    
    # Se não especificou arquivo, procurar o mais recente
    if args.latest or not args.csv_file:
        backtest_dir = Path('backtest_results')
        if not backtest_dir.exists():
            print("❌ Diretório 'backtest_results' não encontrado")
            return
        
        csv_files = sorted(backtest_dir.glob('backtest_*.csv'))
        if not csv_files:
            print("❌ Nenhum arquivo backtest encontrado")
            return
        
        csv_path = str(csv_files[-1])
        print(f"📂 Usando arquivo mais recente: {csv_path}\n")
    else:
        csv_path = args.csv_file
    
    analyze_backtest_csv(csv_path)


if __name__ == '__main__':
    main()
