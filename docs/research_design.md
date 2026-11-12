# Research Design

## Project identity
**Title:** Financial Uncertainty and the U.S. Treasury Term Premium: An Out-of-Sample Forecasting Assessment  
**Field:** Macro-finance, monetary economics, fixed-income markets, uncertainty, time-series econometrics.  
**Status:** Data pipeline and initial estimation/forecasting implementation. Empirical results remain to be generated and validated.

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

For nested forecast comparisons, report Clark-West adjusted MSPE tests for M0-M1, M1-M2, M2-M3 and, in the VIX common sample, M3-M4. The implementation uses a one-sided asymptotic normal p-value and HAC standard errors for the mean adjusted loss differential. Interpret these tests cautiously given finite-sample uncertainty and recursive estimation.

## Component and measurement robustness
Repeat the primary hierarchy for the ACM expected-average-short-rate change, the Kim-Wright term-premium change, and the 12-month uncertainty horizon. These are robustness exercises, not pooled estimates.

## Timing and information set
The panel records the change realised during month t. Daily market predictors are aggregated to month-end and lagged one month; monthly JLN/LMN uncertainty indexes are lagged two months as a conservative publication-delay convention. The model predicts the change realised during month t using the specified lagged information set.

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

## Reproducibility decision gates
Before interpreting results, confirm source downloads, ACM definitions, common samples, frequency alignment, forecast timing, vintage practices, test results, and plausibility of generated outputs.
