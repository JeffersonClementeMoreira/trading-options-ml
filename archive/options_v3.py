#!/usr/bin/env python3
"""Pipeline v3 para analise de opcoes usando a estrutura modular do projeto."""

import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path

import pandas as pd

from config.settings import LOG_FILES, PATHS
from core.expected_move import calculate_expected_move_from_expiration, get_next_options_expiration
from core.indicators import build_indicators
from core.options_engine import run_options_engine
from core.regime import detect_regime, detect_regime_details, summarize_flow
from core.sd_confluence import evaluate_sd_confluence
from core.smc import calculate_extremes, detect_smc_signals
from core.sweeps import detect_sweeps
from core.validation import validate_prediction


DEFAULT_TAIL_SIZE = 1500
DEFAULT_ANALYSIS_HOUR = 16
DEFAULT_ANALYSIS_MINUTE = 0
DEFAULT_EXPIRY_HOUR = 14
DEFAULT_EXPIRY_MINUTE = 0
DEFAULT_EXPIRY_DAYS = 1
DEFAULT_STRATEGY_MODE = "strangle"
DEFAULT_HEDGE_TRIGGER_RATIO = 0.10
DEFAULT_ROLL_TRIGGER_RATIO = 0.20
DEFAULT_ROLL_TARGET_RATIO = 0.35

EXTERNAL_SD_COLS = ("mt5_sd_confluence", "sd_confluence_mt5", "sd_confluence_ext")
EXTERNAL_FLOW_COLS = ("mt5_flow_score", "flow_score_mt5", "flow_score_ext")
EXTERNAL_ER_COLS = ("mt5_er_mean", "er_mean_mt5", "er_mean_ext")
EXTERNAL_KAMA_COLS = ("mt5_kama_slope", "kama_slope_mt5", "kama_slope_ext")
EXTERNAL_REGIME_COLS = ("mt5_regime", "regime_mt5", "regime_ext")


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


def _extract_best_strikes(option_strikes: list[dict]) -> tuple[dict | None, dict | None]:
    calls = [row for row in option_strikes if row.get("side") == "SELL_CALL"]
    puts = [row for row in option_strikes if row.get("side") == "SELL_PUT"]

    best_call = calls[0] if calls else None
    best_put = puts[0] if puts else None
    return best_call, best_put


def _extract_top3_strikes(option_strikes: list[dict]) -> tuple[list[dict], list[dict]]:
    calls = [row for row in option_strikes if row.get("side") == "SELL_CALL" and row.get("strike") is not None]
    puts = [row for row in option_strikes if row.get("side") == "SELL_PUT" and row.get("strike") is not None]

    # Convencao de exibicao: *_1 mais proxima do preco, *_3 mais distante.
    # Calls (acima do spot): menor strike primeiro (mais perto -> mais longe).
    calls = sorted(calls, key=lambda row: float(row["strike"]))
    # Puts (abaixo do spot): maior strike primeiro (mais perto -> mais longe).
    puts = sorted(puts, key=lambda row: float(row["strike"]), reverse=True)

    return calls[:3], puts[:3]


def _evaluate_trigger_conditions(
    df: pd.DataFrame,
    sd_payload: dict,
) -> dict:
    """
    Avalia condições de TRIGGER de forma FLEXÍVEL (não é imposição rígida).
    
    Retorna scores para cada trigger:
    - distance_to_sd_pct: Quão perto está da SD? (0% = dentro, >1% = longe)
    - sd_quality_score: Score 0-100 (100 = dentro da SD)
    - fvg_proximity_score: Score 0-100 (100 = exatamente em cima do FVG)
    - overall_entry_quality: Score 0-100 baseado em TODOS os fatores
    
    Permite que o usuário AVALIE manualmente se quer entrar ou não.
    
    Args:
        df: DataFrame com OHLC
        sd_payload: Supply/Demand zones from evaluate_sd_confluence
    
    Returns:
        dict com scores e análise detalhada (sem imposições)
    """
    if df.empty:
        return {
            "distance_to_sd_pct": None,
            "sd_quality_score": 0,
            "in_sd_zone": False,
            "closest_sd_zone": None,
            "overall_entry_quality": 0,
            "summary": "DataFrame vazio - nenhuma análise possível",
        }
    
    current_price = float(df["close"].iloc[-1])
    current_high = float(df["high"].iloc[-1])
    current_low = float(df["low"].iloc[-1])
    
    # ===== TRIGGER 1: DISTÂNCIA À SUPPLY/DEMAND =====
    distance_to_sd_pct = None
    in_sd_zone = False
    closest_sd_zone = None
    sd_quality_score = 0
    
    zones = sd_payload.get("zones", [])
    if zones:
        for zone in zones:
            zone_price = float(zone.get("price", 0))
            zone_range = float(zone.get("range", 0))
            
            if zone_price <= 0 or zone_range <= 0:
                continue
                
            zone_top = zone_price + zone_range / 2
            zone_bottom = zone_price - zone_range / 2
            
            # Verificar se candle está dentro da SD
            if zone_bottom <= current_price <= zone_top:
                in_sd_zone = True
                distance_to_sd_pct = 0.0
                closest_sd_zone = zone
                sd_quality_score = 100  # Perfect score
                break
            
            # Calcular distância (não é imposição, só informação)
            dist_to_zone = min(
                abs(current_price - zone_top),
                abs(current_price - zone_bottom)
            )
            pct_distance = (dist_to_zone / zone_price) * 100 if zone_price > 0 else 100
            
            # Manter a zona mais próxima
            if distance_to_sd_pct is None or pct_distance < distance_to_sd_pct:
                distance_to_sd_pct = pct_distance
                closest_sd_zone = zone
    
    # Calcular SD quality score (não é obrigação ter 0.5%)
    # 100 = dentro da SD
    # 75 = ≤0.5% de distância
    # 50 = ≤1% de distância
    # 25 = ≤2% de distância
    # 0 = >2% de distância
    if in_sd_zone:
        sd_quality_score = 100
    elif distance_to_sd_pct is not None:
        if distance_to_sd_pct <= 0.5:
            sd_quality_score = 75
        elif distance_to_sd_pct <= 1.0:
            sd_quality_score = 50
        elif distance_to_sd_pct <= 2.0:
            sd_quality_score = 25
        else:
            sd_quality_score = 0
    
    # ===== TRIGGER 2: CONFLUÊNCIA COM OUTROS FATORES =====
    # Usar outros sinais do sd_payload se disponíveis
    confluences = sd_payload.get("confluences", [])
    confluence_count = len(confluences) if confluences else 0
    confluence_score = min(100, confluence_count * 20)  # Múltiplas confluências aumentam score
    
    # ===== SCORE FINAL DE QUALIDADE DE ENTRADA =====
    # Combina:
    # - 50% SD proximity
    # - 30% Confluências
    # - 20% Regime (se em trends/manipulation tem menos risco)
    overall_entry_quality = int(
        (sd_quality_score * 0.5) +
        (confluence_score * 0.3) +
        (40 * 0.2)  # 40 por padrão (sem regime info aqui)
    )
    
    summary = ""
    if in_sd_zone:
        summary = "✅ ÓTIMO: Candle DENTRO da Supply/Demand (máxima confiança)"
    elif distance_to_sd_pct is not None:
        if distance_to_sd_pct <= 0.5:
            summary = f"🟢 BOM: Apenas {distance_to_sd_pct:.3f}% de distância da SD (muito próximo)"
        elif distance_to_sd_pct <= 1.0:
            summary = f"🟡 MEDIANO: {distance_to_sd_pct:.3f}% de distância da SD (aceitável)"
        elif distance_to_sd_pct <= 2.0:
            summary = f"🟠 FRACO: {distance_to_sd_pct:.3f}% de distância da SD (longe)"
        else:
            summary = f"🔴 RUIM: {distance_to_sd_pct:.3f}% de distância da SD (muito longe)"
    else:
        summary = "❓ SEM DADOS: Nenhuma SD zone encontrada"
    
    if confluence_count > 0:
        summary += f" | {confluence_count} confluências extras"
    
    return {
        "distance_to_sd_pct": round(distance_to_sd_pct, 4) if distance_to_sd_pct is not None else None,
        "in_sd_zone": bool(in_sd_zone),
        "sd_quality_score": int(sd_quality_score),  # 0-100
        "confluence_count": confluence_count,
        "confluence_score": int(confluence_score),  # 0-100
        "overall_entry_quality": overall_entry_quality,  # 0-100
        "closest_sd_zone": closest_sd_zone,
        "summary": summary,
        "recommendation": (
            "FORTE" if overall_entry_quality >= 75
            else "MÉDIA" if overall_entry_quality >= 50
            else "FRACA" if overall_entry_quality >= 25
            else "EVITAR"
        ),
    }


def _estimate_strategy_chances(
    spot: float,
    expected_move: float,
    call_strike: float | None,
    put_strike: float | None,
) -> dict:
    if spot <= 0 or expected_move <= 0:
        return {
            "chance_call_only_pct": None,
            "chance_put_only_pct": None,
            "chance_strangle_pct": None,
        }

    sigma_move = expected_move / spot
    if sigma_move <= 0:
        return {
            "chance_call_only_pct": None,
            "chance_put_only_pct": None,
            "chance_strangle_pct": None,
        }

    chance_call = None
    chance_put = None
    chance_strangle = None

    if call_strike is not None and call_strike > 0:
        z_call = math.log(call_strike / spot) / sigma_move
        # SELL_CALL acerta se fechar abaixo da strike.
        chance_call = _std_norm_cdf(z_call)

    if put_strike is not None and put_strike > 0:
        z_put = math.log(put_strike / spot) / sigma_move
        # SELL_PUT acerta se fechar acima da strike.
        chance_put = 1.0 - _std_norm_cdf(z_put)

    if call_strike is not None and put_strike is not None and call_strike > 0 and put_strike > 0:
        z_call = math.log(call_strike / spot) / sigma_move
        z_put = math.log(put_strike / spot) / sigma_move
        # STRANGLE acerta se fechar entre put e call.
        chance_strangle = max(0.0, _std_norm_cdf(z_call) - _std_norm_cdf(z_put))

    return {
        "chance_call_only_pct": round(chance_call * 100.0, 2) if chance_call is not None else None,
        "chance_put_only_pct": round(chance_put * 100.0, 2) if chance_put is not None else None,
        "chance_strangle_pct": round(chance_strangle * 100.0, 2) if chance_strangle is not None else None,
    }


def _build_risk_management_levels(
    put_strike: float | None,
    call_strike: float | None,
    expected_move: float,
) -> dict:
    if expected_move <= 0:
        return {
            "hedge_trigger_points": None,
            "roll_trigger_points": None,
            "roll_target_points": None,
            "put_hedge_trigger_price": None,
            "put_hedge_buy_strike": None,
            "put_roll_trigger_price": None,
            "put_roll_target_strike": None,
            "call_hedge_trigger_price": None,
            "call_hedge_buy_strike": None,
            "call_roll_trigger_price": None,
            "call_roll_target_strike": None,
        }

    hedge_points = max(1.0, expected_move * DEFAULT_HEDGE_TRIGGER_RATIO)
    roll_points = max(hedge_points * 1.5, expected_move * DEFAULT_ROLL_TRIGGER_RATIO)
    roll_target_points = max(hedge_points * 2.0, expected_move * DEFAULT_ROLL_TARGET_RATIO)

    put_hedge_trigger_price = (put_strike - hedge_points) if put_strike is not None else None
    put_roll_trigger_price = (put_strike - roll_points) if put_strike is not None else None
    put_roll_target_strike = (put_strike - roll_target_points) if put_strike is not None else None

    call_hedge_trigger_price = (call_strike + hedge_points) if call_strike is not None else None
    call_roll_trigger_price = (call_strike + roll_points) if call_strike is not None else None
    call_roll_target_strike = (call_strike + roll_target_points) if call_strike is not None else None

    return {
        "hedge_trigger_points": hedge_points,
        "roll_trigger_points": roll_points,
        "roll_target_points": roll_target_points,
        "put_hedge_trigger_price": put_hedge_trigger_price,
        "put_hedge_buy_strike": put_hedge_trigger_price,
        "put_roll_trigger_price": put_roll_trigger_price,
        "put_roll_target_strike": put_roll_target_strike,
        "call_hedge_trigger_price": call_hedge_trigger_price,
        "call_hedge_buy_strike": call_hedge_trigger_price,
        "call_roll_trigger_price": call_roll_trigger_price,
        "call_roll_target_strike": call_roll_target_strike,
    }


def _get_external_value(df: pd.DataFrame, candidates: tuple[str, ...]) -> float | str | None:
    for col in candidates:
        if col not in df.columns:
            continue

        series = df[col].dropna()
        if series.empty:
            continue

        value = series.iloc[-1]
        if isinstance(value, str):
            return value.strip()

        num = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.notna(num):
            return float(num)
    return None


def _evaluate_next_day(
    df_full: pd.DataFrame,
    analysis_ts: pd.Timestamp,
    prediction: dict,
    expiry_hour: int,
    expiry_minute: int,
    expiry_days: int = DEFAULT_EXPIRY_DAYS,
    strategy_mode: str = DEFAULT_STRATEGY_MODE,
) -> dict:
    context = prediction["context"]
    engine_result = prediction["engine_result"]

    future_dates = sorted({d for d in df_full.index.date if d > analysis_ts.date()})
    if not future_dates:
        return {
            "status": "PENDING",
            "reason": "Nao ha dados do dia seguinte para avaliacao",
            "analysis_timestamp": str(analysis_ts),
        }

    if expiry_days < 1:
        return {
            "status": "PENDING",
            "reason": "expiry_days deve ser >= 1",
            "analysis_timestamp": str(analysis_ts),
        }

    if len(future_dates) < expiry_days:
        return {
            "status": "PENDING",
            "reason": f"Nao ha dados suficientes para avaliar D+{expiry_days}",
            "analysis_timestamp": str(analysis_ts),
        }

    eval_date = future_dates[expiry_days - 1]
    eval_df = df_full[df_full.index.date == eval_date]
    if eval_df.empty:
        return {
            "status": "PENDING",
            "reason": "Dia seguinte sem candles",
            "analysis_timestamp": str(analysis_ts),
            "target_date": str(eval_date),
        }

    eval_close_candidates = eval_df[
        (eval_df.index.hour < expiry_hour)
        | ((eval_df.index.hour == expiry_hour) & (eval_df.index.minute <= expiry_minute))
    ]
    if eval_close_candidates.empty:
        return {
            "status": "PENDING",
            "reason": f"Nao ha candle ate o horario de vencimento no D+{expiry_days}",
            "analysis_timestamp": str(analysis_ts),
            "target_date": str(eval_date),
        }

    close_ts = eval_close_candidates.index[-1]
    next_close = float(eval_close_candidates["close"].iloc[-1])
    next_high = float(eval_df["high"].max())
    next_low = float(eval_df["low"].min())

    option_strikes = engine_result.get("option_strikes", [])
    best_call, best_put = _extract_best_strikes(option_strikes)
    top_calls, top_puts = _extract_top3_strikes(option_strikes)

    call_strike = float(best_call["strike"]) if best_call else None
    put_strike = float(best_put["strike"]) if best_put else None
    call_delta = float(best_call["delta"]) if best_call and best_call.get("delta") is not None else None
    put_delta = float(best_put["delta"]) if best_put and best_put.get("delta") is not None else None
    mean_primary_delta = None
    if call_delta is not None and put_delta is not None:
        mean_primary_delta = (call_delta + put_delta) / 2.0

    call_1 = float(top_calls[0]["strike"]) if len(top_calls) > 0 else None
    call_2 = float(top_calls[1]["strike"]) if len(top_calls) > 1 else None
    call_3 = float(top_calls[2]["strike"]) if len(top_calls) > 2 else None
    put_1 = float(top_puts[0]["strike"]) if len(top_puts) > 0 else None
    put_2 = float(top_puts[1]["strike"]) if len(top_puts) > 1 else None
    put_3 = float(top_puts[2]["strike"]) if len(top_puts) > 2 else None

    call_otm = (next_close <= call_strike) if call_strike is not None else None
    put_otm = (next_close >= put_strike) if put_strike is not None else None
    call_not_touched = (next_high < call_strike) if call_strike is not None else None
    put_not_touched = (next_low > put_strike) if put_strike is not None else None

    spot = float(context["spot"])
    expected_move = float(context["expected_move"])
    expected_upper = spot + expected_move
    expected_lower = spot - expected_move
    realized_move = abs(next_close - spot)
    expected_move_respected = realized_move <= expected_move
    close_within_expected_band = expected_lower <= next_close <= expected_upper
    close_within_strikes = (
        (put_strike is not None and call_strike is not None and put_strike <= next_close <= call_strike)
    )

    close_within_pair_1 = (put_1 is not None and call_1 is not None and put_1 <= next_close <= call_1)
    close_within_pair_2 = (put_2 is not None and call_2 is not None and put_2 <= next_close <= call_2)
    close_within_pair_3 = (put_3 is not None and call_3 is not None and put_3 <= next_close <= call_3)
    close_within_any_pair = bool(close_within_pair_1 or close_within_pair_2 or close_within_pair_3)

    strategy_chances = _estimate_strategy_chances(
        spot=spot,
        expected_move=expected_move,
        call_strike=call_strike,
        put_strike=put_strike,
    )
    risk_levels = _build_risk_management_levels(
        put_strike=put_strike,
        call_strike=call_strike,
        expected_move=expected_move,
    )

    success_call_only = bool(call_otm) if call_otm is not None else False
    success_put_only = bool(put_otm) if put_otm is not None else False
    success_strangle = bool(close_within_strikes)

    put_hedge_trigger_hit = (
        risk_levels["put_hedge_trigger_price"] is not None and next_low <= float(risk_levels["put_hedge_trigger_price"])
    )
    put_roll_trigger_hit = (
        risk_levels["put_roll_trigger_price"] is not None and next_low <= float(risk_levels["put_roll_trigger_price"])
    )
    call_hedge_trigger_hit = (
        risk_levels["call_hedge_trigger_price"] is not None and next_high >= float(risk_levels["call_hedge_trigger_price"])
    )
    call_roll_trigger_hit = (
        risk_levels["call_roll_trigger_price"] is not None and next_high >= float(risk_levels["call_roll_trigger_price"])
    )

    # Zone entry detection: did price touch support and/or resistance during the day?
    touched_support = (put_strike is not None and next_low <= put_strike)
    touched_resistance = (call_strike is not None and next_high >= call_strike)
    entered_zone = touched_support or touched_resistance

    next_sweeps = context.get("next_sweeps", {})
    next_top_sweep = next_sweeps.get("next_top_sweep")
    next_bottom_sweep = next_sweeps.get("next_bottom_sweep")
    hit_next_top_sweep = (next_top_sweep is not None and next_high >= float(next_top_sweep))
    hit_next_bottom_sweep = (next_bottom_sweep is not None and next_low <= float(next_bottom_sweep))

    regime_details = context.get("regime_details", {})
    flow_score = float(regime_details.get("flow_score", 0.0))
    er_mean = float(regime_details.get("er_mean", 0.0))
    kama_slope = float(regime_details.get("kama_slope", 0.0))
    sd_confluence = float(context.get("sd_confluence", 0.0))

    if strategy_mode == "call-only":
        satisfied = success_call_only
        satisfactory_rule = "call_otm_at_close"
    elif strategy_mode == "put-only":
        satisfied = success_put_only
        satisfactory_rule = "put_otm_at_close"
    else:
        # Critico para venda de opcoes no strangle: fechamento dentro do corredor put/call.
        satisfied = success_strangle
        satisfactory_rule = "close_within_primary_put_call"

    return {
        "status": "EVALUATED",
        "analysis_timestamp": str(analysis_ts),
        "target_date": str(eval_date),
        "expiry_days": int(expiry_days),
        "expiry_close_timestamp": str(close_ts),
        "expiry_hour": f"{expiry_hour:02d}:{expiry_minute:02d}",
        "analysis_price": spot,
        "next_day_close": next_close,
        "next_day_high": next_high,
        "next_day_low": next_low,
        "expected_move": expected_move,
        "expected_upper": expected_upper,
        "expected_lower": expected_lower,
        "realized_move": realized_move,
        "expected_move_respected": expected_move_respected,
        "close_within_expected_band": close_within_expected_band,
        "best_call_strike": call_strike,
        "best_put_strike": put_strike,
        "best_call_delta": call_delta,
        "best_put_delta": put_delta,
        "mean_primary_delta": mean_primary_delta,
        "touched_support": bool(touched_support),
        "touched_resistance": bool(touched_resistance),
        "entered_zone": bool(entered_zone),
        "call_1": call_1,
        "call_2": call_2,
        "call_3": call_3,
        "put_1": put_1,
        "put_2": put_2,
        "put_3": put_3,
        "close_within_strikes": close_within_strikes,
        "close_within_pair_1": close_within_pair_1,
        "close_within_pair_2": close_within_pair_2,
        "close_within_pair_3": close_within_pair_3,
        "close_within_any_pair": close_within_any_pair,
        "chance_call_only_pct": strategy_chances["chance_call_only_pct"],
        "chance_put_only_pct": strategy_chances["chance_put_only_pct"],
        "chance_strangle_pct": strategy_chances["chance_strangle_pct"],
        "hedge_trigger_points": risk_levels["hedge_trigger_points"],
        "roll_trigger_points": risk_levels["roll_trigger_points"],
        "roll_target_points": risk_levels["roll_target_points"],
        "put_hedge_trigger_price": risk_levels["put_hedge_trigger_price"],
        "put_hedge_buy_strike": risk_levels["put_hedge_buy_strike"],
        "put_roll_trigger_price": risk_levels["put_roll_trigger_price"],
        "put_roll_target_strike": risk_levels["put_roll_target_strike"],
        "call_hedge_trigger_price": risk_levels["call_hedge_trigger_price"],
        "call_hedge_buy_strike": risk_levels["call_hedge_buy_strike"],
        "call_roll_trigger_price": risk_levels["call_roll_trigger_price"],
        "call_roll_target_strike": risk_levels["call_roll_target_strike"],
        "put_hedge_trigger_hit": bool(put_hedge_trigger_hit),
        "put_roll_trigger_hit": bool(put_roll_trigger_hit),
        "call_hedge_trigger_hit": bool(call_hedge_trigger_hit),
        "call_roll_trigger_hit": bool(call_roll_trigger_hit),
        "success_call_only": success_call_only,
        "success_put_only": success_put_only,
        "success_strangle": success_strangle,
        "call_otm_at_close": call_otm,
        "put_otm_at_close": put_otm,
        "call_not_touched": call_not_touched,
        "put_not_touched": put_not_touched,
        "next_top_sweep": float(next_top_sweep) if next_top_sweep is not None else None,
        "next_bottom_sweep": float(next_bottom_sweep) if next_bottom_sweep is not None else None,
        "hit_next_top_sweep": bool(hit_next_top_sweep),
        "hit_next_bottom_sweep": bool(hit_next_bottom_sweep),
        "flow_score": flow_score,
        "er_mean": er_mean,
        "kama_slope": kama_slope,
        "sd_confluence": sd_confluence,
        "strategy_mode": strategy_mode,
        "satisfactory": satisfied,
        "satisfactory_rule": satisfactory_rule,
    }


def build_context(
    df: pd.DataFrame,
    iv: float,
    days: int,
    expiry_days: int = DEFAULT_EXPIRY_DAYS,
    expiry_hour: int = DEFAULT_EXPIRY_HOUR,
    expiry_minute: int = DEFAULT_EXPIRY_MINUTE,
    strategy_mode: str = DEFAULT_STRATEGY_MODE,
    prefer_external_features: bool = False,
) -> dict:
    enriched_df = build_indicators(df.copy())
    regime = detect_regime(enriched_df)
    regime_details = detect_regime_details(enriched_df)
    flow_summary = summarize_flow(enriched_df)
    smc_signals = detect_smc_signals(enriched_df)
    sweeps = detect_sweeps(enriched_df)
    sd_payload = evaluate_sd_confluence(enriched_df)
    
    # Avaliar triggers FLEXÍVEIS (não é imposição)
    trigger_evaluation = _evaluate_trigger_conditions(enriched_df, sd_payload)

    if prefer_external_features:
        ext_sd = _get_external_value(enriched_df, EXTERNAL_SD_COLS)
        ext_flow = _get_external_value(enriched_df, EXTERNAL_FLOW_COLS)
        ext_er = _get_external_value(enriched_df, EXTERNAL_ER_COLS)
        ext_kama = _get_external_value(enriched_df, EXTERNAL_KAMA_COLS)
        ext_regime = _get_external_value(enriched_df, EXTERNAL_REGIME_COLS)

        if ext_sd is not None:
            sd_payload = {
                "score": float(ext_sd),
                "zones": [],
                "confluences": [],
                "source": "external_mt5",
            }

        if any(x is not None for x in (ext_flow, ext_er, ext_kama, ext_regime)):
            regime_details = {
                **regime_details,
                "flow_score": float(ext_flow) if ext_flow is not None else float(regime_details.get("flow_score", 0.0)),
                "er_mean": float(ext_er) if ext_er is not None else float(regime_details.get("er_mean", 0.0)),
                "kama_slope": float(ext_kama) if ext_kama is not None else float(regime_details.get("kama_slope", 0.0)),
                "regime": str(ext_regime).upper() if ext_regime is not None else regime_details.get("regime", "RANGE"),
            }
            regime = regime_details["regime"]
            flow_summary = summarize_flow(enriched_df)

    last_close = float(enriched_df["close"].iloc[-1])
    current_vol = (
        float(enriched_df["realized_vol"].dropna().iloc[-1])
        if "realized_vol" in enriched_df.columns and not enriched_df["realized_vol"].dropna().empty
        else float(iv)
    )

    expiration = get_next_options_expiration(
        enriched_df.index[-1],
        expiration_hour=expiry_hour,
        expiration_minute=expiry_minute,
    )
    expected_move_base = float(
        calculate_expected_move_from_expiration(
            last_close,
            current_vol,
            enriched_df.index[-1],
            expiration,
            multiplier=_expected_move_multiplier(regime_details["regime"]),
        )
    )
    horizon_factor = math.sqrt(max(1, int(expiry_days)))
    expected_move = expected_move_base * horizon_factor

    extremos = calculate_extremes(enriched_df)
    next_sweeps = _detect_next_sweeps(last_close, extremos)

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "rows": int(len(enriched_df)),
        "spot": last_close,
        "implied_vol": float(current_vol),
        "days_to_expiry": int(days),
        "expiry_days": int(expiry_days),
        "expiration": str(expiration),
        "expected_move_base_1d": expected_move_base,
        "expected_move": expected_move,
        "regime": regime,
        "regime_label": regime_details["regime"],
        "flow": flow_summary,
        "regime_details": regime_details,
        "strategy_mode": strategy_mode,
        "smc_signals": smc_signals,
        "sweeps": sweeps,
        "next_sweeps": next_sweeps,
        "sd_payload": sd_payload,
        "sd_confluence": float(sd_payload.get("score", 0.0)),
        "trigger_evaluation": trigger_evaluation,  # Avaliação FLEXÍVEL de entrada
    }


def run_pipeline(
    csv_file: Path,
    iv: float,
    days: int,
    expiry_days: int = DEFAULT_EXPIRY_DAYS,
    tail_size: int = DEFAULT_TAIL_SIZE,
    analysis_hour: int = DEFAULT_ANALYSIS_HOUR,
    analysis_minute: int = DEFAULT_ANALYSIS_MINUTE,
    expiry_hour: int = DEFAULT_EXPIRY_HOUR,
    expiry_minute: int = DEFAULT_EXPIRY_MINUTE,
    strategy_mode: str = DEFAULT_STRATEGY_MODE,
    prefer_external_features: bool = False,
) -> dict:
    df = _load_ohlc(csv_file)
    if tail_size > 0:
        df = df.tail(tail_size)

    if df.empty:
        raise ValueError("DataFrame vazio apos carregar dados")

    analysis_ts = _select_analysis_timestamp(df, analysis_hour=analysis_hour, analysis_minute=analysis_minute)
    df_until_analysis = df[df.index <= analysis_ts].copy()
    if df_until_analysis.empty:
        raise ValueError("Sem dados ate o horario de analise")

    context = build_context(
        df_until_analysis,
        iv=iv,
        days=days,
        expiry_days=expiry_days,
        expiry_hour=expiry_hour,
        expiry_minute=expiry_minute,
        strategy_mode=strategy_mode,
        prefer_external_features=prefer_external_features,
    )
    context["analysis_timestamp"] = str(analysis_ts)
    context["analysis_hour"] = f"{analysis_hour:02d}:{analysis_minute:02d}"
    context["expiry_hour"] = f"{expiry_hour:02d}:{expiry_minute:02d}"
    engine_result = run_options_engine(context)

    prediction = {
        "source_file": str(csv_file),
        "context": context,
        "engine_result": engine_result,
    }

    evaluation = _evaluate_next_day(
        df,
        analysis_ts=analysis_ts,
        prediction=prediction,
        expiry_hour=expiry_hour,
        expiry_minute=expiry_minute,
        expiry_days=expiry_days,
        strategy_mode=strategy_mode,
    )
    prediction["evaluation"] = evaluation

    is_valid = validate_prediction(prediction)
    open_path, final_path = _save_prediction(prediction, is_valid)
    report_path = _save_evaluation_report(
        {
            "source_file": str(csv_file),
            "prediction_path": str(final_path),
            "evaluation": evaluation,
            "analysis_timestamp": context["analysis_timestamp"],
            "analysis_hour": context["analysis_hour"],
            "expiry_hour": context["expiry_hour"],
            "tail_size": tail_size,
        }
    )

    prediction["is_valid"] = bool(is_valid)
    prediction["open_path"] = str(open_path)
    prediction["final_path"] = str(final_path)
    prediction["evaluation_report_path"] = str(report_path)

    return prediction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Executa pipeline modular v3 de opcoes")
    parser.add_argument("--file", type=str, default=None, help="CSV especifico; sem isso usa o mais recente")
    parser.add_argument("--iv", type=float, default=0.25, help="Fallback de volatilidade implicita (0-1)")
    parser.add_argument("--days", type=int, default=5, help="Dias uteis ate expiracao")
    parser.add_argument("--tail", type=int, default=DEFAULT_TAIL_SIZE, help="Quantidade de candles processados (padrao=1500)")
    parser.add_argument("--analysis-hour", type=int, default=DEFAULT_ANALYSIS_HOUR, help="Hora da corretora para gerar a previsao")
    parser.add_argument("--analysis-minute", type=int, default=DEFAULT_ANALYSIS_MINUTE, help="Minuto da hora de analise")
    parser.add_argument("--expiry-hour", type=int, default=DEFAULT_EXPIRY_HOUR, help="Hora de vencimento para avaliar fechamento")
    parser.add_argument("--expiry-minute", type=int, default=DEFAULT_EXPIRY_MINUTE, help="Minuto de vencimento para avaliar fechamento")
    parser.add_argument(
        "--expiry-days",
        type=int,
        default=DEFAULT_EXPIRY_DAYS,
        help="Quantidade de dias uteis a frente para avaliar (D+N); expected_move escala por sqrt(N)",
    )
    parser.add_argument(
        "--strategy-mode",
        type=str,
        choices=["strangle", "call-only", "put-only"],
        default=DEFAULT_STRATEGY_MODE,
        help="Modo operacional: strangle (padrao), venda apenas de call ou apenas de put",
    )
    parser.add_argument(
        "--prefer-external-features",
        action="store_true",
        help="Usa colunas pre-calculadas do MT5 (se presentes) para sd_confluence/flow/er/kama/regime",
    )
    parser.add_argument("--backtest", action="store_true", help="Executa backtest tabular dia a dia")
    parser.add_argument("--backtest-days", type=int, default=30, help="Quantidade maxima de dias para avaliar no backtest")
    parser.add_argument("--show-backtest-table", action="store_true", help="Exibe tabela completa no terminal (padrao: somente resumo)")
    parser.add_argument("--csv-only", action="store_true", help="No backtest, gera apenas CSV (sem HTML colorido)")
    parser.add_argument("--no-plot", action="store_true", help="Desativa exibicao do grafico")
    return parser.parse_args()


def _print_rich_summary(result: dict) -> None:
    context = result["context"]
    engine_result = result["engine_result"]
    evaluation = result.get("evaluation", {})

    print("\n" + "=" * 60)
    print("RESUMO OPERACIONAL")
    print("=" * 60)
    print(f"\nAnalise ancorada em: {context.get('analysis_timestamp')}")
    print(f"Hora alvo da corretora: {context.get('analysis_hour')}")
    print(f"\nExpiracao opcoes broker: {context['expiration']}")
    print(f"\nHorizonte de avaliacao: D+{context.get('expiry_days', DEFAULT_EXPIRY_DAYS)}")
    print(f"Expected Move base (D+1): {context.get('expected_move_base_1d', context['expected_move']):.2f} pontos")
    print(f"Expected Move ajustado: {context['expected_move']:.2f} pontos")
    print(f"\nRegime atual: {context['regime']}")
    print(f"\nFlow atual: {context['flow']}")
    print(f"\nModo de estrategia: {context.get('strategy_mode', DEFAULT_STRATEGY_MODE)}")

    # ===== TRIGGER EVALUATION =====
    trigger_eval = context.get("trigger_evaluation", {})
    if trigger_eval:
        print("\n" + "=" * 60)
        print("AVALIAÇÃO DE TRIGGERS (FLEXÍVEL - Não é imposição)")
        print("=" * 60)
        
        overall_quality = trigger_eval.get("overall_entry_quality", 0)
        recommendation = trigger_eval.get("recommendation", "DESCONHECIDO")
        
        # Barra de qualidade visual
        filled = int(overall_quality / 10)
        bar = "█" * filled + "░" * (10 - filled)
        
        print(f"\n📊 QUALIDADE GERAL DA ENTRADA: {bar} {overall_quality}%")
        print(f"   Recomendação: {recommendation}")
        
        # Detalhes de cada componente
        sd_score = trigger_eval.get("sd_quality_score", 0)
        conf_score = trigger_eval.get("confluence_score", 0)
        distance_pct = trigger_eval.get("distance_to_sd_pct")
        
        print(f"\n   • Supply/Demand Score: {sd_score}%", end="")
        if distance_pct is not None:
            print(f" (Distância: {distance_pct:.4f}%)")
        else:
            print(" (Nenhuma SD zone)")
        
        print(f"   • Confluências Score: {conf_score}%", end="")
        conf_count = trigger_eval.get("confluence_count", 0)
        if conf_count > 0:
            print(f" ({conf_count} confluência(s))")
        else:
            print()
        
        print(f"\n   Summary: {trigger_eval.get('summary', 'Sem informação')}")
        
        in_sd = trigger_eval.get("in_sd_zone", False)
        if in_sd:
            print("\n   ✅ ÓTIMO: Candle dentro da SD zone!")

    print("\n" + "=" * 60)
    print("SWEEPS")
    print("=" * 60)
    sweeps = context.get("sweeps", [])
    if sweeps:
        sweeps_df = pd.DataFrame(sweeps)
        print(sweeps_df.tail(10).to_string(index=False))
    else:
        print("Nenhum sweep encontrado.")

    print("\n" + "=" * 60)
    print("MAPA DE LIQUIDEZ")
    print("=" * 60)
    next_sweeps = context.get("next_sweeps", {})
    print(f"\nProximo sweep superior: {next_sweeps.get('next_top_sweep')}")
    print(f"Proximo sweep inferior: {next_sweeps.get('next_bottom_sweep')}")

    print("\n" + "=" * 60)
    print("CONFLUENCIAS SD")
    print("=" * 60)
    confluences = context.get("sd_payload", {}).get("confluences", [])
    if confluences:
        print(pd.DataFrame(confluences).tail(10).to_string(index=False))
    else:
        print("Nenhuma confluencia encontrada.")

    print("\n" + "=" * 60)
    print(f"STRIKES SUGERIDOS - {context['expiration']}")
    print("=" * 60)
    strikes = engine_result.get("option_strikes", [])
    if strikes:
        strikes_df = pd.DataFrame(strikes)
        view = strikes_df[["side", "strike", "sd_level", "prob_otm", "delta", "reversal_score"]].copy()
        view["prob_otm"] = (view["prob_otm"] * 100).round(2)
        view["delta"] = view["delta"].round(3)
        print(view.head(10).to_string(index=False))
    else:
        print("Nenhum strike encontrado.")

    print("\n" + "=" * 60)
    print("AVALIACAO DIA SEGUINTE")
    print("=" * 60)
    if evaluation.get("status") == "EVALUATED":
        print(f"Data avaliada: {evaluation['target_date']}")
        print(f"Candle de fechamento avaliado: {evaluation['expiry_close_timestamp']} (vencimento {evaluation['expiry_hour']})")
        print(f"Close do dia seguinte: {evaluation['next_day_close']:.2f}")
        print(f"Movimento realizado: {evaluation['realized_move']:.2f}")
        print(f"Faixa esperada: [{evaluation['expected_lower']:.2f}, {evaluation['expected_upper']:.2f}]")
        print(f"Strikes primarios (melhor edge por lado): PUT={evaluation['best_put_strike']} | CALL={evaluation['best_call_strike']}")
        print(f"Top 3 PUTs: {evaluation['put_1']}, {evaluation['put_2']}, {evaluation['put_3']}")
        print(f"Top 3 CALLs: {evaluation['call_1']}, {evaluation['call_2']}, {evaluation['call_3']}")
        print(f"Expected move respeitado: {evaluation['expected_move_respected']}")
        print(f"Fechou dentro da faixa esperada: {evaluation['close_within_expected_band']}")
        print(f"Fechou dentro dos strikes primarios: {evaluation['close_within_strikes']}")
        print(f"Fechou dentro de algum par (1/2/3): {evaluation['close_within_any_pair']}")
        print(
            "Chance por estrategia (%): "
            f"CALL={evaluation.get('chance_call_only_pct')} | "
            f"PUT={evaluation.get('chance_put_only_pct')} | "
            f"STRANGLE={evaluation.get('chance_strangle_pct')}"
        )
        print(
            "Gestao sugerida (trava/rolagem): "
            f"hedge_pts={evaluation.get('hedge_trigger_points')} | "
            f"roll_pts={evaluation.get('roll_trigger_points')}"
        )
        print(
            "PUT vendido -> trava/rolagem: "
            f"trava_preco={evaluation.get('put_hedge_trigger_price')} "
            f"(buy put {evaluation.get('put_hedge_buy_strike')}) | "
            f"rolar_se={evaluation.get('put_roll_trigger_price')} "
            f"(novo strike {evaluation.get('put_roll_target_strike')})"
        )
        print(
            "CALL vendido -> trava/rolagem: "
            f"trava_preco={evaluation.get('call_hedge_trigger_price')} "
            f"(buy call {evaluation.get('call_hedge_buy_strike')}) | "
            f"rolar_se={evaluation.get('call_roll_trigger_price')} "
            f"(novo strike {evaluation.get('call_roll_target_strike')})"
        )
        print(
            "Gatilhos atingidos no periodo avaliado: "
            f"put_trava={evaluation.get('put_hedge_trigger_hit')} | "
            f"put_rolagem={evaluation.get('put_roll_trigger_hit')} | "
            f"call_trava={evaluation.get('call_hedge_trigger_hit')} | "
            f"call_rolagem={evaluation.get('call_roll_trigger_hit')}"
        )
        print(
            "Resultado por estrategia: "
            f"CALL={evaluation.get('success_call_only')} | "
            f"PUT={evaluation.get('success_put_only')} | "
            f"STRANGLE={evaluation.get('success_strangle')}"
        )
        print(f"Hit sweep superior/inferior: {evaluation['hit_next_top_sweep']} / {evaluation['hit_next_bottom_sweep']}")
        print(f"Flow/ER/KAMA slope: {evaluation['flow_score']:.2f} / {evaluation['er_mean']:.2f} / {evaluation['kama_slope']:.2f}")
        print(f"Resultado satisfatorio: {evaluation['satisfactory']}")
        print(f"Regra do satisfatorio: {evaluation['satisfactory_rule']}")
    else:
        print(f"Avaliacao pendente: {evaluation.get('reason', 'Sem detalhe')}")


def _extract_asset_tf(file_path: Path) -> tuple[str, str]:
    parts = file_path.stem.split("_")
    asset = parts[0] if parts else "UNKNOWN"
    tf = parts[1].lower() if len(parts) > 1 else "unknown"
    return asset, tf


def _plot_candles_with_sd(df: pd.DataFrame, context: dict, csv_file: Path) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        print("Plotly nao esta instalado. Grafico nao gerado.")
        return

    asset, tf = _extract_asset_tf(csv_file)
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Price",
        )
    )

    analysis_cutoff = pd.to_datetime(context.get("analysis_timestamp"), errors="coerce")
    if not pd.isna(analysis_cutoff):
        fig.add_vline(
            x=analysis_cutoff,
            line_width=2,
            line_dash="dot",
            line_color="royalblue",
        )
        fig.add_annotation(
            x=analysis_cutoff,
            y=1.0,
            xref="x",
            yref="paper",
            text="Corte da analise",
            showarrow=False,
            yshift=10,
            bgcolor="rgba(65,105,225,0.2)",
            font=dict(color="royalblue", size=10),
        )

    zones = context.get("sd_payload", {}).get("zones", [])
    colors = [
        "rgba(255,0,0,0.6)",
        "rgba(255,100,0,0.5)",
        "rgba(255,150,0,0.4)",
        "rgba(0,255,0,0.6)",
        "rgba(0,200,0,0.5)",
        "rgba(0,150,0,0.4)",
    ]
    levels = ["support_1", "support_2", "support_3", "resistance_1", "resistance_2", "resistance_3"]

    for row in zones:
        day_start = pd.to_datetime(row.get("day_start"), errors="coerce")
        day_end = pd.to_datetime(row.get("day_end"), errors="coerce")

        if pd.isna(day_start) or pd.isna(day_end):
            continue

        for i, (level, color) in enumerate(zip(levels, colors)):
            if level not in row:
                continue
            y_value = row[level]
            if pd.isna(y_value):
                continue

            fig.add_shape(
                type="line",
                xref="x",
                yref="y",
                x0=day_start,
                x1=day_end,
                y0=y_value,
                y1=y_value,
                line=dict(color=color, width=2, dash="dash"),
            )

            fig.add_annotation(
                x=day_start,
                y=y_value,
                text=f"{'S' if i < 3 else 'R'}{i % 3 + 1}",
                showarrow=False,
                yshift=10 if i < 3 else -10,
                bgcolor=color,
                font=dict(color="white", size=10),
            )

    fig.update_layout(
        title=f"{asset} - Analise Completa ({tf}) - Candles + S&D",
        xaxis_title="Data",
        yaxis_title="Preco",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        hovermode="x unified",
        height=800,
    )
    fig.update_xaxes(rangeslider_visible=False, showspikes=True)
    fig.update_yaxes(showspikes=True)

    plots_dir = PATHS["analytics"] / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    html_path = plots_dir / f"{asset}_{tf}_latest.html"
    fig.write_html(str(html_path), include_plotlyjs="cdn")
    print(f"Grafico salvo em: {html_path}")

    try:
        fig.show(config={"displaylogo": False, "scrollZoom": True, "displayModeBar": True})
    except Exception as exc:
        print(f"Nao foi possivel abrir janela do grafico automaticamente: {exc}")


def _save_backtest_table(backtest_df: pd.DataFrame, csv_file: Path) -> Path:
    stats_dir = PATHS["analytics"] / "stats"
    stats_dir.mkdir(parents=True, exist_ok=True)
    asset, tf = _extract_asset_tf(csv_file)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = stats_dir / f"backtest_{asset}_{tf}_{timestamp}.csv"
    backtest_df.to_csv(out_path, index=False)
    return out_path


def _save_backtest_html_styled(backtest_df: pd.DataFrame, csv_file: Path) -> Path:
    """Salva backtest como HTML colorido com estilos condicionais."""
    stats_dir = PATHS["analytics"] / "stats"
    stats_dir.mkdir(parents=True, exist_ok=True)
    asset, tf = _extract_asset_tf(csv_file)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = stats_dir / f"backtest_{asset}_{tf}_{timestamp}_colored.html"
    
    bool_color_columns = {
        "satisfactory",
        "expected_move_respected",
        "close_within_expected_band",
        "close_within_strikes",
        "close_within_pair_1",
        "close_within_pair_2",
        "close_within_pair_3",
        "close_within_any_pair",
        "success_call_only",
        "success_put_only",
        "success_strangle",
        "call_otm_at_close",
        "put_otm_at_close",
        "hit_next_top_sweep",
        "hit_next_bottom_sweep",
    }

    # Criar HTML manualmente
    html_lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        "<title>Backtest Colorido</title>",
        "<style>",
        "table { border-collapse: collapse; font-family: Arial, sans-serif; font-size: 12px; }",
        "th { background-color: #333; color: white; padding: 8px; text-align: left; border: 1px solid #ddd; }",
        "td { padding: 6px; border: 1px solid #ddd; }",
        "tr:nth-child(even) { background-color: #f9f9f9; }",
        ".green { background-color: #90EE90; }",
        ".red { background-color: #FFB6C6; }",
        "</style>",
        "</head>",
        "<body>",
        "<h2>Backtest - Coloração de Strikes</h2>",
        "<p>Verde: PUT > close (OTM bom) | CALL &lt; close (OTM bom)</p>",
        "<p>Vermelho: PUT ≤ close (ITM ruim) | CALL ≥ close (ITM ruim)</p>",
        "<p>Colunas booleanas de performance: Verde=True | Vermelho=False</p>",
        "<table>",
    ]
    
    # Header
    html_lines.append("<tr>")
    for col in backtest_df.columns:
        html_lines.append(f"<th>{col}</th>")
    html_lines.append("</tr>")
    
    # Dados
    for _, row in backtest_df.iterrows():
        html_lines.append("<tr>")
        next_day_close = row.get("next_day_close")
        
        for col in backtest_df.columns:
            val = row[col]
            css_class = ""
            
            # Aplicar cores se for strike
            if pd.notna(val) and pd.notna(next_day_close):
                # PUTs: verde se close > put (put fica OTM = bom)
                if col.startswith("put_") and len(col) > 4 and col[4].isdigit():
                    if next_day_close > val:
                        css_class = "class='green'"
                    else:
                        css_class = "class='red'"
                # CALLs: verde se close < call (call fica OTM = bom)
                elif col.startswith("call_") and len(col) > 5 and col[5].isdigit():
                    if next_day_close < val:
                        css_class = "class='green'"
                    else:
                        css_class = "class='red'"

            # Colunas booleanas de performance: True=verde, False=vermelho
            if col in bool_color_columns and isinstance(val, bool):
                css_class = "class='green'" if val else "class='red'"
            
            # Formatação do valor
            if isinstance(val, bool):
                display_val = "Sim" if val else "Não"
            elif isinstance(val, float):
                display_val = f"{val:.4f}"
            else:
                display_val = str(val)
            
            html_lines.append(f"<td {css_class}>{display_val}</td>")
        html_lines.append("</tr>")
    
    html_lines.extend([
        "</table>",
        "</body>",
        "</html>",
    ])
    
    with out_path.open("w", encoding="utf-8") as fp:
        fp.write("\n".join(html_lines))
    
    return out_path


def _run_backtest_table(
    csv_file: Path,
    iv: float,
    days: int,
    expiry_days: int,
    tail_size: int,
    analysis_hour: int,
    analysis_minute: int,
    expiry_hour: int,
    expiry_minute: int,
    backtest_days: int,
    strategy_mode: str,
    save_html: bool,
    prefer_external_features: bool,
) -> tuple[pd.DataFrame, Path, Path | None]:
    df = _load_ohlc(csv_file)
    if tail_size > 0:
        df = df.tail(tail_size)

    unique_dates = sorted(pd.Series(df.index.date).unique())
    if len(unique_dates) < 3:
        raise ValueError("Dados insuficientes para backtest (minimo 3 dias)")

    candidate_days = unique_dates[:-1]
    if backtest_days > 0:
        candidate_days = candidate_days[-backtest_days:]

    rows = []
    for day in candidate_days:
        day_df = df[df.index.date == day]
        candidates = day_df[
            (day_df.index.hour < analysis_hour)
            | ((day_df.index.hour == analysis_hour) & (day_df.index.minute <= analysis_minute))
        ]

        if candidates.empty:
            continue

        analysis_ts = candidates.index[-1]
        df_until_analysis = df[df.index <= analysis_ts]
        if df_until_analysis.empty:
            continue

        context = build_context(
            df_until_analysis,
            iv=iv,
            days=days,
            expiry_days=expiry_days,
            expiry_hour=expiry_hour,
            expiry_minute=expiry_minute,
            strategy_mode=strategy_mode,
            prefer_external_features=prefer_external_features,
        )
        context["analysis_timestamp"] = str(analysis_ts)
        context["analysis_hour"] = f"{analysis_hour:02d}:{analysis_minute:02d}"
        context["expiry_hour"] = f"{expiry_hour:02d}:{expiry_minute:02d}"
        engine_result = run_options_engine(context)

        prediction = {"context": context, "engine_result": engine_result}
        evaluation = _evaluate_next_day(
            df,
            analysis_ts=analysis_ts,
            prediction=prediction,
            expiry_hour=expiry_hour,
            expiry_minute=expiry_minute,
            expiry_days=expiry_days,
            strategy_mode=strategy_mode,
        )
        if evaluation.get("status") != "EVALUATED":
            continue

        rows.append(
            {
                "analysis_timestamp": evaluation["analysis_timestamp"],
                "target_date": evaluation["target_date"],
                "expiry_days": int(evaluation.get("expiry_days", expiry_days)),
                "expiry_close_timestamp": evaluation["expiry_close_timestamp"],
                "strategy_mode": evaluation["strategy_mode"],
                "regime": context["regime_label"],
                "analysis_price": round(float(evaluation["analysis_price"]), 4),
                "expected_move": round(float(evaluation["expected_move"]), 4),
                "expected_lower": round(float(evaluation["expected_lower"]), 4),
                "expected_upper": round(float(evaluation["expected_upper"]), 4),
                "expected_put_strike": round(float(evaluation["best_put_strike"]), 4) if evaluation["best_put_strike"] is not None else None,
                "expected_call_strike": round(float(evaluation["best_call_strike"]), 4) if evaluation["best_call_strike"] is not None else None,
                "best_put_delta": round(float(evaluation["best_put_delta"]), 4) if evaluation.get("best_put_delta") is not None else None,
                "best_call_delta": round(float(evaluation["best_call_delta"]), 4) if evaluation.get("best_call_delta") is not None else None,
                "mean_primary_delta": round(float(evaluation["mean_primary_delta"]), 4) if evaluation.get("mean_primary_delta") is not None else None,
                "touched_support": bool(evaluation.get("touched_support", False)),
                "touched_resistance": bool(evaluation.get("touched_resistance", False)),
                "entered_zone": bool(evaluation.get("entered_zone", False)),
                "put_1": round(float(evaluation["put_1"]), 4) if evaluation["put_1"] is not None else None,
                "put_2": round(float(evaluation["put_2"]), 4) if evaluation["put_2"] is not None else None,
                "put_3": round(float(evaluation["put_3"]), 4) if evaluation["put_3"] is not None else None,
                "call_1": round(float(evaluation["call_1"]), 4) if evaluation["call_1"] is not None else None,
                "call_2": round(float(evaluation["call_2"]), 4) if evaluation["call_2"] is not None else None,
                "call_3": round(float(evaluation["call_3"]), 4) if evaluation["call_3"] is not None else None,
                "next_day_close": round(float(evaluation["next_day_close"]), 4),
                "realized_move": round(float(evaluation["realized_move"]), 4),
                "expected_move_respected": bool(evaluation["expected_move_respected"]),
                "close_within_expected_band": bool(evaluation["close_within_expected_band"]),
                "close_within_strikes": bool(evaluation["close_within_strikes"]),
                "close_within_pair_1": bool(evaluation["close_within_pair_1"]),
                "close_within_pair_2": bool(evaluation["close_within_pair_2"]),
                "close_within_pair_3": bool(evaluation["close_within_pair_3"]),
                "close_within_any_pair": bool(evaluation["close_within_any_pair"]),
                "chance_call_only_pct": round(float(evaluation["chance_call_only_pct"]), 2) if evaluation["chance_call_only_pct"] is not None else None,
                "chance_put_only_pct": round(float(evaluation["chance_put_only_pct"]), 2) if evaluation["chance_put_only_pct"] is not None else None,
                "chance_strangle_pct": round(float(evaluation["chance_strangle_pct"]), 2) if evaluation["chance_strangle_pct"] is not None else None,
                "hedge_trigger_points": round(float(evaluation["hedge_trigger_points"]), 4) if evaluation.get("hedge_trigger_points") is not None else None,
                "roll_trigger_points": round(float(evaluation["roll_trigger_points"]), 4) if evaluation.get("roll_trigger_points") is not None else None,
                "roll_target_points": round(float(evaluation["roll_target_points"]), 4) if evaluation.get("roll_target_points") is not None else None,
                "put_hedge_trigger_price": round(float(evaluation["put_hedge_trigger_price"]), 4) if evaluation.get("put_hedge_trigger_price") is not None else None,
                "put_hedge_buy_strike": round(float(evaluation["put_hedge_buy_strike"]), 4) if evaluation.get("put_hedge_buy_strike") is not None else None,
                "put_roll_trigger_price": round(float(evaluation["put_roll_trigger_price"]), 4) if evaluation.get("put_roll_trigger_price") is not None else None,
                "put_roll_target_strike": round(float(evaluation["put_roll_target_strike"]), 4) if evaluation.get("put_roll_target_strike") is not None else None,
                "call_hedge_trigger_price": round(float(evaluation["call_hedge_trigger_price"]), 4) if evaluation.get("call_hedge_trigger_price") is not None else None,
                "call_hedge_buy_strike": round(float(evaluation["call_hedge_buy_strike"]), 4) if evaluation.get("call_hedge_buy_strike") is not None else None,
                "call_roll_trigger_price": round(float(evaluation["call_roll_trigger_price"]), 4) if evaluation.get("call_roll_trigger_price") is not None else None,
                "call_roll_target_strike": round(float(evaluation["call_roll_target_strike"]), 4) if evaluation.get("call_roll_target_strike") is not None else None,
                "put_hedge_trigger_hit": bool(evaluation.get("put_hedge_trigger_hit", False)),
                "put_roll_trigger_hit": bool(evaluation.get("put_roll_trigger_hit", False)),
                "call_hedge_trigger_hit": bool(evaluation.get("call_hedge_trigger_hit", False)),
                "call_roll_trigger_hit": bool(evaluation.get("call_roll_trigger_hit", False)),
                "success_call_only": bool(evaluation["success_call_only"]),
                "success_put_only": bool(evaluation["success_put_only"]),
                "success_strangle": bool(evaluation["success_strangle"]),
                "call_otm_at_close": bool(evaluation["call_otm_at_close"]),
                "put_otm_at_close": bool(evaluation["put_otm_at_close"]),
                "next_top_sweep": round(float(evaluation["next_top_sweep"]), 4) if evaluation["next_top_sweep"] is not None else None,
                "next_bottom_sweep": round(float(evaluation["next_bottom_sweep"]), 4) if evaluation["next_bottom_sweep"] is not None else None,
                "hit_next_top_sweep": bool(evaluation["hit_next_top_sweep"]),
                "hit_next_bottom_sweep": bool(evaluation["hit_next_bottom_sweep"]),
                "flow_score": round(float(evaluation["flow_score"]), 4),
                "er_mean": round(float(evaluation["er_mean"]), 4),
                "kama_slope": round(float(evaluation["kama_slope"]), 4),
                "sd_confluence": round(float(evaluation["sd_confluence"]), 4),
                "satisfactory": bool(evaluation["satisfactory"]),
                "satisfactory_rule": evaluation["satisfactory_rule"],
            }
        )

    if not rows:
        raise ValueError("Nenhuma linha de backtest gerada para os filtros atuais")

    backtest_df = pd.DataFrame(rows)
    output_csv = _save_backtest_table(backtest_df, csv_file)
    output_html = _save_backtest_html_styled(backtest_df, csv_file) if save_html else None
    return backtest_df, output_csv, output_html


def _print_strategy_calibration_summary(backtest_df: pd.DataFrame) -> None:
    strategy_specs = [
        ("CALL-ONLY", "chance_call_only_pct", "success_call_only"),
        ("PUT-ONLY", "chance_put_only_pct", "success_put_only"),
        ("STRANGLE", "chance_strangle_pct", "success_strangle"),
    ]

    print("\nComparativo de estrategias (chance prevista vs acerto real):")
    for label, chance_col, success_col in strategy_specs:
        if chance_col not in backtest_df.columns or success_col not in backtest_df.columns:
            continue

        chance_series = pd.to_numeric(backtest_df[chance_col], errors="coerce")
        success_series = backtest_df[success_col].astype(bool)

        chance_mean = float(chance_series.mean()) if not chance_series.empty else float("nan")
        success_rate = float(success_series.mean() * 100.0) if not success_series.empty else float("nan")
        calibration_error = abs(chance_mean - success_rate)

        print(
            f"- {label}: chance_media={chance_mean:.2f}% | "
            f"acerto_real={success_rate:.2f}% | erro={calibration_error:.2f} p.p."
        )


def main() -> int:
    _ensure_directories()
    args = parse_args()

    try:
        csv_file = _choose_csv_file(PATHS["dados"], args.file)
        print(f"Arquivo selecionado: {csv_file.name}")

        if args.backtest:
            print(f"Executando backtest tabular para os ultimos {args.backtest_days} dias...")
            backtest_df, output_csv, output_html = _run_backtest_table(
                csv_file=csv_file,
                iv=args.iv,
                days=args.days,
                expiry_days=args.expiry_days,
                tail_size=args.tail,
                analysis_hour=args.analysis_hour,
                analysis_minute=args.analysis_minute,
                expiry_hour=args.expiry_hour,
                expiry_minute=args.expiry_minute,
                backtest_days=args.backtest_days,
                strategy_mode=args.strategy_mode,
                save_html=not args.csv_only,
                prefer_external_features=args.prefer_external_features,
            )

            total = len(backtest_df)
            positive = int(backtest_df["satisfactory"].sum())
            hit_rate = (positive / total) * 100 if total else 0.0

            print("\n" + "=" * 60)
            print("BACKTEST - EXPECTATIVA VS REALIZADO")
            print("=" * 60)
            print(f"Modo de estrategia: {args.strategy_mode}")
            print(f"Horizonte de avaliacao: D+{args.expiry_days}")
            if args.show_backtest_table:
                print(backtest_df.to_string(index=False))
            else:
                print("Tabela completa omitida no terminal para melhor leitura.")
            print("\nResumo:")
            print(f"Total avaliacoes: {total}")
            print(f"Satisfatorias: {positive}")
            print(f"Taxa de acerto: {hit_rate:.2f}%")
            print(f"Tabela CSV salva em: {output_csv}")
            if output_html is not None:
                print(f"Tabela colorida (HTML) salva em: {output_html}")
            else:
                print("Tabela colorida (HTML): desativada via --csv-only")
            _print_strategy_calibration_summary(backtest_df)

            _append_log("execution", f"Backtest executado para {csv_file.name} com {total} linhas")
            return 0

        print(f"Processando ultimos {args.tail} candles...")
        print(f"Gerando previsao na hora fixa da corretora: {args.analysis_hour:02d}:{args.analysis_minute:02d}")
        print(f"Avaliando fechamento no vencimento: {args.expiry_hour:02d}:{args.expiry_minute:02d}")
        print(f"Horizonte de avaliacao: D+{args.expiry_days}")
        print(f"Modo de estrategia: {args.strategy_mode}")
        result = run_pipeline(
            csv_file,
            iv=args.iv,
            days=args.days,
            expiry_days=args.expiry_days,
            tail_size=args.tail,
            analysis_hour=args.analysis_hour,
            analysis_minute=args.analysis_minute,
            expiry_hour=args.expiry_hour,
            expiry_minute=args.expiry_minute,
            strategy_mode=args.strategy_mode,
            prefer_external_features=args.prefer_external_features,
        )

        _append_log("execution", f"Pipeline v3 executado com sucesso para {csv_file.name}")
        _append_log("validation", f"Resultado validado={result['is_valid']} em {result['final_path']}")

        print("Pipeline v3 concluido")
        print(f"Arquivo origem: {result['source_file']}")
        print(f"Ativo spot: {result['context']['spot']:.2f}")
        print(f"Expected move: {result['context']['expected_move']:.4f}")
        print(f"Regime: {result['context']['regime']}")
        print(f"SMC signals: {len(result['context']['smc_signals'])}")
        print(f"Sweeps: {len(result['context']['sweeps'])}")
        print(f"Confluencia SD: {result['context']['sd_confluence']}")
        print(f"Validado: {result['is_valid']}")
        print(f"Open: {result['open_path']}")
        print(f"Destino final: {result['final_path']}")
        print(f"Relatorio de avaliacao: {result['evaluation_report_path']}")
        _print_rich_summary(result)

        if not args.no_plot:
            print("Gerando grafico...")
            chart_df = _load_ohlc(csv_file)
            if args.tail > 0:
                chart_df = chart_df.tail(args.tail)
            _plot_candles_with_sd(chart_df, result["context"], csv_file)
        return 0

    except Exception as exc:
        _append_log("errors", f"Falha no pipeline v3: {exc}")
        print(f"Erro no pipeline v3: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
