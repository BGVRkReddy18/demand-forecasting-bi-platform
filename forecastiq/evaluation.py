"""Forecast accuracy metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd


def wape(y, f):
    y, f = np.asarray(y, float), np.asarray(f, float)
    d = np.abs(y).sum()
    return float(np.abs(y - f).sum() / d) if d > 0 else float("nan")


def mae(y, f):
    return float(np.mean(np.abs(np.asarray(y, float) - np.asarray(f, float))))


def rmse(y, f):
    return float(np.sqrt(np.mean((np.asarray(y, float) - np.asarray(f, float)) ** 2)))


def bias(y, f):
    """Positive = over-forecast, as a share of actual demand."""
    y, f = np.asarray(y, float), np.asarray(f, float)
    d = y.sum()
    return float((f - y).sum() / d) if d > 0 else float("nan")


def smape(y, f):
    y, f = np.asarray(y, float), np.asarray(f, float)
    den = np.abs(y) + np.abs(f)
    return float(np.mean(np.where(den == 0, 0.0, 2 * np.abs(y - f) / np.where(den == 0, 1, den))))


def pinball(y, q_pred, q):
    y, q_pred = np.asarray(y, float), np.asarray(q_pred, float)
    d = y - q_pred
    return float(np.mean(np.maximum(q * d, (q - 1) * d)))


def naive_scale(Y: np.ndarray, season: int = 7) -> np.ndarray:
    """In-sample seasonal-naive MAE per series: the denominator of MASE."""
    return np.abs(Y[:, season:] - Y[:, :-season]).mean(axis=1)


def summarise(df: pd.DataFrame, models: list[str], scale_col: str | None = None) -> list[dict]:
    """One row of metrics per model for a frame holding `actual` + model columns."""
    out = []
    for m in models:
        row = dict(model=m, wape=wape(df.actual, df[m]), mae=mae(df.actual, df[m]),
                   rmse=rmse(df.actual, df[m]), smape=smape(df.actual, df[m]), bias=bias(df.actual, df[m]))
        if scale_col:
            row["mase"] = float((np.abs(df.actual - df[m]) / df[scale_col]).mean())
        out.append(row)
    return out
