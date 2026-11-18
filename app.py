"""ForecastIQ web application: REST API + single-page dashboard.

The app only reads pre-computed JSON artifacts (see forecastiq/pipeline.py),
so it starts in about a second and fits comfortably in a free 512 MB instance.
"""
from __future__ import annotations

import json
import os

import pandas as pd
from flask import Flask, Response, jsonify, render_template, request

from forecastiq import __version__
from forecastiq import analytics as A
from forecastiq.config import ARTIFACT_DIR
from forecastiq.quick import UploadError, forecast_series, parse_csv

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
app.json.sort_keys = False

NAMES = ["meta", "overview", "performance", "forecast", "inventory", "pricing", "anomalies"]
STORE: dict = {}


def load_artifacts() -> None:
    missing = [n for n in NAMES if not (ARTIFACT_DIR / f"{n}.json").exists()]
    if missing:
        raise RuntimeError(f"Missing artifacts {missing}. Run:  python -m forecastiq.pipeline")
    for n in NAMES:
        STORE[n] = json.loads((ARTIFACT_DIR / f"{n}.json").read_text())
    STORE["scenario_base"] = pd.DataFrame(STORE["pricing"]["scenario_base"])
    STORE["response"] = {r["category"]: r for r in STORE["pricing"]["response"]}
    STORE["nodes"] = [dict(id=k, level=v["level"], label=v["label"]) for k, v in STORE["forecast"].items()]


load_artifacts()


@app.get("/")
def index():
    return render_template("index.html", version=__version__)


@app.get("/api/health")
def health():
    return jsonify(status="ok", version=__version__, generated_at=STORE["meta"]["generated_at"])


@app.get("/api/meta")
def meta():
    return jsonify(dict(STORE["meta"], nodes=STORE["nodes"]))


@app.get("/api/overview")
def overview():
    return jsonify(STORE["overview"])


@app.get("/api/performance")
def performance():
    return jsonify(STORE["performance"])


@app.get("/api/forecast")
def forecast():
    node = request.args.get("node", "total:All stores")
    if node not in STORE["forecast"]:
        return jsonify(error=f"Unknown node '{node}'."), 404
    return jsonify(STORE["forecast"][node])


@app.get("/api/inventory")
def inventory():
    return jsonify(STORE["inventory"])


@app.get("/api/pricing")
def pricing():
    return jsonify(response=STORE["pricing"]["response"])


@app.get("/api/anomalies")
def anomalies():
    return jsonify(STORE["anomalies"])


@app.post("/api/scenario")
def scenario():
    body = request.get_json(silent=True) or {}
    try:
        change = float(body.get("price_change", 0))
    except (TypeError, ValueError):
        return jsonify(error="price_change must be a number."), 400
    if not -0.5 <= change <= 0.5:
        return jsonify(error="price_change must be between -0.5 and 0.5."), 400
    promo = bool(body.get("promo", False))
    base = STORE["scenario_base"]
    if body.get("category") and body["category"] != "all":
        base = base[base.category == body["category"]]
    if body.get("store") and body["store"] != "all":
        base = base[base.store_id == body["store"]]
    if base.empty:
        return jsonify(error="No products match that selection."), 404
    return jsonify(result=A.simulate(base, change, promo, STORE["response"]),
                   curve=A.profit_curve(base, promo, STORE["response"]), n_series=int(len(base)))


@app.post("/api/forecast-upload")
def forecast_upload():
    f = request.files.get("file")
    if f is None:
        return jsonify(error="Attach a CSV file in the 'file' field."), 400
    try:
        return jsonify(forecast_series(parse_csv(f.read())))
    except UploadError as exc:
        return jsonify(error=str(exc)), 400


@app.get("/api/sample.csv")
def sample_csv():
    node = STORE["forecast"]["category:Apparel"]
    rows = "date,units\n" + "\n".join(f"{d},{v}" for d, v in zip(node["hist_dates"], node["hist"]))
    return Response(rows, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=sample_demand.csv"})


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="File is larger than 2 MB."), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)), debug=False)
