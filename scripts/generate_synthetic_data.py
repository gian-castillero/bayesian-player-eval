"""Generate synthetic Wyscout-style per-player CSV files for pipeline testing.

Simulates a Panama league season spanning 2025-2026.
Run once: conda run -n player-eval python scripts/generate_synthetic_data.py
Output:   data/raw/players/{player_id}_{player_name}.csv  (one file per player)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from config import DATA_RAW_DIR, SEASON_YEARS

RNG = np.random.default_rng(42)
OUTPUT_DIR = DATA_RAW_DIR / "players"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── League and teams ───────────────────────────────────────────────────────────
COMPETITION = "Liga Panameña de Fútbol"

TEAMS = {
    "T01": "Tauro FC",
    "T02": "Club Atlético Independiente",
    "T03": "San Francisco FC",
    "T04": "Club Deportivo Plaza Amador",
}

# ── Wyscout position names (full strings, as exported) ────────────────────────
# wrangle.py will map these to FW / MF / DF
POSITION_MAP = {
    "FW": ["Centre forward", "Left winger", "Right winger", "Second striker"],
    "MF": ["Central midfielder", "Defensive midfielder", "Attacking midfielder"],
    "DF": ["Centre back", "Left back", "Right back"],
}

# ── Per-position stat distributions (mean, std) ───────────────────────────────
# Tuned so per-90 values land in realistic ranges
STAT_PROFILES: dict[str, dict[str, tuple[float, float]]] = {
    "FW": {
        "xG":               (0.28, 0.18),
        "Goals":            (0.15, 0.20),
        "Assists":          (0.05, 0.08),
        "Key passes":       (0.6,  0.5),
        "Progressive runs": (1.8,  1.0),
        "Duels won":        (2.5,  1.5),
        "Duels":            (5.0,  2.0),
        "Aerial duels won": (0.8,  0.7),
        "Aerial duels":     (1.8,  1.0),
    },
    "MF": {
        "xG":               (0.08, 0.07),
        "Goals":            (0.04, 0.06),
        "Assists":          (0.08, 0.08),
        "Key passes":       (1.2,  0.7),
        "Progressive runs": (2.5,  1.2),
        "Duels won":        (3.5,  1.8),
        "Duels":            (7.0,  2.5),
        "Aerial duels won": (0.5,  0.5),
        "Aerial duels":     (1.0,  0.8),
    },
    "DF": {
        "xG":               (0.03, 0.04),
        "Goals":            (0.02, 0.03),
        "Assists":          (0.03, 0.04),
        "Key passes":       (0.4,  0.4),
        "Progressive runs": (1.2,  0.8),
        "Duels won":        (5.0,  2.0),
        "Duels":            (9.0,  2.5),
        "Aerial duels won": (1.8,  1.0),
        "Aerial duels":     (3.0,  1.2),
    },
}

# ── Match schedule ─────────────────────────────────────────────────────────────
def _make_schedule() -> list[dict]:
    """Generate a 22-match round-robin schedule across 2025-2026."""
    team_ids = list(TEAMS.keys())
    matches = []
    match_id = 1
    # roughly one matchday per fortnight, spanning Mar 2025 – Feb 2026
    start = pd.Timestamp("2025-03-01")
    for round_num in range(22):
        date = start + pd.Timedelta(weeks=round_num * 2)
        if date.year not in SEASON_YEARS:
            continue
        for i, home in enumerate(team_ids):
            away = team_ids[(i + round_num + 1) % len(team_ids)]
            if home != away:
                matches.append({
                    "match_id": f"M{match_id:04d}",
                    "date":     date.strftime("%Y-%m-%d"),
                    "home":     home,
                    "away":     away,
                })
                match_id += 1
    return matches


# ── Player roster ──────────────────────────────────────────────────────────────
def _make_roster() -> list[dict]:
    """Create 15 outfield players per team with assigned positions."""
    first_names = [
        "Carlos", "Luis", "Miguel", "Andrés", "José", "Diego", "Alejandro",
        "Sergio", "Raúl", "Javier", "Pedro", "Fernando", "Marcos", "Iván", "Eduardo",
    ]
    last_names = [
        "González", "Rodríguez", "Martínez", "García", "López", "Pérez",
        "Sánchez", "Morales", "Jiménez", "Herrera", "Torres", "Vargas",
        "Castro", "Ramos", "Mendoza",
    ]
    slots = (
        [("FW", p) for p in POSITION_MAP["FW"]] * 2 +
        [("MF", p) for p in POSITION_MAP["MF"]] * 2 +
        [("DF", p) for p in POSITION_MAP["DF"]] * 2
    )[:15]

    roster = []
    player_counter = 1
    for team_id in TEAMS:
        for i, (pos_group, wyscout_pos) in enumerate(slots):
            pid = f"P{player_counter:04d}"
            name = f"{first_names[i]} {last_names[i]}"
            # give each player a latent quality offset so rankings are non-trivial
            quality = float(RNG.normal(0, 0.3))
            roster.append({
                "player_id":    pid,
                "player_name":  name,
                "team_id":      team_id,
                "pos_group":    pos_group,
                "wyscout_pos":  wyscout_pos,
                "quality":      quality,
            })
            player_counter += 1
    return roster


# ── Stat generation ────────────────────────────────────────────────────────────
def _make_match_row(
    player: dict,
    match: dict,
    team_id: str,
    team_quality: float,
) -> dict | None:
    """Return one match row for a player, or None if they didn't play."""
    # 15% chance of not appearing (rotation / injury)
    if RNG.random() < 0.15:
        return None

    minutes = int(RNG.choice([45, 60, 75, 90, 90, 90], p=[0.05, 0.10, 0.15, 0.35, 0.35, 0.00][:6]))
    minutes = max(30, min(90, minutes))  # clamp to [30, 90]

    scale = minutes / 90
    profile = STAT_PROFILES[player["pos_group"]]
    signal = player["quality"] + team_quality

    row: dict = {
        "Date":        match["date"],
        "Competition": COMPETITION,
        "Team":        TEAMS[team_id],
        "Opponent":    TEAMS[match["away"] if team_id == match["home"] else match["home"]],
        "Position":    player["wyscout_pos"],
        "Minutes played": minutes,
    }
    for stat, (mu, sigma) in profile.items():
        raw = float(RNG.normal(mu + signal * 0.15, sigma)) * scale
        if stat in ("Goals", "Assists", "Key passes", "Progressive runs",
                    "Duels won", "Duels", "Aerial duels won", "Aerial duels"):
            row[stat] = max(0, round(raw))
        else:
            row[stat] = max(0.0, round(raw, 3))

    # enforce logical constraints
    row["Duels won"]        = min(row["Duels won"], row["Duels"])
    row["Aerial duels won"] = min(row["Aerial duels won"], row["Aerial duels"])
    return row


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    schedule = _make_schedule()
    roster   = _make_roster()

    # random team quality offsets
    team_quality = {tid: float(RNG.normal(0, 0.2)) for tid in TEAMS}

    files_written = 0
    for player in roster:
        rows = []
        for match in schedule:
            if player["team_id"] not in (match["home"], match["away"]):
                continue
            row = _make_match_row(player, match, player["team_id"], team_quality[player["team_id"]])
            if row is not None:
                rows.append(row)

        if not rows:
            continue

        df = pd.DataFrame(rows)
        fname = f"{player['player_id']}_{player['player_name'].replace(' ', '_')}.csv"
        df.to_csv(OUTPUT_DIR / fname, index=False)
        files_written += 1

    print(f"Written {files_written} player files to {OUTPUT_DIR}")
    print(f"Total match rows: {sum(len(pd.read_csv(OUTPUT_DIR / f)) for f in os.listdir(OUTPUT_DIR) if f.endswith('.csv'))}")
    print(f"Sample file: {list(OUTPUT_DIR.iterdir())[0].name}")


if __name__ == "__main__":
    main()
