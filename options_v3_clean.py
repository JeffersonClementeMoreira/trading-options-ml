#!/usr/bin/env python3
"""
Pipeline v3 CLEAN - Versão simplificada focada em backtest

Funções removidas (trading de opções):
- _save_prediction
- _save_evaluation_report
- _expected_move_multiplier
- _detect_next_sweeps
- _extract_best_strikes
- _extract_top3_strikes
- _std_norm_cdf
- _evaluate_trigger_conditions (muito longo)
- _estimate_strategy_chances
- _build_risk_management_levels

Mantém apenas:
- Carregamento e validação de dados
- Cálculo de indicadores
- Análise de confluência
- Backtest

Nova arquitetura:
- MQL5: Calcula TUDO
- Python: XGBoost faz ML
- Backtest: Valida histórico
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from config.settings import LOG_FILES, PATHS
from core.indicators import build_indicators
from core.regime import detect_regime, detect_regime_details, summarize_flow
from core.sd_confluence import evaluate_sd_confluence
from core.smc import calculate_extremes, detect_smc_signals
from core.sweeps import detect_sweeps


DEFAULT_TAIL_SIZE = 1500


def _ensure_directories() -> None:
    for key in ("predictions", "analytics", "logs", "dados"):
        PATHS[key].mkdir(parents=True, exist_ok=True)
    
    for sub in ("open", "validated", "archive"):
        (PATHS["predictions"] / sub).mkdir(parents=True, exist_ok=True)


def _append_log(log_name: str, message: str) -> None:
    log_file = LOG_FILES[log_name]
    log_file.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with log_file.open("a", encoding="utf-8") as fp:
        fp.write(f"[{stamp}] {message}\n")


def _detect_csv_delimiter(file_path: Path) -> str:
    with file_path.open("r", encoding="utf-8", errors="ignore", newline="") as fp:
        sample = fp.read(2048)
    
    try:
        dialect = csv.Sniffer().sniff(sample)
        return dialect.delimiter
    except csv.Error:
        for delimiter in (",", ";", "\t"):
            if delimiter in sample:
                return delimiter
    
    return ","


def _load_ohlc(file_path: Path) -> pd.DataFrame:
    delimiter = _detect_csv_delimiter(file_path)
    df = pd.read_csv(file_path, sep=delimiter, encoding="utf-8")
    
    df.columns = [col.strip().lower().replace("<", "").replace(">", "") for col in df.columns]
    required = {"date", "time", "open", "high", "low", "close"}
    
    if not required.issubset(df.columns):
        missing = required.difference(df.columns)
        raise KeyError(f"Arquivo sem colunas obrigatorias: {sorted(missing)}")
    
    df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce")
    df = df.dropna(subset=["datetime"]).set_index("datetime").sort_index()
    
    for col in ("open", "high", "low", "close"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    df = df.dropna(subset=["open", "high", "low", "close"])
    df["return"] = df["close"].pct_change()
    
    return df


def _choose_csv_file(data_dir: Path, explicit_file: str | None) -> Path:
    if explicit_file:
        file_path = Path(explicit_file).expanduser().resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo informado nao existe: {file_path}")
        return file_path
    
    files = sorted(data_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {data_dir}")
    
    print("Arquivos disponiveis:")
    for i, path in enumerate(files):
        print(f"{i}: {path.name}")
    
    default_idx = len(files) - 1
    raw = input(f"Digite o numero do arquivo desejado (padrao={default_idx}): ").strip()
    if raw == "":
        return files[default_idx]
    
    try:
        idx = int(raw)
        return files[idx]
    except (ValueError, IndexError) as exc:
        raise ValueError("Indice de arquivo invalido") from exc


def _select_analysis_timestamp(df: pd.DataFrame, analysis_hour: int, analysis_minute: int) -> pd.Timestamp:
    if df.empty:
        raise ValueError("Sem dados para selecionar horario de analise")
    
    unique_dates = sorted(pd.Series(df.index.date).unique())
    if len(unique_dates) < 2:
        raise ValueError("Sao necessarios ao menos 2 dias para prever e avaliar o dia seguinte")
    
    for day in reversed(unique_dates[:-1]):
        day_df = df[df.index.date == day]
        candidates = day_df[
            (day_df.index.hour < analysis_hour)
            | ((day_df.index.hour == analysis_hour) & (day_df.index.minute <= analysis_minute))
        ]
        if not candidates.empty:
            return candidates.index[-1]
    
    raise ValueError("Nao foi encontrado candle no horario de analise configurado")


def _get_external_value(df: pd.DataFrame, candidates: tuple[str, ...]) -> float | str | None:
    if df.empty:
        return None
    
    for col in candidates:
        if col in df.columns:
            val = df[col].iloc[-1]
            if pd.notna(val):
                return val
    
    return None


def build_context(
    df: pd.DataFrame,
    tail_size: int = DEFAULT_TAIL_SIZE,
) -> dict:
    """
    Constrói contexto de análise com indicadores, confluência, sweeps, regime.
    Versão limpa (sem opções).
    """
    if df.empty:
        return {
            "status": "vazio",
            "error": "DataFrame vazio",
        }
    
    # Últimos N candles
    analysis_df = df.tail(tail_size)
    
    # Indicadores
    indicators = build_indicators(analysis_df)
    
    # Confluência SD
    sd_data = evaluate_sd_confluence(analysis_df)
    
    # Sweeps
    sweeps_data = detect_sweeps(analysis_df)
    
    # SMC
    extremes = calculate_extremes(analysis_df)
    smc_signals = detect_smc_signals(analysis_df, extremes)
    
    # Regime
    regime_label = detect_regime(analysis_df)
    regime_details = detect_regime_details(analysis_df, regime_label)
    
    # Flow summary
    flow_summary = summarize_flow(analysis_df)
    
    context = {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "data_points": len(analysis_df),
        "price_current": float(analysis_df["close"].iloc[-1]),
        "price_high_tail": float(analysis_df["high"].max()),
        "price_low_tail": float(analysis_df["low"].min()),
        
        "indicators": indicators,
        "sd_confluence": sd_data,
        "sweeps": sweeps_data,
        "smc": {
            "extremes": extremes,
            "signals": smc_signals,
        },
        "regime": {
            "label": regime_label,
            "details": regime_details,
        },
        "flow": flow_summary,
    }
    
    return context


def run_pipeline(
    data_file: str | None = None,
    tail_size: int = DEFAULT_TAIL_SIZE,
) -> dict:
    """
    Executa pipeline completo de análise.
    """
    _ensure_directories()
    
    # Carregar dados
    data_dir = PATHS["dados"]
    csv_file = _choose_csv_file(data_dir, data_file)
    
    print(f"\n📂 Carregando: {csv_file.name}")
    df = _load_ohlc(csv_file)
    
    print(f"✅ Carregado: {len(df)} candles de {df.index[0]} a {df.index[-1]}")
    
    # Análise
    print("\n📊 Construindo contexto...")
    context = build_context(df, tail_size=tail_size)
    
    return context


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pipeline v3 CLEAN - Análise e Backtest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLOS:

  # Análise interativa
  python3 options_v3_clean.py

  # Com arquivo específico
  python3 options_v3_clean.py /path/to/data.csv

  # Com tamanho de análise customizado
  python3 options_v3_clean.py --tail 2000
        """
    )
    
    parser.add_argument("data_file", nargs="?", default=None, help="Arquivo CSV (opcional)")
    parser.add_argument("--tail", type=int, default=DEFAULT_TAIL_SIZE, help=f"Últimos N candles (padrão: {DEFAULT_TAIL_SIZE})")
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    try:
        context = run_pipeline(
            data_file=args.data_file,
            tail_size=args.tail,
        )
        
        # Output
        print("\n" + "="*80)
        print("RESULTADO DA ANÁLISE")
        print("="*80)
        print(json.dumps(context, indent=2, default=str))
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
