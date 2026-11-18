import io

import numpy as np
import pandas as pd
import pytest


@pytest.mark.parametrize("path", ["/", "/api/health", "/api/meta", "/api/overview", "/api/performance",
                                  "/api/forecast", "/api/inventory", "/api/pricing", "/api/anomalies"])
def test_endpoints_respond(client, path):
    assert client.get(path).status_code == 200


def test_forecast_nodes_are_coherent(client):
    """Bottom-up: category forecasts must add up to the total."""
    meta = client.get("/api/meta").json
    total = np.array(client.get("/api/forecast?node=total:All stores").json["forecast"])
    parts = sum(np.array(client.get(f"/api/forecast?node=category:{c}".replace("&", "%26")).json["forecast"])
                for c in meta["categories"])
    assert np.allclose(total, parts, atol=1.0)
    d = client.get("/api/forecast?node=series:S01|GRO-01").json
    assert len(d["forecast"]) == meta["horizon"]
    assert all(lo <= f <= hi for lo, f, hi in zip(d["lo"], d["forecast"], d["hi"]))
    assert client.get("/api/forecast?node=nope").status_code == 404


def test_champion_beats_the_naive_benchmark(client):
    p = client.get("/api/performance").json
    board = {r["model"]: r for r in p["leaderboard"]}
    assert board[p["champion"]]["wape"] < board["snaive"]["wape"] * 0.8
    assert board[p["champion"]]["mase"] < 1
    assert 0.70 <= p["intervals"]["coverage"] <= 0.90


def test_scenario(client):
    r = client.post("/api/scenario", json=dict(category="Apparel", store="all", price_change=-0.1, promo=False))
    assert r.status_code == 200 and r.json["result"]["units"] > r.json["result"]["base_units"]
    assert len(r.json["curve"]["margin"]) == 25
    assert client.post("/api/scenario", json=dict(price_change=3)).status_code == 400
    assert client.post("/api/scenario", json=dict(price_change="abc")).status_code == 400
    assert client.post("/api/scenario", json=dict(category="Nope", price_change=0)).status_code == 404


def _csv(freq, n):
    rng = np.random.default_rng(1)
    idx = pd.date_range("2022-01-01", periods=n, freq=freq)
    season = {"D": 7, "W-SUN": 52, "MS": 12}[freq]
    y = 200 + 40 * np.sin(2 * np.pi * np.arange(n) / season) + rng.normal(0, 5, n)
    return pd.DataFrame(dict(date=idx, sales=y.round(1))).to_csv(index=False).encode()


@pytest.mark.parametrize("freq,n,name", [("D", 200, "daily"), ("W-SUN", 300, "weekly"), ("MS", 72, "monthly")])
def test_upload_forecast(client, freq, n, name):
    r = client.post("/api/forecast-upload", data=dict(file=(io.BytesIO(_csv(freq, n)), "x.csv")))
    assert r.status_code == 200, r.json
    d = r.json
    assert d["frequency"] == name and len(d["forecast"]) == d["horizon"] == len(d["fc_dates"])
    assert all(lo <= f <= hi for lo, f, hi in zip(d["lo"], d["forecast"], d["hi"]))
    assert min(m["wape"] for m in d["metrics"]) < 0.10


@pytest.mark.parametrize("payload", [b"", b"a,b\n1,2\n", b"date,units\n2024-01-01,-5\n" * 20, b"\x00\x01\x02garbage"])
def test_upload_rejects_bad_files(client, payload):
    r = client.post("/api/forecast-upload", data=dict(file=(io.BytesIO(payload), "x.csv")))
    assert r.status_code == 400 and "error" in r.json


def test_upload_requires_file(client):
    assert client.post("/api/forecast-upload").status_code == 400
