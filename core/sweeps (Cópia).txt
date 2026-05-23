"""Liquidity sweep detection."""

import pandas as pd

from .smc import calculate_extremes


def detect_liquidity_sweep(
    df: pd.DataFrame,
    extremos: pd.DataFrame,
    candles_validacao: int = 8,
    atr_filter: float = 0.5,
) -> pd.DataFrame:
    sweeps = []

    for idx, row in extremos.iterrows():
        future = df[df.index > idx].head(candles_validacao)
        if future.empty:
            continue

        nivel = row["price"]
        for candle_idx, candle in future.iterrows():
            atr = candle.get("atr")
            if pd.isna(atr) or atr <= 0:
                continue

            if row["type"] == "top":
                wick = candle["high"] - nivel
                displacement = wick / atr
                if (
                    candle["high"] > nivel
                    and candle["close"] < (nivel - atr * 0.15)
                    and displacement >= atr_filter
                ):
                    sweeps.append(
                        {
                            "datetime": candle_idx,
                            "event": "SWEEP_TOP",
                            "price": candle["close"],
                            "displacement": displacement,
                        }
                    )
                    break

            elif row["type"] == "bottom":
                wick = nivel - candle["low"]
                displacement = wick / atr
                if (
                    candle["low"] < nivel
                    and candle["close"] > (nivel + atr * 0.15)
                    and displacement >= atr_filter
                ):
                    sweeps.append(
                        {
                            "datetime": candle_idx,
                            "event": "SWEEP_BOTTOM",
                            "price": candle["close"],
                            "displacement": displacement,
                        }
                    )
                    break

    if not sweeps:
        return pd.DataFrame(columns=["event"], index=pd.Index([], name="datetime"))

    return pd.DataFrame(sweeps).set_index("datetime")


def detect_sweeps(df):
    """Return sweep events as list of serializable records."""
    extremos = calculate_extremes(df)
    sweeps_df = detect_liquidity_sweep(df, extremos, candles_validacao=8, atr_filter=0.5)

    if sweeps_df.empty:
        return []

    records = sweeps_df.tail(20).reset_index().to_dict(orient="records")
    for record in records:
        record["datetime"] = str(record["datetime"])
        record["price"] = float(record["price"])
        record["displacement"] = float(record["displacement"])
    return records
