/* ForecastIQ single-page dashboard. Vanilla JS, no build step. */
(function () {
  "use strict";
  const $ = (s, r) => (r || document).querySelector(s);
  const view = $("#view");
  const cache = {};
  let META = null;

  // ---------------------------------------------------------------- helpers
  const api = async (path, opts) => {
    if (!opts && cache[path]) return cache[path];
    const res = await fetch(path, opts);
    const body = await res.json().catch(() => ({ error: "Unexpected server response." }));
    if (!res.ok) throw new Error(body.error || `Request failed (${res.status})`);
    if (!opts) cache[path] = body;
    return body;
  };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const num = (v, d) => (v == null ? "-" : Number(v).toLocaleString("en-IN", { maximumFractionDigits: d == null ? 0 : d, minimumFractionDigits: d == null ? 0 : d }));
  const compact = (v) => {
    const a = Math.abs(v);
    if (a >= 1e7) return (v / 1e7).toFixed(a >= 1e9 ? 0 : 2) + " Cr";
    if (a >= 1e5) return (v / 1e5).toFixed(a >= 1e6 ? 1 : 2) + " L";
    if (a >= 1e3) return (v / 1e3).toFixed(a >= 1e4 ? 0 : 1) + "K";
    return num(v);
  };
  const inr = (v) => (v == null ? "-" : "₹" + compact(v));
  const pct = (v, d) => (v == null ? "-" : (v * 100).toFixed(d == null ? 1 : d) + "%");
  const delta = (v) => (v == null ? "" : `<span class="delta ${v >= 0 ? "up" : "down"}">${v >= 0 ? "▲" : "▼"} ${Math.abs(v * 100).toFixed(1)}%</span>`);
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const dShort = (s) => `${+s.slice(8, 10)} ${MONTHS[+s.slice(5, 7) - 1]}`;
  const dLong = (s) => `${dShort(s)} ${s.slice(0, 4)}`;
  const mShort = (s) => `${MONTHS[+s.slice(5, 7) - 1]} ${s.slice(2, 4)}`;
  const SERIES = ["var(--series-1)", "var(--series-2)", "var(--series-3)", "var(--series-4)", "var(--series-5)"];
  const catColor = (c) => SERIES[META.categories.indexOf(c)];
  const MODEL_COLOR = { snaive: "var(--neutral)", ets: "var(--series-3)", gbm: "var(--series-1)", ensemble: "var(--series-2)" };
  const legend = (items) => `<div class="legend">${items.map((i) => `<span><i class="${i.box ? "box" : ""} ${i.dash ? "dash" : ""}" style="background:${i.color};color:${i.color}"></i>${esc(i.name)}</span>`).join("")}</div>`;
  const kpi = (label, value, foot) => `<div class="card kpi"><div class="label">${label}</div><div class="value">${value}</div><div class="foot">${foot || ""}</div></div>`;
  const csvDownload = (name, rows) => {
    const blob = new Blob([rows.map((r) => r.join(",")).join("\n")], { type: "text/csv" });
    const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: name });
    a.click();
    URL.revokeObjectURL(a.href);
  };

  /* Sortable table. cols: [{key,label,num,fmt}] */
  function table(node, cols, rows, opts) {
    opts = opts || {};
    let sortKey = opts.sort || null, dir = opts.dir || -1;
    node.classList.add("tbl");
    const draw = () => {
      const data = rows.slice();
      if (sortKey) data.sort((a, b) => (a[sortKey] > b[sortKey] ? 1 : a[sortKey] < b[sortKey] ? -1 : 0) * dir);
      node.innerHTML = `<table><thead><tr>${cols.map((c) => `<th class="${c.num ? "num" : ""} ${opts.sortable ? "sortable" : ""}" data-k="${c.key}">${c.label}${sortKey === c.key ? (dir > 0 ? " ↑" : " ↓") : ""}</th>`).join("")}</tr></thead><tbody>${
        data.slice(0, opts.limit || 500).map((r) => `<tr class="${opts.rowClass ? opts.rowClass(r) : ""}">${cols.map((c) => `<td class="${c.num ? "num" : ""}">${c.fmt ? c.fmt(r[c.key], r) : esc(r[c.key])}</td>`).join("")}</tr>`).join("")
      }</tbody></table>`;
      if (opts.sortable) node.querySelectorAll("th").forEach((th) => th.addEventListener("click", () => {
        const k = th.dataset.k;
        if (sortKey === k) dir = -dir; else { sortKey = k; dir = -1; }
        draw();
      }));
    };
    draw();
  }

  // --------------------------------------------------------------- overview
  async function overview() {
    const [o, total] = await Promise.all([api("/api/overview"), api("/api/forecast?node=" + encodeURIComponent("total:All stores"))]);
    const k = o.kpis;
    const fest = META.holidays_in_horizon.map((h) => `${h.name} (${dShort(h.date)})`).join(", ");
    view.innerHTML = `
      <div class="stack">
        <div class="grid g-kpi">
          ${kpi("Revenue, last 28 days", inr(k.revenue), `${delta(k.revenue / k.revenue_prev - 1)} vs prior 28 days`)}
          ${kpi("Forecast revenue, next 28 days", inr(k.forecast_revenue), `${delta(k.forecast_revenue / k.revenue - 1)} vs last 28 days`)}
          ${kpi("Gross margin", pct(k.margin_pct), `${inr(k.margin)} · was ${pct(k.margin_pct_prev)}`)}
          ${kpi("Forecast accuracy (1 − WAPE)", pct(1 - k.forecast_wape), `seasonal-naive baseline ${pct(1 - k.naive_wape)}`)}
          ${kpi("SKUs needing replenishment", num(k.at_risk_skus), `${inr(k.revenue_at_risk)} revenue at risk`)}
        </div>
        <div class="note"><b>What the forecast is saying.</b> Demand is expected to ${k.forecast_units >= k.units ? "rise" : "fall"} ${Math.abs((k.forecast_units / k.units - 1) * 100).toFixed(1)}% in units over the next four weeks${fest ? `, a window that contains ${esc(fest)}` : ""}.
          Revenue is ${k.revenue >= k.revenue_ly ? "up" : "down"} ${Math.abs((k.revenue / k.revenue_ly - 1) * 100).toFixed(1)}% on the same weeks last year${k.holidays_ly.length ? ` — note that last year's window contained ${esc(k.holidays_ly.join(", "))}, so festival timing rather than underlying demand explains much of that gap` : ""}.</div>
        <div class="grid g-main">
          <div class="card"><h2>Total demand: last 26 weeks and 28-day forecast</h2><p class="sub">Units per day across all stores. Shaded area is the 80% prediction interval.</p>
            ${legend([{ name: "Actual", color: "var(--text-secondary)" }, { name: "Forecast", color: SERIES[0] }, { name: "80% interval", color: "var(--band)", box: true }])}
            <div id="c-total"></div></div>
          <div class="card"><h2>Biggest expected movers</h2><p class="sub">Forecast units for the next 28 days vs the last 28.</p><div id="t-movers"></div></div>
        </div>
        <div class="card"><h2>Monthly revenue by category</h2><p class="sub">Three years of history. Hover for the breakdown.</p>
          ${legend(META.categories.map((c) => ({ name: c, color: catColor(c), box: true })))}<div id="c-month"></div></div>
        <div class="grid g2">
          <div class="card"><h2>Categories</h2><p class="sub">Last 28 days, year-on-year, and the forecast for the next 28.</p><div id="t-cat"></div></div>
          <div class="card"><h2>Stores</h2><p class="sub">Same measures by store.</p><div id="t-store"></div></div>
        </div>
      </div>`;
    forecastChart($("#c-total"), total, { height: 300 });
    Charts.bar($("#c-month"), {
      categories: o.monthly.months, stacked: true, height: 280, yFmt: inr, xFmt: mShort, labelWidth: 56,
      series: META.categories.map((c) => ({ name: c, color: catColor(c), values: o.monthly.series[c] })),
    });
    const cols = [{ key: "name", label: "" }, { key: "revenue", label: "Revenue", num: 1, fmt: inr }, { key: "yoy", label: "YoY", num: 1, fmt: delta },
      { key: "forecast", label: "Forecast", num: 1, fmt: inr }, { key: "change", label: "Change", num: 1, fmt: delta }];
    table($("#t-cat"), cols, o.by_category);
    table($("#t-store"), cols, o.by_store);
    table($("#t-movers"), [{ key: "sku_id", label: "SKU" }, { key: "category", label: "Category" }, { key: "forecast", label: "Forecast", num: 1, fmt: (v) => num(v) }, { key: "change", label: "Change", num: 1, fmt: delta }],
      o.movers_up.concat(o.movers_down));
  }

  /* history + forecast (+ optional backtest overlay) on one shared axis */
  function forecastChart(node, d, opts) {
    opts = opts || {};
    const h = d.hist.length, f = d.forecast.length, x = d.hist_dates.concat(d.fc_dates);
    const pad = (n) => Array(n).fill(null);
    const series = [
      { name: "Actual", color: "var(--text-secondary)", values: d.hist.concat(pad(f)), width: 1.6 },
      { name: "Forecast", color: SERIES[0], values: pad(h - 1).concat([d.hist[h - 1]], d.forecast) },
    ];
    const bands = [{ name: "80% interval", lo: pad(h).concat(d.lo), hi: pad(h).concat(d.hi) }];
    if (opts.backtest) {
      const start = d.hist_dates.indexOf(d.bt_dates[0]), bt = pad(x.length), blo = pad(x.length), bhi = pad(x.length);
      d.bt_pred.forEach((v, i) => { bt[start + i] = v; blo[start + i] = d.bt_lo[i]; bhi[start + i] = d.bt_hi[i]; });
      series.push({ name: "Backtest forecast", color: SERIES[1], values: bt, width: 1.6 });
      bands.push({ name: "Backtest 80% interval", lo: blo, hi: bhi, color: "color-mix(in srgb, var(--series-2) 14%, transparent)" });
    }
    const marks = META.holidays_in_horizon.map((hd) => ({ at: x.indexOf(hd.date), label: hd.name })).filter((m) => m.at >= 0);
    Charts.line(node, { x, series, bands, marks, height: opts.height || 340, yFmt: (v) => num(v), xFmt: dShort, xTip: dLong, vline: { at: h - 1, label: "forecast starts" } });
  }

  // --------------------------------------------------------------- forecast
  async function forecast() {
    const levels = [["total", "All stores"], ["region", "Region"], ["category", "Category"], ["store", "Store"], ["series", "SKU × store"]];
    view.innerHTML = `
      <div class="stack"><div class="card">
        <div class="controls">
          <label>Level<select id="f-level">${levels.map((l) => `<option value="${l[0]}">${l[1]}</option>`).join("")}</select></label>
          <label>Selection<select id="f-node"></select></label>
          <label class="check"><input type="checkbox" id="f-bt"> Overlay backtest (what the model predicted, before it saw the outcome)</label>
          <button class="btn right" id="f-csv" type="button">Download forecast CSV</button>
        </div>
        <div id="f-legend"></div><div id="c-fc"></div>
      </div>
      <div class="grid g-kpi" id="f-kpis"></div>
      <div class="grid g2">
        <div class="card"><h2>Model comparison for this selection</h2><p class="sub">Next 28 days. The champion model is the production forecast.</p>
          ${legend([["snaive", "Seasonal naive"], ["ets", "Holt-Winters"], ["gbm", "Gradient boosting"]].map((m) => ({ name: m[1], color: MODEL_COLOR[m[0]] })))}<div id="c-models"></div></div>
        <div class="card"><h2>Daily forecast</h2><p class="sub">Point forecast with 80% interval, units.</p><div class="scroll" style="max-height:290px" id="t-fc"></div></div>
      </div></div>`;
    const levelSel = $("#f-level"), nodeSel = $("#f-node"), bt = $("#f-bt");
    let current = null;
    const fill = () => {
      nodeSel.innerHTML = META.nodes.filter((n) => n.level === levelSel.value).map((n) => `<option value="${esc(n.id)}">${esc(n.label)}</option>`).join("");
      nodeSel.disabled = levelSel.value === "total";
    };
    const draw = async () => {
      const d = (current = await api("/api/forecast?node=" + encodeURIComponent(nodeSel.value)));
      const items = [{ name: "Actual", color: "var(--text-secondary)" }, { name: "Forecast", color: SERIES[0] }, { name: "80% interval", color: "var(--band)", box: true }];
      if (bt.checked) items.push({ name: "Backtest forecast", color: SERIES[1] });
      $("#f-legend").innerHTML = legend(items);
      forecastChart($("#c-fc"), d, { backtest: bt.checked });
      const lo = d.lo.reduce((a, b) => a + b, 0), hi = d.hi.reduce((a, b) => a + b, 0);
      $("#f-kpis").innerHTML =
        kpi("Forecast, next 28 days", num(d.fc_total) + " units", `${delta(d.fc_total / d.hist_total - 1)} vs last 28 days`) +
        kpi("Last 28 days, actual", num(d.hist_total) + " units", esc(d.label)) +
        kpi("Backtest error (WAPE)", pct(d.bt_wape), "daily, 4 rolling 28-day windows") +
        kpi("Days on promotion", pct(d.promo_share.reduce((a, b) => a + b, 0) / d.promo_share.length, 0), "planned share of SKU-days in the horizon");
      const labels = { snaive: "Seasonal naive", ets: "Holt-Winters", gbm: "Gradient boosting" };
      Charts.line($("#c-models"), { x: d.fc_dates, height: 250, yFmt: (v) => num(v), xFmt: dShort, zero: false,
        series: ["snaive", "ets", "gbm"].map((m) => ({ name: labels[m], color: MODEL_COLOR[m], values: d.models[m] })) });
      table($("#t-fc"), [{ key: "date", label: "Date", fmt: dLong }, { key: "f", label: "Forecast", num: 1, fmt: (v) => num(v, 1) }, { key: "lo", label: "Low", num: 1, fmt: (v) => num(v, 1) }, { key: "hi", label: "High", num: 1, fmt: (v) => num(v, 1) }],
        d.fc_dates.map((date, i) => ({ date, f: d.forecast[i], lo: d.lo[i], hi: d.hi[i] })));
    };
    levelSel.addEventListener("change", () => { fill(); draw(); });
    nodeSel.addEventListener("change", draw);
    bt.addEventListener("change", draw);
    $("#f-csv").addEventListener("click", () => current && csvDownload(`forecast_${current.key.replace(/\W+/g, "_")}.csv`,
      [["date", "forecast", "lower_80", "upper_80"]].concat(current.fc_dates.map((d, i) => [d, current.forecast[i], current.lo[i], current.hi[i]]))));
    fill();
    await draw();
  }

  // ----------------------------------------------------------------- models
  async function models() {
    const p = await api("/api/performance");
    const order = ["snaive", "ets", "gbm", "ensemble"];
    const SHORT = { snaive: "Naive", ets: "ETS", gbm: "GBM", ensemble: "Ensemble" };
    const lb = order.map((m) => p.leaderboard.find((r) => r.model === m));
    const iv = p.intervals, maxImp = p.importance[0].importance;
    const by = (rows, key, m) => (rows.find((r) => r.key === String(key) && r.model === m) || {}).wape;
    const base = lb[0].wape, champ = lb.find((r) => r.model === p.champion);
    view.innerHTML = `
      <div class="stack">
        <div class="grid g-kpi">
          ${kpi("Champion model", esc(SHORT[p.champion]), `${esc(p.labels[p.champion])}, selected automatically on out-of-sample error`)}
          ${kpi("Error vs seasonal naive", pct(champ.wape / base - 1), `WAPE ${pct(champ.wape)} vs ${pct(base)}`)}
          ${kpi("MASE", champ.mase.toFixed(2), "below 1.0 beats the naive benchmark")}
          ${kpi("80% interval coverage", pct(iv.coverage), `${pct(iv.raw_coverage)} before conformal calibration`)}
          ${kpi("Out-of-sample forecasts", num(p.n_forecasts), `${dShort(p.test_window[0])} – ${dLong(p.test_window[1])}`)}
        </div>
        <div class="card"><h2>Leaderboard</h2><p class="sub">Rolling-origin backtest, three 28-day test windows, 180 series, daily grain. Every number is out of sample.</p><div id="t-lb"></div></div>
        <div class="grid g2">
          <div class="card"><h2>Error by category</h2><p class="sub">WAPE, lower is better.</p>${legend(order.map((m) => ({ name: p.labels[m], color: MODEL_COLOR[m], box: true })))}<div id="c-cat"></div></div>
          <div class="card"><h2>Error by forecast week</h2><p class="sub">Does accuracy decay further into the horizon?</p>${legend(order.map((m) => ({ name: p.labels[m], color: MODEL_COLOR[m] })))}<div id="c-week"></div></div>
        </div>
        <div class="grid g2">
          <div class="card"><h2>Error across the hierarchy</h2><p class="sub">Bottom-up forecasts summed to each level. Errors cancel as you aggregate.</p><div id="t-levels"></div></div>
          <div class="card"><h2>What drives the gradient-boosting forecast</h2><p class="sub">Permutation importance on the last test window: increase in MAE (units) when the feature is shuffled.</p>
            <div class="hbar">${p.importance.slice(0, 10).map((r) => `<code>${esc(r.feature)}</code><div class="track"><div class="fill" style="width:${Math.max(0.5, (r.importance / maxImp) * 100)}%"></div></div><div class="v">${r.importance.toFixed(2)}</div>`).join("")}</div></div>
        </div>
        <div class="note"><b>Reading this honestly.</b> The inverse-error weighted ensemble did <b>not</b> beat the global gradient-boosting model here (${pct(lb[3].wape)} vs ${pct(lb[2].wape)} WAPE): the classical models cannot see price and promotion plans, so blending them in dilutes the one model that can. The pipeline therefore promotes the model with the lowest error on earlier folds instead of assuming an ensemble is better. Interval coverage is ${pct(iv.coverage)} against an 80% target.</div>
      </div>`;
    table($("#t-lb"), [
      { key: "model", label: "Model", fmt: (v) => esc(p.labels[v]) + (v === p.champion ? '<span class="tag champ">champion</span>' : "") },
      { key: "wape", label: "WAPE", num: 1, fmt: (v) => pct(v) }, { key: "mase", label: "MASE", num: 1, fmt: (v) => v.toFixed(3) },
      { key: "mae", label: "MAE", num: 1, fmt: (v) => v.toFixed(2) }, { key: "rmse", label: "RMSE", num: 1, fmt: (v) => v.toFixed(2) },
      { key: "smape", label: "sMAPE", num: 1, fmt: (v) => pct(v) }, { key: "bias", label: "Bias", num: 1, fmt: (v) => (v > 0 ? "+" : "") + pct(v) },
    ], lb, { rowClass: (r) => (r.model === p.champion ? "hl" : "") });
    Charts.bar($("#c-cat"), { categories: META.categories, yFmt: (v) => pct(v, 0), height: 260, labelWidth: 78,
      series: order.map((m) => ({ name: p.labels[m], color: MODEL_COLOR[m], values: META.categories.map((c) => by(p.by_category, c, m)) })) });
    Charts.line($("#c-week"), { x: ["Week 1", "Week 2", "Week 3", "Week 4"], yFmt: (v) => pct(v, 0), height: 260,
      series: order.map((m) => ({ name: p.labels[m], color: MODEL_COLOR[m], values: [1, 2, 3, 4].map((w) => by(p.by_week, w, m)) })) });
    table($("#t-levels"), [{ key: "level", label: "Level" }, { key: "n", label: "Points", num: 1, fmt: (v) => num(v) }]
      .concat(order.map((m) => ({ key: m, label: SHORT[m], num: 1, fmt: (v) => pct(v) }))), p.levels);
  }

  // -------------------------------------------------------------- inventory
  async function inventory() {
    const inv = await api("/api/inventory");
    const city = Object.fromEntries(META.stores.map((s) => [s.store_id, s.city]));
    const rows = inv.rows.map((r) => Object.assign({ city: city[r.store_id], rank: { Critical: 3, Reorder: 2, Overstock: 1, Healthy: 0 }[r.status] }, r));
    const count = (s) => rows.filter((r) => r.status === s).length;
    const sum = (k) => rows.reduce((a, r) => a + r[k], 0);
    const totalRev = inv.matrix.reduce((a, m) => a + m.revenue, 0);
    const cell = (a, x) => {
      const m = inv.matrix.find((r) => r.abc === a && r.xyz === x) || { n: 0, revenue: 0 };
      const share = m.revenue / totalRev, tone = share > 0.2 ? 3 : share > 0.07 ? 2 : 1;
      return `<div class="cell" style="background:var(--seq-${tone});color:${tone === 3 ? "#fff" : "var(--text-primary)"}"><b>${m.n}</b><span>${pct(share, 0)} of revenue</span></div>`;
    };
    const a = META.assumptions;
    view.innerHTML = `
      <div class="stack">
        <div class="grid g-kpi">
          ${kpi('<span class="badge Critical"><i></i>Critical</span>', count("Critical"), "stock will run out before a new order can arrive")}
          ${kpi('<span class="badge Reorder"><i></i>Reorder</span>', count("Reorder"), "at or below the reorder point")}
          ${kpi('<span class="badge Overstock"><i></i>Overstock</span>', count("Overstock"), `more than ${a.overstock_days} days of cover`)}
          ${kpi("Revenue at risk", inr(sum("revenue_at_risk")), "forecast demand that cannot be served during lead time")}
          ${kpi("Recommended orders", inr(sum("order_value")), `${inr(sum("excess_capital"))} tied up in excess stock`)}
        </div>
        <div class="grid g-main">
          <div class="card"><h2>Replenishment plan</h2><p class="sub">Click a column to sort. Safety stock uses the model's own out-of-sample forecast error, not raw demand variance.</p>
            <div class="controls">
              <label>Status<select id="i-status"><option value="">All</option><option>Critical</option><option>Reorder</option><option>Overstock</option><option>Healthy</option></select></label>
              <label>Store<select id="i-store"><option value="">All</option>${META.stores.map((s) => `<option value="${s.store_id}">${esc(s.city)}</option>`).join("")}</select></label>
              <label>Category<select id="i-cat"><option value="">All</option>${META.categories.map((c) => `<option>${esc(c)}</option>`).join("")}</select></label>
              <span class="muted" id="i-count"></span>
              <button class="btn right" id="i-csv" type="button">Download CSV</button>
            </div>
            <div class="scroll" id="t-inv"></div></div>
          <div class="stack">
            <div class="card"><h2>ABC-XYZ segmentation</h2><p class="sub">Rows: revenue importance (A = top 80%). Columns: demand variability (X = steady, Z = erratic). Count of SKU-store pairs.</p>
              <div class="matrix"><div></div><div class="h">X</div><div class="h">Y</div><div class="h">Z</div>
                ${["A", "B", "C"].map((r) => `<div class="h">${r}</div>` + ["X", "Y", "Z"].map((c) => cell(r, c)).join("")).join("")}</div></div>
            <div class="card prose"><h2>Policy</h2><ul>
              <li>Safety stock = z × σ<sub>forecast error</sub> × √lead time</li>
              <li>Reorder point = forecast demand over lead time + safety stock</li>
              <li>Order size = economic order quantity (order cost ₹${num(a.order_cost)}, holding ${pct(a.holding_rate, 0)} a year)</li>
              <li>Service level by class: A ${pct(a.service_level.A, 0)}, B ${pct(a.service_level.B, 0)}, C ${pct(a.service_level.C, 0)}</li></ul></div>
          </div>
        </div>
      </div>`;
    const cols = [
      { key: "rank", label: "Status", fmt: (_, r) => `<span class="badge ${r.status}"><i></i>${r.status}</span>` },
      { key: "sku_id", label: "SKU" }, { key: "city", label: "Store" }, { key: "abc", label: "Class", fmt: (v, r) => v + r.xyz },
      { key: "on_hand", label: "On hand", num: 1, fmt: (v) => num(v) }, { key: "daily_forecast", label: "Forecast / day", num: 1, fmt: (v) => num(v, 1) },
      { key: "days_cover", label: "Days cover", num: 1, fmt: (v) => num(v, 0) }, { key: "lead_time", label: "Lead time", num: 1, fmt: (v) => v + " d" },
      { key: "safety_stock", label: "Safety stock", num: 1, fmt: (v) => num(v) }, { key: "reorder_point", label: "Reorder point", num: 1, fmt: (v) => num(v) },
      { key: "order_qty", label: "Order qty", num: 1, fmt: (v) => (v ? num(v) : "-") }, { key: "order_value", label: "Order value", num: 1, fmt: (v) => (v ? inr(v) : "-") },
    ];
    let shown = rows;
    const draw = () => {
      const s = $("#i-status").value, st = $("#i-store").value, c = $("#i-cat").value;
      shown = rows.filter((r) => (!s || r.status === s) && (!st || r.store_id === st) && (!c || r.category === c));
      $("#i-count").textContent = `${shown.length} of ${rows.length} SKU-store pairs`;
      table($("#t-inv"), cols, shown, { sortable: true, sort: "rank" });
    };
    ["#i-status", "#i-store", "#i-cat"].forEach((s) => $(s).addEventListener("change", draw));
    $("#i-csv").addEventListener("click", () => csvDownload("replenishment_plan.csv",
      [["status", "sku", "store", "class", "on_hand", "daily_forecast", "days_cover", "lead_time", "safety_stock", "reorder_point", "order_qty", "order_value"]]
        .concat(shown.map((r) => [r.status, r.sku_id, r.city, r.abc + r.xyz, r.on_hand, r.daily_forecast, r.days_cover, r.lead_time, r.safety_stock, r.reorder_point, r.order_qty, r.order_value]))));
    draw();
  }

  // ---------------------------------------------------------------- pricing
  function intervalPlot(node, rows) {
    Charts.mount(node, rows, (n, data, W) => {
      const rowH = 34, m = { l: 118, r: 20, t: 8, b: 26 }, H = m.t + m.b + rowH * data.length, iw = W - m.l - m.r;
      const lo = -2.8, hi = 0, X = (v) => m.l + ((v - lo) / (hi - lo)) * iw;
      const svg = Charts.el("svg", { viewBox: `0 0 ${W} ${H}`, height: H, role: "img", "aria-label": "Estimated price elasticity with confidence intervals" }, n);
      [-2.5, -2, -1.5, -1, -0.5, 0].forEach((v) => {
        Charts.el("line", { x1: X(v), x2: X(v), y1: m.t, y2: H - m.b, stroke: v === -1 ? "var(--neutral)" : "var(--line-soft)", "stroke-dasharray": v === -1 ? "3 4" : "" }, svg);
        Charts.el("text", { x: X(v), y: H - 8, "text-anchor": "middle" }, svg).textContent = v.toFixed(1);
      });
      data.forEach((r, i) => {
        const y = m.t + rowH * (i + 0.5);
        Charts.el("text", { x: m.l - 10, y: y + 4, "text-anchor": "end", style: "fill:var(--text-secondary);font-size:12px" }, svg).textContent = r.category;
        Charts.el("line", { x1: X(r.elasticity_lo), x2: X(r.elasticity_hi), y1: y, y2: y, stroke: "var(--series-1)", "stroke-width": 2, "stroke-linecap": "round" }, svg);
        Charts.el("path", { d: `M${X(r.elasticity_true)},${y - 9}V${y + 9}`, stroke: "var(--text-primary)", "stroke-width": 2 }, svg);
        Charts.el("circle", { cx: X(r.elasticity), cy: y, r: 5, fill: "var(--series-1)", stroke: "var(--surface-1)", "stroke-width": 2 }, svg);
        const hit = Charts.el("rect", { x: m.l, y: y - rowH / 2, width: iw, height: rowH, fill: "transparent" }, svg);
        hit.addEventListener("mousemove", (e) => Charts.showTip(e, `<b>${esc(r.category)}</b><div><span>Estimate</span><span>${r.elasticity.toFixed(2)}</span></div><div><span>95% CI</span><span>${r.elasticity_lo.toFixed(2)} to ${r.elasticity_hi.toFixed(2)}</span></div><div><span>True value</span><span>${r.elasticity_true.toFixed(2)}</span></div>`));
        hit.addEventListener("mouseleave", Charts.hideTip);
      });
    });
  }

  async function pricing() {
    const p = await api("/api/pricing");
    const rows = META.categories.map((c) => p.response.find((r) => r.category === c));
    view.innerHTML = `
      <div class="stack">
        <div class="grid g2">
          <div class="card"><h2>Own-price elasticity by category</h2><p class="sub">Poisson regression with SKU-store fixed effects and cluster-robust 95% intervals. A value of −1.5 means a 1% price rise loses about 1.5% of units.</p>
            ${legend([{ name: "Estimate and 95% interval", color: SERIES[0] }, { name: "True value in the simulator", color: "var(--text-primary)" }])}<div id="c-el"></div>
            <p class="sub" style="margin:8px 0 0">Left of the dashed line (−1) demand is elastic: cutting price raises revenue.</p></div>
          <div class="card"><h2>Promotion lift</h2><p class="sub">Extra demand from running a promotion, over and above the effect of its discount.</p><div id="t-promo"></div></div>
        </div>
        <div class="card"><h2>What-if simulator</h2><p class="sub">Apply a price change to the next 28 days of forecast demand using the estimated elasticities.</p>
          <div class="controls">
            <label>Category<select id="s-cat"><option value="all">All categories</option>${META.categories.map((c) => `<option>${esc(c)}</option>`).join("")}</select></label>
            <label>Store<select id="s-store"><option value="all">All stores</option>${META.stores.map((s) => `<option value="${s.store_id}">${esc(s.city)}</option>`).join("")}</select></label>
            <label>Price change: <b id="s-val">0%</b><input type="range" id="s-price" min="-30" max="30" step="1" value="0"></label>
            <label class="check"><input type="checkbox" id="s-promo"> Run as a promotion</label>
          </div>
          <div class="grid g-kpi" id="s-kpis"></div>
          <div style="margin-top:16px">${legend([{ name: "Gross margin", color: SERIES[0] }, { name: "Revenue", color: SERIES[1] }])}<div id="c-curve"></div>
          <p class="sub" id="s-best" style="margin:8px 0 0"></p></div>
        </div>
      </div>`;
    intervalPlot($("#c-el"), rows);
    table($("#t-promo"), [{ key: "category", label: "Category" }, { key: "promo_lift", label: "Estimated lift", num: 1, fmt: (v) => "+" + pct(v) },
      { key: "promo_lift_lo", label: "95% interval", num: 1, fmt: (v, r) => `${pct(v)} to ${pct(r.promo_lift_hi)}` },
      { key: "promo_lift_true", label: "True", num: 1, fmt: (v) => "+" + pct(v) }, { key: "avg_discount", label: "Avg discount", num: 1, fmt: (v) => pct(v, 0) }], rows);
    let timer;
    const edge = (c) => Math.abs(c.best_price_change) >= 0.299;
    const run = async () => {
      const change = +$("#s-price").value / 100;
      $("#s-val").textContent = (change > 0 ? "+" : "") + (change * 100).toFixed(0) + "%";
      try {
        const res = await api("/api/scenario", { method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ category: $("#s-cat").value, store: $("#s-store").value, price_change: change, promo: $("#s-promo").checked }) });
        const r = res.result, c = res.curve;
        $("#s-kpis").innerHTML =
          kpi("Units", num(r.units), `${delta(r.units / r.base_units - 1)} vs baseline ${num(r.base_units)}`) +
          kpi("Revenue", inr(r.revenue), `${delta(r.revenue / r.base_revenue - 1)} vs baseline ${inr(r.base_revenue)}`) +
          kpi("Gross margin", inr(r.margin), `${delta(r.margin / r.base_margin - 1)} vs baseline ${inr(r.base_margin)}`);
        const at = c.price_change.reduce((b, v, i) => (Math.abs(v - change) < Math.abs(c.price_change[b] - change) ? i : b), 0);
        const best = c.price_change.indexOf(c.best_price_change);
        Charts.line($("#c-curve"), { x: c.price_change, height: 250, yFmt: inr, xFmt: (v) => (v > 0 ? "+" : "") + (v * 100).toFixed(0) + "%", zero: false,
          series: [{ name: "Gross margin", color: SERIES[0], values: c.margin }, { name: "Revenue", color: SERIES[1], values: c.revenue }],
          points: [{ at, value: c.margin[at], color: SERIES[0] }, { at, value: c.revenue[at], color: SERIES[1] }],
          vline: edge(c) ? null : { at: best, label: "margin peak" } });
        $("#s-best").textContent = `Across ${res.n_series} SKU-store pairs, ` + (edge(c)
          ? `margin keeps rising as price ${c.best_price_change > 0 ? "rises" : "falls"} across the whole tested range, so read this as a direction rather than a target.`
          : `margin peaks at a ${(c.best_price_change * 100).toFixed(1)}% price change.`) + " The model assumes constant elasticity: it is reliable for moderate changes and ignores competitor reaction and cross-product effects.";
      } catch (e) { $("#s-kpis").innerHTML = `<p class="err">${esc(e.message)}</p>`; }
    };
    ["#s-cat", "#s-store", "#s-promo"].forEach((s) => $(s).addEventListener("change", run));
    $("#s-price").addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(run, 120); });
    run();
  }

  // -------------------------------------------------------------- anomalies
  async function anomalies() {
    const a = await api("/api/anomalies"), s = a.scorecard;
    const months = a.by_month.slice(-18);
    view.innerHTML = `
      <div class="stack">
        <div class="grid g-kpi">
          ${kpi("Days flagged", num(s.flagged_days), "across three years of history")}
          ${kpi("Precision", pct(s.precision, 0), "flagged days that were genuinely injected anomalies")}
          ${kpi("Recall", pct(s.recall, 0), `${s.events_found} of ${s.events} injected events detected`)}
          ${kpi("Flagged, last 180 days", num(a.recent.length), `threshold |z| > ${a.threshold}`)}
        </div>
        <div class="card"><h2>Anomalies per month</h2><p class="sub">Spikes are unexplained surges; drops include likely stock-outs (runs of zero sales).</p>
          ${legend([{ name: "Spike", color: SERIES[0], box: true }, { name: "Drop", color: SERIES[1], box: true }])}<div id="c-anom"></div></div>
        <div class="card"><h2>Recent anomalies</h2><p class="sub">Expected demand is the trailing same-weekday median, adjusted for promotions. Festival windows are excluded because those peaks are explained.</p>
          <div class="scroll" id="t-anom"></div></div>
      </div>`;
    Charts.bar($("#c-anom"), { categories: months.map((m) => m.month + "-01"), stacked: true, height: 220, xFmt: mShort,
      series: [{ name: "Spike", color: SERIES[0], values: months.map((m) => m.spike) }, { name: "Drop", color: SERIES[1], values: months.map((m) => m.drop) }] });
    table($("#t-anom"), [{ key: "date", label: "Date", fmt: dLong }, { key: "kind", label: "Type", fmt: (v) => (v === "spike" ? "▲ Spike" : "▼ Drop") },
      { key: "sku_id", label: "SKU" }, { key: "city", label: "Store" }, { key: "category", label: "Category" },
      { key: "units", label: "Actual", num: 1, fmt: (v) => num(v) }, { key: "expected", label: "Expected", num: 1, fmt: (v) => num(v, 1) },
      { key: "z", label: "z-score", num: 1, fmt: (v) => v.toFixed(1) }, { key: "revenue_impact", label: "Revenue impact", num: 1, fmt: (v) => (v < 0 ? "−" : "+") + inr(Math.abs(v)) }],
      a.recent, { sortable: true, sort: "date", limit: 400 });
  }

  // ----------------------------------------------------------------- upload
  async function upload() {
    view.innerHTML = `
      <div class="stack">
        <div class="card"><h2>Forecast your own series</h2><p class="sub">Upload a CSV with a date column and a numeric column (daily, weekly or monthly). The server fits a damped Holt-Winters model, checks it against a seasonal-naive benchmark on a hold-out, and returns a forecast. Nothing is stored.</p>
          <div class="drop"><input type="file" id="u-file" accept=".csv,text/csv"><button class="btn primary" id="u-go" type="button">Forecast</button>
            <button class="btn" id="u-sample" type="button">Try the sample series</button><a class="muted" href="/api/sample.csv">Download sample CSV</a></div>
          <p id="u-msg" class="sub" style="margin:10px 0 0"></p></div>
        <div id="u-out" class="stack"></div>
      </div>`;
    const send = async (blob, name) => {
      const msg = $("#u-msg");
      msg.className = "sub"; msg.textContent = "Fitting models…";
      const fd = new FormData();
      fd.append("file", blob, name);
      try {
        const d = await api("/api/forecast-upload", { method: "POST", body: fd });
        msg.textContent = `${num(d.n_obs)} ${d.frequency} observations · seasonal period ${d.season} · ${d.horizon}-step forecast`;
        const h = d.hist.length, f = d.forecast.length, pad = (n) => Array(n).fill(null), x = d.hist_dates.concat(d.fc_dates);
        const hold = pad(x.length), start = d.hist_dates.indexOf(d.holdout_dates[0]);
        if (start >= 0) d.holdout_pred.forEach((v, i) => { hold[start + i] = v; });
        const names = { ets: "Holt-Winters (damped)", snaive: "Seasonal naive" };
        $("#u-out").innerHTML = `
          <div class="card"><h2>Forecast</h2><p class="sub">Selected model: ${names[d.best]}. Interval is an approximate 80% band from in-sample residuals.</p>
            ${legend([{ name: "Actual", color: "var(--text-secondary)" }, { name: "Forecast", color: SERIES[0] }, { name: "Hold-out forecast", color: SERIES[1] }, { name: "80% interval", color: "var(--band)", box: true }])}<div id="c-up"></div></div>
          <div class="card"><h2>Hold-out accuracy</h2><p class="sub">Each model was fitted without the last ${d.horizon} points and scored on them.</p><div id="t-up"></div></div>`;
        Charts.line($("#c-up"), { x, height: 320, yFmt: (v) => num(v), xFmt: dShort, xTip: dLong, vline: { at: h - 1, label: "forecast starts" },
          series: [{ name: "Actual", color: "var(--text-secondary)", values: d.hist.concat(pad(f)), width: 1.6 },
            { name: "Forecast", color: SERIES[0], values: pad(h - 1).concat([d.hist[h - 1]], d.forecast) },
            { name: "Hold-out forecast", color: SERIES[1], values: hold, width: 1.6 }],
          bands: [{ name: "80% interval", lo: pad(h).concat(d.lo), hi: pad(h).concat(d.hi) }] });
        table($("#t-up"), [{ key: "model", label: "Model", fmt: (v) => names[v] + (v === d.best ? '<span class="tag champ">selected</span>' : "") },
          { key: "wape", label: "WAPE", num: 1, fmt: (v) => pct(v) }, { key: "mae", label: "MAE", num: 1, fmt: (v) => num(v, 2) },
          { key: "rmse", label: "RMSE", num: 1, fmt: (v) => num(v, 2) }, { key: "mase", label: "MASE", num: 1, fmt: (v) => v.toFixed(2) }], d.metrics);
      } catch (e) { msg.className = "sub err"; msg.textContent = e.message; $("#u-out").innerHTML = ""; }
    };
    $("#u-go").addEventListener("click", () => {
      const f = $("#u-file").files[0];
      if (!f) { $("#u-msg").className = "sub err"; $("#u-msg").textContent = "Choose a CSV file first."; return; }
      send(f, f.name);
    });
    $("#u-sample").addEventListener("click", async () => send(await (await fetch("/api/sample.csv")).blob(), "sample.csv"));
  }

  // ------------------------------------------------------------------ about
  async function about() {
    const p = await api("/api/performance");
    view.innerHTML = `<div class="card prose">
      <h2>What this is</h2>
      <p>An end-to-end demand forecasting and decision-support system for a multi-store retailer: ${num(META.n_rows)} daily observations across ${META.n_series} SKU-store series, forecast ${META.horizon} days ahead with calibrated uncertainty, then translated into replenishment and pricing decisions.</p>
      <h2>Data</h2>
      <p><b>The data is simulated.</b> Demand comes from an explicit structural model: trend, weekly and yearly seasonality, a festival calendar with moving dates, price elasticity, promotion lift, autocorrelated noise and negative-binomial counts, with stock-outs and spikes injected. Because the true elasticities and anomalies are known, the analytics can be checked against ground truth rather than taken on faith.</p>
      <h2>Forecasting</h2>
      <ul>
        <li><b>Seasonal naive</b>: the benchmark.</li>
        <li><b>Holt-Winters (damped additive ETS on the log scale)</b>, written from scratch and vectorised across series; smoothing parameters chosen per series (median α ${p.ets_params.alpha}, γ ${p.ets_params.gamma}, φ ${p.ets_params.phi}).</li>
        <li><b>Global gradient boosting</b>: one model across all series with a Poisson objective and ${META.n_features} features. It is direct and non-recursive: every demand feature is lagged by at least the horizon, so nothing leaks and no forecast is fed back as an input.</li>
        <li><b>Champion/challenger</b>: an inverse-error weighted ensemble is evaluated alongside; whichever model has the lowest out-of-sample error is promoted.</li>
      </ul>
      <h2>Uncertainty</h2>
      <p>Pinball-loss models give raw 10th and 90th percentiles. Conformalised quantile regression then widens or narrows them using errors from earlier folds, moving coverage from ${pct(p.intervals.raw_coverage)} to ${pct(p.intervals.coverage)} against an 80% target.</p>
      <h2>Evaluation</h2>
      <p>Rolling-origin backtest with four 28-day windows. The first only calibrates; the other three are reported. Ensemble weights, champion choice and the conformal correction for each window use earlier windows only.</p>
      <h2>Decisions</h2>
      <ul>
        <li><b>Inventory</b>: (s, Q) policy with safety stock sized from out-of-sample forecast error and service levels set by ABC class.</li>
        <li><b>Pricing</b>: elasticity and promotion lift from Poisson pseudo-maximum-likelihood with fixed effects and cluster-robust errors.</li>
        <li><b>Monitoring</b>: negative-binomial anomaly scores, including joint probability of zero-sales runs to catch stock-outs on slow movers.</li>
      </ul>
      <h2>Architecture</h2>
      <p>An offline pipeline (<code>python -m forecastiq.pipeline</code>) trains, backtests and writes JSON artifacts. A Flask API serves them and this dependency-free front end renders them, so the web tier starts in about a second and runs on a free 512 MB instance. Charts are hand-written SVG.</p>
      <h2>Limits</h2>
      <ul><li>Simulated data is cleaner than real point-of-sale data: no assortment changes, returns or missing days.</li>
      <li>The what-if simulator assumes constant elasticity and no cross-product cannibalisation.</li>
      <li>Festival effects are learned from only three years of history.</li></ul>
    </div>`;
  }

  // ----------------------------------------------------------------- router
  const PAGES = {
    overview: [overview, "Overview", "Where the business stands and where demand is heading."],
    forecast: [forecast, "Forecast explorer", "Drill from the whole business down to one SKU in one store."],
    models: [models, "Model performance", "How accurate the forecasts are, measured out of sample."],
    inventory: [inventory, "Inventory planning", "What to reorder, how much, and where stock is stuck."],
    pricing: [pricing, "Pricing & promotions", "How demand responds to price, and what a change would do."],
    anomalies: [anomalies, "Anomaly monitor", "Sales that the usual pattern does not explain."],
    upload: [upload, "Forecast your data", "Bring a CSV and get a forecast in seconds."],
    about: [about, "Methodology", "How it works, and what it does not do."],
  };
  async function go() {
    const page = PAGES[location.hash.slice(1)] ? location.hash.slice(1) : "overview";
    document.querySelectorAll("#nav button").forEach((b) => b.classList.toggle("on", b.dataset.page === page));
    $("#title").textContent = PAGES[page][1];
    $("#subtitle").textContent = PAGES[page][2];
    Charts.hideTip();
    view.innerHTML = '<p class="skeleton">Loading…</p>';
    try { await PAGES[page][0](); } catch (e) { view.innerHTML = `<div class="card"><p class="err">Could not load this page: ${esc(e.message)}</p></div>`; }
    window.scrollTo(0, 0);
  }

  $("#nav").addEventListener("click", (e) => { if (e.target.dataset.page) location.hash = e.target.dataset.page; });
  $("#theme").addEventListener("click", () => {
    const root = document.documentElement;
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
  });
  window.addEventListener("hashchange", go);
  (async () => {
    try {
      META = await api("/api/meta");
      $("#stamp").textContent = `Models trained ${META.generated_at}. History ${dLong(META.history[0])} – ${dLong(META.history[1])}.`;
      go();
    } catch (e) { view.innerHTML = `<div class="card"><p class="err">${esc(e.message)}</p></div>`; }
  })();
})();
