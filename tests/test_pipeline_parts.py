import numpy as np
import pandas as pd

from forecastiq import analytics as A
from forecastiq import config as C
from forecastiq.features import FEATURES, build_features


def test_generator_is_deterministic_and_complete(data):
    s = data["sales"]
    n_series = len(C.STORES) * sum(c["n"] for c in C.CATEGORIES.values())
    assert s.series_id.nunique() == n_series
    assert len(s) == n_series * s.date.nunique()
    assert (s.units >= 0).all() and s.units.notna().all()
    assert len(data["future"]) == n_series * C.HORIZON
    from forecastiq.data import generate
    assert generate()["sales"].units.sum() == s.units.sum()


def test_features_do_not_leak_the_forecast_window(data):
    """Changing demand inside the last HORIZON-1 days must not change any
    feature of the future rows: that is what makes the backtest honest."""
    ids = sorted(data["sales"].series_id.unique())[:6]
    sales = data["sales"][data["sales"].series_id.isin(ids)]
    future = data["future"][data["future"].series_id.isin(ids)]
    a = build_features(pd.concat([sales, future], ignore_index=True))

    tampered = sales.copy()
    recent = tampered.date > tampered.date.max() - pd.Timedelta(days=C.HORIZON - 1)
    tampered.loc[recent, "units"] = 9999.0
    b = build_features(pd.concat([tampered, future], ignore_index=True))

    # day 1 of the horizon may only see demand that is at least HORIZON days old
    day1 = a.date == a.date.max() - pd.Timedelta(days=C.HORIZON - 1)
    fa, fb = a.loc[day1, FEATURES].to_numpy(float), b.loc[day1, FEATURES].to_numpy(float)
    assert np.allclose(fa, fb, equal_nan=True)


def test_elasticity_recovers_ground_truth(data):
    for r in A.price_response(data["sales"], data["truth"]):
        assert abs(r["elasticity"] - r["elasticity_true"]) < 0.15, r["category"]
        assert abs(r["promo_lift"] - r["promo_lift_true"]) < 0.05, r["category"]
        assert r["elasticity_lo"] < r["elasticity"] < r["elasticity_hi"]


def test_anomaly_detector_finds_most_injected_events(data):
    det = A.detect_anomalies(data["sales"])
    score = A.anomaly_scorecard(det, data["truth"]["anomalies"])
    assert score["recall"] > 0.6 and score["precision"] > 0.5
    assert det.flag.mean() < 0.02                                  # not crying wolf


def test_abc_classes_follow_revenue(data):
    seg = A.abc_xyz(data["sales"])
    rev = seg.groupby("abc").revenue_12m
    assert rev.min()["A"] >= rev.max()["B"] >= rev.min()["B"] >= rev.max()["C"]
    assert 0.75 <= seg[seg.abc == "A"].revenue_12m.sum() / seg.revenue_12m.sum() <= 0.82


def test_scenario_direction_matches_elasticity():
    base = pd.DataFrame(dict(category=["x"], units=[100.0], price=[10.0], unit_cost=[6.0]))
    elastic = {"x": dict(elasticity=-2.0, promo_lift=0.2)}
    cut = A.simulate(base, -0.10, False, elastic)
    assert cut["units"] > 100 and cut["revenue"] > cut["base_revenue"]
    assert A.simulate(base, 0.0, False, elastic)["revenue"] == cut["base_revenue"]
    assert A.simulate(base, 0.0, True, elastic)["units"] == 120.0
    inelastic = {"x": dict(elasticity=-0.5, promo_lift=0.0)}
    assert A.simulate(base, -0.10, False, inelastic)["revenue"] < 1000
