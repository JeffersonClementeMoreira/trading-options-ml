"""Prediction and signal validation rules."""


def validate_prediction(prediction):
    """Return True when prediction passes current rule set."""
    if not isinstance(prediction, dict):
        return False

    context = prediction.get("context", {})
    engine_result = prediction.get("engine_result", {})

    has_spot = float(context.get("spot", 0.0)) > 0
    has_expected_move = float(context.get("expected_move", 0.0)) > 0
    has_regime = bool(context.get("regime"))

    strikes = engine_result.get("option_strikes", [])
    has_strikes = isinstance(strikes, list) and len(strikes) > 0

    return bool(has_spot and has_expected_move and has_regime and has_strikes)
