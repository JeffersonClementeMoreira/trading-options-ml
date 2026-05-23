"""Options strategy engine."""

import math

import pandas as pd
from scipy.stats import norm


def _zscore_log_moneyness(current_price: float, strike: float, expected_move: float) -> float | None:
    if expected_move <= 0 or current_price <= 0:
        return None
    sigma_move = expected_move / current_price
    if sigma_move <= 0:
        return None
    return math.log(strike / current_price) / sigma_move


def _probability_expire_otm(side: str, current_price: float, strike: float, expected_move: float) -> float:
    z = _zscore_log_moneyness(current_price, strike, expected_move)
    if z is None:
        return 0.5

    # CALL OTM: S_T < K => CDF(z)
    if side == "SELL_CALL":
        return float(norm.cdf(z))

    # PUT OTM: S_T > K => 1 - CDF(z)
    if side == "SELL_PUT":
        return float(1.0 - norm.cdf(z))

    return 0.5


def _approx_delta(current_price: float, strike: float, expected_move: float) -> float:
    z = _zscore_log_moneyness(current_price, strike, expected_move)
    if z is None:
        return 0.5
    return norm.cdf(-abs(z))


def _extract_latest_zone(sd_payload: dict) -> dict | None:
    zones = sd_payload.get("zones", []) if isinstance(sd_payload, dict) else []
    if not zones:
        return None
    return zones[-1]


def run_options_engine(context):
    """Run strategy engine with prepared context."""
    current_price = float(context.get("spot", 0.0))
    expected_move = float(context.get("expected_move", 0.0))
    sd_payload = context.get("sd_payload", {})

    latest_zone = _extract_latest_zone(sd_payload)
    if not latest_zone:
        return {"signals": [], "option_strikes": [], "meta": context}

    confluencias = pd.DataFrame(sd_payload.get("confluences", []))
    suggestions = []

    for n in range(1, 4):
        strike = float(latest_zone.get(f"resistance_{n}", 0.0))
        if strike <= 0:
            continue

        prob_otm = _probability_expire_otm("SELL_CALL", current_price, strike, expected_move)
        delta = _approx_delta(current_price, strike, expected_move)
        reversal_score = 0

        if not confluencias.empty:
            confl = confluencias[(confluencias["type"] == "RESISTANCE") & (confluencias["price"].sub(strike).abs() <= expected_move * 0.25)]
            if not confl.empty:
                reversal_score = int(confl["score"].max())

        edge_score = prob_otm * 100 + reversal_score * 12 - delta * 40 - n * 2
        suggestions.append(
            {
                "side": "SELL_CALL",
                "strike": strike,
                "sd_level": n,
                "prob_otm": float(prob_otm),
                "delta": float(delta),
                "reversal_score": reversal_score,
                "edge_score": float(edge_score),
            }
        )

    for n in range(1, 4):
        strike = float(latest_zone.get(f"support_{n}", 0.0))
        if strike <= 0:
            continue

        prob_otm = _probability_expire_otm("SELL_PUT", current_price, strike, expected_move)
        delta = _approx_delta(current_price, strike, expected_move)
        reversal_score = 0

        if not confluencias.empty:
            confl = confluencias[(confluencias["type"] == "SUPPORT") & (confluencias["price"].sub(strike).abs() <= expected_move * 0.25)]
            if not confl.empty:
                reversal_score = int(confl["score"].max())

        edge_score = prob_otm * 100 + reversal_score * 12 - delta * 40 - n * 2
        suggestions.append(
            {
                "side": "SELL_PUT",
                "strike": strike,
                "sd_level": n,
                "prob_otm": float(prob_otm),
                "delta": float(delta),
                "reversal_score": reversal_score,
                "edge_score": float(edge_score),
            }
        )

    suggestions = sorted(suggestions, key=lambda x: x["edge_score"], reverse=True)
    signals = [f"{row['side']} @ {row['strike']:.2f}" for row in suggestions[:3]]

    return {"signals": signals, "option_strikes": suggestions, "meta": context}
