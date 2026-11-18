# Resume and interview notes

Every number below comes from `artifacts/performance.json` and the test suite. If you retrain or change the model, update them.

## Resume entry

**Demand Forecasting & Business Intelligence Platform** | Python, scikit-learn, NumPy, pandas, SciPy, Flask, JavaScript, Docker | [live link] | [GitHub link]

- Built an end-to-end retail demand forecasting system for 180 SKU-store series (197K daily records, simulated with known ground truth), cutting forecast error 34% against a seasonal-naive benchmark (WAPE 39.1% to 25.9%, MASE 0.71) in a rolling-origin backtest.
- Trained a global gradient-boosting model with a leakage-safe direct 28-day horizon and produced calibrated 80% prediction intervals using conformalised quantile regression (78.7% empirical coverage).
- Implemented damped Holt-Winters from scratch in vectorised NumPy and an automated champion/challenger step that selects the production model on out-of-sample error.
- Converted forecasts into decisions: ABC-XYZ segmentation, safety stock and reorder points sized from forecast error, and price elasticities estimated by Poisson regression with fixed effects and cluster-robust errors (recovered true values to within 0.06).
- Shipped a Flask REST API and a dependency-free dashboard with hand-written SVG charts, deployed on a free 512 MB instance; 32 automated tests with CI.

Shorter, two-line version:

- Built and deployed a demand forecasting platform (global gradient boosting, conformal prediction intervals, inventory and price-elasticity analytics) that cut error 34% against a seasonal-naive benchmark across 180 series; Flask API, custom dashboard, 32 tests, CI.

## Say this clearly in interviews

The data is simulated. Say so before you are asked, and explain why it is useful: the true elasticities and anomalies are known, so you could test whether the analytics recover them. Do not describe it as real company data.

## Questions you should be ready for

1. **Why did the ensemble lose?** ETS and seasonal naive cannot see price or promotions. Averaging them with a model that can pulls its forecasts toward a less informed answer. Ensembles help when members are comparably accurate and make different errors.
2. **How do you know there is no leakage?** Every demand feature is lagged at least 28 days. `tests/test_pipeline_parts.py` overwrites the last 27 days of demand and checks the forecast-window features do not change. Ensemble weights, champion choice and conformal correction for each fold use earlier folds only.
3. **Why WAPE and MASE rather than MAPE?** MAPE is undefined at zero sales and explodes on slow movers. WAPE weights by volume; MASE compares with a naive forecast and is scale-free.
4. **What is conformal prediction doing here?** Quantile models gave 76.9% coverage against an 80% target. CQR measures how far outcomes fell outside the band on held-out folds and widens the band by that quantile. It is distribution-free, but assumes the calibration data resembles the future.
5. **Why Poisson regression for elasticity?** Demand is a count with zeros. Log-linear OLS drops or distorts zeros; PPML is consistent under heteroskedasticity. Fixed effects absorb product and store differences; clustering by series handles autocorrelated errors.
6. **Why safety stock from forecast error rather than demand variance?** The forecast already explains seasonality and promotions. Stock only needs to cover what the forecast gets wrong.
7. **Why a global model?** One model learns shared patterns (weekend lift, festival build-up, price response) from all 180 series, which helps slow movers with little history of their own.
8. **What would change with real data?** Missing days, assortment changes, stock-outs censoring true demand, hierarchy reconciliation (MinT), and a retraining schedule with drift monitoring.
9. **Why 25.9% WAPE and not lower?** At SKU-store-day grain most of the remaining error is count noise. The same forecasts have 11.7% WAPE at SKU-day and 3.5% at total-day.

## Extensions worth doing

- Run it on a public dataset (M5, Favorita, Rossmann) by replacing `forecastiq/data.py`.
- Hierarchical reconciliation (MinT) instead of plain bottom-up.
- Intermittent-demand methods (Croston, TSB) for the slow movers.
- Scheduled retraining with GitHub Actions that commits fresh artifacts.
