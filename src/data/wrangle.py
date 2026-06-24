"""Raw Wyscout CSV directory → tidy long-format DataFrame."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import MIN_MINUTES, POSITIONS, SEASON_YEARS

# ── Column rename: Wyscout export names → internal names ──────────────────────
_COLUMN_MAP: dict[str, str] = {
    "Date":              "date",
    "Competition":       "league_name",
    "Team":              "team_name",
    "Opponent":          "opponent_name",
    "Position":          "position_raw",
    "Minutes played":    "minutes",
    "xG":                "xg",
    "Key passes":        "key_passes",
    "Progressive runs":  "progressive_carries",
    "Duels won":         "duels_won",
    "Goals":             "goals",
    "Assists":           "assists",
    "Aerial duels won":  "aerial_duels_won",
    "Aerial duels":      "aerial_duels",
    "Duels":             "duels",
}

# ── Position standardisation: Wyscout full names → FW / MF / DF ──────────────
_POSITION_GROUPS: dict[str, str] = {
    "Centre forward":       "FW",
    "Left winger":          "FW",
    "Right winger":         "FW",
    "Second striker":       "FW",
    "Central midfielder":   "MF",
    "Defensive midfielder": "MF",
    "Attacking midfielder": "MF",
    "Left midfielder":      "MF",
    "Right midfielder":     "MF",
    "Centre back":          "DF",
    "Left back":            "DF",
    "Right back":           "DF",
    "Left wing back":       "DF",
    "Right wing back":      "DF",
    "Goalkeeper":           "GK",
}

# ── Metrics that get a per-90 derived column ───────────────────────────────────
_METRICS_TO_NORMALISE: list[str] = ["xg", "key_passes", "progressive_carries", "duels_won"]


def wrangle(raw_dir: str | Path) -> pd.DataFrame:
    """Read all per-player CSVs, clean, normalise, and return a tidy DataFrame.

    Args:
        raw_dir: Directory containing one CSV per player (Wyscout export format).

    Returns:
        Long-format DataFrame with one row per (player, match). Columns include
        match_id, player_id, player_name, team_name, league_name, position,
        date, minutes, xg, key_passes, progressive_carries, duels_won, and
        per-90 derived columns: xg_p90, key_passes_p90, prog_carries_p90,
        duels_won_p90.

    Raises:
        ValueError: If no CSV files are found in raw_dir.
    """
    raw_dir = Path(raw_dir)
    csv_files = sorted(raw_dir.glob("*.csv"))

    if not csv_files:
        raise ValueError(f"No CSV files found in {raw_dir}")

    # ── Read and concatenate all per-player files ──────────────────────────────
    frames: list[pd.DataFrame] = []
    for fpath in csv_files:
        # Filename format: "P0001_Carlos_González.csv"
        stem = fpath.stem                          # "P0001_Carlos_González"
        parts = stem.split("_", 1)                 # ["P0001", "Carlos_González"]
        player_id   = parts[0]
        player_name = parts[1].replace("_", " ") if len(parts) > 1 else player_id

        df = pd.read_csv(fpath)
        df["player_id"]   = player_id
        df["player_name"] = player_name
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)

    # ── Rename columns to internal names ──────────────────────────────────────
    df = df.rename(columns=_COLUMN_MAP)

    # ── Parse date and filter to SEASON_YEARS ─────────────────────────────────
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year.isin(SEASON_YEARS)].copy()

    # ── Add a synthetic match_id (date + both teams) ──────────────────────────
    df["match_id"] = (
        df["date"].dt.strftime("%Y%m%d") + "_" +
        df["team_name"].str.replace(" ", "") + "_vs_" +
        df["opponent_name"].str.replace(" ", "")
    )

    # ── YOUR TURN — write the three blocks below ───────────────────────────────
    # Block 1: drop rows where minutes < MIN_MINUTES
    # Block 2: per-90 normalisation for each metric in _METRICS_TO_NORMALISE
    # Block 3: position standardisation using _POSITION_GROUPS; drop GK rows

    # ── Final column selection and ordering ───────────────────────────────────
    output_cols = [
        "match_id", "player_id", "player_name", "team_name", "league_name",
        "position", "date", "minutes",
        "xg", "key_passes", "progressive_carries", "duels_won",
        "xg_p90", "key_passes_p90", "prog_carries_p90", "duels_won_p90",
    ]
    return df[output_cols].reset_index(drop=True)


if __name__ == "__main__":
    from rich import print as rprint

    from config import DATA_RAW_DIR

    df = wrangle(DATA_RAW_DIR / "players")
    rprint(df.head(5))
    rprint(f"\nShape:      {df.shape}")
    rprint(f"Players:    {df['player_id'].nunique()}")
    rprint(f"Positions:  {df['position'].value_counts().to_dict()}")
    rprint(f"Date range: {df['date'].min().date()} → {df['date'].max().date()}")
