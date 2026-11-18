"""Forecasting models.

* SeasonalNaive  - the benchmark every model must beat
* HoltWinters    - damped-trend additive ETS on the log scale, implemented from
                   scratch and vectorised across all series (no statsmodels)
* GlobalGBM      - one gradient-boosted model trained across every series, with
                   a Poisson objective for the mean and pinball-loss models for
                   the interval bounds
* conformal utilities - turn raw quantile bands into calibrated intervals
"""
from __future__ import annotations

from itertools import product

import numpy as np

from . import config as C
from .features import categorical_mask


# --------------------------------------------------------------------------
def seasonal_naive(Y: np.ndarray, h: int, season: int = C.SEASON) -> np.ndarray:
    """Repeat the last observed season. Y: (n_series, T) -> (n_series, h)."""
    last = Y[:, -season:]
    reps = int(np.ceil(h / season))
    return np.tile(last, reps)[:, :h]


# --------------------------------------------------------------------------
class HoltWinters:
    """Additive damped-trend Holt-Winters fitted on log1p(y).

    Smoothing parameters are selected per series by minimising one-step-ahead
    squared error over a grid. The recursion is run once per grid point for all
    series simultaneously, so fitting hundreds of series takes about a second.
    """

    GRID = list(product((0.05, 0.1, 0.2, 0.35, 0.5),      # alpha  (level)
                        (0.0, 0.02, 0.1),                 # beta   (trend)
                        (0.02, 0.1, 0.25),                # gamma  (seasonal)
                        (0.90, 0.98)))                    # phi    (damping)

    def __init__(self, season: int = C.SEASON, burn_in: int = 28):
        self.m, self.burn_in = season, burn_in

    def _run(self, Z, a, b, g, phi):
        n, T = Z.shape
        m = self.m
        level = Z[:, : 2 * m].mean(axis=1)
        trend = np.zeros(n)
        seas = Z[:, : 4 * m].reshape(n, 4, m).mean(axis=1) - level[:, None]
        sse = np.zeros(n)
        resid = np.empty((n, T))
        for t in range(T):
            k = t % m
            pred = level + phi * trend + seas[:, k]
            e = Z[:, t] - pred
            resid[:, t] = e
            if t >= self.burn_in:
                sse += e * e
            new_level = a * (Z[:, t] - seas[:, k]) + (1 - a) * (level + phi * trend)
            trend = b * (new_level - level) + (1 - b) * phi * trend
            seas[:, k] = g * (Z[:, t] - new_level) + (1 - g) * seas[:, k]
            level = new_level
        return sse, level, trend, seas, resid

    def fit(self, Y: np.ndarray) -> "HoltWinters":
        Z = np.log1p(np.asarray(Y, dtype=float))
        n, T = Z.shape
        best = np.full(n, np.inf)
        self.level, self.trend = np.zeros(n), np.zeros(n)
        self.seas, self.phi = np.zeros((n, self.m)), np.zeros(n)
        self.params = np.zeros((n, 4))
        self.resid = np.zeros((n, T))
        for a, b, g, phi in self.GRID:
            sse, level, trend, seas, resid = self._run(Z, a, b, g, phi)
            win = sse < best
            best[win] = sse[win]
            self.level[win], self.trend[win], self.seas[win] = level[win], trend[win], seas[win]
            self.phi[win] = phi
            self.params[win] = (a, b, g, phi)
            self.resid[win] = resid[win]
        self.T = T
        self.sigma = np.sqrt(best / max(T - self.burn_in, 1))
        return self

    def predict(self, h: int) -> np.ndarray:
        steps = np.arange(1, h + 1)
        damp = np.cumsum(self.phi[:, None] ** steps[None, :], axis=1)
        idx = (self.T + steps - 1) % self.m
        z = self.level[:, None] + damp * self.trend[:, None] + self.seas[:, idx]
        return np.clip(np.expm1(z), 0, None)


# --------------------------------------------------------------------------
class GlobalGBM:
    """Cross-series gradient boosting: Poisson mean + quantile bounds."""

    def __init__(self, quantiles=(C.QUANTILES[0], C.QUANTILES[-1]), seed: int = C.SEED, max_iter: int = 300):
        # imported here so the web tier, which never trains, does not need scikit-learn
        from sklearn.ensemble import HistGradientBoostingRegressor

        common = dict(max_iter=max_iter, learning_rate=0.06, max_leaf_nodes=48, min_samples_leaf=40,
                      l2_regularization=1.0, categorical_features=categorical_mask(), random_state=seed)
        self.mean = HistGradientBoostingRegressor(loss="poisson", **common)
        self.q = {q: HistGradientBoostingRegressor(loss="quantile", quantile=q, **common) for q in quantiles}

    def fit(self, X, y):
        self.mean.fit(X, y)
        for m in self.q.values():
            m.fit(X, y)
        return self

    def predict(self, X):
        """Returns (mean, lower, upper) with the bounds forced to bracket the mean."""
        mu = self.mean.predict(X)
        lo, hi = (np.clip(m.predict(X), 0, None) for m in self.q.values())
        return mu, np.minimum(lo, mu), np.maximum(hi, mu)


# --------------------------------------------------------------------------
def conformal_scores(y, lo, hi, scale):
    """CQR non-conformity score, normalised by a Poisson-like scale."""
    return np.maximum(lo - y, y - hi) / scale


def conformal_quantile(scores: np.ndarray, coverage: float = C.COVERAGE) -> float:
    n = len(scores)
    level = min(1.0, np.ceil((n + 1) * coverage) / n)
    return float(np.quantile(scores, level))


def inverse_error_weights(mae: np.ndarray, power: float = 2.0) -> np.ndarray:
    """mae: (n_series, n_models) -> row-normalised weights favouring low error."""
    w = 1.0 / np.power(mae + 1e-6, power)
    return w / w.sum(axis=1, keepdims=True)
