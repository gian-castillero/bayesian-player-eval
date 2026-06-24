"""Raw Wyscout CSV → tidy long-format DataFrame."""
from __future__ import annotations

import pandas as pd


def wrangle(raw_path: str) -> pd.DataFrame:
    """Clean and normalize raw Wyscout match export.

    Args:
        raw_path: Path to the raw Wyscout CSV export.

    Returns:
        Long-format DataFrame with one row per (player, match).
    """
    raise NotImplementedError("Implemented in STEP 6")
