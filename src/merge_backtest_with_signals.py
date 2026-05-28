#!/usr/bin/env python3
"""
Unifica BACKTEST_DETAILED com ACTIONABLE_SIGNALS em um único arquivo.

Entrada:
  - backtest_{symbol}_DETAILED.csv (17,871 linhas com todas as amostras)
  - ACTIONABLE_SIGNALS_{symbol}.csv (101 linhas com decisões de entrada)

Saída:
  - UNIFIED_{symbol}_COMPLETE.csv (17,871 linhas com indicadores + decisões)

Lógica:
  1. Para cada linha do backtest, verificar se há sinal correspondente
  2. Se há sinal → adicionar Decision (ENTER/SKIP) + Reasons + Quality Score
  3. Se não há sinal → marcar como "NO_SIGNAL"
"""

import pandas as pd
import sys
from pathlib import Path

def merge_backtest_with_signals(symbol='EURUSD', backtest_file=None, signals_file=None, output_file=None):
    """
    Unifica backtest detalhado com sinais acionáveis.
    
    Args:
        symbol: Ativo (ex: EURUSD)
        backtest_file: Caminho customizado para backtest_DETAILED
        signals_file: Caminho customizado para ACTIONABLE_SIGNALS
        output_file: Caminho customizado para saída
    
    Returns:
        DataFrame unificado
    """
    
    # Definir caminhos padrão
    if backtest_file is None:
        backtest_file = f'results/backtest_{symbol}_DETAILED.csv'
    if signals_file is None:
        signals_file = f'results/ACTIONABLE_SIGNALS_{symbol}.csv'
    if output_file is None:
        output_file = f'results/UNIFIED_{symbol}_COMPLETE.csv'
    
    print(f"\n{'='*80}")
    print(f"🔗 UNIFICANDO BACKTEST + SIGNALS para {symbol}")
    print(f"{'='*80}")
    
    # Verificar arquivos existem
    if not Path(backtest_file).exists():
        print(f"❌ Arquivo não encontrado: {backtest_file}")
        return None
    
    if not Path(signals_file).exists():
        print(f"❌ Arquivo não encontrado: {signals_file}")
        return None
    
    print(f"\n📂 Carregando arquivos...")
    print(f"   📄 {backtest_file}")
    backtest = pd.read_csv(backtest_file)
    print(f"      → {len(backtest):,} linhas")
    
    print(f"   📄 {signals_file}")
    signals = pd.read_csv(signals_file)
    print(f"      → {len(signals)} sinais")
    
    # Normalizar timestamps
    print(f"\n🔄 Normalizando timestamps...")
    
    # Encontrar coluna de tempo no backtest (pode ser 'timestamp' ou outra)
    backtest_time_col = None
    for col in backtest.columns:
        if 'time' in col.lower() or 'date' in col.lower():
            backtest_time_col = col
            break
    
    if backtest_time_col is None:
        print(f"❌ Coluna de timestamp não encontrada no backtest")
        return None
    
    # Encontrar coluna de tempo nos sinais
    signals_time_col = [col for col in signals.columns if 'time' in col.lower() or 'entry' in col.lower()][0]
    
    backtest['_timestamp'] = pd.to_datetime(backtest[backtest_time_col])
    signals['_timestamp'] = pd.to_datetime(signals[signals_time_col])
    
    print(f"   ✅ Coluna backtest: {backtest_time_col}")
    print(f"   ✅ Coluna sinais: {signals_time_col}")
    
    # Merge left (manter todas as linhas do backtest)
    print(f"\n🔀 Fazendo merge...")
    unified = backtest.merge(
        signals[['_timestamp', 'Signal Time (ENTRY)', 'Decision', 'Reasons', 
                'Quality Score', 'Criteria Count', 'High Conf (≥90%)', 
                'Good Ref (≥0.6)', 'Excel Ref (≥0.75)', 'Dir History', 'Result']],
        on='_timestamp',
        how='left'
    )
    
    # Preencher NaN com "NO_SIGNAL"
    unified['Decision'] = unified['Decision'].fillna('NO_SIGNAL')
    unified['Reasons'] = unified['Reasons'].fillna('-')
    unified['Quality Score'] = unified['Quality Score'].fillna(0.0)
    unified['Result'] = unified['Result'].fillna('-')
    
    # Contar sinais encontrados
    signals_found = (unified['Decision'] != 'NO_SIGNAL').sum()
    
    print(f"   ✅ {signals_found}/{len(signals)} sinais mapeados")
    print(f"   ✅ {len(unified) - signals_found} amostras sem sinal")
    
    # Reordenar colunas
    print(f"\n📋 Reorganizando colunas...")
    
    # Identificar colunas de indicador (todas exceto as da primeira parte)
    core_cols = [backtest_time_col, 'open', 'high', 'low', 'close', 'target_price', 
                 'predicted_price_xgb', 'predicted_price_rf', 'predicted_price_ensemble',
                 'confidence_pct', 'ensemble_direction', 'refined_direction', 'refinement_score',
                 'predicted_pips', 'actual_pips', 'error_pips']
    
    indicator_cols = [col for col in backtest.columns if col not in core_cols and col != '_timestamp']
    
    # Colunas da decisão
    decision_cols = ['Decision', 'Reasons', 'Quality Score', 'Criteria Count',
                     'High Conf (≥90%)', 'Good Ref (≥0.6)', 'Excel Ref (≥0.75)', 
                     'Dir History', 'Result']
    
    # Ordem final
    final_order = (core_cols + indicator_cols + decision_cols)
    final_order = [col for col in final_order if col in unified.columns]
    
    unified = unified[final_order]
    
    # Salvar
    print(f"\n💾 Salvando arquivo unificado...")
    unified.to_csv(output_file, index=False)
    print(f"   ✅ {output_file}")
    
    # Estatísticas finais
    print(f"\n📊 RESUMO FINAL:")
    print(f"   Total linhas: {len(unified):,}")
    print(f"   Colunas: {len(unified.columns)}")
    print(f"   Sinais ENTER: {(unified['Decision'] == 'ENTER').sum()}")
    print(f"   Sinais SKIP: {(unified['Decision'] == 'SKIP').sum()}")
    print(f"   Sem sinal: {(unified['Decision'] == 'NO_SIGNAL').sum()}")
    
    print(f"\n✅ Unificação concluída!\n")
    
    return unified


if __name__ == "__main__":
    
    symbol = 'EURUSD'
    
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
    
    merge_backtest_with_signals(symbol)
