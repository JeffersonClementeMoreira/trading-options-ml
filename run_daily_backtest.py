#!/usr/bin/env python3
"""
Daily Backtest Runner com Multi-Timeframe Confluence

Uso:
    python3 run_daily_backtest.py                    # Últimos 30 dias
    python3 run_daily_backtest.py --days 60          # Últimos 60 dias
    python3 run_daily_backtest.py --start 2026-01-01 --end 2026-05-25
    python3 run_daily_backtest.py --full             # Todos os dados
"""

import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar path
sys.path.insert(0, '/home/ubuntu/pessoal/options')

from core.daily_backtester import DailyBacktester


def main():
    parser = argparse.ArgumentParser(description='Daily Backtest com Confluência Multi-TF')
    parser.add_argument('--days', type=int, default=30, help='Últimos N dias (padrão: 30)')
    parser.add_argument('--start', type=str, help='Data início (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='Data fim (YYYY-MM-DD)')
    parser.add_argument('--full', action='store_true', help='Usar todos os dados')
    parser.add_argument('--output', type=str, default='backtest_results', help='Diretório output')
    parser.add_argument('--no-model', action='store_true', help='Usar apenas análise técnica (sem XGBoost)')
    
    args = parser.parse_args()
    
    # Definir caminhos
    data_path = '/home/ubuntu/pessoal/options/dados/EURUSD_M15_202301012200_202605222015.csv'
    model_path = '/home/ubuntu/pessoal/options/models/xgboost_model.pkl' if not args.no_model else None
    
    # Verificar arquivos
    if not Path(data_path).exists():
        print(f"❌ Arquivo de dados não encontrado: {data_path}")
        return
    
    if model_path and not Path(model_path).exists():
        print(f"⚠️ Modelo XGBoost não encontrado: {model_path}")
        print("   Usando apenas análise técnica...")
        model_path = None
    
    # Criar backtester
    print("\n" + "="*80)
    print("🚀 MULTI-TIMEFRAME CONFLUENCE DAILY BACKTESTER")
    print("="*80)
    
    backtester = DailyBacktester(
        data_path=data_path,
        model_path=model_path,
        output_dir=args.output
    )
    
    # Determinar período
    if args.full:
        start_date = None
        end_date = None
        print("\n📊 Modo: TODOS OS DADOS")
    elif args.start and args.end:
        start_date = args.start
        end_date = args.end
        print(f"\n📊 Modo: {start_date} a {end_date}")
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
        print(f"\n📊 Modo: Últimos {args.days} dias ({start_date} a {end_date})")
    
    # Rodar backtest
    backtester.run_backtest(start_date=start_date, end_date=end_date)
    
    # Salvar resultados
    csv_file = backtester.save_results_to_csv()
    
    # Mostrar amostra
    backtester.print_sample_results(n=10)
    
    print(f"\n{'='*80}")
    print(f"✅ BACKTEST CONCLUÍDO")
    print(f"{'='*80}")
    print(f"\n📁 Resultados salvos em: {csv_file}")
    print(f"\n💡 Para visualizar os resultados:")
    print(f"   • Abrir em Excel/Google Sheets: {csv_file}")
    print(f"   • Usar Pandas: pd.read_csv('{csv_file}')")
    print(f"\n🎯 Você pode analisar:")
    print(f"   • Taxa de acerto com confluência vs sem")
    print(f"   • Impacto do ajuste de confiança")
    print(f"   • Padrões por dia da semana")
    print(f"   • Trades com melhor/pior performance")


if __name__ == '__main__':
    main()
