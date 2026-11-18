"""Step 6: Holt-Winters (level + trend + weekly season) on the same series."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # lets Python find the forecastiq folder

from forecastiq.data import generate
from forecastiq.evaluation import wape
from forecastiq.models import HoltWinters, seasonal_naive

sales = generate()["sales"]
y = sales[sales["series_id"] == "S01|GRO-01"].sort_values("date")["units"].to_numpy()
train, test = y[:-28], y[-28:]

hw = HoltWinters().fit(train[None, -365:])        # learn from the last year
f_hw = hw.predict(28)[0]
f_naive = seasonal_naive(train[None, :], 28)[0]

a, b, g, phi = hw.params[0]
print(f"Settings it picked: alpha={a}  beta={b}  gamma={g}  phi={phi}")
print("Holt-Winters forecast, first week:", f_hw[:7].round(1))
print()
print("WAPE seasonal naive:", round(wape(test, f_naive) * 100, 1), "%")
print("WAPE Holt-Winters:  ", round(wape(test, f_hw) * 100, 1), "%")
