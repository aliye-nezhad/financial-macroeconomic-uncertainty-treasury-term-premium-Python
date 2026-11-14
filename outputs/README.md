# Results files

The CSVs in this directory are selected aggregate results from the preserved, audited source snapshot. They correspond to the sample and specifications reported in [the empirical-results memo](../docs/empirical_results.md). They are not newly estimated from current downloads.

| File | Contents |
| --- | --- |
| [Primary forecast accuracy](forecasting/forecast_accuracy_acm_term_premium_1m.csv) | RMSE, MAE, out-of-sample R-squared and forecast counts for M0–M3 |
| [Primary Clark–West tests](forecasting/clark_west_acm_term_premium_1m.csv) | One-sided nested forecast-comparison tests |
| [Expected-short-rate forecast accuracy](forecasting/forecast_accuracy_acm_expected_short_rate_1m.csv) | Secondary ACM component |
| [Kim–Wright forecast accuracy](forecasting/forecast_accuracy_kim_wright_term_premium_1m.csv) | Alternative term-premium measure |
| [M3 influence summary](diagnostics/m3_influence_summary.csv) | Screening counts and leave-one-month-out coefficient sensitivity |
| [DFF aggregation forecast comparison](dff_aggregation_sensitivity/forecast_accuracy.csv) | Month-end versus monthly-mean DFF specifications |
| [FEDFUNDS validation](dff_aggregation_sensitivity/fedfunds_validation_summary.csv) | Check of monthly-mean DFF against the published monthly series |

The primary estimation sample comprises 602 observations from July 1976 through August 2026; the primary pseudo-out-of-sample evaluation contains 482 monthly forecasts from July 1986 through August 2026. The Kim–Wright comparison has a shorter sample.

The full pipeline writes additional outputs into these directories, including regression tables, residual diagnostics, rolling-window results, and figures. Those files are excluded from version control unless explicitly selected for publication. Run the code with the corresponding preserved raw snapshots to recreate the archived analysis. Downloading current upstream series does not guarantee identical results because some source data are revised.

The files report predictive associations, not causal effects. See the [research design](../docs/research_design.md) and [interpretation](../docs/empirical_results.md) before comparing specifications.
