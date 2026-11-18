"""Step 10: the business analysis. Takes about 15-30 seconds."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # lets Python find the forecastiq folder

import json
import pandas as pd
from forecastiq import analytics as A
from forecastiq.data import generate

data = generate()
sales = data["sales"]

print("1) ABC-XYZ: how many product-store pairs in each group")
seg = A.abc_xyz(sales)
print(pd.crosstab(seg["abc"], seg["xyz"]))
print()

print("2) Price sensitivity: our estimate vs the truth we planted")
for r in A.price_response(sales, data["truth"]):
    print(f"   {r['category']:15s} estimate {r['elasticity']:.2f}   truth {r['elasticity_true']:.2f}")
print()

print("3) Anomaly detector score")
det = A.detect_anomalies(sales)
s = A.anomaly_scorecard(det, data["truth"]["anomalies"])
print(f"   precision {s['precision']:.0%}   recall {s['recall']:.0%}   ({s['events_found']} of {s['events']} found)")
print()

print("4) One line of the inventory plan (from artifacts/inventory.json)")
rows = json.load(open("artifacts/inventory.json"))["rows"]
r = next(x for x in rows if x["series_id"] == "S01|APP-02")
for k in ["on_hand", "daily_forecast", "lead_time", "safety_stock", "reorder_point", "days_cover", "status", "order_qty"]:
    print(f"   {k:15s} {r[k]}")
