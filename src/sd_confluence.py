"""Supply and demand confluence helpers."""

from datetime import timedelta

import numpy as np
import pandas as pd


def calculate_sd_reversal_tolerance(current_price, atr, realized_vol, regime=None):
    atr_pct = atr / current_price if current_price else 0.0
    vol_component = realized_vol / np.sqrt(252) if realized_vol else 0.0

    tolerance = atr_pct * 0.75 + vol_component * 0.25

    if regime == "RANGE":
        tolerance *= 0.7
    elif regime == "MANIPULATION":
        tolerance *= 1.35
    elif regime in ["TREND_BULL", "TREND_BEAR"]:
        tolerance *= 1.10

    return float(np.clip(tolerance, 0.0015, 0.0150))


def calculate_zonas_sd(df: pd.DataFrame, vol_period: int = 20, tf: str = "m15", hour_daily: int = 23) -> pd.DataFrame:
    tf_map = {"m1": 1440, "m5": 288, "m15": 96, "m30": 48, "h1": 24, "h4": 6}
    barras_dia = tf_map.get(tf, 96)

    dfc = df.copy()
    dfc["returns"] = dfc["close"].pct_change()
    dfc["vol"] = dfc["returns"].rolling(vol_period).std() * np.sqrt(barras_dia)

    daily = dfc.groupby(dfc.index.date).agg({"close": "last", "vol": "last"})
    daily.index = pd.to_datetime(daily.index)
    daily["close_prev"] = daily["close"].shift(1)
    daily["vol_prev"] = daily["vol"].shift(1)
    daily = daily.dropna()

    for n in range(1, 4):
        offset = n * daily["vol_prev"] * daily["close_prev"]
        daily[f"support_{n}"] = daily["close_prev"] - offset
        daily[f"resistance_{n}"] = daily["close_prev"] + offset

    daily["day_start"] = daily.index.normalize()
    daily["day_end"] = daily["day_start"] + pd.Timedelta(hours=hour_daily)
    return daily


def detect_sd_confluence(zonas_sd: pd.DataFrame, tolerance: float, lookback_sd: int = 20) -> pd.DataFrame:
    if len(zonas_sd) < 2:
        return pd.DataFrame()

    confluencias = []
    for i in range(1, len(zonas_sd)):
        atual = zonas_sd.iloc[i]
        historico = zonas_sd.iloc[max(0, i - lookback_sd):i]

        for n_atual in range(1, 4):
            r_atual = atual[f"resistance_{n_atual}"]
            s_atual = atual[f"support_{n_atual}"]

            for _, row_hist in historico.iterrows():
                for n_prev in range(1, 4):
                    r_prev = row_hist[f"resistance_{n_prev}"]
                    s_prev = row_hist[f"support_{n_prev}"]

                    if pd.isna(r_prev) or pd.isna(s_prev):
                        continue

                    tol_r = abs(r_prev) * tolerance
                    tol_s = abs(s_prev) * tolerance

                    if abs(r_atual - r_prev) <= tol_r:
                        confluencias.append(
                            {
                                "datetime": atual.name,
                                "type": "RESISTANCE",
                                "price": r_atual,
                                "score": n_atual + n_prev,
                                "current_sd": n_atual,
                                "previous_sd": n_prev,
                            }
                        )

                    if abs(s_atual - s_prev) <= tol_s:
                        confluencias.append(
                            {
                                "datetime": atual.name,
                                "type": "SUPPORT",
                                "price": s_atual,
                                "score": n_atual + n_prev,
                                "current_sd": n_atual,
                                "previous_sd": n_prev,
                            }
                        )

    if not confluencias:
        return pd.DataFrame()

    return pd.DataFrame(confluencias)


def _next_business_day(ts: pd.Timestamp) -> pd.Timestamp:
    next_day = ts.normalize() + timedelta(days=1)
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    return next_day


def _append_projected_next_day_zone(df: pd.DataFrame, zonas_sd: pd.DataFrame, hour_daily: int = 23) -> pd.DataFrame:
    """Project next-day SD levels from the latest available day at analysis cutoff."""
    if df.empty:
        return zonas_sd

    dfc = df.copy()
    if "returns" not in dfc.columns:
        dfc["returns"] = dfc["close"].pct_change()

    # Use m15 by default to be consistent with the rest of the pipeline.
    bars_per_day = 96
    if "vol" not in dfc.columns:
        dfc["vol"] = dfc["returns"].rolling(20).std() * np.sqrt(bars_per_day)

    last_ts = dfc.index[-1]
    last_day_df = dfc[dfc.index.date == last_ts.date()]
    if last_day_df.empty:
        return zonas_sd

    close_prev = float(last_day_df["close"].iloc[-1])
    vol_prev_series = last_day_df["vol"].dropna()
    if vol_prev_series.empty:
        vol_prev_series = dfc["vol"].dropna()
    if vol_prev_series.empty:
        return zonas_sd

    vol_prev = float(vol_prev_series.iloc[-1])

    # Avoid collapsed projected levels when intraday vol at cutoff is zero.
    historical_vol = pd.concat(
        [
            last_day_df["vol"],
            dfc["vol"],
            zonas_sd.get("vol_prev", pd.Series(dtype=float)),
        ]
    ).dropna()
    historical_vol = historical_vol[historical_vol > 0]
    if not historical_vol.empty:
        robust_floor = float(historical_vol.quantile(0.25))
        vol_prev = max(vol_prev, robust_floor)

    if vol_prev <= 0:
        return zonas_sd

    projected_idx = _next_business_day(last_ts)

    projected_row = {
        "close": np.nan,
        "vol": np.nan,
        "close_prev": close_prev,
        "vol_prev": vol_prev,
        "day_start": projected_idx,
        "day_end": projected_idx + pd.Timedelta(hours=hour_daily),
        "projected": True,
    }

    for n in range(1, 4):
        offset = n * vol_prev * close_prev
        projected_row[f"support_{n}"] = close_prev - offset
        projected_row[f"resistance_{n}"] = close_prev + offset

    out = zonas_sd.copy()
    if "projected" not in out.columns:
        out["projected"] = False

    if projected_idx in out.index:
        for col, value in projected_row.items():
            out.loc[projected_idx, col] = value
    else:
        out.loc[projected_idx] = projected_row

    return out.sort_index()


def evaluate_sd_confluence(df: pd.DataFrame):
    """Return SD summary used by v3 engine and output."""
    if df.empty:
        return {"score": 0.0, "zones": [], "confluences": [], "tolerance": 0.0}

    zonas_sd = calculate_zonas_sd(df, vol_period=20, tf="m15", hour_daily=23)
    if zonas_sd.empty:
        return {"score": 0.0, "zones": [], "confluences": [], "tolerance": 0.0}

    zonas_sd = _append_projected_next_day_zone(df, zonas_sd, hour_daily=23)

    current_price = float(df["close"].iloc[-1])
    atr = float(df["atr"].dropna().iloc[-1]) if "atr" in df.columns and not df["atr"].dropna().empty else 0.0
    rv = float(df["realized_vol"].dropna().iloc[-1]) if "realized_vol" in df.columns and not df["realized_vol"].dropna().empty else 0.2

    tolerance = calculate_sd_reversal_tolerance(current_price, atr, rv)
    confluencias = detect_sd_confluence(zonas_sd, tolerance=tolerance, lookback_sd=20)

    score = float(confluencias["score"].tail(10).mean()) if not confluencias.empty else 0.0

    zones_payload = zonas_sd.reset_index().to_dict(orient="records")
    for row in zones_payload:
        row["index"] = str(row["index"])
        row["projected"] = bool(row.get("projected", False))

    confluence_payload = confluencias.tail(10).to_dict(orient="records") if not confluencias.empty else []
    for row in confluence_payload:
        row["datetime"] = str(row["datetime"])
        row["price"] = float(row["price"])
        row["score"] = int(row["score"])

    return {
        "score": score,
        "zones": zones_payload,
        "confluences": confluence_payload,
        "tolerance": tolerance,
    }
