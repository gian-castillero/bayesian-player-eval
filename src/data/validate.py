"""Schema checks and missing-value assertions for wrangled DataFrames."""
from __future__ import annotations

import pandas as pd


def validate(df: pd.DataFrame) -> None:
    """Assert that df matches the expected schema from wrangle().

    Args:
        df: Output of wrangle().

    Raises:
        ValueError: If any required column is missing or contains nulls.
    """
    raise NotImplementedError("Implemented in STEP 6")
