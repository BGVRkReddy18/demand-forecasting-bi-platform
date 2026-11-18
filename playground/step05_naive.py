"""Step 5: the simplest forecast (seasonal naive) and how to score it."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # lets Python find the forecastiq folder

import numpy as np
from forecastiq.data import generate
from forecastiq.evaluation import mae, wape
from forecastiq.models import seasonal_naive

sales = generate()["sales"]
y = sales[sales["series_id"] == "S01|GRO-01"].sort_values("date")["units"].to_numpy()

train, test = y[:-28], y[-28:]          # hide the last 28 days: that is our "exam"
forecast = seasonal_naive(train[None, :], 28)[0]

print("Last week of training data:", train[-7:])
print("Forecast for first week:   ", forecast[:7])
print("What really happened:      ", test[:7])
print()
print("MAE  (average miss in units):", round(mae(test, forecast), 1))
print("WAPE (miss as % of volume):  ", round(wape(test, forecast) * 100, 1), "%")
