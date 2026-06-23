# Model specification — Bayesian Hierarchical Player Evaluation

---

## 1. Indices and sets

| Symbol | Meaning |
|---|---|
| $i \in \{1, \ldots, N_p\}$ | players |
| $j \in \{1, \ldots, N_m\}$ | match observations (rows in the data) |
| $t \in \{1, \ldots, N_T\}$ | teams |
| $l \in \{1, \ldots, N_L\}$ | leagues |
| $p \in \{\text{FW, MF, DF, GK}\}$ | positions |

---

## 2. Observed quantities

| Symbol | Meaning |
|---|---|
| $y_{ij}$ | per-90 metric for player $i$ in match $j$ (e.g. xG/90) |
| $m_{ij}$ | minutes played by player $i$ in match $j$ |
| $\text{pos}(i)$ | position of player $i$ — fixed, one of {FW, MF, DF, GK} |
| $t(i,j)$ | team of player $i$ in match $j$ — allows mid-season transfers |
| $\text{league}(t)$ | league that team $t$ belongs to |

---

## 3. Full model

### Level 0 — Global hyperpriors

$$
\mu_{\text{global}} \sim \mathcal{N}(0,\ 1)
$$

$$
\sigma_{\text{global}} \sim \text{HalfNormal}(1)
$$

These govern the overall scale of the metric across all leagues.
Adjust the scale parameter based on the EDA distribution of $y$.

---

### Level 1 — League

$$
\mu_l \sim \mathcal{N}\!\left(\mu_{\text{global}},\ \sigma_{\text{global}}\right), \quad l = 1, \ldots, N_L
$$

$$
\sigma_l \sim \text{HalfNormal}(0.5), \quad l = 1, \ldots, N_L
$$

$\mu_l$ is the average performance baseline in league $l$.
$\sigma_l$ controls how much teams within the league vary from that baseline.

---

### Level 2a — Team quality (nested within league)

$$
\alpha_t \sim \mathcal{N}\!\left(\mu_{\text{league}(t)},\ \sigma_{\text{league}(t)}\right), \quad t = 1, \ldots, N_T
$$

$\alpha_t$ is an additive quality offset for team $t$.
A positive $\alpha_t$ means players on that team accumulate the metric faster
than expected purely from their own ability — the team context inflates raw stats.
**Partialling out $\alpha_t$ is the primary mechanism for fair cross-team comparison.**

---

### Level 2b — Position (crossed with the team track, not nested)

$$
\mu_p \sim \mathcal{N}\!\left(\mu_{\text{global}},\ \sigma_{\text{global}}\right), \quad p \in \{\text{FW, MF, DF, GK}\}
$$

$$
\tau_p \sim \text{HalfNormal}(0.5), \quad p \in \{\text{FW, MF, DF, GK}\}
$$

$\mu_p$ is the expected quality of a player at position $p$.
$\tau_p$ is the standard deviation of true player quality within that position —
how spread out the talent distribution is among, say, all forwards.

> **Note:** The team and position tracks are _crossed_, not nested.
> A forward on Team A is simultaneously governed by $\alpha_{\text{Team A}}$ (team track)
> and $\mu_{\text{FW}}, \tau_{\text{FW}}$ (position track). Both tracks meet at the
> observation level.

---

### Level 3 — Player quality

$$
\theta_i \sim \mathcal{N}\!\left(\mu_{\text{pos}(i)},\ \tau_{\text{pos}(i)}\right), \quad i = 1, \ldots, N_p
$$

$\theta_i$ is the **latent true quality** of player $i$, measured in units of the metric per 90.
This is the primary quantity of interest for rankings.

---

### Level 4 — Observation model (per match row)

$$
\sigma_{\text{obs}} \sim \text{HalfNormal}(0.5)
$$

$$
\hat{\mu}_{ij} = \theta_i + \alpha_{t(i,j)}
$$

$$
\boxed{y_{ij} \sim \mathcal{N}\!\left(\hat{\mu}_{ij},\ \frac{\sigma_{\text{obs}}}{\sqrt{m_{ij} / 90}}\right)}
$$

The $\sqrt{m_{ij}/90}$ scaling is critical for per-match data.
A player who plays 90 minutes contributes a full-weight observation.
A player who plays 30 minutes contributes an observation with $\sqrt{3} \approx 1.73\times$
larger variance — properly reflecting that a 30-minute sample is noisier.

---

## 4. What the model implies (partial pooling)

For a player with $n_i$ match observations, the posterior mean of $\theta_i$
approximately satisfies:

$$
\hat{\theta}_i \approx \lambda_i \, \bar{y}_i^{\text{adj}} + (1 - \lambda_i)\, \mu_p
$$

where $\bar{y}_i^{\text{adj}} = \bar{y}_i - \hat{\alpha}_{t(i)}$ is the team-adjusted
per-90 average, and $\lambda_i$ is the **shrinkage weight**:

$$
\lambda_i = \frac{n_i \, \tau_p^2}{n_i \, \tau_p^2 + \sigma_{\text{obs}}^2}
$$

| Regime | Effect |
|---|---|
| $n_i \to \infty$ | $\lambda_i \to 1$ — player's own data dominates |
| $n_i \to 0$ | $\lambda_i \to 0$ — posterior collapses to position mean |
| $n_i$ moderate | weighted blend — sensible regularization |

This is why a 5-match player never "beats" a 30-match player purely on raw per-90s
in this model. The uncertainty is reflected in the posterior width, not silently ignored.

---

## 5. Joint posterior

We estimate:

$$
p\!\left(\boldsymbol{\theta}, \boldsymbol{\alpha}, \boldsymbol{\mu}_p, \boldsymbol{\tau}_p,
\boldsymbol{\mu}_l, \boldsymbol{\sigma}_l, \mu_{\text{global}}, \sigma_{\text{global}},
\sigma_{\text{obs}} \;\middle|\; \mathbf{y}\right)
$$

via the **NUTS sampler** (No-U-Turn Sampler). PyMC defaults to this.
Run 4 chains × 2000 draws + 1000 tuning steps.

---

## 6. Posterior quantities for the dashboard

Let $\theta_i^{(1)}, \ldots, \theta_i^{(S)}$ denote the $S = 8{,}000$ posterior
draws for player $i$ (4 chains × 2000 draws).

### 6.1 Point estimate

$$
\hat{\theta}_i = \frac{1}{S} \sum_{s=1}^{S} \theta_i^{(s)}
$$

### 6.2 Credible interval

$$
\text{CI}_{90}(\theta_i) = \left[Q_{0.05}\!\left(\boldsymbol{\theta}_i\right),\; Q_{0.95}\!\left(\boldsymbol{\theta}_i\right)\right]
$$

### 6.3 Ranking

Sort all players within a position by $\hat{\theta}_i$, descending.
Represent uncertainty by displaying the CI alongside — wide intervals
indicate data-sparse players who could be ranked higher or lower.

### 6.4 Probability that player A is better than player B

$$
P(\theta_A > \theta_B \mid \mathbf{y}) = \frac{1}{S} \sum_{s=1}^{S} \mathbf{1}\!\left[\theta_A^{(s)} > \theta_B^{(s)}\right]
$$

Compute directly from draws — no parametric assumption needed.
Useful for the dashboard: "We are 83% confident that Player A is better than Player B."

### 6.5 Surprise score (outperformance relative to naive rank)

$$
\text{surprise}_i = \text{rank}_{\text{naive}}(i) - \text{rank}_{\text{posterior}}(i)
$$

where naive rank is computed from raw per-90 average $\bar{y}_i$
and posterior rank from $\hat{\theta}_i$.
A large positive surprise score means the model values the player
significantly more than raw stats suggest — the primary recruitment signal.

---

## 7. Convergence diagnostics (required before trusting rankings)

| Diagnostic | Target | PyMC / ArviZ call |
|---|---|---|
| $\hat{R}$ (R-hat) | $< 1.01$ for all params | `az.summary(trace)` |
| $n_{\text{eff}}$ (bulk ESS) | $> 400$ per param | `az.summary(trace)` |
| $n_{\text{eff}}$ (tail ESS) | $> 400$ per param | `az.summary(trace)` |
| Divergences | $= 0$ after tuning | `trace.sample_stats.diverging.sum()` |
| Trace plots | visually well-mixed | `az.plot_trace(trace, var_names=["theta"])` |

If $\hat{R} > 1.01$: increase `tune` draws or raise `target_accept` toward 0.95.
If divergences persist: reparametrize $\theta_i$ using the non-centered form (see below).

---

## 8. Non-centered reparametrization (if sampling is slow)

The centered form $\theta_i \sim \mathcal{N}(\mu_p, \tau_p)$ can cause
funnel geometry in the posterior when $\tau_p$ is small — the sampler struggles
near the neck of the funnel. The fix is to reparametrize:

$$
\eta_i \sim \mathcal{N}(0, 1)
$$

$$
\theta_i = \mu_{\text{pos}(i)} + \tau_{\text{pos}(i)} \cdot \eta_i
$$

In PyMC:

```python
eta   = pm.Normal("eta", mu=0, sigma=1, dims="player")
theta = pm.Deterministic("theta", mu_pos[pos_idx] + tau_pos[pos_idx] * eta, dims="player")
```

Apply the same reparametrization to $\alpha_t$ if sampling is slow on the team level.

---

## 9. Prior predictive check (run before fitting)

Sample from the model *without* conditioning on data:

$$
\tilde{y}_{ij} \sim p(y_{ij})
$$

Check: do prior predictive samples span the plausible range of $y$?
For xG/90, you expect $\tilde{y} \in [0,\ 1.5]$ for most draws.
If the prior is too wide (e.g. generating $\tilde{y} = 5$) — tighten $\sigma_{\text{global}}$.

```python
with model:
    prior_pred = pm.sample_prior_predictive(500)

az.plot_ppc(prior_pred, group="prior", observed=False)
```

---

## 10. Posterior predictive check (run after fitting)

Sample from the fitted model:

$$
\tilde{y}_{ij}^* \sim p(y_{ij} \mid \hat{\boldsymbol{\theta}})
$$

Check that $\tilde{y}^*$ matches the empirical distribution of $y$:

```python
with model:
    post_pred = pm.sample_posterior_predictive(trace)

az.plot_ppc(post_pred)          # overlay observed vs predicted
az.plot_loo_pit(trace, y="y")   # uniform PIT = well-calibrated model
```

---

## Summary: what each parameter does

| Parameter | Type | What it captures |
|---|---|---|
| $\mu_{\text{global}}, \sigma_{\text{global}}$ | hyperprior | overall scale of the metric |
| $\mu_l, \sigma_l$ | league-level | average quality baseline per competition |
| $\alpha_t$ | team-level | additive team strength offset; confound to partial out |
| $\mu_p, \tau_p$ | position-level | expected quality and spread within each position |
| $\theta_i$ | player-level | **the quantity we care about** — true latent ability |
| $\sigma_{\text{obs}}$ | observation | residual match-to-match noise |
