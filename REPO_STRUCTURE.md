# Repo structure — Bayesian Player Evaluation Model

```
bayesian-player-eval/
│
├── README.md                          # project overview, setup, demo GIF
├── requirements.txt                   # pinned dependencies
├── .gitignore                         # excludes data/raw, outputs/traces, .env
├── config.py                          # global constants (metrics, positions, paths)
│
├── .streamlit/
│   └── config.toml                    # theme, server port, wide layout
│
├── data/
│   ├── raw/                           # ← gitignored — Wyscout exports land here
│   │   └── .gitkeep
│   ├── processed/                     # ← gitignored — cleaned parquet files
│   │   └── .gitkeep
│   └── sample/                        # small anonymized sample (committed for demo)
│       └── plaza_sample.csv
│
├── src/                               # all importable Python source
│   ├── __init__.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── wrangle.py                 # raw Wyscout → tidy long-format DataFrame
│   │   └── validate.py                # schema checks, missing value assertions
│   │
│   ├── model/
│   │   ├── __init__.py
│   │   ├── build.py                   # build_model() — pure PyMC model definition
│   │   ├── fit.py                     # run_sampling() — NUTS + save trace to .nc
│   │   └── postprocess.py             # extract_rankings(), shrinkage_df(), prob_better()
│   │
│   └── utils/
│       ├── __init__.py
│       ├── metrics.py                 # per-90 normalization, minutes filters
│       └── plotting.py                # shared Plotly figure builders used by all pages
│
├── app/                               # Streamlit multi-page app
│   ├── Home.py                        # entry point — model overview + key numbers
│   └── pages/
│       ├── 1_Rankings.py              # Q: who are the best players per position?
│       ├── 2_Player_Deepdive.py       # Q: how has player X evolved this season?
│       ├── 3_Surprise_Players.py      # Q: who is outperforming their naive rank?
│       ├── 4_Team_Quality.py          # Q: how do team quality estimates compare?
│       └── 5_Uncertainty_Explorer.py  # Q: how does uncertainty shrink with more data?
│
├── notebooks/
│   ├── 01_EDA.ipynb                   # metric distributions by position, team, league
│   ├── 02_prior_predictive.ipynb      # prior predictive checks before fitting
│   └── 03_model_validation.ipynb      # R-hat, ESS, LOO, posterior predictive checks
│
├── outputs/
│   ├── traces/                        # ← gitignored — ArviZ .nc files
│   │   └── .gitkeep
│   └── rankings/                      # ← gitignored — exported CSV snapshots
│       └── .gitkeep
│
├── scripts/
│   └── run_pipeline.py                # CLI: python scripts/run_pipeline.py --season 2024
│
└── tests/
    ├── test_wrangle.py                # unit tests for data pipeline
    └── test_postprocess.py            # unit tests for ranking extraction
```

---

## File responsibilities

### `config.py`
Global constants so nothing is hardcoded across files:

```python
POSITIONS    = ["FW", "MF", "DF", "GK"]
METRICS      = ["xg_p90", "key_passes_p90", "prog_carries_p90"]
MIN_MINUTES  = 30          # drop match rows below this threshold
SAMPLE_DRAWS = 2000
TUNE_DRAWS   = 1000
TARGET_ACCEPT = 0.9
TRACE_PATH   = "outputs/traces/trace_{season}.nc"
RANKINGS_PATH = "outputs/rankings/rankings_{season}.csv"
```

---

### `src/data/wrangle.py`
Single function contract:

```python
def wrangle(raw_path: str) -> pd.DataFrame:
    """
    Input:  Wyscout match-level export (CSV or JSON)
    Output: long-format DataFrame with one row per (player, match)

    Columns: match_id | player_id | player_name | team_id | league_id |
             position | minutes | xg | key_passes | prog_carries | ...
             + per-90 derived columns: xg_p90, key_passes_p90, ...
    """
```

---

### `src/model/build.py`
Pure model definition — no sampling, no I/O:

```python
def build_model(df: pd.DataFrame, metric: str) -> tuple[pm.Model, dict]:
    """
    Returns (model, coords) ready for pm.sample().
    All index encoding happens here.
    """
```

---

### `src/model/fit.py`
Sampling and persistence:

```python
def run_sampling(model: pm.Model, trace_path: str) -> az.InferenceData:
    """
    Runs NUTS, saves trace to .nc, returns InferenceData.
    Checks for existing trace and loads if found (skips resampling).
    """
```

---

### `src/model/postprocess.py`
Everything the dashboard needs:

```python
def extract_rankings(trace: az.InferenceData, coords: dict) -> pd.DataFrame:
    """Posterior mean, 5th, 95th percentile per player. Sorted by theta_mean."""

def shrinkage_df(trace: az.InferenceData, df: pd.DataFrame) -> pd.DataFrame:
    """Per-player: naive per-90, posterior mean, shrinkage factor lambda_i."""

def prob_better(trace: az.InferenceData, player_a: str, player_b: str) -> float:
    """P(theta_A > theta_B | y) — computed from MCMC draws."""
```

---

### `app/Home.py`
- Loads the saved trace (does NOT re-run sampling)
- Displays model diagram + key stats (N players, N matches, metric)
- Links to each analysis page

---

### `scripts/run_pipeline.py`
End-to-end CLI runner:

```
python scripts/run_pipeline.py \
    --raw       data/raw/plaza_2024.csv \
    --season    2024 \
    --metric    xg_p90 \
    --force     # re-run sampling even if trace exists
```

---

## Key design decision: load, don't refit

The Streamlit app **never calls `pm.sample()`**. MCMC runs offline via the CLI script
and saves a trace to `outputs/traces/`. Every dashboard page loads the trace with:

```python
trace = az.from_netcdf("outputs/traces/trace_2024.nc")
```

This keeps the app fast (sub-second loads) and separates modeling from serving.
