#!/usr/bin/env python3
"""
Enriquecer Backtest Results com colunas de análise
Adiciona: Decision, Reasons, Result, Quality Score
Cria arquivo ENHANCED para análise rápida
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def calculate_decision(row):
    """Calcular decisão de entrada/hold"""
    conf = row.get('confidence_pct', 0)
    
    # Simular confluence score baseado em indicadores
    confluence = 0
    if row.get('price_above_sma20', 0) == 1:
        confluence += 1
    if row.get('price_above_sma50', 0) == 1:
        confluence += 1
    if row.get('macd_positive', 0) == 1:
        confluence += 1
    if row.get('momentum_positive', 0) == 1:
        confluence += 1
    if row.get('rsi_oversold', 0) == 0 and row.get('rsi_overbought', 0) == 0:
        confluence += 1
    
    # Decisão: ENTER se bom sinal, HOLD se fraco
    if conf >= 90 and confluence >= 3:
        return "ENTER"
    elif conf >= 85 and confluence >= 2:
        return "HOLD"  # Possível, mas aguardar melhor setup
    else:
        return "SKIP"

def calculate_result(actual_pips):
    """Calcular resultado do sinal"""
    if actual_pips > 0:
        return "WIN"
    elif actual_pips < 0:
        return "LOSS"
    else:
        return "BREAKEVEN"

def calculate_reasons(row):
    """Calcular motivos/razões do sinal"""
    reasons = []
    
    conf = row.get('confidence_pct', 0)
    if conf >= 95:
        reasons.append("VeryHighConf")
    elif conf >= 90:
        reasons.append("HighConf")
    elif conf >= 85:
        reasons.append("GoodConf")
    
    # Refinement score (quanto foi refinado)
    refinement = row.get('refinement_score', 0)
    if refinement > 0.8:
        reasons.append("ExcelRef")  # Excelente refinement
    elif refinement > 0.5:
        reasons.append("GoodRef")   # Bom refinement
    else:
        reasons.append("ModRef")     # Moderado
    
    # Direção refinada
    direction_changed = row.get('direction_changed', 0)
    ensemble_dir = row.get('ensemble_direction', '')
    if direction_changed == 1:
        reasons.append(f"DirChange-{ensemble_dir}")
    
    # SMC (Smart Money Concepts)
    if row.get('smc_order_block', 0) == 1:
        reasons.append("OrderBlock")
    if row.get('smc_fvg', 0) == 1:
        reasons.append("FVG")
    
    # Indicadores confluentes
    confluence_count = 0
    if row.get('price_above_sma20', 0) == 1:
        confluence_count += 1
    if row.get('price_above_sma50', 0) == 1:
        confluence_count += 1
    if row.get('macd_positive', 0) == 1:
        confluence_count += 1
    if row.get('momentum_positive', 0) == 1:
        confluence_count += 1
    
    if confluence_count >= 4:
        reasons.append("4Confluent")
    elif confluence_count >= 3:
        reasons.append("3Confluent")
    
    return " | ".join(reasons) if reasons else "Neutral"

def calculate_quality_score(row):
    """Calcular score de qualidade do sinal (1-5)"""
    score = 1
    
    conf = row.get('confidence_pct', 0)
    if conf >= 95:
        score += 1.5
    elif conf >= 90:
        score += 1
    elif conf >= 85:
        score += 0.5
    
    refinement = row.get('refinement_score', 0)
    if refinement >= 0.8:
        score += 1
    elif refinement >= 0.5:
        score += 0.5
    
    # Confluence
    confluence = 0
    if row.get('price_above_sma20', 0) == 1:
        confluence += 1
    if row.get('price_above_sma50', 0) == 1:
        confluence += 1
    if row.get('macd_positive', 0) == 1:
        confluence += 1
    if row.get('momentum_positive', 0) == 1:
        confluence += 1
    
    if confluence >= 4:
        score += 0.5
    elif confluence >= 3:
        score += 0.25
    
    return min(5, score)  # Max 5

def enhance_backtest_file(asset_name):
    """Enriquecer arquivo backtest de um ativo"""
    
    results_dir = Path('results')
    input_file = results_dir / f'backtest_{asset_name}_DETAILED.csv'
    output_file = results_dir / f'ANALYSIS_{asset_name}_ENHANCED.csv'
    
    if not input_file.exists():
        print(f"❌ {asset_name}: Arquivo não encontrado: {input_file}")
        return None
    
    try:
        # Ler arquivo
        df = pd.read_csv(input_file)
        print(f"📊 {asset_name}: {len(df)} linhas carregadas")
        
        # Calcular novas colunas
        df['decision'] = df.apply(calculate_decision, axis=1)
        df['reasons'] = df.apply(calculate_reasons, axis=1)
        df['result'] = df['actual_pips'].apply(calculate_result)
        df['quality_score'] = df.apply(calculate_quality_score, axis=1)
        
        # Reordenar colunas para análise rápida
        priority_cols = [
            'timestamp',
            'close',
            'ensemble_direction',
            'refined_direction',
            'confidence_pct',
            'quality_score',
            'decision',
            'actual_pips',
            'result',
            'reasons',
            'predicted_pips',
            'predicted_price_ensemble',
            'target_price'
        ]
        
        # Adicionar todas as colunas restantes
        remaining_cols = [col for col in df.columns if col not in priority_cols]
        final_cols = priority_cols + remaining_cols
        final_cols = [col for col in final_cols if col in df.columns]
        
        df_final = df[final_cols]
        
        # Salvar
        df_final.to_csv(output_file, index=False)
        print(f"✅ {asset_name}: Salvo em {output_file}")
        
        # Estatísticas rápidas
        enters = len(df[df['decision'] == 'ENTER'])
        wins = len(df[df['result'] == 'WIN'])
        losses = len(df[df['result'] == 'LOSS'])
        avg_quality = df['quality_score'].mean()
        total_pips = df['actual_pips'].sum()
        
        stats = {
            "asset": asset_name,
            "total_candles": len(df),
            "enter_signals": enters,
            "wins": wins,
            "losses": losses,
            "win_rate": f"{(wins/(wins+losses)*100) if (wins+losses)>0 else 0:.1f}%",
            "avg_quality": f"{avg_quality:.2f}",
            "avg_confidence": f"{df['confidence_pct'].mean():.1f}%",
            "total_pips": f"{total_pips:.0f}",
            "avg_pips_per_signal": f"{total_pips/enters:.2f}" if enters > 0 else "0"
        }
        
        return stats
        
    except Exception as e:
        print(f"❌ {asset_name}: Erro - {str(e)}")
        return None

def main():
    """Enriquecer todos os ativos"""
    
    assets = ['EURUSD', 'GBPUSD', 'EURAUD', 'EURJPY', 'NZDUSD', 'GOLD']
    
    print("\n" + "="*80)
    print("🚀 ENRIQUECENDO BACKTEST RESULTS COM ANÁLISE")
    print("="*80)
    print()
    
    all_stats = []
    
    for asset in assets:
        stats = enhance_backtest_file(asset)
        if stats:
            all_stats.append(stats)
    
    # Resumo geral
    print("\n" + "="*80)
    print("📊 RESUMO GERAL")
    print("="*80)
    print()
    
    if all_stats:
        # Mostrar em tabela
        from tabulate import tabulate
        
        headers = [
            "ATIVO", "CANDLES", "ENTERS", "WINS", "LOSSES", 
            "WR%", "QUALITY", "CONF%", "PIPS", "PIPS/SINAL"
        ]
        
        table_data = []
        for stat in all_stats:
            table_data.append([
                stat['asset'],
                stat['total_candles'],
                stat['enter_signals'],
                stat['wins'],
                stat['losses'],
                stat['win_rate'],
                stat['avg_quality'],
                stat['avg_confidence'],
                stat['total_pips'],
                stat['avg_pips_per_signal']
            ])
        
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        print()
    
    # Salvar dashboard
    dashboard = {
        "timestamp": datetime.now().isoformat(),
        "assets": all_stats,
        "version": "1.0"
    }
    
    dashboard_file = Path('results/analysis_dashboard.json')
    with open(dashboard_file, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"💾 Dashboard salvo: {dashboard_file}")
    print()
    
    # Instruções de uso
    print("="*80)
    print("📁 COMO USAR OS ARQUIVOS GERADOS")
    print("="*80)
    print()
    print("Novos arquivos criados:")
    print("  ✅ results/ANALYSIS_EURUSD_ENHANCED.csv")
    print("  ✅ results/ANALYSIS_GBPUSD_ENHANCED.csv")
    print("  ✅ results/ANALYSIS_EURAUD_ENHANCED.csv")
    print("  ✅ results/ANALYSIS_EURJPY_ENHANCED.csv")
    print("  ✅ results/ANALYSIS_NZDUSD_ENHANCED.csv")
    print("  ✅ results/ANALYSIS_GOLD_ENHANCED.csv")
    print()
    print("Para análise rápida:")
    print("  → Abrir em Excel/Calc")
    print("  → Colunas prioritárias: timestamp | direction | confidence | decision | result")
    print()
    print("Colunas úteis:")
    print("  • decision: ENTER (bom sinal), HOLD (pode melhorar), SKIP (fraco)")
    print("  • reasons: Motivos (HighConf, GoodRef, 3Confluent, OrderBlock, etc)")
    print("  • result: WIN, LOSS, BREAKEVEN")
    print("  • quality_score: 1-5 (5 = sinal perfeito)")
    print()
    
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
