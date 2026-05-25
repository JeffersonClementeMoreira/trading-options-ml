#!/usr/bin/env python3
"""
Master Script - Backtest Completo com Multi-Timeframe Confluence + Análise de Sweeps

Roda tudo em uma vez:
1. Backtest dia-a-dia
2. Análise de resultados
3. Detecção de sweeps em H4
4. Validação em M15
5. Gera relatório visual

Uso:
    python3 backtest_complete.py                         # EURUSD, Últimos 30 dias
    python3 backtest_complete.py --symbol EURUSD 60      # EURUSD, Últimos 60 dias
    python3 backtest_complete.py --symbol EURUSD --full  # EURUSD, Todos os dados
    python3 backtest_complete.py --start 2026-03-01 --end 2026-05-25  # Período específico
    python3 backtest_complete.py --symbols               # Listar ativos disponíveis
"""

import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import pandas as pd
import glob

# Adicionar path
sys.path.insert(0, '/home/ubuntu/pessoal/options')

from core.daily_backtester import DailyBacktester


def get_available_symbols():
    """Lista ativos disponíveis."""
    data_dir = Path('/home/ubuntu/pessoal/options/dados')
    files = data_dir.glob('*M15*processed.csv')
    
    symbols = []
    for f in files:
        # Extrair símbolo do nome: EURUSD_M15_...
        parts = f.stem.split('_')
        if parts[1] == 'M15':
            symbols.append(parts[0])
    
    return sorted(set(symbols))


def find_data_file(symbol: str) -> Optional[str]:
    """Encontra arquivo de dados para o símbolo."""
    data_dir = Path('/home/ubuntu/pessoal/options/dados')
    pattern = f"{symbol}_M15*processed.csv"
    files = list(data_dir.glob(pattern))
    
    if files:
        return str(files[0])
    return None


def main():
    parser = argparse.ArgumentParser(
        description='Backtest Completo com Multi-Timeframe Confluence + Análise de Sweeps',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLOS:

  # Últimos 30 dias (padrão)
  python3 backtest_complete.py

  # EURUSD, últimos 60 dias
  python3 backtest_complete.py 60

  # EURUSD, período específico
  python3 backtest_complete.py --start 2026-03-01 --end 2026-05-25

  # Todos os dados (3.5 anos)
  python3 backtest_complete.py --full

  # Listar ativos disponíveis
  python3 backtest_complete.py --symbols

ANÁLISE DE SWEEPS + CONFLUENCE:
  A estratégia funcionará assim:
  1. Detecta SWEEP em H4 (breakout de estrutura)
  2. Valida M15 para confirmar movimento
  3. Verifica se momentum está reduzindo (kamma, aceleração)
  4. Combina com confluência para filtrar sinais
  5. Salva tudo em CSV para análise manual
        """
    )
    parser.add_argument('days', nargs='?', type=int, default=30, help='Últimos N dias (padrão: 30)')
    parser.add_argument('--symbol', type=str, default='EURUSD', help='Ativo (EURUSD, GBPUSD, etc)')
    parser.add_argument('--symbols', action='store_true', help='Listar ativos disponíveis')
    parser.add_argument('--full', action='store_true', help='Usar todos os dados')
    parser.add_argument('--start', type=str, help='Data início (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='Data fim (YYYY-MM-DD)')
    parser.add_argument('--output', type=str, default='backtest_results', help='Diretório output')
    parser.add_argument('--detect-sweeps', action='store_true', help='Detectar sweeps em H4')
    
    args = parser.parse_args()
    
    # Listar ativos disponíveis
    if args.symbols:
        symbols = get_available_symbols()
        print("\n📊 ATIVOS DISPONÍVEIS:\n")
        for sym in symbols:
            data_file = find_data_file(sym)
            if data_file:
                df = pd.read_csv(data_file)
                print(f"   ✓ {sym:<10} ({len(df)} candles)")
        print()
        return 0
    
    print("\n" + "="*80)
    print("🚀 MULTI-TIMEFRAME CONFLUENCE - DAILY BACKTEST")
    print("="*80 + "\n")
    
    # === Encontrar arquivo de dados ===
    print(f"🔍 Procurando dados para {args.symbol}...")
    data_path = find_data_file(args.symbol)
    
    if not data_path:
        available = get_available_symbols()
        print(f"❌ Nenhum arquivo encontrado para {args.symbol}")
        print(f"\n📊 Ativos disponíveis: {', '.join(available)}")
        print(f"\nUse: python3 backtest_complete.py --symbol {available[0] if available else 'EURUSD'}")
        return 1
    
    print(f"✅ Encontrado: {Path(data_path).name}")
    
    model_path = '/home/ubuntu/pessoal/options/models/xgboost_model.pkl'
    
    # Verificar modelo
    if not Path(model_path).exists():
        print(f"⚠️ Modelo não encontrado")
        print("   Usando apenas análise técnica (M15 vs H4)...\n")
        model_path = None
    else:
        print(f"✅ Modelo XGBoost encontrado\n")
    
    # === Criar backtester ===
    print(f"📊 Carregando dados...")
    backtester = DailyBacktester(
        data_path=data_path,
        model_path=model_path,
        output_dir=args.output
    )
    
    # === Determinar período ===
    if args.full:
        start_date = None
        end_date = None
        period_desc = "TODOS OS DADOS"
    elif args.start and args.end:
        start_date = args.start
        end_date = args.end
        period_desc = f"{start_date} a {end_date}"
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
        period_desc = f"Últimos {args.days} dias"
    
    print(f"📅 Período: {period_desc}")
    print(f"   Ativo: {args.symbol}\n")
    
    # === RODAR BACKTEST ===
    print(f"\n{'='*80}")
    print(f"FASE 1: BACKTEST DIA-A-DIA")
    print(f"{'='*80}\n")
    
    backtester.run_backtest(start_date=start_date, end_date=end_date)
    
    # === SALVAR RESULTADOS ===
    print(f"\n{'='*80}")
    print(f"FASE 2: SALVAR RESULTADOS")
    print(f"{'='*80}\n")
    
    csv_file = backtester.save_results_to_csv()
    
    # === ANÁLISE ===
    print(f"\n{'='*80}")
    print(f"FASE 3: ANÁLISE DETALHADA")
    print(f"{'='*80}\n")
    
    analyze_backtest_csv(csv_file)
    
    # === SUMÁRIO FINAL ===
    print(f"\n{'='*80}")
    print(f"✅ BACKTEST CONCLUÍDO COM SUCESSO!")
    print(f"{'='*80}\n")
    
    print(f"📊 Arquivos gerados:")
    print(f"   • Principal: {csv_file}")
    print(f"   • Simplificado: {csv_file.replace('.csv', '_simplified.csv')}")
    print(f"\n💡 Próximos passos:")
    print(f"   1. Abrir {csv_file} em Excel/Google Sheets")
    print(f"   2. Analisar padrões por dia/confluência")
    print(f"   3. Validar melhoria de acerto com confluência")
    print(f"   4. Integrar em options_v3.py se resultados > 55%\n")
    
    return 0


def analyze_backtest_csv(csv_path: str):
    """Análise completa do backtest."""
    
    df = pd.read_csv(csv_path)
    df_valid = df[df['was_correct'].isin(['✅', '❌'])].copy()
    
    if len(df_valid) == 0:
        print("⚠️ Sem dados para análise")
        return
    
    # === ESTATÍSTICAS ===
    total = len(df_valid)
    wins = len(df_valid[df_valid['was_correct'] == '✅'])
    win_rate = wins / total
    
    # Com confluência
    aligned = df_valid[df_valid['is_aligned'] == '✅']
    aligned_wins = len(aligned[aligned['was_correct'] == '✅'])
    aligned_wr = aligned_wins / len(aligned) if len(aligned) > 0 else 0
    
    # Sem confluência
    divergent = df_valid[df_valid['is_aligned'] == '❌']
    divergent_wins = len(divergent[divergent['was_correct'] == '✅'])
    divergent_wr = divergent_wins / len(divergent) if len(divergent) > 0 else 0
    
    improvement = aligned_wr - divergent_wr
    
    # Print estatísticas
    print(f"""
╔════════════════════════════════════════════════════════════╗
║              📊 RESULTADO GERAL                           ║
╠════════════════════════════════════════════════════════════╣
║ Total Trades:               {total:<5}                    ║
║ Acertos:                    {wins:<5} ({win_rate:>6.1%})                 ║
║ Taxa de Acerto:             {win_rate:>6.1%}                           ║
╚════════════════════════════════════════════════════════════╝

╔════════════════════════════════════════════════════════════╗
║          🎯 IMPACTO DA CONFLUÊNCIA MULTI-TF               ║
╠════════════════════════════════════════════════════════════╣
║ COM CONFLUÊNCIA (M15 = H4):                              ║
║   {len(aligned):>3} trades | {aligned_wins:>2} acertos ({aligned_wr:>6.1%})                      ║
║                                                            ║
║ SEM CONFLUÊNCIA (M15 ≠ H4):                              ║
║   {len(divergent):>3} trades | {divergent_wins:>2} acertos ({divergent_wr:>6.1%})                      ║
║                                                            ║
║ 📈 MELHORIA COM CONFLUÊNCIA:  {improvement:+.1%}                    ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Print padrões
    print(f"""
╔════════════════════════════════════════════════════════════╗
║         🎯 PADRÕES DE CONFLUÊNCIA MAIS COMUNS             ║
╠════════════════════════════════════════════════════════════╣
    """)
    
    patterns = df_valid.groupby(['m15_trend', 'h4_trend']).size().sort_values(ascending=False)
    for (m15, h4), count in patterns.head(5).items():
        aligned_symbol = '✅' if m15 == h4 else '❌'
        df_pattern = df_valid[(df_valid['m15_trend'] == m15) & (df_valid['h4_trend'] == h4)]
        pattern_wins = len(df_pattern[df_pattern['was_correct'] == '✅'])
        pattern_wr = pattern_wins / count if count > 0 else 0
        
        print(f"║ M15: {m15:<8s} | H4: {h4:<8s} {aligned_symbol} | {count:>3d}x ({pattern_wr:>6.1%})    ║")
    
    print(f"""║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Recomendações
    print(f"""
╔════════════════════════════════════════════════════════════╗
║              💡 RECOMENDAÇÕES                             ║
╠════════════════════════════════════════════════════════════╣
    """)
    
    if improvement > 0.10:
        print(f"║ ✅ Confluência tem ALTO impacto (+{improvement:.1%})      ║")
        print(f"║    → USAR como filtro principal                          ║")
    elif improvement > 0.05:
        print(f"║ ✓ Confluência tem impacto moderado (+{improvement:.1%})    ║")
        print(f"║    → CONSIDERAR no screening                             ║")
    else:
        print(f"║ ⚠️ Confluência tem baixo impacto ({improvement:+.1%})       ║")
        print(f"║    → REVISAR estratégia                                  ║")
    
    if aligned_wr > 0.60:
        print(f"║ ✅ Trades alinhados: {aligned_wr:.1%} (EXCELENTE)           ║")
    elif aligned_wr > 0.55:
        print(f"║ ✓ Trades alinhados: {aligned_wr:.1%} (BOM)                ║")
    else:
        print(f"║ ⚠️ Trades alinhados: {aligned_wr:.1%} (REVISAR)            ║")
    
    print(f"""║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Criar CSV simplificado
    df_simple = df_valid[[
        'date', 'day_of_week',
        'm15_trend', 'h4_trend', 'is_aligned', 'alignment_score',
        'final_pred', 'final_prob',
        'result', 'change_pct', 'was_correct'
    ]].copy()
    
    simple_path = csv_path.replace('.csv', '_simplified.csv')
    df_simple.to_csv(simple_path, index=False)
    print(f"✅ CSV simplificado salvo: {simple_path}\n")


if __name__ == '__main__':
    exit(main())
