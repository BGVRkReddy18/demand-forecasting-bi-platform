"""Leakage-safe feature engineering for the global gradient-boosting model.

The model is *direct, non-recursive*: every demand-derived feature is lagged by
at least the forecast horizon, so one model can score all 28 future days in a
single pass and no forecast is ever fed back in as an input. Price, promotion
and calendar features are known in advance and are used unlagged.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C

H = C.HORIZON
LAGS = (H, H + 7, H + 14, H + 21, H + 28, 364)
CATEGORICAL = ["store_code", "sku_code", "cat_code", "dow"]
FEATURES = (
    [f"lag_{l}" for l in LAGS]
    + ["roll_mean_7", "roll_mean_28", "roll_mean_56", "roll_std_28", "same_dow_mean", "trend_ratio", "zero_share_28"]
    + ["price", "rel_price", "discount", "promo", "promo_lead_7"]
    + ["dow", "dom", "month", "doy", "is_weekend", "is_month_start"]
    + ["is_holiday", "days_from_holiday", "days_from_major"]
    + ["store_code", "sku_code", "cat_code"]
)


def build_features(panel: pd.DataFrame) -> pd.DataFrame:
    """panel: history + future rows (units = NaN for the future), any order."""
    df = panel.sort_values(["series_id", "date"]).reset_index(drop=True).copy()
    g = df.groupby("series_id", sort=False)["units"]

    for l in LAGS:
        df[f"lag_{l}"] = g.shift(l)

    base = g.shift(H)                                   # newest information allowed
    sid = df["series_id"]

    def roll(s, w, fn):
        return getattr(s.groupby(sid, sort=False).rolling(w, min_periods=max(3, w // 2)), fn)().reset_index(level=0, drop=True)

    df["roll_mean_7"] = roll(base, 7, "mean")
    df["roll_mean_28"] = roll(base, 28, "mean")
    df["roll_mean_56"] = roll(base, 56, "mean")
    df["roll_std_28"] = roll(base, 28, "std")
    df["same_dow_mean"] = df[[f"lag_{l}" for l in LAGS[:4]]].mean(axis=1)
    df["trend_ratio"] = df["roll_mean_28"] / (df["roll_mean_56"] + 1e-6)
    df["zero_share_28"] = roll((base == 0).astype(float).where(base.notna()), 28, "mean")

    ref_price = roll(df.groupby("series_id", sort=False)["list_price"].shift(1), 56, "mean")
    df["rel_price"] = df["price"] / ref_price
    # promotions starting within the next week pull demand forward / delay purchases
    df["promo_lead_7"] = (
        df.iloc[::-1].groupby("series_id", sort=False)["promo"].rolling(7, min_periods=1).sum()
        .reset_index(level=0, drop=True).sort_index()
    )

    d = df["date"].dt
    df["dow"] = d.dayofweek
    df["dom"] = d.day
    df["month"] = d.month
    df["doy"] = d.dayofyear
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["is_month_start"] = (df["dom"] <= 3).astype(int)

    for col, code in (("store_id", "store_code"), ("sku_id", "sku_code"), ("category", "cat_code")):
        df[code] = pd.Categorical(df[col], categories=sorted(df[col].unique())).codes
    return df


def design_matrix(df: pd.DataFrame) -> np.ndarray:
    return df[FEATURES].to_numpy(dtype=float)


def categorical_mask() -> list[bool]:
    return [f in CATEGORICAL for f in FEATURES]
