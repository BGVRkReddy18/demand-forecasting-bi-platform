"""Synthetic retail demand generator with known ground truth.

Real point-of-sale data is rarely shareable, so the platform ships with a
simulator. The simulator is deliberately *structural*: demand is produced by an
explicit causal model (trend x weekly x yearly seasonality x price elasticity x
promotion lift x festival effects x autocorrelated noise, observed through a
negative-binomial count process). Because the true elasticities, promo lifts and
injected anomalies are known, every analytics module can be validated against
ground truth instead of merely being eyeballed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C


def holiday_frame(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Calendar features that are known in advance for any date."""
    out = pd.DataFrame(index=dates)
    all_h = sorted(pd.Timestamp(d) for ds in C.HOLIDAYS.values() for d in ds)
    major = sorted(pd.Timestamp(d) for d in C.HOLIDAYS[C.MAJOR_HOLIDAY])
    names = {pd.Timestamp(d): n for n, ds in C.HOLIDAYS.items() for d in ds}

    def signed_gap(targets, cap):
        t = np.array([x.value for x in targets], dtype="int64") // 86_400_000_000_000
        d = (dates.values.astype("datetime64[D]").astype("int64"))[:, None] - t[None, :]
        nearest = d[np.arange(len(dates)), np.abs(d).argmin(axis=1)]
        return np.clip(nearest, -cap, cap)

    out["is_holiday"] = dates.isin(all_h).astype(int)
    out["holiday_name"] = [names.get(d, "") for d in dates]
    out["days_from_holiday"] = signed_gap(all_h, 15)      # negative = before
    out["days_from_major"] = signed_gap(major, 30)
    return out


def _diwali_shape(days_from_major: np.ndarray) -> np.ndarray:
    """Festival demand curve: a 10-day build-up, a peak, then a short hangover."""
    d = days_from_major.astype(float)
    build = np.where((d >= -12) & (d <= 0), np.exp(-((d + 1.5) / 4.5) ** 2), 0.0)
    hang = np.where((d > 0) & (d <= 6), -0.25 * np.exp(-(d - 1) / 2.5), 0.0)
    return build + hang


def generate(seed: int = C.SEED) -> dict:
    """Return dict(sales, future, products, stores, truth).

    sales  : observed daily history, one row per store x sku x day
    future : known-in-advance covariates (price, promo, calendar) for the horizon
    truth  : generator parameters used later to validate the analytics
    """
    rng = np.random.default_rng(seed)
    hist_dates = pd.date_range(C.START, C.END, freq="D")
    dates = pd.date_range(C.START, periods=len(hist_dates) + C.HORIZON, freq="D")
    T = len(dates)
    cal = holiday_frame(dates)
    doy = dates.dayofyear.values
    dow = dates.dayofweek.values
    years = np.arange(T) / 365.25

    # ---- product master -------------------------------------------------
    prods = []
    for cat, p in C.CATEGORIES.items():
        for i in range(p["n"]):
            lo, hi = p["demand"]
            plo, phi = p["price"]
            base_demand = float(np.exp(rng.uniform(np.log(lo), np.log(hi))))
            base_price = float(np.exp(rng.uniform(np.log(plo), np.log(phi))))
            prods.append(dict(
                sku_id=f"{cat[:3].upper()}-{i + 1:02d}",
                category=cat,
                base_demand=base_demand,
                base_price=round(base_price, -1) if base_price > 200 else round(base_price),
                margin=p["margin"] + rng.uniform(-0.04, 0.04),
                lead_time=int(rng.integers(p["lead"][0], p["lead"][1] + 1)),
                life_trend=float(rng.choice([-0.10, 0.0, 0.0, 0.05, 0.15])),
            ))
    products = pd.DataFrame(prods)
    stores = pd.DataFrame(C.STORES, columns=["store_id", "city", "region", "size", "growth"])

    frames, anomalies = [], []
    for _, s in stores.iterrows():
        store_week_noise = rng.normal(0, 0.03, T // 7 + 2)
        for _, p in products.iterrows():
            cp = C.CATEGORIES[p.category]

            # price path: yearly list-price increases + small weekly experiments
            list_price = p.base_price * (1 + 0.05 * np.floor(years))
            jitter = rng.choice([-0.04, -0.02, 0, 0, 0, 0.02, 0.04], T // 7 + 2)
            list_price = list_price * (1 + np.repeat(jitter, 7)[:T])

            # promotion calendar: ~8 windows a year, more likely pre-festival
            promo = np.zeros(T, dtype=int)
            discount = np.zeros(T)
            weight = 1 + 3 * ((cal.days_from_major.values > -14) & (cal.days_from_major.values <= 0))
            n_promos = int(rng.poisson(8 * T / 365.25))
            starts = rng.choice(T, size=n_promos, replace=False, p=weight / weight.sum())
            for st in starts:
                ln = int(rng.integers(4, 11))
                promo[st:st + ln] = 1
                discount[st:st + ln] = rng.choice([0.10, 0.15, 0.20, 0.25, 0.30])
            price = np.round(list_price * (1 - discount), 2)

            # structural demand model (log-linear)
            log_mu = (
                np.log(p.base_demand * s["size"])
                + (s.growth + p.life_trend) * years
                + cp["weekend"] * np.isin(dow, [5, 6])
                + 0.06 * (dow == 4)
                + cp["yearly"] * np.cos(2 * np.pi * (doy - cp["peak_doy"]) / 365.25)
                + 0.3 * cp["yearly"] * np.cos(4 * np.pi * (doy - cp["peak_doy"]) / 365.25)
                + cp["elasticity"] * np.log(price / p.base_price)
                + cp["promo_lift"] * promo
                + cp["diwali"] * _diwali_shape(cal.days_from_major.values)
                + 0.12 * ((cal.days_from_holiday.values >= -1) & (cal.days_from_holiday.values <= 0))
                + 0.05 * (dates.day.values <= 3)                 # payday effect
                + np.repeat(store_week_noise, 7)[:T]
            )
            ar = np.zeros(T)
            eps = rng.normal(0, 0.10, T)
            for t in range(1, T):
                ar[t] = 0.6 * ar[t - 1] + eps[t]
            mu = np.exp(log_mu + ar)
            r = 20.0                                             # NB dispersion
            units = rng.negative_binomial(r, r / (r + mu)).astype(float)

            # inject anomalies into observed history only
            flag = np.zeros(T, dtype=int)
            H = len(hist_dates)
            for _ in range(int(rng.poisson(3))):
                t0 = int(rng.integers(60, H - 5))
                if rng.random() < 0.5:                           # stock-out
                    ln = int(rng.integers(2, 6))
                    units[t0:t0 + ln] = 0
                    kind = "stockout"
                else:                                            # demand spike
                    ln = int(rng.integers(1, 3))
                    units[t0:t0 + ln] = np.round(units[t0:t0 + ln] * rng.uniform(2.5, 4.0) + 3)
                    kind = "spike"
                flag[t0:t0 + ln] = 1
                anomalies.append(dict(store_id=s.store_id, sku_id=p.sku_id,
                                      date=dates[t0], length=ln, kind=kind))

            frames.append(pd.DataFrame(dict(
                date=dates, store_id=s.store_id, sku_id=p.sku_id, category=p.category,
                units=units, price=price, list_price=np.round(list_price, 2),
                promo=promo, discount=discount, anomaly_truth=flag,
            )))

    full = pd.concat(frames, ignore_index=True)
    full["unit_cost"] = full["sku_id"].map(
        (products.set_index("sku_id").base_price * (1 - products.set_index("sku_id").margin)).round(2))
    full["series_id"] = full["store_id"] + "|" + full["sku_id"]
    full = full.merge(cal.drop(columns="holiday_name").rename_axis("date").reset_index(), on="date")
    full = full.sort_values(["series_id", "date"]).reset_index(drop=True)

    is_future = full["date"] > pd.Timestamp(C.END)
    sales = full[~is_future].reset_index(drop=True)
    future = full[is_future].drop(columns=["units", "anomaly_truth"]).reset_index(drop=True)
    sales["revenue"] = sales["units"] * sales["price"]

    # inventory snapshot at the end of history
    recent = sales[sales.date > pd.Timestamp(C.END) - pd.Timedelta(days=28)].groupby("series_id").units.mean()
    cover = np.exp(rng.normal(np.log(26), 0.65, len(recent)))
    on_hand = pd.Series(np.round(recent.values * cover), index=recent.index, name="on_hand")

    truth = dict(
        elasticity={k: v["elasticity"] for k, v in C.CATEGORIES.items()},
        promo_lift={k: v["promo_lift"] for k, v in C.CATEGORIES.items()},
        anomalies=pd.DataFrame(anomalies),
    )
    return dict(sales=sales, future=future, products=products, stores=stores,
                on_hand=on_hand, truth=truth, calendar=cal)
