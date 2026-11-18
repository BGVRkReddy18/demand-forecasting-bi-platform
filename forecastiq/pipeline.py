"""End-to-end training pipeline:  python -m forecastiq.pipeline

generate data -> features -> rolling-origin backtest -> final forecast ->
analytics -> JSON artifacts consumed by the web app. The web tier never trains
a model, which keeps it fast and small enough for a free hosting instance.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

from . import analytics as A
from . import config as C
from . import evaluation as E
from .data import generate
from .features import FEATURES, build_features, design_matrix
from .models import (GlobalGBM, HoltWinters, conformal_quantile, conformal_scores,
                     inverse_error_weights, seasonal_naive)

BASE_MODELS = ["snaive", "ets", "gbm"]
MODELS = BASE_MODELS + ["ensemble"]
LABELS = {"snaive": "Seasonal naive", "ets": "Holt-Winters (ETS)", "gbm": "Global gradient boosting",
          "ensemble": "Weighted ensemble"}
ETS_WINDOW = 365
MIN_TRAIN_DAY = 92


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.1f}s] {msg}", flush=True)


def _wide(df: pd.DataFrame, col: str = "units") -> pd.DataFrame:
    return df.pivot(index="series_id", columns="date", values=col).sort_index()


def predict_window(feats: pd.DataFrame, cutoff: pd.Timestamp, max_iter: int = 300):
    """Train on everything up to `cutoff`, predict the next HORIZON days."""
    first = feats.date.min() + pd.Timedelta(days=MIN_TRAIN_DAY)
    train = feats[(feats.date <= cutoff) & (feats.date >= first)]
    test = feats[(feats.date > cutoff) & (feats.date <= cutoff + pd.Timedelta(days=C.HORIZON))]
    test = test.sort_values(["series_id", "date"])

    hist = _wide(feats[feats.date <= cutoff])
    Y = hist.to_numpy()
    gbm = GlobalGBM(max_iter=max_iter).fit(design_matrix(train), train.units.to_numpy())
    mu, lo, hi = gbm.predict(design_matrix(test))
    ets = HoltWinters().fit(Y[:, -ETS_WINDOW:])

    out = test[["series_id", "store_id", "sku_id", "category", "date", "units", "price", "unit_cost", "promo"]].copy()
    out = out.rename(columns={"units": "actual"})
    out["snaive"] = seasonal_naive(Y, C.HORIZON).ravel()
    out["ets"] = ets.predict(C.HORIZON).ravel()
    out["gbm"], out["raw_lo"], out["raw_hi"] = mu, lo, hi
    out["step"] = (out.date - cutoff).dt.days
    return out, gbm, test, ets


def finalise(out: pd.DataFrame, weights: pd.DataFrame, q: float | None, champion: str) -> pd.DataFrame:
    """Add the ensemble, promote the champion and attach calibrated intervals."""
    w = weights.reindex(out.series_id).to_numpy()
    out["ensemble"] = (out[BASE_MODELS].to_numpy() * w).sum(axis=1)
    out["champion"] = out[champion]
    shift = out.champion - out.gbm                       # centre the quantile band on the champion
    out["raw_lo"] = np.clip(out.raw_lo + shift, 0, None)
    out["raw_hi"] = out.raw_hi + shift
    out["scale"] = np.sqrt(out.champion + 1.0)
    if q is not None:
        out["lo"] = np.clip(out.raw_lo - q * out["scale"], 0, None)
        out["hi"] = out.raw_hi + q * out["scale"]
    return out


def weights_from(history: list[pd.DataFrame], series: pd.Index) -> pd.DataFrame:
    if not history:
        return pd.DataFrame(1 / len(BASE_MODELS), index=series, columns=BASE_MODELS)
    h = pd.concat(history)
    err = pd.concat({m: (h.actual - h[m]).abs().groupby(h.series_id).mean() for m in BASE_MODELS}, axis=1)
    return pd.DataFrame(inverse_error_weights(err.reindex(series).to_numpy()), index=series, columns=BASE_MODELS)


def pick_champion(history: list[pd.DataFrame]) -> str:
    """Champion/challenger: promote whichever model has the lowest pooled WAPE so far."""
    if not history:
        return "gbm"
    h = pd.concat(history)
    return min(MODELS, key=lambda m: E.wape(h.actual, h[m]))


def backtest(feats: pd.DataFrame, end: pd.Timestamp):
    """Rolling-origin evaluation. Ensemble weights, the champion choice and the
    conformal correction used on fold k are estimated only from folds < k, so
    reported numbers for folds 1..N-1 are genuinely out of sample."""
    series = pd.Index(sorted(feats.series_id.unique()))
    folds, scores, last = [], [], None
    for k in range(C.N_FOLDS):
        cutoff = end - pd.Timedelta(days=C.HORIZON * (C.N_FOLDS - k))
        out, gbm, test, _ = predict_window(feats, cutoff)
        q = conformal_quantile(np.concatenate(scores)) if scores else None
        out = finalise(out, weights_from(folds, series), q, pick_champion(folds))
        out["fold"] = k
        scores.append(conformal_scores(out.actual, out.raw_lo, out.raw_hi, out["scale"]).to_numpy())
        folds.append(out)
        last = (gbm, test)
        log(f"fold {k}: cutoff {cutoff.date()}  WAPE gbm={E.wape(out.actual, out.gbm):.3f} "
            f"ets={E.wape(out.actual, out.ets):.3f} snaive={E.wape(out.actual, out.snaive):.3f} "
            f"ens={E.wape(out.actual, out.ensemble):.3f}")
    return pd.concat(folds, ignore_index=True), np.concatenate(scores), weights_from(folds, series), last, pick_champion(folds)


# ------------------------------------------------------------------ report
def performance_report(bt: pd.DataFrame, sales: pd.DataFrame, stores: pd.DataFrame, weights, importance, ets, champion) -> dict:
    rep = bt[bt.fold >= 1].copy()
    first_cut = rep.date.min()
    scale = pd.Series(E.naive_scale(_wide(sales[sales.date < first_cut]).to_numpy()),
                      index=sorted(sales.series_id.unique()))
    rep["scale"] = rep.series_id.map(scale).clip(lower=0.5)
    rep = rep.merge(stores[["store_id", "region"]], on="store_id")

    def table(group):
        rows = []
        for key, g in rep.groupby(group):
            for r in E.summarise(g, MODELS, "scale"):
                rows.append(dict(key=str(key), **r))
        return rows

    levels = []
    for name, keys in (("SKU x store x day", ["series_id", "date"]), ("SKU x day", ["sku_id", "date"]),
                       ("Category x day", ["category", "date"]), ("Store x day", ["store_id", "date"]),
                       ("Total x day", ["date"]), ("SKU x store x 4 weeks", ["series_id", "fold"])):
        agg = rep.groupby(keys)[["actual"] + MODELS].sum()
        levels.append(dict(level=name, n=int(len(agg)), **{m: E.wape(agg.actual, agg[m]) for m in MODELS}))

    rep["week"] = (rep.step - 1) // 7 + 1
    inside = (rep.actual >= rep.lo) & (rep.actual <= rep.hi)
    raw_inside = (rep.actual >= rep.raw_lo) & (rep.actual <= rep.raw_hi)
    best = rep.assign(**{m: (rep.actual - rep[m]).abs() for m in BASE_MODELS}).groupby("series_id")[BASE_MODELS].mean().idxmin(axis=1)

    return dict(
        labels=LABELS, champion=champion,
        test_window=[str(rep.date.min().date()), str(rep.date.max().date())],
        n_forecasts=int(len(rep)),
        leaderboard=E.summarise(rep, MODELS, "scale"),
        by_category=table("category"), by_fold=table("fold"), by_week=table("week"),
        levels=levels,
        intervals=dict(
            target=C.COVERAGE,
            raw_coverage=float(raw_inside.mean()), coverage=float(inside.mean()),
            raw_width=float((rep.raw_hi - rep.raw_lo).mean()), width=float((rep.hi - rep.lo).mean()),
            by_category=[dict(key=k, coverage=float(v)) for k, v in inside.groupby(rep.category).mean().items()],
            by_fold=[dict(key=int(k), coverage=float(v)) for k, v in inside.groupby(rep.fold).mean().items()],
            pinball_lo=E.pinball(rep.actual, rep.lo, C.QUANTILES[0]), pinball_hi=E.pinball(rep.actual, rep.hi, C.QUANTILES[-1]),
        ),
        ensemble_weights=dict(mean={m: float(weights[m].mean()) for m in BASE_MODELS},
                              best_single={m: int((best == m).sum()) for m in BASE_MODELS}),
        importance=importance,
        ets_params=dict(alpha=float(np.median(ets.params[:, 0])), beta=float(np.median(ets.params[:, 1])),
                        gamma=float(np.median(ets.params[:, 2])), phi=float(np.median(ets.params[:, 3]))),
    )


def feature_importance(gbm: GlobalGBM, test: pd.DataFrame) -> list[dict]:
    r = permutation_importance(gbm.mean, design_matrix(test), test.units.to_numpy(), n_repeats=3,
                               random_state=C.SEED, scoring="neg_mean_absolute_error")
    order = np.argsort(-r.importances_mean)
    return [dict(feature=FEATURES[i], importance=float(r.importances_mean[i])) for i in order[:15]]


# ----------------------------------------------------------- forecast nodes
def node_payloads(sales, fc, bt, stores, hist_days: int = 182) -> dict:
    """Series for the forecast explorer at every level of the hierarchy.
    Bottom-up aggregation keeps all levels coherent. Aggregate intervals come
    from the empirical distribution of that node's own backtest errors."""
    end = sales.date.max()
    region = stores.set_index("store_id").region
    city = stores.set_index("store_id").city
    h = sales[sales.date > end - pd.Timedelta(days=hist_days)]
    frames = dict(hist=h, fc=fc, bt=bt)
    for f in frames.values():
        f["region"] = f.store_id.map(region)
        f["total"] = "All stores"
    nodes = {}
    d2s = lambda idx: [str(x.date()) for x in idx]
    r0 = lambda a: [round(float(x), 1) for x in a]

    for level, key in (("total", "total"), ("region", "region"), ("category", "category"),
                       ("store", "store_id"), ("series", "series_id")):
        gh = h.groupby([key, "date"]).units.sum().unstack(0)
        gp = h.assign(v=h.units * h.price).groupby([key, "date"]).v.sum().unstack(0) / gh.replace(0, np.nan)
        cols = ["forecast", "lo", "hi", "snaive", "ets", "gbm"]
        gf = {c: fc.groupby([key, "date"])[c].sum().unstack(0) for c in cols}
        gpromo = fc.groupby([key, "date"]).promo.mean().unstack(0)
        gb = {c: bt.groupby([key, "date"])[c].sum().unstack(0) for c in ["actual", "champion", "lo", "hi"]}
        for k in gh.columns:
            f = gf["forecast"][k].to_numpy()
            if level == "series":
                lo, hi = gf["lo"][k].to_numpy(), gf["hi"][k].to_numpy()
                blo, bhi = gb["lo"][k], gb["hi"][k]
            else:
                rel = (gb["actual"][k] - gb["champion"][k]) / gb["champion"][k]
                qlo, qhi = np.quantile(rel, [C.QUANTILES[0], C.QUANTILES[-1]])
                lo, hi = f * (1 + qlo), f * (1 + qhi)
                blo, bhi = gb["champion"][k] * (1 + qlo), gb["champion"][k] * (1 + qhi)
            label = k
            if level == "store":
                label = f"{city[k]} ({k})"
            elif level == "series":
                st, sku = k.split("|")
                label = f"{sku} - {city[st]}"
            nodes[f"{level}:{k}"] = dict(
                level=level, key=k, label=label,
                hist_dates=d2s(gh.index), hist=r0(gh[k]),
                fc_dates=d2s(gf["forecast"].index), forecast=r0(f), lo=r0(np.clip(lo, 0, None)), hi=r0(hi),
                models={m: r0(gf[m][k]) for m in BASE_MODELS},
                promo_share=[round(float(x), 2) for x in gpromo[k]],
                bt_dates=d2s(gb["actual"].index), bt_actual=r0(gb["actual"][k]), bt_pred=r0(gb["champion"][k]),
                bt_lo=r0(np.clip(blo, 0, None)), bt_hi=r0(bhi),
                bt_wape=round(E.wape(gb["actual"][k], gb["champion"][k]), 4),
                hist_total=float(gh[k].iloc[-C.HORIZON:].sum()), fc_total=float(f.sum()),
            )
    return nodes


def _dump(name: str, obj) -> None:
    def default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return None if np.isnan(o) else float(o)
        if isinstance(o, (pd.Timestamp,)):
            return str(o.date())
        raise TypeError(type(o))

    def clean(o):
        if isinstance(o, float):
            return None if (np.isnan(o) or np.isinf(o)) else o
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        return o

    C.ARTIFACT_DIR.mkdir(exist_ok=True)
    (C.ARTIFACT_DIR / f"{name}.json").write_text(json.dumps(clean(json.loads(json.dumps(obj, default=default))),
                                                            separators=(",", ":")))


# --------------------------------------------------------------------- run
def run() -> dict:
    data = generate()
    sales, future, products, stores = data["sales"], data["future"], data["products"], data["stores"]
    end = sales.date.max()
    log(f"data: {len(sales):,} rows, {sales.series_id.nunique()} series, {sales.date.min().date()}..{end.date()}")

    feats = build_features(pd.concat([sales, future], ignore_index=True))
    log(f"features: {len(FEATURES)} columns")

    bt, scores, weights, (gbm_last, test_last), champion = backtest(feats, end)
    log(f"champion: {champion}")
    importance = feature_importance(gbm_last, test_last)

    fc, _, _, ets = predict_window(feats, end)
    fc = finalise(fc, weights, conformal_quantile(scores), champion).rename(columns={"champion": "forecast"}).drop(columns="actual")
    log("final forecast done")

    perf = performance_report(bt, sales, stores, weights, importance, ets, champion)
    seg = A.abc_xyz(sales)
    inv = A.inventory_policy(fc, bt, seg.set_index("series_id"), products, data["on_hand"])
    pricing = A.price_response(sales, data["truth"])
    det = A.detect_anomalies(sales)
    score = A.anomaly_scorecard(det, data["truth"]["anomalies"])
    log(f"analytics done; anomaly precision={score['precision']:.2f} recall={score['recall']:.2f}")

    k = A.kpis(sales, fc)
    k["forecast_wape"] = next(r["wape"] for r in perf["leaderboard"] if r["model"] == champion)
    k["naive_wape"] = next(r["wape"] for r in perf["leaderboard"] if r["model"] == "snaive")
    k["at_risk_skus"] = int(inv.status.isin(["Critical", "Reorder"]).sum())
    k["revenue_at_risk"] = float(inv.revenue_at_risk.sum())
    k["excess_capital"] = float(inv.excess_capital.sum())

    def festivals(lo, hi):
        return [n for n, ds in C.HOLIDAYS.items() for d in pd.to_datetime(ds) if lo < d <= hi]

    w, yr = pd.Timedelta(days=C.HORIZON), pd.Timedelta(days=364)
    k["holidays_cur"], k["holidays_ly"] = festivals(end - w, end), festivals(end - w - yr, end - yr)

    city = stores.set_index("store_id").city
    recent = det[det.flag & (det.date > end - pd.Timedelta(days=180))].sort_values("date", ascending=False)
    anomalies = dict(
        scorecard=score, threshold=4.5,
        recent=[dict(date=str(r.date.date()), series_id=r.series_id, sku_id=r.sku_id, city=city[r.store_id],
                     category=r.category, units=float(r.units), expected=round(float(r.expected), 1),
                     z=round(float(r.z), 1), kind=r.kind, revenue_impact=round(float((r.units - r.expected) * r.price), 0))
                for r in recent.itertuples()],
        by_month=[dict(month=str(m), spike=int((g.kind == "spike").sum()), drop=int((g.kind == "drop").sum()))
                  for m, g in det[det.flag].groupby(det[det.flag].date.dt.to_period("M"))],
    )

    seg_out = seg.merge(inv[["series_id", "category", "store_id", "sku_id"]], on="series_id")
    matrix = seg.groupby(["abc", "xyz"]).agg(n=("series_id", "size"), revenue=("revenue_12m", "sum")).reset_index()

    scenario_base = (fc.groupby(["series_id", "store_id", "sku_id", "category"])
                     .apply(lambda g: pd.Series(dict(units=g.forecast.sum(), price=(g.forecast * g.price).sum() / g.forecast.sum(),
                                                     unit_cost=g.unit_cost.iloc[0])), include_groups=False).reset_index())

    meta = dict(
        version="1.0.0", generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        history=[str(sales.date.min().date()), str(end.date())], horizon=C.HORIZON, coverage=C.COVERAGE,
        forecast_window=[str(fc.date.min().date()), str(fc.date.max().date())],
        n_rows=int(len(sales)), n_series=int(sales.series_id.nunique()), n_features=len(FEATURES),
        currency=C.CURRENCY,
        stores=stores[["store_id", "city", "region"]].to_dict("records"),
        categories=list(C.CATEGORIES), regions=sorted(stores.region.unique()),
        products=products[["sku_id", "category", "base_price", "lead_time"]].to_dict("records"),
        holidays_in_horizon=[dict(date=str(d.date()), name=n) for n, ds in C.HOLIDAYS.items() for d in pd.to_datetime(ds)
                             if fc.date.min() <= d <= fc.date.max()],
        assumptions=dict(holding_rate=C.HOLDING_RATE, order_cost=C.ORDER_COST, service_level=C.SERVICE_LEVEL,
                         overstock_days=C.OVERSTOCK_DAYS),
    )

    _dump("meta", meta)
    _dump("overview", dict(kpis=k, **A.breakdowns(sales, fc, stores)))
    _dump("performance", perf)
    _dump("forecast", node_payloads(sales.copy(), fc.copy(), bt.copy(), stores))
    _dump("inventory", dict(rows=inv.to_dict("records"),
                            matrix=matrix.to_dict("records"),
                            segments=seg_out[["series_id", "abc", "xyz", "cv", "revenue_12m"]].round(3).to_dict("records")))
    _dump("pricing", dict(response=pricing, scenario_base=scenario_base.round(3).to_dict("records")))
    _dump("anomalies", anomalies)
    log(f"artifacts written to {C.ARTIFACT_DIR}")
    return dict(perf=perf, kpis=k, pricing=pricing, anomalies=score, inventory=inv, bt=bt, fc=fc)


if __name__ == "__main__":
    out = run()
    print("\nLeaderboard (folds 1-3, out of sample):")
    print(pd.DataFrame(out["perf"]["leaderboard"]).round(4).to_string(index=False))
    print("\nInterval coverage:", {k: round(v, 3) for k, v in out["perf"]["intervals"].items() if isinstance(v, float)})
    print("\nElasticity recovery:")
    print(pd.DataFrame(out["pricing"])[["category", "elasticity", "elasticity_true", "promo_lift", "promo_lift_true"]].round(3).to_string(index=False))
