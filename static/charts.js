/* Dependency-free SVG charts: line (with bands, crosshair) and bar (grouped / stacked).
   Colours are CSS custom properties, so light and dark themes swap without re-rendering. */
(function () {
  const NS = "http://www.w3.org/2000/svg";
  const el = (tag, attrs, parent) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  };
  const tipEl = () => document.getElementById("tip");
  function showTip(evt, html) {
    const t = tipEl();
    t.innerHTML = html;
    t.style.opacity = 1;
    const r = t.getBoundingClientRect();
    let x = evt.clientX + 14, y = evt.clientY + 14;
    if (x + r.width > innerWidth - 8) x = evt.clientX - r.width - 14;
    if (y + r.height > innerHeight - 8) y = evt.clientY - r.height - 14;
    t.style.left = Math.max(4, x) + "px";
    t.style.top = Math.max(4, y) + "px";
  }
  const hideTip = () => { tipEl().style.opacity = 0; };

  function ticks(min, max, n) {
    const span = max - min || 1, raw = span / (n || 5);
    const mag = Math.pow(10, Math.floor(Math.log10(raw))), norm = raw / mag;
    const step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag;
    const out = [];
    for (let v = Math.ceil(min / step - 1e-9) * step; v <= max + 1e-9; v += step) out.push(+v.toFixed(10));
    return out;
  }

  function mount(node, cfg, draw) {
    node.classList.add("chart");
    const render = () => { node.innerHTML = ""; const w = node.clientWidth; node._w = w; if (w > 0) draw(node, cfg, w); };
    render();
    if (node._ro) node._ro.disconnect();
    node._ro = new ResizeObserver(() => { if (node.clientWidth !== node._w) render(); });
    node._ro.observe(node);
  }

  const row = (color, name, val) => `<div><span><i style="background:${color}"></i>${name}</span><span>${val}</span></div>`;

  function yAxis(svg, tk, Y, m, W, fmt) {
    tk.forEach((v) => {
      el("line", { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), stroke: "var(--line-soft)", "stroke-width": 1 }, svg);
      el("text", { x: m.l - 8, y: Y(v) + 4, "text-anchor": "end" }, svg).textContent = fmt(v);
    });
  }

  function drawLine(node, c, W) {
    const H = c.height || 280, m = { l: 54, r: 16, t: 14, b: 26 };
    const n = c.x.length, iw = W - m.l - m.r, ih = H - m.t - m.b;
    const fmt = c.yFmt || ((v) => v), xFmt = c.xFmt || ((v) => v);
    const vals = [];
    c.series.forEach((s) => s.values.forEach((v) => v != null && vals.push(v)));
    (c.bands || []).forEach((b) => { b.lo.forEach((v) => v != null && vals.push(v)); b.hi.forEach((v) => v != null && vals.push(v)); });
    let hi = Math.max.apply(null, vals), lo = c.zero === false ? Math.min.apply(null, vals) : 0;
    if (c.zero === false) lo -= (hi - lo) * 0.08;
    hi += (hi - lo) * 0.06 || 1;
    const X = (i) => m.l + (n > 1 ? i / (n - 1) : 0.5) * iw;
    const Y = (v) => m.t + ih - ((v - lo) / (hi - lo)) * ih;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, height: H, role: "img", "aria-label": c.label || "Line chart" }, node);
    yAxis(svg, ticks(lo, hi, 5), Y, m, W, fmt);

    const count = Math.min(n, Math.max(2, Math.floor(iw / 96)));
    for (let k = 0; k < count; k++) {
      const i = Math.round((k * (n - 1)) / (count - 1 || 1));
      el("text", { x: X(i), y: H - 6, "text-anchor": k === 0 ? "start" : k === count - 1 ? "end" : "middle" }, svg).textContent = xFmt(c.x[i]);
    }

    const segments = (arr) => {
      const out = []; let cur = [];
      arr.forEach((v, i) => { if (v == null) { if (cur.length) out.push(cur); cur = []; } else cur.push(i); });
      if (cur.length) out.push(cur);
      return out;
    };
    (c.bands || []).forEach((b) => segments(b.lo).forEach((seg) => {
      const up = seg.map((i) => `${X(i)},${Y(b.hi[i])}`), dn = seg.slice().reverse().map((i) => `${X(i)},${Y(b.lo[i])}`);
      el("polygon", { points: up.concat(dn).join(" "), fill: b.color || "var(--band)" }, svg);
    }));
    if (c.vline) {
      el("line", { x1: X(c.vline.at), x2: X(c.vline.at), y1: m.t, y2: m.t + ih, stroke: "var(--neutral)", "stroke-dasharray": "3 4" }, svg);
      const right = X(c.vline.at) > m.l + iw * 0.6;
      el("text", { x: X(c.vline.at) + (right ? -6 : 6), y: m.t + 10, "text-anchor": right ? "end" : "start" }, svg).textContent = c.vline.label || "";
    }
    (c.marks || []).forEach((mk) => {
      el("line", { x1: X(mk.at), x2: X(mk.at), y1: m.t, y2: m.t + ih, stroke: "var(--series-2)", "stroke-dasharray": "2 3" }, svg);
      el("text", { x: X(mk.at) + 5, y: m.t + 10, "text-anchor": "start" }, svg).textContent = mk.label;
    });
    c.series.forEach((s) => segments(s.values).forEach((seg) => {
      el("path", {
        d: seg.map((i, k) => `${k ? "L" : "M"}${X(i).toFixed(1)},${Y(s.values[i]).toFixed(1)}`).join(""),
        fill: "none", stroke: s.color, "stroke-width": s.width || 2, "stroke-linejoin": "round", "stroke-linecap": "round",
        "stroke-dasharray": s.dash || "",
      }, svg);
      if (seg.length === 1) el("circle", { cx: X(seg[0]), cy: Y(s.values[seg[0]]), r: 4, fill: s.color }, svg);
    }));
    (c.points || []).forEach((p) => el("circle", { cx: X(p.at), cy: Y(p.value), r: 5, fill: p.color, stroke: "var(--surface-1)", "stroke-width": 2 }, svg));

    const cross = el("line", { y1: m.t, y2: m.t + ih, stroke: "var(--text-muted)", "stroke-width": 1, opacity: 0 }, svg);
    const dots = c.series.map((s) => el("circle", { r: 4, fill: s.color, stroke: "var(--surface-1)", "stroke-width": 2, opacity: 0 }, svg));
    const hit = el("rect", { x: m.l, y: m.t, width: iw, height: ih, fill: "transparent" }, svg);
    hit.addEventListener("mousemove", (e) => {
      const r = svg.getBoundingClientRect();
      const i = Math.max(0, Math.min(n - 1, Math.round(((e.clientX - r.left) * (W / r.width) - m.l) / iw * (n - 1))));
      cross.setAttribute("x1", X(i)); cross.setAttribute("x2", X(i)); cross.setAttribute("opacity", 1);
      let html = `<b>${(c.xTip || xFmt)(c.x[i])}</b>`;
      c.series.forEach((s, k) => {
        const v = s.values[i];
        dots[k].setAttribute("opacity", v == null ? 0 : 1);
        if (v != null) { dots[k].setAttribute("cx", X(i)); dots[k].setAttribute("cy", Y(v)); html += row(s.color, s.name, fmt(v)); }
      });
      (c.bands || []).forEach((b) => { if (b.lo[i] != null) html += row(b.color || "var(--band)", b.name || "Interval", `${fmt(b.lo[i])} - ${fmt(b.hi[i])}`); });
      showTip(e, html);
    });
    hit.addEventListener("mouseleave", () => { cross.setAttribute("opacity", 0); dots.forEach((d) => d.setAttribute("opacity", 0)); hideTip(); });
  }

  function drawBar(node, c, W) {
    const H = c.height || 260, m = { l: 54, r: 10, t: 12, b: 26 };
    const n = c.categories.length, iw = W - m.l - m.r, ih = H - m.t - m.b;
    const fmt = c.yFmt || ((v) => v), xFmt = c.xFmt || ((v) => v);
    const totals = c.categories.map((_, i) => c.stacked ? c.series.reduce((a, s) => a + (s.values[i] || 0), 0) : Math.max.apply(null, c.series.map((s) => s.values[i] || 0)));
    const hi = Math.max.apply(null, totals) * 1.06 || 1;
    const Y = (v) => m.t + ih - (v / hi) * ih;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, height: H, role: "img", "aria-label": c.label || "Bar chart" }, node);
    yAxis(svg, ticks(0, hi, 5), Y, m, W, fmt);
    const slot = iw / n, group = Math.min(slot * 0.74, c.stacked ? 26 : 26 * c.series.length + 2 * (c.series.length - 1));
    const every = Math.ceil(n / Math.max(2, Math.floor(iw / (c.labelWidth || 64))));
    c.categories.forEach((cat, i) => {
      const x0 = m.l + slot * i + (slot - group) / 2;
      const hl = el("rect", { x: m.l + slot * i, y: m.t, width: slot, height: ih, fill: "var(--surface-2)", opacity: 0 }, svg);
      if (c.stacked) {
        let acc = 0;
        c.series.forEach((s) => {
          const v = s.values[i] || 0, y1 = Y(acc + v), h = Math.max(0, Y(acc) - y1 - 2);
          if (v > 0) el("rect", { x: x0, y: y1 + (acc ? 0 : 0), width: group, height: h, fill: s.color, rx: 1.5 }, svg);
          acc += v;
        });
      } else {
        const bw = (group - 2 * (c.series.length - 1)) / c.series.length;
        c.series.forEach((s, k) => {
          const v = s.values[i] || 0, h = Math.max(1, Y(0) - Y(v)), r = Math.min(4, bw / 2, h);
          const x = x0 + k * (bw + 2), y = Y(v);
          el("path", { d: `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + bw - r}Q${x + bw},${y} ${x + bw},${y + r}V${y + h}Z`, fill: s.color }, svg);
        });
      }
      if (i % every === 0) el("text", { x: m.l + slot * (i + 0.5), y: H - 6, "text-anchor": "middle" }, svg).textContent = xFmt(cat);
      const hit = el("rect", { x: m.l + slot * i, y: m.t, width: slot, height: ih, fill: "transparent" }, svg);
      hit.addEventListener("mousemove", (e) => {
        hl.setAttribute("opacity", 0.6);
        let html = `<b>${(c.xTip || xFmt)(cat)}</b>` + c.series.map((s) => row(s.color, s.name, fmt(s.values[i] || 0))).join("");
        if (c.stacked && c.series.length > 1) html += `<div><span>Total</span><span>${fmt(totals[i])}</span></div>`;
        showTip(e, html);
      });
      hit.addEventListener("mouseleave", () => { hl.setAttribute("opacity", 0); hideTip(); });
    });
    el("line", { x1: m.l, x2: W - m.r, y1: Y(0), y2: Y(0), stroke: "var(--line)" }, svg);
  }

  window.Charts = {
    line: (node, cfg) => mount(node, cfg, drawLine),
    bar: (node, cfg) => mount(node, cfg, drawBar),
    el, showTip, hideTip, mount,
  };
})();
