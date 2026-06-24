"""PyMC model definition — pure model, no sampling, no I/O."""
from __future__ import annotations

import pandas as pd
import pymc as pm


def build_model(df: pd.DataFrame, metric: str) -> tuple[pm.Model, dict]:
    """Build the Bayesian hierarchical player evaluation model.

    Args:
        df: Wrangled long-format DataFrame from wrangle().
        metric: Column name of the per-90 metric to model (e.g. 'xg_p90').

    Returns:
        Tuple of (model, coords) ready for pm.sample().
    """
    raise NotImplementedError("Implemented in STEP 7")
