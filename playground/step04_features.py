"""Step 4: build the features (clues) and check the 28-day rule by hand."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # lets Python find the forecastiq folder

import pandas as pd
from forecastiq.data import generate
from forecastiq.features import FEATURES, build_features

data = generate()
sales = data["sales"]
one = sales[sales["series_id"] == "S01|GRO-01"]            # just one series, so it is quick
feats = build_features(one)

print("Number of features:", len(FEATURES))
print(FEATURES[:8], "...")
print()
day = pd.Timestamp("2026-10-31")
row = feats[feats["date"] == day].iloc[0]
earlier = one[one["date"] == day - pd.Timedelta(days=28)]["units"].iloc[0]
print("On", day.date(), "lag_28 =", row["lag_28"])
print("Actual sales 28 days earlier (", (day - pd.Timedelta(days=28)).date(), ") =", earlier)
print("Same number?", row["lag_28"] == earlier)
print()
print("A few clues for that day:")
print(row[["lag_28", "roll_mean_28", "rel_price", "promo", "dow", "days_from_major"]])
