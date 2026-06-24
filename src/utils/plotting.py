"""Shared Plotly figure builders used across all Streamlit pages."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def ranking_chart(rankings: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of posterior means with 90% CI error bars.

    Args:
        rankings: Output of extract_rankings().

    Returns:
        Plotly Figure.
    """
    raise NotImplementedError("Implemented in STEP 11")


def posterior_density(draws: list[float], player_name: str) -> go.Figure:
    """KDE plot of posterior draws for a single player.

    Args:
        draws: 1-D list of theta posterior draws.
        player_name: Display label for the title.

    Returns:
        Plotly Figure.
    """
    raise NotImplementedError("Implemented in STEP 11")
