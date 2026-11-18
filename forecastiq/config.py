"""Central configuration. Everything that defines an experiment lives here."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = ROOT / "artifacts"

SEED = 42
START = "2023-11-01"
END = "2026-10-31"            # last day of observed history
HORIZON = 28                  # forecast horizon in days
N_FOLDS = 4                   # fold 0 is calibration-only, folds 1..3 are reported
SEASON = 7                    # weekly seasonality for classical models
QUANTILES = (0.1, 0.5, 0.9)   # 80% prediction interval
COVERAGE = 0.80

CURRENCY = "INR"

# Inventory policy assumptions
HOLDING_RATE = 0.20           # annual holding cost as a share of unit cost
ORDER_COST = 500.0            # fixed cost per replenishment order (INR)
SERVICE_LEVEL = {"A": 0.98, "B": 0.95, "C": 0.90}
OVERSTOCK_DAYS = 60

STORES = [
    # id, city, region, size multiplier, annual growth
    ("S01", "Bengaluru", "South", 1.30, 0.10),
    ("S02", "Hyderabad", "South", 1.00, 0.07),
    ("S03", "Chennai", "South", 0.85, 0.02),
    ("S04", "Mumbai", "West", 1.45, 0.05),
    ("S05", "Pune", "West", 0.75, 0.12),
    ("S06", "Delhi", "North", 1.20, -0.02),
]

# name -> generator parameters. `elasticity` and `promo_lift` are the ground
# truth the analytics layer is later asked to recover from data alone.
CATEGORIES = {
    "Grocery":        dict(n=6, demand=(40, 120), price=(40, 400),     margin=0.18, elasticity=-0.8, promo_lift=0.10, weekend=0.18, yearly=0.05, peak_doy=300, diwali=0.35, lead=(2, 4)),
    "Personal Care":  dict(n=6, demand=(15, 50),  price=(100, 600),    margin=0.30, elasticity=-1.1, promo_lift=0.14, weekend=0.12, yearly=0.08, peak_doy=150, diwali=0.20, lead=(4, 7)),
    "Home & Kitchen": dict(n=6, demand=(6, 25),   price=(300, 3000),   margin=0.35, elasticity=-1.4, promo_lift=0.18, weekend=0.30, yearly=0.15, peak_doy=295, diwali=0.60, lead=(6, 10)),
    "Apparel":        dict(n=6, demand=(5, 20),   price=(500, 3000),   margin=0.45, elasticity=-1.8, promo_lift=0.22, weekend=0.40, yearly=0.30, peak_doy=330, diwali=0.70, lead=(7, 12)),
    "Electronics":    dict(n=6, demand=(1.5, 8),  price=(1500, 12000), margin=0.15, elasticity=-2.2, promo_lift=0.25, weekend=0.35, yearly=0.20, peak_doy=305, diwali=0.90, lead=(8, 14)),
}

# Festival / public holiday calendar (dates of moving festivals are approximate).
HOLIDAYS = {
    "Diwali":           ["2023-11-12", "2024-11-01", "2025-10-20", "2026-11-08"],
    "Dussehra":         ["2024-10-12", "2025-10-02", "2026-10-20"],
    "Holi":             ["2024-03-25", "2025-03-14", "2026-03-04"],
    "Eid al-Fitr":      ["2024-04-11", "2025-03-31", "2026-03-20"],
    "Raksha Bandhan":   ["2024-08-19", "2025-08-09", "2026-08-28"],
    "Ganesh Chaturthi": ["2024-09-07", "2025-08-27", "2026-09-14"],
    "Independence Day": ["2024-08-15", "2025-08-15", "2026-08-15"],
    "Republic Day":     ["2024-01-26", "2025-01-26", "2026-01-26"],
    "Christmas":        ["2023-12-25", "2024-12-25", "2025-12-25"],
    "New Year":         ["2024-01-01", "2025-01-01", "2026-01-01"],
    "Pongal":           ["2024-01-15", "2025-01-14", "2026-01-14"],
}
MAJOR_HOLIDAY = "Diwali"
