"""Business-intelligence layer: turns history + forecasts into decisions.

* KPI roll-ups and growth
* ABC-XYZ segmentation
* Inventory policy (safety stock, reorder point, EOQ) driven by forecast error
* Price elasticity and promotion lift via Poisson pseudo-maximum-likelihood
  with series fixed effects and cluster-robust standard errors
* Robust anomaly detection
* What-if scenario simulation
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm

from . import config as C


# ---------------------------------------------------------------- KPIs ----
def kpis(sales: pd.DataFrame, fc: pd.DataFrame) -> dict:
    end = sales.date.max()
    w = pd.Timedelta(days=C.HORIZON)
    cur = sales[sales.date > end - w]
    prev = sales[(sales.date > end - 2 * w) & (sales.date <= end - w)]
    ly = sales[(sales.date > end - w - pd.Timedelta(days=364)) & (sales.date <= end - pd.Timedelta(days=364))]

    def tot(d):
        return dict(revenue=float(d.revenue.sum()), units=float(d.units.sum()),
                    margin=float(((d.price - d.unit_cost) * d.units).sum()))

    c, p, l = tot(cur), tot(prev), tot(ly)
    f_rev = float((fc.forecast * fc.price).sum())
    f_margin = float((fc.forecast * (fc.price - fc.unit_cost)).sum())
    return dict(
        window_days=C.HORIZON,
        revenue=c["revenue"], revenue_prev=p["revenue"], revenue_ly=l["revenue"],
        units=c["units"], units_prev=p["units"], units_ly=l["units"],
        margin=c["margin"], margin_pct=c["margin"] / c["revenue"],
        margin_pct_prev=p["margin"] / p["revenue"],
        forecast_revenue=f_rev, forecast_units=float(fc.forecast.sum()),
        forecast_units_lo=None, forecast_units_hi=None,
        forecast_margin=f_margin,
    )


def breakdowns(sales: pd.DataFrame, fc: pd.DataFrame, stores: pd.DataFrame) -> dict:
    end = sales.date.max()
    w = pd.Timedelta(days=C.HORIZON)
    s = sales.merge(stores[["store_id", "city", "region"]], on="store_id")
    f = fc.merge(stores[["store_id", "city", "region"]], on="store_id").assign(frev=lambda d: d.forecast * d.price)

    month = s.assign(month=s.date.dt.to_period("M").astype(str))
    monthly = month.groupby(["month", "category"]).revenue.sum().unstack().round(0)

    def table(key):
        cur = s[s.date > end - w].groupby(key).revenue.sum()
        ly = s[(s.date > end - w - pd.Timedelta(days=364)) & (s.date <= end - pd.Timedelta(days=364))].groupby(key).revenue.sum()
        nxt = f.groupby(key).frev.sum()
        t = pd.DataFrame(dict(revenue=cur, yoy=cur / ly - 1, forecast=nxt, change=nxt / cur - 1)).reset_index()
        t = t.rename(columns={key: "name"}).sort_values("revenue", ascending=False)
        return t.round(4).to_dict("records")

    sku_cur = s[s.date > end - w].groupby("sku_id").units.sum()
    sku_fc = f.groupby("sku_id").forecast.sum()
    movers = pd.DataFrame(dict(units=sku_cur, forecast=sku_fc)).assign(change=lambda d: d.forecast / d.units - 1)
    movers = movers.reset_index().merge(s[["sku_id", "category"]].drop_duplicates(), on="sku_id")
    movers = movers.sort_values("change", ascending=False).round(3)

    return dict(
        monthly=dict(months=list(monthly.index), series={c: monthly[c].tolist() for c in monthly.columns}),
        by_category=table("category"), by_store=table("city"), by_region=table("region"),
        movers_up=movers.head(5).to_dict("records"), movers_down=movers.tail(5).iloc[::-1].to_dict("records"),
    )


# ------------------------------------------------------------- ABC-XYZ ----
def abc_xyz(sales: pd.DataFrame) -> pd.DataFrame:
    """ABC on trailing-year revenue (80/15/5), XYZ on weekly demand variability."""
    end = sales.date.max()
    yr = sales[sales.date > end - pd.Timedelta(days=364)]
    rev = yr.groupby("series_id").revenue.sum().sort_values(ascending=False)
    share = rev.cumsum() / rev.sum()
    abc = pd.Series(np.where(share <= 0.80, "A", np.where(share <= 0.95, "B", "C")), index=rev.index)

    half = sales[sales.date > end - pd.Timedelta(days=182)].copy()
    half["week"] = (end - half.date).dt.days // 7
    wk = half.groupby(["series_id", "week"]).units.sum().unstack()
    cv = wk.std(axis=1) / wk.mean(axis=1)
    xyz = pd.Series(np.where(cv <= 0.20, "X", np.where(cv <= 0.35, "Y", "Z")), index=cv.index)
    return pd.DataFrame(dict(revenue_12m=rev, abc=abc, cv=cv, xyz=xyz)).rename_axis("series_id").reset_index()


# ----------------------------------------------------------- inventory ----
def inventory_policy(fc: pd.DataFrame, backtest: pd.DataFrame, seg: pd.DataFrame,
                     products: pd.DataFrame, on_hand: pd.Series) -> pd.DataFrame:
    """Continuous-review (s, Q) policy.

    safety stock  = z(service level) * sigma_forecast_error * sqrt(lead time)
    reorder point = forecast demand over the lead time + safety stock
    order size    = economic order quantity
    The demand uncertainty term is the *out-of-sample* error of the model being
    used, measured in the rolling backtest - not the raw demand variance.
    """
    sigma = backtest.assign(e=lambda d: (d.actual - d.champion) ** 2).groupby("series_id").e.mean().pow(0.5)
    lead = products.set_index("sku_id").lead_time
    rows = []
    for sid, g in fc.sort_values("date").groupby("series_id"):
        store, sku = sid.split("|")
        f = g.forecast.to_numpy()
        L = int(lead[sku])
        s = seg.loc[sid]
        z = float(norm.ppf(C.SERVICE_LEVEL[s.abc]))
        daily = float(f.mean())
        price, cost = float(g.price.mean()), float(g.unit_cost.iloc[0])
        lt_demand = float(f[:L].sum())
        ss = z * float(sigma[sid]) * np.sqrt(L)
        rop = lt_demand + ss
        eoq = float(np.sqrt(2 * daily * 365 * C.ORDER_COST / (C.HOLDING_RATE * cost)))
        oh = float(on_hand[sid])
        cum = np.cumsum(f)
        hit = np.searchsorted(cum, oh, side="right")
        cover = float(hit) if hit < len(f) else float(len(f) + (oh - cum[-1]) / max(daily, 1e-6))
        if oh < lt_demand:
            status = "Critical"
        elif oh <= rop:
            status = "Reorder"
        elif cover > C.OVERSTOCK_DAYS:
            status = "Overstock"
        else:
            status = "Healthy"
        order = float(np.ceil(max(rop + eoq - oh, 0))) if status in ("Critical", "Reorder") else 0.0
        rows.append(dict(
            series_id=sid, store_id=store, sku_id=sku, category=g.category.iloc[0], abc=s.abc, xyz=s.xyz,
            on_hand=oh, daily_forecast=round(daily, 2), lead_time=L, service_level=C.SERVICE_LEVEL[s.abc],
            sigma=round(float(sigma[sid]), 2), safety_stock=round(ss, 1), reorder_point=round(rop, 1),
            eoq=round(eoq, 0), days_cover=round(cover, 1), status=status, order_qty=order,
            order_value=round(order * cost, 0),
            revenue_at_risk=round(max(lt_demand - oh, 0) * price, 0),
            excess_capital=round(max(oh - daily * C.OVERSTOCK_DAYS, 0) * cost, 0),
        ))
    return pd.DataFrame(rows)


# ------------------------------------------------- price elasticity -------
def _ppml(X: np.ndarray, y: np.ndarray, groups: np.ndarray, iters: int = 50, tol: float = 1e-8):
    """Poisson pseudo-ML by IRLS; returns coefficients and cluster-robust SEs."""
    beta = np.zeros(X.shape[1])
    beta[0] = np.log(y.mean() + 1e-9)
    for _ in range(iters):
        eta = np.clip(X @ beta, -30, 30)
        mu = np.exp(eta)
        z = eta + (y - mu) / mu
        XtW = X.T * mu
        new = np.linalg.solve(XtW @ X + 1e-8 * np.eye(X.shape[1]), XtW @ z)
        done = np.max(np.abs(new - beta)) < tol
        beta = new
        if done:
            break
    mu = np.exp(np.clip(X @ beta, -30, 30))
    bread = np.linalg.inv((X.T * mu) @ X + 1e-8 * np.eye(X.shape[1]))
    score = X * (y - mu)[:, None]
    order = np.argsort(groups, kind="stable")
    cuts = np.flatnonzero(np.diff(groups[order])) + 1
    S = np.add.reduceat(score[order], np.r_[0, cuts], axis=0)
    G = S.shape[0]
    cov = bread @ (S.T @ S) @ bread * (G / (G - 1))
    return beta, np.sqrt(np.diag(cov))


def price_response(sales: pd.DataFrame, truth: dict | None = None) -> list[dict]:
    """Own-price elasticity and promotion lift per category.

    units ~ Poisson(exp(b1*log(price) + b2*promo + series FE + day-of-week
            + year-month + festival-window dummies))
    b1 is the elasticity; exp(b2)-1 is the promotion's lift beyond its discount.
    """
    out = []
    for cat, d in sales.groupby("category"):
        d = d.reset_index(drop=True)
        sid = pd.Categorical(d.series_id).codes
        ym = pd.Categorical(d.date.dt.to_period("M").astype(str)).codes
        fest = np.where(d.days_from_major.between(-13, 7), d.days_from_major + 14, 0)
        dummies = [
            np.eye(sid.max() + 1)[sid],                       # series fixed effects (acts as intercept)
            np.eye(7)[d.date.dt.dayofweek][:, 1:],
            np.eye(ym.max() + 1)[ym][:, 1:],
            np.eye(22)[fest][:, 1:],
            ((d.days_from_holiday >= -1) & (d.days_from_holiday <= 0)).to_numpy(float)[:, None],
            (d.date.dt.day <= 3).to_numpy(float)[:, None],
        ]
        base_price = d.groupby("series_id").list_price.transform("first")
        core = np.column_stack([np.log(d.price / base_price), d.promo])
        X = np.column_stack([core] + dummies)
        beta, se = _ppml(X, d.units.to_numpy(float), sid)
        row = dict(
            category=cat, n_obs=int(len(d)),
            elasticity=float(beta[0]), elasticity_se=float(se[0]),
            elasticity_lo=float(beta[0] - 1.96 * se[0]), elasticity_hi=float(beta[0] + 1.96 * se[0]),
            promo_lift=float(np.exp(beta[1]) - 1),
            promo_lift_lo=float(np.exp(beta[1] - 1.96 * se[1]) - 1),
            promo_lift_hi=float(np.exp(beta[1] + 1.96 * se[1]) - 1),
            avg_discount=float(d.loc[d.promo == 1, "discount"].mean()),
            promo_share=float(d.promo.mean()),
        )
        if truth:
            row["elasticity_true"] = truth["elasticity"][cat]
            row["promo_lift_true"] = float(np.exp(truth["promo_lift"][cat]) - 1)
        out.append(row)
    return out


# ----------------------------------------------------------- anomalies ----
def detect_anomalies(sales: pd.DataFrame, threshold: float = 4.5, window: int = 8) -> pd.DataFrame:
    """Count-aware anomaly detection.

    expected demand = trailing same-weekday median of non-promo days, scaled by
                      the series' own typical promotion uplift on promo days
    noise model     = negative binomial: Var = e + a*e^2, with the
                      over-dispersion `a` estimated robustly per series
    A day is flagged when its standardised residual exceeds `threshold`; a run
    of consecutive zero-sales days is flagged when its joint probability under
    the noise model is below the same tail probability (catches stock-outs on
    slow movers, where a single zero is unremarkable). Festival windows are
    excluded because those peaks are explained.
    """
    d = sales.sort_values(["series_id", "date"]).reset_index(drop=True)
    key = [d.series_id, d.date.dt.dayofweek]
    prior = d.units.where(d.promo == 0).groupby(key).shift(1)
    base = prior.groupby(key).rolling(window, min_periods=4).median().reset_index(level=[0, 1], drop=True).sort_index()
    ratio = (d.units / base.where(base > 0)).where(d.promo == 1)
    uplift = ratio.groupby(d.series_id).transform("median").fillna(1.0).clip(1.0, 4.0)
    e = (base * np.where(d.promo == 1, uplift, 1.0)).clip(lower=0.05)

    resid2 = (d.units - e) ** 2
    g = d.series_id
    # median of a chi-square(1) is 0.455 -> robust variance estimate
    a = ((resid2.groupby(g).transform("median") / 0.455 - e.groupby(g).transform("mean"))
         / (e ** 2).groupby(g).transform("mean")).clip(lower=0.02)
    d["expected"] = e
    d["z"] = (d.units - e) / np.sqrt(e + a * e ** 2)

    explained = d.days_from_major.between(-13, 7) | d.days_from_holiday.between(-2, 1)
    usable = base.notna() & ~explained
    point = (d.z.abs() > threshold) & usable

    # zero runs: joint NB probability of the whole run
    log_p0 = -np.log1p(a * e) / a
    zero = (d.units == 0) & usable
    run_id = (zero != zero.groupby(g).shift(1, fill_value=False)).cumsum()
    run_logp = log_p0.where(zero).groupby(run_id).transform("sum")
    run = zero & (run_logp < np.log(2 * norm.sf(threshold)))

    d["flag"] = point | run
    d["kind"] = np.where(d.units < e, "drop", "spike")
    return d


def anomaly_scorecard(det: pd.DataFrame, truth_events: pd.DataFrame) -> dict:
    """Day-level precision and event-level recall against injected anomalies."""
    flagged = det[det.flag]
    precision = float(flagged.anomaly_truth.mean()) if len(flagged) else float("nan")
    hit = set(zip(flagged.series_id, flagged.date))
    found = 0
    for e in truth_events.itertuples():
        sid = f"{e.store_id}|{e.sku_id}"
        if any((sid, e.date + pd.Timedelta(days=k)) in hit for k in range(e.length)):
            found += 1
    return dict(flagged_days=int(len(flagged)), precision=precision,
                events=int(len(truth_events)), events_found=found,
                recall=found / max(len(truth_events), 1))


# ------------------------------------------------------------ scenario ----
def simulate(base: pd.DataFrame, price_change: float, promo: bool, response: dict) -> dict:
    """Constant-elasticity what-if on the forecast.

    base: rows with category, units, price, unit_cost (forecast totals per series)
    response: {category: {"elasticity": e, "promo_lift": l}}
    """
    e = base.category.map(lambda c: response[c]["elasticity"]).to_numpy()
    lift = base.category.map(lambda c: response[c]["promo_lift"]).to_numpy() if promo else 0.0
    new_price = base.price.to_numpy() * (1 + price_change)
    units = base.units.to_numpy() * (1 + price_change) ** e * (1 + lift)
    b_rev = float((base.units * base.price).sum())
    b_mar = float((base.units * (base.price - base.unit_cost)).sum())
    rev = float((units * new_price).sum())
    mar = float((units * (new_price - base.unit_cost.to_numpy())).sum())
    return dict(base_units=float(base.units.sum()), units=float(units.sum()),
                base_revenue=b_rev, revenue=rev, base_margin=b_mar, margin=mar)


def profit_curve(base: pd.DataFrame, promo: bool, response: dict, lo: float = -0.30, hi: float = 0.30, n: int = 25) -> dict:
    grid = np.linspace(lo, hi, n)
    sims = [simulate(base, float(g), promo, response) for g in grid]
    best = int(np.argmax([s["margin"] for s in sims]))
    return dict(price_change=[round(float(g), 4) for g in grid],
                revenue=[s["revenue"] for s in sims], margin=[s["margin"] for s in sims],
                units=[s["units"] for s in sims], best_price_change=round(float(grid[best]), 4))
