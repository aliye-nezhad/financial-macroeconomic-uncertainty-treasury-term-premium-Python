# Research Design

## Project identity
**Title:** Financial and Macroeconomic Uncertainty and the U.S. Treasury Term Premium: A Pseudo-Out-of-Sample Forecasting Assessment  
**Field:** Macro-finance, monetary economics, fixed-income markets, uncertainty, time-series econometrics.  
**Status:** Data acquisition, panel construction, baseline estimation, forecasting and diagnostic/sensitivity pipelines are implemented. The baseline and supplementary empirical results, including rolling-stability, influence and DFF aggregation analyses, are summarized in [empirical_results.md](empirical_results.md). An independent clean Windows audit worktree at code commit `221a56e` completed dataset construction and scripts 03-12 from preserved raw snapshots; the 59-test suite passed on Python 3.13.15 and all 11 raw-source hashes matched. The original 12 raw-data files and 84 output files were each compared with their preserved backup copies (96/96 matches), verifying backup integrity rather than regenerated-output equivalence. GitHub Actions run #119 on merged `main` commit `06af936` passed all 59 tests on Python 3.11. Raw data and generated outputs remain local and are not committed to Git. Exact reproduction requires preserved snapshots; fresh downloads may differ because source series are revised. The forecasting exercise is pseudo-out-of-sample rather than genuine real-time, and the two-month uncertainty lag is a conservative timing convention rather than a reconstruction of historical release dates.

## Main research question
Does financial-sector uncertainty contain incremental predictive information for changes in the U.S. 10-year Treasury term premium, beyond macroeconomic uncertainty and conventional monetary-policy and yield-curve indicators?

A secondary question is whether predictive information differs between the term-premium component and the expected-average-short-rate component of long-term yields.

## Economic motivation
A long-term nominal Treasury yield can be decomposed, approximately and model-dependently, into an expected average future short-rate component and a term premium. The expected-rate component is closely connected to the expected path of monetary policy. The term premium captures compensation for bearing interest-rate risk and other model-dependent components.

Financial uncertainty may affect these components through competing channels:
- Greater uncertainty may increase required compensation for duration risk.
- Flight-to-safety demand may increase demand for Treasuries and compress yields or term premia.
- Uncertainty may change expectations about future monetary policy and the economic outlook.

The sign is therefore an empirical question. We will not impose a directional hypothesis as a condition for success.

## Hypotheses
- **H1 (incremental information):** Financial uncertainty improves forecasts of the next month's change in the 10-year term premium relative to a benchmark containing macroeconomic uncertainty and standard monetary/market predictors.
- **H2 (component specificity):** The incremental predictive content of financial uncertainty differs between the term-premium and expected-short-rate components.
- **H3 (measurement robustness):** The main forecasting conclusion is not entirely dependent on one published term-premium estimate.

These are forecasting hypotheses, not causal hypotheses.

## Variables and measurement
### Primary dependent variable
One-month-ahead change in the 10-year ACM term premium:
\[
\Delta TP^{ACM}_{t}=TP^{ACM}_{t}-TP^{ACM}_{t-1}.
\]
The forecast is formed using information dated no later than the end of month t-1, and predicts the change realised during month t.

### Secondary dependent variable
Change in the ACM expected-average-short-rate component. This assesses whether predictive information differs across the two components of the 10-year yield decomposition.

### Alternative dependent variable
Change in the 10-year Kim-Wright term premium (FRED: THREEFYTP10), aggregated to month-end. This is a robustness check, not an interchangeable measure: ACM and Kim-Wright use different model specifications and definitions.

### Uncertainty measures
- **Primary financial uncertainty:** LMN 1-month-ahead financial uncertainty (FRED: LMNUF1M).
- **Macroeconomic uncertainty comparator:** JLN 1-month-ahead macroeconomic uncertainty (FRED: JLNUM1M).
- **Market-based proxy:** VIX (VIXCLS), used as a secondary proxy/robustness measure, not as a comprehensive uncertainty measure.
- **Alternative horizon:** LMN and JLN 12-month-ahead indexes, estimated in a separate model hierarchy.

The LMN financial and JLN macroeconomic measures are produced in related but distinct research frameworks. Their levels should not be treated as directly comparable. The empirical question concerns incremental predictive content conditional on each measure's own variation.

### Monetary and market controls
- Lagged effective federal funds rate level.
- Lagged change in the effective federal funds rate.
- Lagged 10-year less 2-year Treasury yield spread.

The lagged dependent variable captures autoregressive dynamics. Additional controls will not be added mechanically.

### Federal-funds-rate aggregation sensitivity
The primary specification uses the last valid daily DFF observation in each completed month, aligning the monetary-policy control with the month-end ACM outcome. A supplementary sensitivity replaces month-end DFF with the arithmetic mean of daily DFF observations within each completed month. The resulting monthly mean is checked against FRED's official monthly FEDFUNDS series. FEDFUNDS is a validation reference only; it is not entered as a separate predictor. This exercise assesses whether the forecast results depend on the aggregation convention without changing the pre-specified M0-M3 hierarchy.

## Nested model hierarchy
All models within a given comparison use the same complete-case sample.

Let y_t be the change in the ACM term premium, y_(t-1) its one-month lag, J_(t-2) lagged JLN macroeconomic uncertainty, L_(t-2) lagged LMN financial uncertainty, and X_(t-1) the monetary/yield-curve controls.

- **M0:** y_t = constant + AR(1) term-premium change.
- **M1:** M0 plus lagged federal funds rate, lagged change in the federal funds rate, and lagged 10y-2y yield spread.
- **M2:** M1 plus lagged JLN macroeconomic uncertainty.
- **M3:** M2 plus lagged LMN financial uncertainty.
- **M4:** M3 plus lagged VIX, estimated on a separate VIX-available common sample.

M0-M3 form the primary hierarchy. M0-M4 are re-estimated on the VIX-available common sample for the M3/M4 comparison. This avoids confusing a change in sample composition with the effect of adding VIX.

The 12-month uncertainty measures replace the 1-month measures in a separate hierarchy; the two horizons are not entered simultaneously.

## Estimation and inference
- Estimate predictive regressions by OLS.
- Report Newey-West/HAC standard errors with six monthly lags initially.
- Report coefficients, standard errors, confidence intervals, p-values, sample sizes, R-squared, adjusted R-squared, Durbin-Watson statistics and Ljung-Box residual diagnostics.
- HAC inference affects standard errors and tests, not OLS point estimates or causal interpretation.


## Residual autocorrelation diagnostics
For each pre-specified regression hierarchy, inspect residual autocorrelations at lags 1-12 and report Ljung-Box Q-statistics and p-values at lags 1, 3, 6 and 12. Approximate pointwise 95% white-noise bands of plus/minus 1.96 divided by the square root of the sample size are included as a screening aid. These bands are not simultaneous confidence bands, and flagged autocorrelations are diagnostic evidence rather than an automatic instruction to add regressors or change the model. HAC standard errors do not remove residual serial correlation or repair forecast misspecification.

## Pseudo-out-of-sample forecast design
The primary exercise is a recursive expanding-window, one-month-ahead forecast:
1. Use the first 120 complete monthly observations as the initial estimation window.
2. Estimate each model using data strictly before the forecast target month.
3. Produce a one-month-ahead forecast.
4. Expand the estimation window by one observation and repeat.
5. Keep each model comparison on an identical target-month sample.

Report RMSE, MAE, mean forecast error and out-of-sample R-squared relative to the AR(1) benchmark.

For nested forecast comparisons, report Clark-West adjusted MSPE tests for M0-M1, M1-M2, M2-M3 and, in the VIX common sample, M3-M4. The implementation uses a one-sided asymptotic normal p-value and HAC standard errors for the mean adjusted loss differential. Interpret these tests cautiously given finite-sample uncertainty and recursive estimation. The sensitivity output also reports Holm and Bonferroni adjusted p-values across the 16 nested model comparisons within each HAC bandwidth. HAC bandwidths are treated as alternative covariance estimates for the same hypotheses, not as additional independent tests. This broad family adjustment is a conservative multiplicity check; interpretation must still distinguish the pre-specified primary ACM term-premium comparison from secondary component and measurement exercises.

## Component and measurement robustness
Repeat the primary hierarchy for the ACM expected-average-short-rate change, the Kim-Wright term-premium change, and the 12-month uncertainty horizon. These are robustness exercises, not pooled estimates.

## Timing and information set
The panel records the change realised during month t. Daily market predictors are aggregated to month-end and lagged one month; the DFF monthly-mean alternative is examined separately as an aggregation sensitivity and validated against FEDFUNDS. Monthly JLN/LMN uncertainty indexes are lagged two months as a conservative publication-delay convention. The model predicts the change realised during month t using the specified lagged information set.

The two-month uncertainty lag is not a reconstruction of each historical release date. Monthly uncertainty series are revised periodically. The first implementation uses the latest available vintage and is therefore **pseudo-out-of-sample**, not genuine real-time forecasting. We will not claim real-time forecasting unless historical vintages and publication availability are reconstructed.

## Interpretation and limitations
- Predictive regressions do not identify causal effects of uncertainty.
- Uncertainty indexes may be endogenous to financial and macroeconomic conditions.
- ACM and Kim-Wright term premia are estimated latent components, not directly observed prices.
- Term-premium estimates can be revised and differ across models.
- Monthly data and persistent uncertainty measures require careful treatment of serial correlation.
- Forecast comparison tests must account for nested-model structure and finite out-of-sample periods.
- Results may be sensitive to crisis episodes and sample endpoints.

## Literature positioning
The project does not claim that uncertainty and term premia have not been studied. The contribution at this stage is a transparent independent forecasting comparison of financial versus macroeconomic uncertainty, examining incremental predictive content and the decomposition into expected rates and term premia, with an alternative term-premium estimate as a measurement robustness check.

A stronger novelty claim requires a completed literature review and evidence that the exact forecasting comparison is not already covered.

## Reproducibility verification
The computational release checks are complete. The independent Windows audit used preserved raw snapshots, completed dataset construction and scripts 03-12, passed all 59 tests, and verified all 11 source hashes. The archived raw-data and output folders were copied to a separate backup and their 96 files matched their backup counterparts. This is a backup-integrity check, not a comparison between newly regenerated outputs and the archived outputs. GitHub Actions run #119 on merged `main` commit `06af936` passed all 59 tests on Python 3.11. Exact reproduction still depends on preserving the raw snapshots because source series can be revised.

## Empirical findings
The primary ACM term-premium forecast results do not show an incremental improvement from adding JLN or LMN uncertainty to the AR/monetary benchmark. The expected-short-rate component contains a secondary in-sample LMN association, but the adjusted nested forecast comparisons and absolute forecast accuracy do not support a robust predictive gain. The VIX, 12-month uncertainty, Kim-Wright, rolling-stability, influence and DFF aggregation exercises do not overturn the primary conclusion. Full results and qualifications are recorded in [empirical_results.md](empirical_results.md).


## Stability analysis

The pre-specified M0-M4 hierarchy remains unchanged. Stability checks are supplementary and do not select a replacement model based on observed results.

The first stability exercise estimates the M3 coefficient on lagged LMN financial uncertainty in overlapping 120-month rolling windows, using OLS with six-lag HAC covariance estimates. It also compares already-generated recursive one-month-ahead M2 and M3 forecasts over overlapping 120-target-month windows and reports descriptive performance by non-overlapping calendar decade. Rolling windows overlap and their coefficient intervals are not independent repeated hypothesis tests. Decade-level results are descriptive and no decade-specific significance tests are performed.

The purpose is to assess whether the full-sample coefficient and forecast comparison conceal time variation. The rolling coefficient intervals and rolling forecast metrics are descriptive; overlapping windows are not independent tests.

The primary instability question is whether M3's relative forecast performance versus M2 changes over time, not whether the regression coefficients exhibit a structural break. Parameter breaks are neither necessary nor sufficient for time variation in forecasting performance (Rossi, 2021). The current 120-month rolling comparisons are descriptive and show no persistent M3 advantage; see [empirical_results.md](empirical_results.md). The standard Giacomini-Rossi (2010) Fluctuation Test must not be applied directly to the current recursive expanding-window forecasts: Rossi and Soupre (2018) describe its implementation as requiring fixed or rolling parameter-estimation windows of fixed size and explicitly rule out recursive estimation. If formal local forecast-comparison inference is later warranted, use a separately labelled fixed/rolling-estimation forecast exercise or identify a different procedure valid for recursive forecasts. Andrews or Bai-Perron parameter-break tests are not the default next step because the primary question concerns relative forecast performance, not structural parameter breaks. Any formal test remains supplementary to M0-M4 and must be motivated independently of a favorable result.


## Observation influence and outlier review

The data audit uses robust modified-z scores to flag unusual levels and first differences. These flags are screening aids only: a large observation may represent a genuine crisis or policy episode rather than a data error, and no value is winsorized or deleted automatically.

The supplementary M3 influence exercise reports conventional OLS leverage, externally studentized residuals, Cook's distance, DFFITS and DFBETAS for the lagged LMN coefficient. Common rule-of-thumb thresholds are used to prioritize manual inspection; they are not formal tests and do not incorporate the HAC covariance estimator.

An exact leave-one-month-out exercise records how the M3 LMN OLS point estimate changes when each month is omitted in turn. This is a coefficient-influence diagnostic only. Omitting an interior month creates an irregular time index, so no HAC standard errors, p-values or forecast comparisons are calculated on these deletion samples. The full-sample model and its HAC inference remain the reference.

A flagged month is not grounds for exclusion. Review must first establish whether the source observation is erroneous, whether its date and transformation are correct, and whether the movement is economically plausible. Genuine extreme episodes remain part of the primary analysis. Any exclusion would require a documented source/data error or a separately justified design decision, not a preferred coefficient or p-value.
