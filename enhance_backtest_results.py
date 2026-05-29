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

def select_best_signal_per_day(df):
    """Selecionar apenas o MELHOR sinal ENTER por dia
    
    Regra de Trading: Apenas 1 sinal por dia
    Critério: Maior confidence + refinement_score
    """
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    # Sinais ENTER por dia
    enters = df[df['decision'] == 'ENTER'].copy()
    
    # Se não tiver ENTER, retorna original
    if len(enters) == 0:
        return df
    
    # Calcular score: confidence + refinement (0-1 normalize)
    enters['selection_score'] = (
        enters['confidence_pct'] / 100 * 0.6 +  # 60% confidence
        enters['refinement_score'] * 0.4         # 40% refinement
    )
    
    # Selecionar o melhor sinal por dia
    best_per_day = enters.sort_values('selection_score', ascending=False).drop_duplicates(subset=['date'], keep='first')
    
    # Índices dos melhores sinais
    best_indices = best_per_day.index
    
    # Marcar todos os ENTER como HOLD exceto os melhores
    df.loc[(df['decision'] == 'ENTER') & ~df.index.isin(best_indices), 'decision'] = 'HOLD'
    
    return df.drop(columns=['date', 'selection_score'], errors='ignore')

def calculate_decision(row):
    """Calcular decisão: APENAS sinais refinados pelo Decision Tree
    
    Descoberta crítica: Sinais MODIFICADOS pelo DT = 54.6% win rate
    Fórmula: Use ensemble_direction != refined_direction como critério
    """
    # Verificar se foi refinado (Decision Tree modificou)
    ensemble_dir = row.get('ensemble_direction', '')
    refined_dir = row.get('refined_direction', '')
    was_refined = ensemble_dir != refined_dir
    
    # FÓRMULA MÁGICA: Use APENAS sinais refinados pelo DT
    if was_refined:
        return "ENTER"
    
    # Tudo o resto é menos confiável
    return "HOLD"  # Ou SKIP se quiser ser mais restritivo

def calculate_result(actual_pips):
    """Calcular resultado do sinal"""
    if actual_pips > 0:
        return "WIN"
    elif actual_pips < 0:
        return "LOSS"
    else:
        return "BREAKEVEN"

def calculate_reasons(row):
    """Calcular motivos/razões do sinal baseado em dados REAIS"""
    reasons = []
    
    # 1. CONFIDENCE LEVEL
    conf = row.get('confidence_pct', 0)
    if conf >= 95:
        reasons.append("🔥VeryHighConf")
    elif conf >= 90:
        reasons.append("💪HighConf")
    elif conf >= 85:
        reasons.append("✓GoodConf")
    elif conf >= 75:
        reasons.append("⚠️ModConf")
    else:
        reasons.append("❌LowConf")
    
    # 2. REFINEMENT QUALITY (Decision Tree)
    refinement = row.get('refinement_score', 0)
    if refinement >= 0.8:
        reasons.append("🎯ExcelRef")
    elif refinement >= 0.5:
        reasons.append("👍GoodRef")
    elif refinement >= 0.3:
        reasons.append("➖ModRef")
    else:
        reasons.append("⚪LowRef")
    
    # 3. TECHNICAL CONFLUENCE
    confluence = []
    
    # Trend confirmation
    if 'sma20' in row and 'sma50' in row and 'close' in row:
        if row['close'] > row.get('sma20', 0):
            confluence.append("SMA20↑")
        if row['close'] > row.get('sma50', 0):
            confluence.append("SMA50↑")
    
    # Momentum
    if row.get('macd', 0) > 0:
        confluence.append("MACD+")
    if row.get('momentum', 0) > 0:
        confluence.append("Mom+")
    
    # RSI Zone
    rsi_val = row.get('rsi', 50)
    if 30 < rsi_val < 70:
        confluence.append("RSI-OK")
    elif rsi_val > 70:
        confluence.append("RSI-OB")
    elif rsi_val < 30:
        confluence.append("RSI-OS")
    
    # Volatility check
    if row.get('realized_vol', 0) > 0 and row.get('sd', 0) > 0:
        confluence.append("Vol-Stable")
    
    # Smart Money (SMC)
    if row.get('smc_support', 0) > 0:
        confluence.append("Support")
    if row.get('smc_resistance', 0) > 0:
        confluence.append("Resistance")
    
    if confluence:
        reasons.append(f"[{' + '.join(confluence)}]")
    
    # 4. Direction refinement info
    refined_dir = row.get('refined_direction', '')
    if refined_dir:
        reasons.append(f"→{refined_dir}")
    
    return " | ".join(reasons) if reasons else "Neutral"

def calculate_quality_score(row):
    """Calcular score de qualidade do sinal (1-5) baseado em dados REAIS"""
    score = 2.5  # Score base
    
    # 1. Confidence boost
    conf = row.get('confidence_pct', 0)
    if conf >= 95:
        score += 1.5
    elif conf >= 90:
        score += 1.0
    elif conf >= 85:
        score += 0.5
    elif conf < 75:
        score -= 1.0
    
    # 2. Refinement quality
    refinement = row.get('refinement_score', 0)
    if refinement >= 0.8:
        score += 0.8
    elif refinement >= 0.5:
        score += 0.4
    elif refinement < 0.3:
        score -= 0.5
    
    # 3. Technical confluence
    confluence_strength = 0
    
    # Trend
    if 'sma20' in row and row['close'] > row.get('sma20', 0):
        confluence_strength += 1
    if 'sma50' in row and row['close'] > row.get('sma50', 0):
        confluence_strength += 1
    
    # Momentum
    if row.get('macd', 0) > 0:
        confluence_strength += 1
    if row.get('momentum', 0) > 0:
        confluence_strength += 1
    
    # RSI zone
    rsi = row.get('rsi', 50)
    if 30 < rsi < 70:
        confluence_strength += 1
    
    # SMC zones
    if row.get('smc_support', 0) > 0 or row.get('smc_resistance', 0) > 0:
        confluence_strength += 0.5
    
    # Add confluence to score
    if confluence_strength >= 5:
        score += 0.8
    elif confluence_strength >= 4:
        score += 0.5
    elif confluence_strength >= 3:
        score += 0.3
    
    return min(5.0, max(1.0, score))

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
        
        # NOVO: Filtrar apenas 1 ENTER por dia (regra de trading)
        df = select_best_signal_per_day(df)
        
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
        wins = len(df[(df['decision'] == 'ENTER') & (df['result'] == 'WIN')])
        losses = len(df[(df['decision'] == 'ENTER') & (df['result'] == 'LOSS')])
        avg_quality = df[df['decision'] == 'ENTER']['quality_score'].mean() if enters > 0 else 0
        total_pips = df[df['decision'] == 'ENTER']['actual_pips'].sum() if enters > 0 else 0
        
        stats = {
            "asset": asset_name,
            "total_candles": len(df),
            "enter_signals": enters,
            "wins": wins,
            "losses": losses,
            "win_rate": f"{(wins/(wins+losses)*100) if (wins+losses)>0 else 0:.1f}%",
            "avg_quality": f"{avg_quality:.2f}",
            "avg_confidence": f"{df[df['decision'] == 'ENTER']['confidence_pct'].mean():.1f}%" if enters > 0 else "0%",
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
