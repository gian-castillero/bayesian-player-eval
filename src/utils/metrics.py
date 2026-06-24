"""Per-90 normalization and minutes filters."""
from __future__ import annotations

import pandas as pd


def per_90(series: pd.Series, minutes: pd.Series) -> pd.Series:
    """Normalize a counting stat to a per-90-minute rate.

    Args:
        series: Raw counting stat (e.g. goals, key passes).
        minutes: Minutes played in the same match.

    Returns:
        Per-90 normalized Series.
    """
    raise NotImplementedError("Implemented in STEP 6")
