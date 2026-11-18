"""Step 2: make the data and look at it."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # lets Python find the forecastiq folder

from forecastiq.data import generate

data = generate()                 # runs the simulator (about 1 second)
sales = data["sales"]             # the main table

print("Rows and columns:", sales.shape)
print()
print("First 5 rows (a few columns):")
print(sales[["date", "store_id", "sku_id", "category", "units", "price", "promo"]].head())
print()
print("Number of product-store series:", sales["series_id"].nunique())
print("First day:", sales["date"].min().date(), "  Last day:", sales["date"].max().date())
print()
print("Revenue by category over 3 years (in crore rupees):")
print((sales.groupby("category")["revenue"].sum() / 1e7).round(1))

# Save one series to a CSV file you can open in Numbers or Excel and chart yourself
one = sales[sales["series_id"] == "S01|GRO-01"][["date", "units", "price", "promo"]]
one.to_csv("playground/one_series.csv", index=False)
print()
print("Saved playground/one_series.csv with", len(one), "rows")
