"""Smart Money Concepts (SMC) helpers."""

import numpy as np
import pandas as pd


def directional_change(close, high, low, sigma, min_sigma=1e-4):
    sigma = max(abs(float(sigma)), min_sigma)
    n = len(close)
    if n == 0:
        return [], []

    up_zig = True
    tmp_max, tmp_min = high[0], low[0]
    tmp_max_i, tmp_min_i = 0, 0
    tops, bottoms = [], []

    for i in range(1, n):
        price = close[i]
        if up_zig:
            if high[i] >= tmp_max:
                tmp_max = high[i]
                tmp_max_i = i
            reversal = (tmp_max - price) / tmp_max
            if reversal >= sigma:
                tops.append([i, tmp_max_i, tmp_max])
                up_zig = False
                tmp_min = low[i]
                tmp_min_i = i
        else:
            if low[i] <= tmp_min:
                tmp_min = low[i]
                tmp_min_i = i
            reversal = (price - tmp_min) / tmp_min
            if reversal >= sigma:
                bottoms.append([i, tmp_min_i, tmp_min])
                up_zig = True
                tmp_max = high[i]
                tmp_max_i = i

    return tops, bottoms


def calculate_extremes(df: pd.DataFrame) -> pd.DataFrame:
    vol_series = df["close"].pct_change().rolling(20).std()
    sigma = vol_series.iloc[-1]
    if np.isnan(sigma):
        sigma = 0.002
    sigma = np.clip(sigma, 0.002, 0.02)

    tops, bottoms = directional_change(
        df["close"].to_numpy(),
        df["high"].to_numpy(),
        df["low"].to_numpy(),
        sigma,
    )

    extremos = []
    for entry in tops:
        i = entry[1]
        extremos.append({"datetime": df.index[i], "price": entry[2], "type": "top"})
    for entry in bottoms:
        i = entry[1]
        extremos.append({"datetime": df.index[i], "price": entry[2], "type": "bottom"})

    if not extremos:
        return pd.DataFrame(columns=["price", "type"], index=pd.Index([], name="datetime"))

    return pd.DataFrame(extremos).set_index("datetime").sort_index()


def detect_bos_choch(df: pd.DataFrame, extremos: pd.DataFrame, atr_mult: float = 1.0) -> pd.DataFrame:
    eventos = []
    tendencia = None
    ultimo_bos_topo = None
    ultimo_bos_fundo = None

    for idx, row in extremos.iterrows():
        close = row["price"]
        ult_topo = row.get("last_top")
        ult_fundo = row.get("last_bottom")
        atr = df.loc[idx, "atr"] if "atr" in df.columns and idx in df.index else 1.0

        if ult_topo is not None and close > ult_topo and ult_topo != ultimo_bos_topo and atr > 0:
            displacement = abs(close - ult_topo) / atr
            if displacement >= atr_mult:
                eventos.append({"datetime": idx, "event": "BOS_BULL", "price": close, "displacement": displacement})
                if tendencia == "bearish":
                    eventos.append({"datetime": idx, "event": "CHOCH_BULL", "price": close, "displacement": displacement})
                tendencia = "bullish"
                ultimo_bos_topo = ult_topo

        if ult_fundo is not None and close < ult_fundo and ult_fundo != ultimo_bos_fundo and atr > 0:
            displacement = abs(close - ult_fundo) / atr
            if displacement >= atr_mult:
                eventos.append({"datetime": idx, "event": "BOS_BEAR", "price": close, "displacement": displacement})
                if tendencia == "bullish":
                    eventos.append({"datetime": idx, "event": "CHOCH_BEAR", "price": close, "displacement": displacement})
                tendencia = "bearish"
                ultimo_bos_fundo = ult_fundo

    if not eventos:
        return pd.DataFrame(columns=["event"], index=pd.Index([], name="datetime"))

    return pd.DataFrame(eventos).set_index("datetime")


def detect_fvg(df: pd.DataFrame) -> pd.DataFrame:
    fvgs = []
    for i in range(2, len(df)):
        candle_0 = df.iloc[i - 2]
        candle_2 = df.iloc[i]
        if candle_2["low"] > candle_0["high"]:
            fvgs.append({"datetime": df.index[i], "event": "FVG_BULL"})
        elif candle_2["high"] < candle_0["low"]:
            fvgs.append({"datetime": df.index[i], "event": "FVG_BEAR"})

    if not fvgs:
        return pd.DataFrame(columns=["event"], index=pd.Index([], name="datetime"))
    return pd.DataFrame(fvgs).set_index("datetime")


def calculate_score_smc(df: pd.DataFrame, eventos: pd.DataFrame, fvgs: pd.DataFrame) -> pd.DataFrame:
    score = pd.DataFrame(index=df.index)
    score["score"] = 0.0

    if not eventos.empty:
        for idx, row in eventos.iterrows():
            if row["event"] == "BOS_BULL":
                score.loc[idx, "score"] += 2
            elif row["event"] == "BOS_BEAR":
                score.loc[idx, "score"] -= 2
            elif row["event"] == "CHOCH_BULL":
                score.loc[idx, "score"] += 3
            elif row["event"] == "CHOCH_BEAR":
                score.loc[idx, "score"] -= 3

    if not fvgs.empty:
        for idx, row in fvgs.iterrows():
            if row["event"] == "FVG_BULL":
                score.loc[idx, "score"] += 1
            elif row["event"] == "FVG_BEAR":
                score.loc[idx, "score"] -= 1

    score["flow_score"] = score["score"].ewm(alpha=0.2, adjust=False, ignore_na=True).mean()
    score["flow_std"] = score["score"].ewm(alpha=0.2, adjust=False).std().fillna(0)
    return score


def detect_smc_signals(df: pd.DataFrame):
    """Detect SMC events from OHLC dataframe and return recent events as records."""
    extremos = calculate_extremes(df)
    eventos = detect_bos_choch(df, extremos, atr_mult=1.0)
    fvgs = detect_fvg(df)

    records = []
    if not eventos.empty:
        recent_events = eventos.tail(10).reset_index().to_dict(orient="records")
        for record in recent_events:
            record["datetime"] = str(record["datetime"])
            records.append(record)

    if not fvgs.empty:
        recent_fvgs = fvgs.tail(5).reset_index().to_dict(orient="records")
        for record in recent_fvgs:
            record["datetime"] = str(record["datetime"])
            records.append(record)

    return records
