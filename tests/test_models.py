import numpy as np
import pytest

from forecastiq import evaluation as E
from forecastiq.models import (HoltWinters, conformal_quantile, conformal_scores,
                               inverse_error_weights, seasonal_naive)


def seasonal_series(n=4, T=280, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(T)
    base = 50 + 0.05 * t + 15 * np.sin(2 * np.pi * t / 7)
    return np.clip(base[None, :] * rng.uniform(0.5, 2, (n, 1)) + rng.normal(0, 2, (n, T)), 0, None)


def test_seasonal_naive_repeats_last_week():
    Y = np.arange(28, dtype=float)[None, :]
    f = seasonal_naive(Y, 10)
    assert f.shape == (1, 10)
    assert np.allclose(f[0, :7], Y[0, -7:]) and np.allclose(f[0, 7:], Y[0, -7:-4])


def test_holt_winters_beats_naive_on_trending_seasonal_data():
    Y = seasonal_series()
    train, test = Y[:, :-28], Y[:, -28:]
    hw = HoltWinters().fit(train)
    f = hw.predict(28)
    assert f.shape == test.shape and (f >= 0).all()
    assert E.wape(test, f) < 0.08
    assert E.mae(test, f) <= E.mae(test, seasonal_naive(train, 28)) * 1.05


def test_holt_winters_selects_parameters_per_series():
    Y = seasonal_series(n=6)
    Y[0] = np.random.default_rng(1).poisson(3, Y.shape[1])        # a pure-noise series
    hw = HoltWinters().fit(Y)
    assert hw.params.shape == (6, 4)
    assert set(map(tuple, hw.params)) <= set(HoltWinters.GRID)


def test_metrics_on_known_values():
    y, f = np.array([10.0, 20, 30]), np.array([12.0, 18, 30])
    assert E.wape(y, f) == pytest.approx(4 / 60)
    assert E.mae(y, f) == pytest.approx(4 / 3)
    assert E.bias(y, f) == pytest.approx(0.0)
    assert E.pinball(y, y, 0.9) == 0.0
    assert E.pinball(np.array([10.0]), np.array([0.0]), 0.9) == pytest.approx(9.0)


def test_conformal_correction_restores_coverage():
    rng = np.random.default_rng(0)
    y = rng.normal(100, 10, 4000)
    lo, hi = np.full(4000, 95.0), np.full(4000, 105.0)            # far too narrow
    scale = np.ones(4000)
    q = conformal_quantile(conformal_scores(y[:2000], lo[:2000], hi[:2000], scale[:2000]), 0.8)
    covered = ((y[2000:] >= lo[2000:] - q) & (y[2000:] <= hi[2000:] + q)).mean()
    assert 0.77 <= covered <= 0.83


def test_inverse_error_weights():
    w = inverse_error_weights(np.array([[1.0, 2.0, 4.0]]))
    assert w.sum() == pytest.approx(1.0) and w[0, 0] > w[0, 1] > w[0, 2]
