"""Expected move calculations."""

from datetime import timedelta

import numpy as np


def get_next_options_expiration(last_timestamp, expiration_hour: int = 14, expiration_minute: int = 0):
    """Return next broker option expiration timestamp (daily 14:00 UTC)."""
    expiration = last_timestamp.replace(
        hour=expiration_hour,
        minute=expiration_minute,
        second=0,
        microsecond=0,
    )

    if last_timestamp >= expiration:
        expiration += timedelta(days=1)
        while expiration.weekday() >= 5:
            expiration += timedelta(days=1)

    return expiration


def time_to_expiration_years(now_ts, expiration_ts) -> float:
    seconds = (expiration_ts - now_ts).total_seconds()
    return max(seconds / (60 * 60 * 24 * 365.25), 1e-6)


def calculate_expected_move(spot, implied_vol, days):
    """Calculate expected move for the selected horizon in trading days."""
    if days <= 0:
        return 0.0
    return spot * implied_vol * (days / 252.0) ** 0.5


def calculate_expected_move_from_expiration(spot, annualized_vol, now_ts, expiration_ts, multiplier: float = 1.0):
    """Calculate expected move based on annualized volatility and exact expiration time."""
    t = time_to_expiration_years(now_ts, expiration_ts)
    return float(spot * annualized_vol * np.sqrt(t) * multiplier)
