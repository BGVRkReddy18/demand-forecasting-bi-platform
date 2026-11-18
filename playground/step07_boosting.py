"""Step 7: train the global gradient-boosting model and compare all three.
Takes about 20-40 seconds."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # lets Python find the forecastiq folder

import time
import pandas as pd
from forecastiq.data import generate
from forecastiq.evaluation import wape
from forecastiq.features import build_features
from forecastiq.pipeline import predict_window

data = generate()
feats = build_features(pd.concat([data["sales"], data["future"]], ignore_index=True))

cutoff = pd.Timestamp("2026-10-03")      # pretend today is 3 Oct; forecast 4-31 Oct
t = time.time()
out, gbm, test, ets = predict_window(feats, cutoff)
print("Trained and forecast 180 series in", round(time.time() - t), "seconds")
print()
for name in ["snaive", "ets", "gbm"]:
    print(f"{name:7s} WAPE = {wape(out['actual'], out[name]) * 100:.1f} %")
print()
one = out[out["series_id"] == "S01|APP-01"].head(7)
one = one.assign(date=one["date"].dt.strftime("%d %b"))
print(one[["date", "actual", "snaive", "ets", "gbm", "promo"]].round(1).to_string(index=False))
