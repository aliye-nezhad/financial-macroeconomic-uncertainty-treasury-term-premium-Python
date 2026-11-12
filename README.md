# Financial and Macroeconomic Uncertainty and the U.S. Treasury Term Premium

**Python | Macro-finance | Monetary economics | Term structure | Forecast evaluation**

## Research question
Does financial-sector uncertainty contain incremental predictive information for changes in the U.S. 10-year Treasury term premium, beyond macroeconomic uncertainty and conventional monetary-policy and yield-curve indicators? Does predictive information differ between the term-premium and expected-short-rate components?

## Research status
The raw-data acquisition, monthly panel construction, source diagnostics, initial HAC regression pipeline, and expanding-window forecast pipeline are implemented. Empirical results have not yet been generated and validated by the project author.

This is a predictive project, not a causal identification design. The first forecasting exercise uses currently available revised uncertainty-index data and must be described as pseudo-out-of-sample, not genuine real-time forecasting.

## Empirical design
The primary outcome is the one-month change in the 10-year ACM term premium. The secondary outcome is the change in the ACM expected-average-short-rate component. The Kim-Wright 10-year term premium is an alternative outcome measurement.

The nested model hierarchy is:
- **M0:** AR(1) benchmark.
- **M1:** M0 plus lagged federal funds rate, change in the federal funds rate, and 10y-2y Treasury yield spread.
- **M2:** M1 plus lagged JLN macroeconomic uncertainty.
- **M3:** M2 plus lagged LMN financial uncertainty.
- **M4:** M3 plus lagged VIX, estimated on a separate common sample.

M0-M3 use the longest common sample. M0-M4 are re-estimated on the VIX-available common sample for the M3/M4 comparison. A separate hierarchy replaces the one-month uncertainty indexes with their 12-month counterparts.

The primary regressions use OLS with Newey-West/HAC standard errors (six lags initially). Forecast evaluation uses recursive expanding-window one-month-ahead forecasts with a 120-observation initial window, RMSE, MAE, out-of-sample R-squared, and Clark-West tests for nested forecasts.

See docs/research_design.md, docs/literature_review.md, and docs/data_plan.md.

## Data sources
- [New York Fed Treasury Term Premia (ACM)](https://www.newyorkfed.org/research/data_indicators/term-premia-tabs)
- [JLN and LMN Macro and Financial Uncertainty Indexes](https://www.sydneyludvigson.com/macro-and-financial-uncertainty-indexes)
- [FRED Kim-Wright 10-year term premium (THREEFYTP10)](https://fred.stlouisfed.org/series/THREEFYTP10)
- [FRED VIXCLS](https://fred.stlouisfed.org/series/VIXCLS)
- [FRED DFF](https://fred.stlouisfed.org/series/DFF)
- [FRED DGS2](https://fred.stlouisfed.org/series/DGS2)
- [FRED DGS10](https://fred.stlouisfed.org/series/DGS10)

Raw source files are downloaded locally and excluded from Git by default. The downloader records source URLs, retrieval times and SHA-256 hashes.

## Repository workflow (Windows PowerShell)
Activate the existing environment, then run:

    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    python -m pip install -e .
    python -m pytest -q
    python scripts/01_download_data.py
    python scripts/02_build_dataset.py
    python scripts/03_data_audit.py
    python scripts/04_estimate_models.py
    python scripts/05_forecast_evaluation.py

Use python scripts/01_download_data.py --refresh to request fresh source snapshots.

## Code map
- src/term_premium/data.py: source downloads, caching, hashes, source parsers, month-end alignment, ACM decomposition validation, and panel construction.
- src/term_premium/analysis.py: model specifications, common-sample validation, HAC regressions, expanding-window forecasts, forecast metrics, and Clark-West tests.
- scripts/01_download_data.py: source acquisition.
- scripts/02_build_dataset.py: processed panel construction.
- scripts/03_data_audit.py: source coverage, edge/interior missingness, monthly-index integrity, robust extreme-observation flags, correlations, pairwise counts and matched-sample diagnostics.
- src/term_premium/diagnostics.py: reusable non-destructive missingness and modified-z outlier screening.
- scripts/04_estimate_models.py: nested OLS estimation and HAC inference.
- scripts/05_forecast_evaluation.py: expanding-window forecasts, accuracy metrics, Clark-West tests and forecast plots.
- tests/: parser, timing, model, inference and forecast tests.

## Output locations
- outputs/diagnostics/: source coverage, missingness profiles, monthly-index audit, extreme-observation review flags, descriptive statistics, correlations, pairwise counts and matched-sample diagnostics.
- outputs/estimation/: regression summaries, coefficients and estimation samples.
- outputs/forecasting/: forecast series, forecast accuracy, Clark-West tests and plots.

Generated outputs and local data are not committed by default. Re-run the scripts to recreate them from the raw source snapshots.

## Interpretation guardrails
- No causal interpretation of uncertainty coefficients.
- VIX is an equity-market implied-volatility proxy, not a comprehensive uncertainty measure.
- ACM and Kim-Wright are distinct model-based estimates.
- The two-month uncertainty lag is a conservative timing convention, not a historical release-calendar reconstruction.
- Current revised data imply pseudo-out-of-sample, not genuine real-time, forecasting.
- No empirical result or novelty claim should be made before reviewing generated outputs and completing the literature review.
