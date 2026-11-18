"""On-demand forecasting for a user-uploaded series (no pre-training needed)."""
from __future__ import annotations

import io

import numpy as np
import pandas as pd
from scipy.stats import norm

from . import evaluation as E
from .models import HoltWinters, seasonal_naive

FREQS = {"D": (7, "daily"), "W": (52, "weekly"), "M": (12, "monthly")}
MAX_ROWS = 5000


class UploadError(ValueError):
    pass


def parse_csv(raw: bytes) -> pd.Series:
    try:
        df = pd.read_csv(io.BytesIO(raw), nrows=MAX_ROWS + 1)
    except Exception as exc:  # noqa: BLE001
        raise UploadError("Could not read the file as CSV.") from exc
    if df.shape[1] < 2:
        raise UploadError("Expected two columns: a date column and a numeric value column.")
    if len(df) > MAX_ROWS:
        raise UploadError(f"Please upload at most {MAX_ROWS} rows.")
    cols = {c.lower().strip(): c for c in df.columns}
    dcol = next((cols[c] for c in ("date", "ds", "day", "week", "month", "timestamp") if c in cols), df.columns[0])
    vcol = next((cols[c] for c in ("value", "y", "units", "sales", "demand", "quantity", "qty") if c in cols),
                next((c for c in df.columns if c != dcol), None))
    dates = pd.to_datetime(df[dcol], errors="coerce")
    vals = pd.to_numeric(df[vcol], errors="coerce")
    ok = dates.notna() & vals.notna()
    if ok.sum() < 10:
        raise UploadError("Could not find enough rows with a valid date and a numeric value.")
    s = pd.Series(vals[ok].to_numpy(float), index=pd.DatetimeIndex(dates[ok])).groupby(level=0).sum().sort_index()
    if (s < 0).any():
        raise UploadError("Values must be non-negative (this model is built for demand / sales counts).")
    return s


def _regularise(s: pd.Series):
    gap = float(np.median(np.diff(s.index.values).astype("timedelta64[D]").astype(float)))
    code = "D" if gap <= 2 else "W" if gap <= 10 else "M"
    if code == "D":
        s = s.asfreq("D").interpolate(limit_direction="both")
    elif code == "W":
        s = s.resample("W").sum()
    else:
        s = s.resample("MS").sum()
    return s, code


def forecast_series(s: pd.Series, horizon: int | None = None) -> dict:
    s, code = _regularise(s)
    m, name = FREQS[code]
    n = len(s)
    if code == "W" and n < 5 * m + 8:
        m = 13                                            # fall back to quarterly seasonality
    if n < 5 * m:
        raise UploadError(f"Need at least {5 * m} {name} observations to fit a seasonal model; got {n}.")
    h = horizon or {"D": 28, "W": 13, "M": 6}[code]
    h = int(min(h, n // 5))
    y = s.to_numpy(float)[None, :]

    # hold-out evaluation on the last h points
    tr, te = y[:, :-h], y[0, -h:]
    hw = HoltWinters(season=m, burn_in=2 * m).fit(tr)
    cand = {"ets": hw.predict(h)[0], "snaive": seasonal_naive(tr, h, m)[0]}
    metrics = [dict(model=k, wape=E.wape(te, v), mae=E.mae(te, v), rmse=E.rmse(te, v)) for k, v in cand.items()]
    scale = float(np.abs(tr[0, m:] - tr[0, :-m]).mean()) or 1.0
    for r in metrics:
        r["mase"] = r["mae"] / scale
    best = min(metrics, key=lambda r: r["mae"])["model"]

    # refit on everything; log-scale interval that widens with the horizon
    hw = HoltWinters(season=m, burn_in=2 * m).fit(y)
    point = hw.predict(h)[0] if best == "ets" else seasonal_naive(y, h, m)[0]
    alpha, sigma = float(hw.params[0, 0]), float(hw.sigma[0])
    z = norm.ppf(0.9)
    spread = z * sigma * np.sqrt(1 + np.arange(h) * alpha ** 2)
    lo, hi = np.expm1(np.log1p(point) - spread), np.expm1(np.log1p(point) + spread)
    future = pd.date_range(s.index[-1], periods=h + 1, freq={"D": "D", "W": "W", "M": "MS"}[code])[1:]

    r1 = lambda a: [round(float(v), 2) for v in a]
    keep = min(n, 8 * m if code != "D" else 180)
    return dict(
        frequency=name, season=m, n_obs=n, horizon=h, best=best, metrics=metrics,
        params=dict(alpha=alpha, beta=float(hw.params[0, 1]), gamma=float(hw.params[0, 2]), phi=float(hw.params[0, 3])),
        hist_dates=[str(d.date()) for d in s.index[-keep:]], hist=r1(s.to_numpy()[-keep:]),
        holdout_dates=[str(d.date()) for d in s.index[-h:]], holdout_pred=r1(cand[best]),
        fc_dates=[str(d.date()) for d in future], forecast=r1(point), lo=r1(np.clip(lo, 0, None)), hi=r1(hi),
    )
