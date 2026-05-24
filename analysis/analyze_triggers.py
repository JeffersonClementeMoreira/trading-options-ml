#!/usr/bin/env python3
"""
Analisa triggers e mostra scoring para diferentes cenários.

Uso:
  python3 analyze_triggers.py --file dados.csv
  python3 analyze_triggers.py --file dados.csv --show-all  (mostra todos os setups)
  python3 analyze_triggers.py --file dados.csv --min-quality 60  (filtra só ≥60%)
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from config.settings import PATHS
from options_v3 import _load_ohlc, _select_analysis_timestamp, build_context


def _print_trigger_table(results: list[dict]) -> None:
    """Exibe tabela de triggers com scores."""
    
    if not results:
        print("Nenhum resultado encontrado.")
        return
    
    # Preparar dados para tabela
    rows = []
    for res in results:
        context = res["context"]
        trigger = context.get("trigger_evaluation", {})
        
        rows.append({
            "timestamp": context.get("analysis_timestamp", "?"),
            "spot": f"{context.get('spot', 0):.4f}",
            "dist_sd%": f"{trigger.get('distance_to_sd_pct', 0):.3f}",
            "sd_score": f"{trigger.get('sd_quality_score', 0)}%",
            "conf_score": f"{trigger.get('confluence_score', 0)}%",
            "overall": f"{trigger.get('overall_entry_quality', 0)}%",
            "recommendation": trigger.get("recommendation", "?"),
        })
    
    df_results = pd.DataFrame(rows)
    
    # Colorir baseado em recommendation (simulado com emojis)
    def add_emoji(rec):
        if rec == "FORTE":
            return f"🟢 {rec}"
        elif rec == "MÉDIA":
            return f"🟡 {rec}"
        elif rec == "FRACA":
            return f"🟠 {rec}"
        else:
            return f"🔴 {rec}"
    
    df_results["recommendation"] = df_results["recommendation"].apply(add_emoji)
    
    print("\n" + "=" * 120)
    print("ANÁLISE DE TRIGGERS - SCORING FLEXÍVEL")
    print("=" * 120)
    print(df_results.to_string(index=False))
    print("=" * 120)
    
    # Estatísticas
    overall_scores = [int(r["overall"].rstrip("%")) for r in rows]
    if overall_scores:
        print(f"\nEstatísticas:")
        print(f"  Score médio:    {sum(overall_scores) / len(overall_scores):.1f}%")
        print(f"  Score máximo:   {max(overall_scores)}%")
        print(f"  Score mínimo:   {min(overall_scores)}%")
        
        forte_count = sum(1 for s in overall_scores if s >= 75)
        media_count = sum(1 for s in overall_scores if 50 <= s < 75)
        fraca_count = sum(1 for s in overall_scores if 25 <= s < 50)
        evitar_count = sum(1 for s in overall_scores if s < 25)
        
        print(f"\nDistribuição:")
        print(f"  🟢 FORTE (≥75%):  {forte_count}")
        print(f"  🟡 MÉDIA (50-74%): {media_count}")
        print(f"  🟠 FRACA (25-49%): {fraca_count}")
        print(f"  🔴 EVITAR (<25%):  {evitar_count}")
        print()


def _analyze_single_day(df: pd.DataFrame, analysis_hour: int, analysis_minute: int) -> dict:
    """Analisa um único dia."""
    
    try:
        analysis_ts = _select_analysis_timestamp(df, analysis_hour, analysis_minute)
        df_until_analysis = df[df.index <= analysis_ts].copy()
        
        context = build_context(
            df_until_analysis,
            iv=0.25,
            days=5,
        )
        context["analysis_timestamp"] = str(analysis_ts)
        context["analysis_hour"] = f"{analysis_hour:02d}:{analysis_minute:02d}"
        
        return {"status": "success", "context": context}
    
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _backtest_all_days(
    df: pd.DataFrame,
    analysis_hour: int = 16,
    analysis_minute: int = 0,
) -> list[dict]:
    """Backtest analisando todos os dias."""
    
    results = []
    
    unique_dates = sorted(set(df.index.date))
    if len(unique_dates) < 2:
        print("❌ Precisa de pelo menos 2 dias para análise.")
        return results
    
    # Analisar cada dia (exceto o último)
    for target_date in unique_dates[:-1]:
        day_df = df[df.index.date == target_date]
        
        if day_df.empty:
            continue
        
        # Usar dados até esse dia
        df_until_day = df[df.index.date <= target_date]
        
        res = _analyze_single_day(df_until_day, analysis_hour, analysis_minute)
        if res["status"] == "success":
            results.append(res)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Analisa triggers com scoring flexível")
    parser.add_argument("--file", type=str, required=True, help="CSV de entrada")
    parser.add_argument(
        "--analysis-hour",
        type=int,
        default=16,
        help="Hora para análise (padrão=16)",
    )
    parser.add_argument(
        "--analysis-minute",
        type=int,
        default=0,
        help="Minuto para análise (padrão=0)",
    )
    parser.add_argument(
        "--min-quality",
        type=int,
        default=0,
        help="Filtrar scores ≥ este valor (%)",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Mostrar todos os dias (padrão: apenas últimos 30)",
    )
    parser.add_argument(
        "--save-json",
        type=str,
        default=None,
        help="Salvar resultados em JSON",
    )
    
    args = parser.parse_args()
    
    # Carregar dados
    csv_path = Path(args.file).expanduser().resolve()
    if not csv_path.exists():
        print(f"❌ Arquivo não encontrado: {csv_path}")
        return
    
    print(f"📂 Carregando: {csv_path}")
    df = _load_ohlc(csv_path)
    print(f"✅ {len(df)} candles carregados")
    
    # Backtest
    print(f"\n🔍 Analisando triggers...")
    results = _backtest_all_days(df, args.analysis_hour, args.analysis_minute)
    
    # Filtrar por qualidade mínima
    if args.min_quality > 0:
        results_filtered = []
        for res in results:
            quality = res["context"].get("trigger_evaluation", {}).get("overall_entry_quality", 0)
            if quality >= args.min_quality:
                results_filtered.append(res)
        
        print(f"📊 {len(results_filtered)} de {len(results)} setups com score ≥{args.min_quality}%")
        results = results_filtered
    
    # Limitar a últimos 30 se não mostrar tudo
    if not args.show_all and len(results) > 30:
        results = results[-30:]
        print(f"📋 Mostrando últimos 30 (total: {len(results)})")
    
    # Exibir tabela
    _print_trigger_table(
        [{"context": r["context"]} for r in results]
    )
    
    # Salvar em JSON se pedido
    if args.save_json:
        output_path = Path(args.save_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Serializar com tratamento de tipos especiais
        def default_handler(obj):
            if isinstance(obj, (pd.Timestamp, datetime)):
                return str(obj)
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict()
            return str(obj)
        
        with output_path.open("w") as f:
            json.dump(results, f, indent=2, default=default_handler)
        
        print(f"\n💾 Resultados salvos em: {output_path}")


if __name__ == "__main__":
    main()
