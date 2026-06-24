"""Posterior extraction and ranking utilities for the dashboard."""
from __future__ import annotations

import arviz as az
import pandas as pd


def extract_rankings(trace: az.InferenceData, coords: dict) -> pd.DataFrame:
    """Compute posterior mean and 90% CI per player.

    Args:
        trace: ArviZ InferenceData from run_sampling().
        coords: Coordinate dict from build_model().

    Returns:
        DataFrame with columns: player_id, theta_mean, theta_lo, theta_hi.
    """
    raise NotImplementedError("Implemented in STEP 9")


def shrinkage_df(trace: az.InferenceData, df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-player naive per-90, posterior mean, and shrinkage factor.

    Args:
        trace: ArviZ InferenceData from run_sampling().
        df: Wrangled DataFrame from wrangle().

    Returns:
        DataFrame with columns: player_id, naive_p90, theta_mean, lambda_i.
    """
    raise NotImplementedError("Implemented in STEP 9")


def prob_better(
    trace: az.InferenceData,
    player_a: str,
    player_b: str,
) -> float:
    """Compute P(theta_A > theta_B | y) from MCMC draws.

    Args:
        trace: ArviZ InferenceData from run_sampling().
        player_a: player_id of the first player.
        player_b: player_id of the second player.

    Returns:
        Probability in [0, 1].
    """
    raise NotImplementedError("Implemented in STEP 9")
