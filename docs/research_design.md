# Research Design

## Project identity
**Title:** Financial Uncertainty and the U.S. Treasury Term Premium: An Out-of-Sample Forecasting Assessment  
**Field:** Macro-finance, monetary economics, fixed-income markets, uncertainty, time-series econometrics.  
**Status:** Proposed design, subject to the data audit. No results or originality claims are made.

## Main research question
Does financial-sector uncertainty contain incremental predictive information for changes in the U.S. 10-year Treasury term premium, beyond macroeconomic uncertainty and conventional monetary-policy and yield-curve indicators?

A secondary question is whether the predictive content is concentrated in the term-premium component of long-term yields rather than the expected-average-short-rate component.

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
  
    ΔTP_ACM,t = TP_ACM,t - TP_ACM,t-1

The forecast is formed using information dated no later than t-1 and predicts the change during month t.

### Secondary dependent variable
Change in the ACM expected-average-short-rate component. This is used to assess whether predictive information differs across the two components of the 10-year yield decomposition.

### Alternative dependent variable
Change in the 10-year Kim-Wright term premium (FRED: THREEFYTP10), aggregated to month-end. This is a robustness check, not an interchangeable measure: ACM and Kim-Wright use different model specifications and definitions.

### Uncertainty measures
- **Primary financial uncertainty:** LMN 1-month-ahead financial uncertainty (FRED: LMNUF1M).
- **Macroeconomic uncertainty comparator:** JLN 1-month-ahead macroeconomic uncertainty (FRED: JLNUM1M).
- **Market-based proxy:** VIX (VIXCLS), used as a secondary proxy/robustness measure, not as a comprehensive uncertainty measure.

The LMN financial and JLN macroeconomic measures are produced in related but distinct research frameworks. Their levels should not be treated as directly comparable. The empirical question concerns incremental predictive content conditional on each measure's own variation. Standardization within the estimation sample may be used for coefficient comparability, without implying common construction.

### Conventional controls
Initial candidates:
- Lagged term-premium changes.
- Change in the effective federal funds rate (DFF).
- Treasury yield-curve slope, constructed from 10-year less 2-year Treasury yields (DGS10 minus DGS2).
- Lagged macroeconomic uncertainty.

Controls will be reduced if collinearity, timing, or sample constraints make the specification unstable. We will not add predictors mechanically.

## Forecasting design
The primary exercise is a one-month-ahead pseudo-out-of-sample forecast using an expanding estimation window.

Three nested model groups:
1. **Benchmark:** autoregressive dynamics of the term-premium change.
2. **Macro-monetary benchmark:** benchmark plus macroeconomic uncertainty and selected monetary/yield-curve controls.
3. **Financial-uncertainty model:** macro-monetary benchmark plus financial uncertainty.

VIX enters a separate proxy specification. It is not added automatically to the primary model because VIX and the broad LMN financial uncertainty measure may capture overlapping information.

The main comparison is whether the financial-uncertainty model improves forecast performance over the macro-monetary benchmark.

Evaluation metrics:
- RMSE.
- MAE.
- Out-of-sample R-squared relative to the benchmark.
- A forecast comparison test appropriate for nested models, with its assumptions and implementation documented.

A one-month horizon is chosen for the initial project to keep timing transparent. Longer horizons may be considered only after the one-month design is validated.

## Timing and information set
The forecast-origin convention must be explicit. The analysis panel records the realised change during month t. Daily market predictors are aggregated to month-end and lagged one month; monthly JLN/LMN uncertainty indexes are lagged two months as a conservative publication-delay convention. This means that at the end of month t-1 the model predicts the term-premium change realised during month t. Daily series are converted to month-end observations, not monthly averages, to align with the New York Fed ACM monthly end-of-month estimates. The two-month uncertainty lag is a conservative convention, not a reconstruction of each historical release date.

Monthly uncertainty series are currently revised and updated periodically. The first implementation uses the latest available vintage and is therefore a **pseudo-out-of-sample exercise**, not a genuine real-time forecasting exercise. We will not claim real-time forecasting unless historical vintages and publication availability are reconstructed.

For unemployment or other delayed-release macro controls, use an additional lag or exclude them from the baseline unless the information set can be documented.

## Inference and limitations
- Predictive regressions do not identify causal effects of uncertainty.
- Uncertainty indexes may be endogenous to financial and macroeconomic conditions.
- ACM and Kim-Wright term premia are estimated latent components, not directly observed prices.
- Term-premium estimates can be revised and differ across models.
- Monthly data and persistent uncertainty measures require careful treatment of serial correlation.
- Forecast comparison tests must account for nested-model structure and the finite out-of-sample period.
- Results may be sensitive to crisis episodes and sample endpoints.

## Literature positioning
The project does not claim that uncertainty and term premia have not been studied. The contribution at this stage is a transparent independent forecasting comparison of financial versus macroeconomic uncertainty, examining incremental predictive content and the decomposition into expected rates and term premia, with an alternative term-premium estimate as a measurement robustness check.

A stronger novelty claim would require a completed literature review and evidence that the exact comparison is not already covered.

## Decision gates
Do not proceed to final estimation until:
1. All source series download reproducibly.
2. The ACM workbook structure and variable definitions are verified.
3. The common sample and missingness are documented.
4. Daily-to-month-end alignment is tested.
5. Forecast-origin and outcome timing are tested with a small hand-checked example.
6. Uncertainty definitions and vintage/revision practices are documented.
