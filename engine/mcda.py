"""Multi-criteria decision analysis with uncertain weights and uncertain metrics.

P(best) = share of Monte Carlo draws (Dirichlet-sampled priority weights x metric draws from
the p10/p50/p90 intervals) in which a strategy has the highest weighted score.
This is decision support: it describes outcomes under stated priorities, it does not
recommend.

Architectural decision note:
P(best) is computed live in the web application (web/src/lib/ranking.ts) rather than
being statically precomputed in engine.export. Statically baking P(best) into export would
require fixing arbitrary priority weights in advance, removing the farmer's decision
agency. The client performs 2,000 Monte Carlo draws in <10ms for instant 60fps slider
response. This module is the canonical Python specification and batch implementation,
kept in strict parity with ranking.ts.
"""

from __future__ import annotations

from typing import Any

import numpy as np

PRIORITIES = ("water", "income", "soil", "erosion", "labour")
METRIC_KEYS = ("water_use_mm", "income_usd_ha", "soil_index", "erosion_t_ha", "labour_index")
METRIC_FOR_PRIORITY = {
    "water": "water_use_mm",
    "income": "income_usd_ha",
    "soil": "soil_index",
    "erosion": "erosion_t_ha",
    "labour": "labour_index",
}
LOWER_IS_BETTER = {"water_use_mm", "erosion_t_ha", "labour_index"}
Z90 = 1.2815515655446004  # standard-normal quantile at 0.9


def normalise_metrics(values: np.ndarray, lower_is_better: np.ndarray) -> np.ndarray:
    """Min-max normalise each metric column across strategies to [0, 1], 1 = best.

    ``values``: (..., n_strategies, n_metrics). ``lower_is_better``: bool (n_metrics,).
    Columns with zero range map to 0.5.
    """
    lo = values.min(axis=-2, keepdims=True)
    hi = values.max(axis=-2, keepdims=True)
    rng = hi - lo
    with np.errstate(invalid="ignore", divide="ignore"):
        x = np.where(rng > 0, (values - lo) / rng, 0.5)
    return np.where(lower_is_better, 1.0 - x, x)


def sample_dirichlet_weights(
    weights: np.ndarray, concentration: float, n: int, rng: np.random.Generator
) -> np.ndarray:
    """Draw ``n`` weight vectors ~ Dirichlet(concentration * w / sum(w)).

    Higher ``concentration`` = farmer is more certain of their slider settings.
    Zero weights get a tiny alpha so the distribution stays proper.
    """
    w = np.asarray(weights, dtype=float)
    if w.sum() <= 0:
        w = np.ones_like(w)
    alpha = np.maximum(concentration * w / w.sum(), 1e-3)
    return rng.dirichlet(alpha, size=n)


def sample_split_normal(p10: np.ndarray, p50: np.ndarray, p90: np.ndarray, n: int, rng):
    """Draw from a split-normal matching p10/p50/p90 (separate sigma below/above the median)."""
    z = rng.standard_normal((n, *np.shape(p50)))
    sig_lo = (p50 - p10) / Z90
    sig_hi = (p90 - p50) / Z90
    return p50 + np.where(z < 0, z * sig_lo, z * sig_hi)


def p_best(
    p10: np.ndarray,
    p50: np.ndarray,
    p90: np.ndarray,
    weights: np.ndarray,
    lower_is_better: np.ndarray,
    n: int = 4000,
    concentration: float = 20.0,
    seed: int = 0,
) -> np.ndarray:
    """Probability each strategy scores highest. Arrays are (n_strategies, n_metrics);
    ``weights`` is (n_metrics,). Returns (n_strategies,) summing to 1."""
    rng = np.random.default_rng(seed)
    draws = sample_split_normal(p10, p50, p90, n, rng)  # (n, S, M)
    w = sample_dirichlet_weights(weights, concentration, n, rng)  # (n, M)
    score = (normalise_metrics(draws, lower_is_better) * w[:, None, :]).sum(axis=-1)
    winners = score.argmax(axis=1)
    return np.bincount(winners, minlength=p50.shape[0]) / n


def rank_strategies(
    strategies: list[dict[str, Any]],
    priorities: dict[str, float | int] | None = None,
    n: int = 4000,
    concentration: float = 20.0,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Rank strategies mirroring web/src/lib/ranking.ts.

    Calculates medianScore (composite score at p50 with exact slider weights) and
    pBest (fraction of Monte Carlo draws where the strategy ranks #1 under Dirichlet
    weights and split-normal metric intervals).

    Returns a list of dicts with 'strategy', 'medianScore', and 'pBest',
    sorted by pBest descending, then medianScore descending.
    """
    if not strategies:
        return []

    priorities_dict = priorities or {p: 3.0 for p in PRIORITIES}
    weights = np.array([float(priorities_dict.get(p, 3.0)) for p in PRIORITIES], dtype=float)
    lower_is_better = np.array([m in LOWER_IS_BETTER for m in METRIC_KEYS], dtype=bool)

    n_strat = len(strategies)
    p10 = np.zeros((n_strat, len(METRIC_KEYS)), dtype=float)
    p50 = np.zeros((n_strat, len(METRIC_KEYS)), dtype=float)
    p90 = np.zeros((n_strat, len(METRIC_KEYS)), dtype=float)

    for i, s in enumerate(strategies):
        strat_obj = s.get("strategy", s)
        m_dict = strat_obj["metrics"]
        for j, m_key in enumerate(METRIC_KEYS):
            q = m_dict[m_key]
            p10[i, j] = q["p10"]
            p50[i, j] = q["p50"]
            p90[i, j] = q["p90"]

    # Exact weights normalized
    w_sum = weights.sum()
    w_norm = weights / w_sum if w_sum > 0 else np.ones_like(weights) / len(weights)

    # Median score at p50
    norm_p50 = normalise_metrics(p50, lower_is_better)
    median_scores = (norm_p50 * w_norm).sum(axis=-1)

    # p_best via Monte Carlo
    pb = p_best(
        p10,
        p50,
        p90,
        weights=weights,
        lower_is_better=lower_is_better,
        n=n,
        concentration=concentration,
        seed=seed,
    )

    ranked = [
        {
            "strategy": strategies[i].get("strategy", strategies[i]),
            "medianScore": float(median_scores[i]),
            "pBest": float(pb[i]),
        }
        for i in range(n_strat)
    ]
    ranked.sort(key=lambda r: (r["pBest"], r["medianScore"]), reverse=True)
    return ranked
