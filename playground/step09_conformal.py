"""Step 9: the idea behind conformal calibration, with made-up numbers."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # lets Python find the forecastiq folder

import numpy as np
from forecastiq.models import conformal_quantile, conformal_scores

rng = np.random.default_rng(0)
actual = rng.normal(100, 10, 2000)          # real sales vary around 100
lo, hi = np.full(2000, 95.0), np.full(2000, 105.0)   # a range that is far too narrow
ones = np.ones(2000)

inside = ((actual >= lo) & (actual <= hi)).mean()
print("Before: the range 95-105 contains the real value", round(inside * 100), "% of the time")

past, future = slice(0, 1000), slice(1000, 2000)
widen = conformal_quantile(conformal_scores(actual[past], lo[past], hi[past], ones[past]), 0.80)
print("Conformal says: widen each side by", round(widen, 1))

new_lo, new_hi = lo[future] - widen, hi[future] + widen
inside = ((actual[future] >= new_lo) & (actual[future] <= new_hi)).mean()
print(f"After: the range {95 - widen:.1f}-{105 + widen:.1f} contains it", round(inside * 100), "% of the time (target 80%)")
