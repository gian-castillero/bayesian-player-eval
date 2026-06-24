"""NUTS sampling and trace persistence."""
from __future__ import annotations

import arviz as az
import pymc as pm


def run_sampling(model: pm.Model, trace_path: str) -> az.InferenceData:
    """Run NUTS sampler and save trace to disk.

    Args:
        model: Compiled PyMC model from build_model().
        trace_path: Destination path for the ArviZ .nc file.

    Returns:
        ArviZ InferenceData object with posterior draws.
    """
    raise NotImplementedError("Implemented in STEP 8")
