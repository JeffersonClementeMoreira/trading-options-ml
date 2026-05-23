"""Market regime detection."""

import pandas as pd


def detect_regime_details(df: pd.DataFrame, window: int = 10) -> dict:
    if df.empty:
        return {
            "regime": "UNDEFINED",
            "score_roll": 0.0,
            "er_mean": 0.0,
            "kama_slope": 0.0,
            "flow_score": 0.0,
        }

    er_series = df.get("er", pd.Series(0.0, index=df.index)).rolling(window).mean().fillna(0.0)
    kama_slope_series = df.get("kama", df["close"]).diff(window).fillna(0.0)

    # Proxy de fluxo usando retorno recente quando o score SMC detalhado nao esta disponivel.
    flow_series = df.get("return", pd.Series(0.0, index=df.index)).fillna(0.0).ewm(alpha=0.2, adjust=False).mean()
    flow_score = float((flow_series.iloc[-1] * 1000.0))
    score_roll = float(flow_score * window)

    er = float(er_series.iloc[-1])
    slope = float(kama_slope_series.iloc[-1])

    if er > 0.45 and slope > 0:
        regime_label = "TREND_BULL"
    elif er > 0.45 and slope < 0:
        regime_label = "TREND_BEAR"
    elif er < 0.25 and abs(flow_score) < 0.5:
        regime_label = "RANGE"
    else:
        regime_label = "MANIPULATION"

    return {
        "regime": regime_label,
        "score_roll": score_roll,
        "er_mean": er,
        "kama_slope": slope,
        "flow_score": flow_score,
    }


def detect_regime(df: pd.DataFrame) -> str:
    """Return current market regime summary label."""
    details = detect_regime_details(df)
    return (
        f"{details['regime']} | "
        f"Flow={details['score_roll']:.2f} | "
        f"ER={details['er_mean']:.2f} | "
        f"KAMA slope={details['kama_slope']:.2f}"
    )


def summarize_flow(df: pd.DataFrame) -> str:
    details = detect_regime_details(df)
    flow = details["flow_score"]

    if flow > 3:
        direction = "FORTE COMPRADOR"
    elif flow > 1:
        direction = "COMPRADOR"
    elif flow < -3:
        direction = "FORTE VENDEDOR"
    elif flow < -1:
        direction = "VENDEDOR"
    else:
        direction = "NEUTRO"

    return f"{direction} (flow={flow:.2f})"
