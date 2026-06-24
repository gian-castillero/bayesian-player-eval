"""Global constants and path helpers for the player evaluation project.

Import from here in every module — never hardcode these values elsewhere.
"""
from __future__ import annotations

from pathlib import Path

# ── Root ───────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.resolve()

# ── Data ───────────────────────────────────────────────────────────────────────
DATA_RAW_DIR       = ROOT / "data" / "raw"
DATA_PROCESSED_DIR = ROOT / "data" / "processed"
DATA_SAMPLE_DIR    = ROOT / "data" / "sample"

# ── Outputs ────────────────────────────────────────────────────────────────────
TRACES_DIR   = ROOT / "outputs" / "traces"
RANKINGS_DIR = ROOT / "outputs" / "rankings"

# ── Domain constants ───────────────────────────────────────────────────────────
POSITIONS: list[str] = ["FW", "MF", "DF"]  # GK excluded — needs separate model with GK-specific metrics

# Calendar years that define the current season (Panama league spans two calendar years)
SEASON_YEARS: list[int] = [2025, 2026]

# Per-90 metrics modelled — each one triggers a separate model run / trace file
METRICS: list[str] = ["xg_p90", "key_passes_p90", "prog_carries_p90"]

# Minimum minutes in a single match observation to be included
# Below 30 min the sample is too noisy to carry useful signal (≈ ⅓ of a match)
MIN_MINUTES: int = 30

# ── Sampling parameters (Section 5 of MODEL_MATH.md) ─────────────────────────
SAMPLE_DRAWS:  int   = 2000   # posterior draws per chain
TUNE_DRAWS:    int   = 1000   # warm-up / adaptation draws
N_CHAINS:      int   = 4      # independent chains for R-hat diagnostics
TARGET_ACCEPT: float = 0.9    # NUTS step-size target; raise to 0.95 if divergences

# ── File path helpers ──────────────────────────────────────────────────────────

def trace_path(season: str | int, metric: str) -> Path:
    """Return the .nc file path for a given season and metric.

    Args:
        season: Season identifier, e.g. 2024.
        metric: Metric name, e.g. 'xg_p90'.

    Returns:
        Absolute Path to the ArviZ trace file.
    """
    return TRACES_DIR / f"trace_{season}_{metric}.nc"


def rankings_path(season: str | int, metric: str) -> Path:
    """Return the CSV path for exported rankings.

    Args:
        season: Season identifier.
        metric: Metric name.

    Returns:
        Absolute Path to the rankings CSV.
    """
    return RANKINGS_DIR / f"rankings_{season}_{metric}.csv"


def processed_path(season: str | int) -> Path:
    """Return the Parquet path for the wrangled DataFrame.

    Args:
        season: Season identifier.

    Returns:
        Absolute Path to the processed Parquet file.
    """
    return DATA_PROCESSED_DIR / f"wrangled_{season}.parquet"
