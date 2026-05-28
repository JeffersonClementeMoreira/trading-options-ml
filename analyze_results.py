#!/usr/bin/env python3
"""
Análise de Resultados - Todos os Ativos
Gera dashboard e relatório de performance
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

def analyze_asset(asset_name):
    """Analisar performance de um ativo"""
    
    results_dir = Path('results')
    csv_file = results_dir / f'UNIFIED_SIGNALS_{asset_name}.csv'
    
    if not csv_file.exists():
        return {
            "status": "❌ Arquivo não encontrado",
            "asset": asset_name
        }
    
    try:
        df = pd.read_csv(csv_file)
        
        # Métricas
        total_signals = len(df)
        wins = (df['Result'] == 'WIN').sum()
        win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
        total_pips = df['Actual Pips'].sum() if 'Actual Pips' in df.columns else 0
        avg_confidence = df['Confidence %'].mean() if 'Confidence %' in df.columns else 0
        avg_confluence = df.get('Confluence Score', [3]).mean() if 'Confluence Score' in df.columns else 3
        
        return {
            "asset": asset_name,
            "status": "✅ OK",
            "total_signals": total_signals,
            "wins": wins,
            "losses": total_signals - wins,
            "win_rate": f"{win_rate:.1f}%",
            "total_pips": f"{total_pips:+.1f}",
            "avg_confidence": f"{avg_confidence:.1f}%",
            "avg_confluence": f"{avg_confluence:.1f}",
            "rating": "🟢 GOOD" if win_rate > 60 else "🟡 OK" if win_rate > 50 else "🔴 POOR"
        }
    except Exception as e:
        return {
            "asset": asset_name,
            "status": f"⚠️ Erro: {str(e)[:30]}"
        }

def main():
    """Gerar relatório completo"""
    
    assets = ['EURUSD', 'GBPUSD', 'EURAUD', 'EURJPY', 'NZDUSD', 'GOLD']
    
    print("\n")
    print("╔" + "═" * 98 + "╗")
    print("║" + " " * 30 + "📊 ANÁLISE DE PERFORMANCE" + " " * 44 + "║")
    print("╚" + "═" * 98 + "╝")
    print()
    
    results = []
    for asset in assets:
        result = analyze_asset(asset)
        results.append(result)
    
    # Mostrar tabela
    headers = ["Asset", "Status", "Sinais", "Ganhos", "Perdas", "WR", "Pips", "Conf", "Confluência", "Rating"]
    rows = []
    
    for r in results:
        if r.get("status") == "✅ OK":
            rows.append([
                r['asset'],
                r['status'],
                r['total_signals'],
                r['wins'],
                r['losses'],
                r['win_rate'],
                r['total_pips'],
                r['avg_confidence'],
                r['avg_confluence'],
                r['rating']
            ])
        else:
            rows.append([
                r['asset'],
                r['status'],
                '-', '-', '-', '-', '-', '-', '-', '❌'
            ])
    
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print()
    
    # Resumo geral
    valid_results = [r for r in results if r.get('status') == '✅ OK']
    
    if valid_results:
        total_signals = sum(r['total_signals'] for r in valid_results)
        total_wins = sum(r['wins'] for r in valid_results)
        overall_wr = (total_wins / total_signals * 100) if total_signals > 0 else 0
        
        print("┌" + "─" * 96 + "┐")
        print(f"│ {'📈 RESUMO GERAL':^94} │")
        print("├" + "─" * 96 + "┤")
        print(f"│ Ativos Testados: {len(valid_results):2} | Total Sinais: {total_signals:5} | Ganhos: {total_wins:4} | Win Rate Geral: {overall_wr:5.1f}% " + " " * 24 + "│")
        print("└" + "─" * 96 + "┘")
        print()
        
        # Recomendação
        if overall_wr > 60:
            print("🚀 RECOMENDAÇÃO: ✅ Pronto para Produção!")
            print("   - Win rate > 60% em múltiplos ativos")
            print("   - Desempenho consistente")
            print("   - Pode proceder com deployment")
        elif overall_wr > 50:
            print("⚠️  RECOMENDAÇÃO: 🟡 Revisar antes da Produ�