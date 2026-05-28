#!/usr/bin/env python3
"""
Análise de Resultados - Pipeline Novo (6 Ativos)
Compatível com backtest_*_DETAILED.csv
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from tabulate import tabulate
import sys

def analyze_backtest_file(asset_name):
    """Analisar performance via arquivo backtest DETAILED"""
    
    results_dir = Path('results')
    csv_file = results_dir / f'backtest_{asset_name}_DETAILED.csv'
    
    if not csv_file.exists():
        return {
            "asset": asset_name,
            "status": "❌ Arquivo não encontrado",
            "signals": 0,
            "win_rate": "0%",
            "total_pips": "0",
            "avg_confidence": "0%",
            "avg_confluence": "0",
            "rating": "❌ ERROR"
        }
    
    try:
        df = pd.read_csv(csv_file)
        
        # Filtrar apenas direções que têm valor (SEND ou UP/DOWN)
        # Usar ensemble_direction como principal indicador de sinal
        valid_rows = df[df['ensemble_direction'].notna()].copy()
        
        if len(valid_rows) == 0:
            return {
                "asset": asset_name,
                "status": "⚠️ Sem sinais válidos",
                "signals": 0,
                "win_rate": "0%",
                "total_pips": "0",
                "avg_confidence": "0%",
                "avg_confluence": "0",
                "rating": "❌ NO DATA"
            }
        
        # Contar winners (onde actual_pips > 0)
        wins = (valid_rows['actual_pips'] > 0).sum()
        total_signals = len(valid_rows)
        win_rate = (wins / total_signals * 100) if total_signals > 0 else 0
        
        # Total de pips
        total_pips = valid_rows['actual_pips'].sum()
        
        # Confiança média
        avg_confidence = valid_rows['confidence_pct'].mean() if 'confidence_pct' in valid_rows.columns else 0
        
        # Confluência (usando um score simples: número de indicadores que concordam)
        # Para agora, usar 3.5 como padrão (pode melhorar depois)
        avg_confluence = 3.5
        
        # Rating
        if win_rate >= 65 and avg_confidence >= 85:
            rating = "🟢 EXCELLENT"
        elif win_rate >= 55 and avg_confidence >= 80:
            rating = "🟢 GOOD"
        elif win_rate >= 50 and avg_confidence >= 75:
            rating = "🟡 OK"
        elif win_rate >= 45:
            rating = "🟡 CAUTION"
        else:
            rating = "🔴 POOR"
        
        return {
            "asset": asset_name,
            "status": "✅ OK",
            "signals": total_signals,
            "wins": wins,
            "losses": total_signals - wins,
            "win_rate": f"{win_rate:.1f}%",
            "total_pips": f"{total_pips:+.1f}",
            "avg_confidence": f"{avg_confidence:.1f}%",
            "avg_confluence": f"{avg_confluence:.1f}",
            "rating": rating
        }
    
    except Exception as e:
        print(f"[ERROR] {asset_name}: {str(e)}", file=sys.stderr)
        return {
            "asset": asset_name,
            "status": f"❌ Erro: {str(e)[:30]}",
            "signals": 0,
            "win_rate": "0%",
            "total_pips": "0",
            "avg_confidence": "0%",
            "avg_confluence": "0",
            "rating": "❌ ERROR"
        }

def main():
    """Análise principal"""
    
    assets = ['EURUSD', 'GBPUSD', 'EURAUD', 'EURJPY', 'NZDUSD', 'GOLD']
    
    print("\n" + "="*100)
    print("🚀 ANÁLISE DE RESULTADOS - PIPELINE ML v1.1.0 (6 Ativos)")
    print("="*100)
    
    results = []
    total_signals = 0
    total_wins = 0
    total_pips = 0
    
    for asset in assets:
        print(f"📊 Analisando {asset}...", end=" ", flush=True)
        analysis = analyze_backtest_file(asset)
        results.append(analysis)
        
        if analysis['status'] == "✅ OK":
            total_signals += analysis['signals']
            total_wins += analysis.get('wins', 0)
            try:
                total_pips += float(analysis['total_pips'])
            except:
                pass
            print("✅")
        else:
            print(f"{analysis['status']}")
    
    # Tabela de resultados
    print("\n" + "="*100)
    print("📋 RESUMO DE PERFORMANCE")
    print("="*100)
    
    table_data = []
    for r in results:
        table_data.append([
            r['asset'],
            r['status'],
            r.get('signals', 0),
            r.get('wins', 0),
            r.get('losses', 0),
            r['win_rate'],
            r['total_pips'],
            r['avg_confidence'],
            r['avg_confluence'],
            r['rating']
        ])
    
    headers = ['ATIVO', 'STATUS', 'SINAIS', 'GANHOS', 'PERDAS', 'WR%', 'PIPS', 'CONF%', 'FLUÊNCIA', 'RATING']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    # Resumo geral
    print("\n" + "="*100)
    print("🎯 RESUMO GERAL")
    print("="*100)
    if total_signals > 0:
        overall_wr = (total_wins / total_signals * 100)
        print(f"  Total de Sinais:      {total_signals}")
        print(f"  Sinais Vencedores:    {total_wins}")
        print(f"  Win Rate Geral:       {overall_wr:.1f}%")
        print(f"  Pips Totais:          {total_pips:+.1f}")
        print(f"  Pips Médios/Sinal:    {total_pips/total_signals:+.2f}")
    else:
        print("  ⚠️ Nenhum sinal válido encontrado")
    
    # Recomendação
    print("\n" + "="*100)
    print("🚀 RECOMENDAÇÃO DE PRODUÇÃO")
    print("="*100)
    
    good_assets = [r for r in results if r['rating'] in ['🟢 EXCELLENT', '🟢 GOOD']]
    caution_assets = [r for r in results if r['rating'] in ['🟡 OK', '🟡 CAUTION']]
    poor_assets = [r for r in results if r['rating'] in ['🔴 POOR', '❌ ERROR']]
    
    if len(good_assets) >= 2:
        print(f"✅ RECOMENDADO PARA PRODUÇÃO")
        print(f"   • Ativos com bom performance: {', '.join([r['asset'] for r in good_assets])}")
        print(f"   • Próximo passo: Configurar Cron/Systemd scheduler")
        print(f"   • Comando: 0 22 * * * cd /home/ubuntu/pessoal/options && python3 src/run_full_pipeline.py --all")
    elif len(good_assets) + len(caution_assets) >= 2:
        print(f"⚠️ CONDICIONALMENTE PRONTO")
        print(f"   • Bons ativos: {', '.join([r['asset'] for r in good_assets])}")
        print(f"   • Ativos em observação: {', '.join([r['asset'] for r in caution_assets])}")
        print(f"   • Recomendação: Monitorar por 5-10 dias antes de expansão")
    else:
        print(f"❌ NÃO RECOMENDADO")
        print(f"   • Nenhum ativo com performance satisfatória")
        print(f"   • Próximo passo: Revisar parâmetros em config.json")
        print(f"   • Aumentar janela de dados ou ajustar thresholds")
    
    # Salvar dashboard JSON
    dashboard = {
        "timestamp": datetime.now().isoformat(),
        "assets": results,
        "summary": {
            "total_signals": total_signals,
            "total_wins": total_wins,
            "overall_win_rate": f"{(total_wins/total_signals*100) if total_signals > 0 else 0:.1f}%",
            "total_pips": f"{total_pips:+.1f}",
            "good_assets": [r['asset'] for r in good_assets],
            "caution_assets": [r['asset'] for r in caution_assets],
            "poor_assets": [r['asset'] for r in poor_assets]
        }
    }
    
    dashboard_path = Path('results/dashboard.json')
    with open(dashboard_path, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n💾 Dashboard salvo em: results/dashboard.json")
    print("="*100 + "\n")

if __name__ == '__main__':
    main()
