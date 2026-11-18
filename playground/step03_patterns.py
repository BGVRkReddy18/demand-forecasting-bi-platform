"""Step 3: check that the patterns we put in the data are really there."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # lets Python find the forecastiq folder

from forecastiq.data import generate

sales = generate()["sales"]

print("Average units sold, by day of week (0 = Monday, 6 = Sunday):")
print(sales.groupby(sales["date"].dt.dayofweek)["units"].mean().round(1))
print()
print("Average units: normal days vs promotion days")
print(sales.groupby("promo")["units"].mean().round(1))
print()
near = sales["days_from_major"].between(-7, 0)
print("Average units in the week before Diwali:", round(sales.loc[near, "units"].mean(), 1))
print("Average units on all other days:        ", round(sales.loc[~near, "units"].mean(), 1))
print()
print("How many days had zero sales:", int((sales["units"] == 0).sum()))
print("Hidden problem days planted by the simulator:", int(sales["anomaly_truth"].sum()))
