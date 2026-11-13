# Financial and Macroeconomic Uncertainty and the U.S. Treasury Term Premium: A Pseudo-Out-of-Sample Forecasting Assessment

**Python | Macro-finance | Monetary economics | Term structure | Forecast evaluation**

## Research question
Does financial-sector uncertainty contain incremental predictive information for changes in the U.S. 10-year Treasury term premium, beyond macroeconomic uncertainty and conventional monetary-policy and yield-curve indicators? Does predictive information differ between the term-premium and expected-short-rate components?

## Research status
The project implements programmatic source acquisition, monthly panel construction, source diagnostics, nested OLS regressions with HAC inference, recursive expanding-window forecasts, forecast-accuracy metrics, Clark-West comparisons, and residual autocorrelation diagnostics. The pre-specified M0-M4 hierarchy remains the primary design; additional autoregressive-lag comparisons are exploratory and do not replace it.

The rolling-stability, observation-influence, alternative uncertainty-horizon, Kim-Wright measurement, VIX, and DFF aggregation exercises have been completed and are summarized in [docs/empirical_results.md](docs/empirical_results.md). The primary finding is that adding JLN and LMN uncertainty does not improve pseudo-out-of-sample forecasts of monthly changes in the 10-year ACM term premium over the AR(1)/monetary benchmark. The secondary expected-short-rate result is more nuanced but does not establish a robust forecast improvement.

The full pipeline from dataset construction through scripts 03-12 was run in an independent clean Windows audit worktree at code commit `221a56e`; all scripts completed successfully, the 59-test suite passed on Python 3.13.15, and all 11 raw-source hashes matched the manifest. The subsequent merges into `main` changed documentation only: the output-reconciliation record and the focused literature review were updated, with no changes to source code, scripts, tests, dependencies, or workflows. The latest `main` head is `f38dda3`. GitHub Actions run #121 passed all 59 tests on Python 3.11 in 4.49 seconds on its then-current `main` commit `2808114`; that run predates the two documentation-only merges and is not represented as a CI run on `f38dda3`.

The original 12 raw-data files and 84 output files each matched their preserved backup copies (96/96), verifying backup integrity. A separate reconciliation of regenerated outputs against the archived output set found 75/84 byte-identical files, one schema-only metric rename with all 40 model-by-metric comparisons matching, and eight archived paths not reproduced at their original locations. Those eight were accounted for: three diagnostic CSVs matched current canonical outputs, two legacy tables were reconstructed from preserved raw data and matched at numerical precision, the archived HAC ZIP passed CRC validation and both contained CSVs matched current HAC outputs, and two historical run logs were not regenerated. No substantive analytical discrepancy was identified. Raw data and generated outputs are not committed to Git.

This is a predictive project, not a causal identification design. The forecasting exercise uses currently revised uncertainty-index vintages and must be described as pseudo-out-of-sample, not genuine real-time forecasting.

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

See docs/research_design.md, docs/literature_review.md, docs/data_plan.md, and docs/empirical_results.md for the research design, literature positioning, data construction, and empirical results.

## Main empirical finding
For the primary ACM term-premium outcome, the AR(1) benchmark (M0) has an RMSE of 0.231417. Adding monetary controls, JLN macroeconomic uncertainty, and LMN financial uncertainty raises M3 RMSE to 0.236518; M3's out-of-sample R-squared relative to M0 is -0.044572. The M2-to-M3 Clark-West p-value is 0.340455. The results therefore do not support incremental forecast improvement from adding LMN financial uncertainty in the primary specification.

The ACM expected-short-rate component has a negative in-sample LMN coefficient with HAC p-values between 0.0106 and 0.0166, but M3 forecast RMSE (0.187538) exceeds the AR(1) benchmark (0.182450), and the broader Holm-adjusted nested forecast comparisons do not reject at the 5% level. This is a secondary, qualified result rather than evidence of a robust predictive gain.

See [docs/empirical_results.md](docs/empirical_results.md) for the full results, sensitivity analyses, and interpretation limits.

## Data sources
- [New York Fed Treasury Term Premia (ACM)](https://www.newyorkfed.org/research/data_indicators/term-premia-tabs)
- [JLN and LMN Macro and Financial Uncertainty Indexes](https://www.sydneyludvigson.com/macro-and-financial-uncertainty-indexes)
- [FRED Kim-Wright 10-year term premium (THREEFYTP10)](https://fred.stlouisfed.org/series/THREEFYTP10)
- [FRED VIXCLS](https://fred.stlouisfed.org/series/VIXCLS)
- [FRED DFF](https://fred.stlouisfed.org/series/DFF)
- [FRED FEDFUNDS](https://fred.stlouisfed.org/series/FEDFUNDS), used only to validate the monthly average of daily DFF
- [FRED DGS2](https://fred.stlouisfed.org/series/DGS2)
- [FRED DGS10](https://fred.stlouisfed.org/series/DGS10)

Raw source files are downloaded locally and excluded from Git by default. The manifest records source URLs, per-source snapshot retrieval timestamps and SHA-256 hashes. Daily observations from an incomplete final month are retained in the raw files but excluded from the processed monthly panel.

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
    python scripts/06_residual_diagnostics.py
    python scripts/07_hac_sensitivity.py
    python scripts/08_forecast_test_sensitivity.py
    python scripts/09_dynamic_specification_sensitivity.py
    python scripts/10_stability_analysis.py
    python scripts/11_influence_sensitivity.py
    python scripts/12_dff_aggregation_sensitivity.py

Use python scripts/01_download_data.py --refresh to request fresh source snapshots. Refresh replaces the cached source files and updates their manifest hashes; it does not archive the previous files. Keep a separate copy of any snapshot needed for historical-vintage comparisons.

Exact reproduction of the reported results requires the preserved raw-data snapshots and matching source manifest used for the audited run. These files are not committed to Git. If they are unavailable, running the downloader obtains current source versions; because some source series are revised, regenerated values may differ from the documented results. Do not use `--refresh` when reproducing the archived run; it replaces cached source files and updates the manifest.

## Code map
- src/term_premium/data.py: source downloads, caching, SHA-256 snapshot verification, source parsers, month-end alignment, ACM decomposition validation, and panel construction.
- src/term_premium/analysis.py: model specifications, common-sample validation, HAC regressions, expanding-window forecasts, forecast metrics, and Clark-West tests.
- scripts/01_download_data.py: source acquisition.
- scripts/02_build_dataset.py: processed panel construction.
- scripts/03_data_audit.py: source coverage, edge/interior missingness, monthly-index integrity, robust extreme-observation flags, correlations, pairwise counts and matched-sample diagnostics.
- src/term_premium/diagnostics.py: reusable non-destructive missingness and modified-z outlier screening.
- scripts/04_estimate_models.py: nested OLS estimation and HAC inference.
- scripts/05_forecast_evaluation.py: expanding-window forecasts, accuracy metrics, Clark-West tests and black-and-white forecast plots.
- scripts/06_residual_diagnostics.py: residual ACFs at lags 1-12, Ljung-Box tests at lags 1, 3, 6 and 12, and Breusch-Godfrey LM/F tests at lags 6 and 12 for every pre-specified regression hierarchy.
- scripts/07_hac_sensitivity.py: re-estimates the same pre-specified models with HAC bandwidths of 6, 12 and 18 months to assess inference sensitivity without changing OLS coefficients.
- scripts/08_forecast_test_sensitivity.py: reuses saved expanding-window forecasts to test Clark-West sensitivity at HAC bandwidths of 3, 6, 12 and 18 months, verifies the original three-lag baseline, and reports Holm and Bonferroni adjustments across nested comparisons within each bandwidth.
- scripts/09_dynamic_specification_sensitivity.py: compares exploratory autoregressive specifications using identical samples, residual diagnostics, recursive forecasts and nested Clark-West tests; it does not replace the pre-specified baseline.
- scripts/10_stability_analysis.py: examines 120-month rolling HAC estimates of the primary M3 LMN coefficient, rolling M3-versus-M2 forecast performance, and descriptive calendar-decade forecast metrics. Overlapping windows are descriptive, not independent hypothesis tests.
- scripts/11_influence_sensitivity.py: reports OLS leverage, externally studentized residuals, Cook's distance, DFFITS and focal-coefficient DFBETAS, alongside exact leave-one-month-out changes in the M3 LMN point estimate. No observations are automatically removed; deletion-sample HAC inference is not reported because an interior deletion breaks monthly spacing.
- scripts/12_dff_aggregation_sensitivity.py: compares month-end DFF with the daily monthly mean, reports the absolute-difference distribution, validates the monthly mean against official FEDFUNDS, and repeats the same estimation and forecast comparisons on identical samples.
- tests/: parser, timing, model, inference and forecast tests.

## Output locations
- outputs/diagnostics/: source coverage, missingness profiles, monthly-index audit, extreme-observation review flags, descriptive statistics, correlations, pairwise counts, matched-sample diagnostics, residual autocorrelation diagnostics, Breusch-Godfrey tests, rolling LMN coefficient estimates and influence diagnostics.
  - HAC sensitivity summaries and coefficient-inference tables.
  - Leave-one-month-out coefficient sensitivity and influence-screening summaries.
- outputs/estimation/: regression summaries, coefficients and estimation samples.
- outputs/forecasting/: forecast series, forecast accuracy, Clark-West tests, HAC sensitivity results, rolling M3-versus-M2 performance, decade summaries and black-and-white plots.
- outputs/dff_aggregation_sensitivity/: DFF monthly-average validation and aggregation-sensitivity tables.

Generated outputs and local data are not committed by default. Re-run the scripts to recreate them from the raw source snapshots.

## Interpretation guardrails
- No causal interpretation of uncertainty coefficients.
- VIX is an equity-market implied-volatility proxy, not a comprehensive uncertainty measure.
- ACM and Kim-Wright are distinct model-based estimates.
- The two-month uncertainty lag is a conservative timing convention, not a historical release-calendar reconstruction.
- Current revised data imply pseudo-out-of-sample, not genuine real-time, forecasting.
- Empirical claims must remain within the reviewed results and the stated design limitations.
- The literature review does not support a broad novelty claim; see docs/literature_review.md for the defensible scope of the project.
