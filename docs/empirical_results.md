# Initial Empirical Results and Interpretation

## Status and scope

This memo records the first generated and reviewed empirical results. It is a research log, not a final paper section. The original M0-M4 hierarchy remains the pre-specified baseline. The additional dynamic autoregressive comparisons are exploratory and must not be used to replace the baseline after inspecting the results.

The exercise is pseudo-out-of-sample, not genuine real-time forecasting: it uses current revised uncertainty-index vintages and a conservative two-month lag convention, not reconstructed historical release calendars.

## 1. Primary ACM term-premium outcome

The primary outcome is the one-month change in the 10-year ACM term premium. The common M0-M3 estimation sample contains 602 monthly observations, July 1976-August 2026. The expanding-window forecast evaluation contains 482 target months, July 1986-August 2026.

| Model | RMSE | MAE | OOS R-squared versus M0 |
|---|---:|---:|---:|
| M0: AR(1) | 0.231417 | 0.169517 | 0.000000 |
| M1: Monetary controls | 0.233421 | 0.170520 | -0.017389 |
| M2: + JLN uncertainty | 0.236000 | 0.171723 | -0.039999 |
| M3: + LMN financial uncertainty | 0.236518 | 0.171133 | -0.044572 |

The richer models do not improve forecast accuracy relative to the AR(1) benchmark. The M2-to-M3 Clark-West comparison has a one-sided p-value of 0.340455 at the three-lag HAC bandwidth. The result does not support incremental forecast improvement from adding LMN financial uncertainty to the primary term-premium specification.

In the primary M3 regression, the LMN coefficient is 0.063254. Its p-values under HAC bandwidths 6, 12 and 18 are 0.332470, 0.328029 and 0.289911, respectively. The coefficient is not statistically distinguishable from zero under these specifications. The lagged 10-year-minus-2-year yield spread is negative and statistically significant across these bandwidths (coefficient approximately -0.034).

## 2. Secondary outcomes and measurement checks

The ACM expected-short-rate component shows a different in-sample pattern. In M3, the LMN coefficient is -0.179358, with HAC p-values 0.010601, 0.015511 and 0.016611 for bandwidths 6, 12 and 18. However, the forecast RMSE is 0.187538 for M3 versus 0.182450 for the AR(1) benchmark; OOS R-squared is -0.056550. The M2-to-M3 Clark-West raw p-values are 0.003687, 0.004477, 0.006949 and 0.007527 for HAC bandwidths 3, 6, 12 and 18. The corresponding Holm-adjusted values across the pre-specified family of nested comparisons are 0.058986, 0.071637, 0.111185 and 0.120437. This is a potentially interesting component-specific signal, but it does not survive the broader adjustment at the 5% level and does not translate into better absolute forecast accuracy.

For the alternative Kim-Wright term-premium outcome, the M0 benchmark RMSE is 0.139502 and the M3 RMSE is 0.143748. The M2-to-M3 Clark-West p-value is 0.481160. This does not support an incremental forecasting contribution from LMN in that alternative measurement.

In the VIX-available ACM common sample (439 estimation observations; 319 forecasts, February 2000-August 2026), adding VIX also does not improve forecast accuracy. RMSE rises from 0.249290 for M0 to 0.263330 for M4. The M3-to-M4 Clark-West p-value is 0.883896.

The separate 12-month uncertainty hierarchy also fails to improve the primary forecast. RMSE rises from 0.231417 for M0 to 0.235907 for M3. The M2-to-M3 Clark-West p-value is 0.227005.

## 3. HAC inference sensitivity

The HAC sensitivity exercise re-estimates identical OLS specifications with covariance bandwidths of 6, 12 and 18 monthly lags. As expected, the OLS point estimates and conventional fit statistics do not change across bandwidths; standard errors, confidence intervals and p-values do.

For the primary ACM term-premium M3 model, the LMN coefficient remains insignificant across all three bandwidths. The negative yield-curve-slope coefficient remains statistically significant. This supports the robustness of those particular inference statements to the selected HAC bandwidths, but does not resolve residual autocorrelation or model specification concerns.

HAC standard errors change estimated uncertainty around coefficients. They do not remove serial correlation from residuals, correct forecast misspecification, or establish causality.

## 4. Exploratory dynamic specification sensitivity

Five specifications were compared on one identical 602-observation estimation sample (July 1976-August 2026), with 482 expanding-window forecasts (July 1986-August 2026). They are exploratory additions to, not replacements for, M0-M4.

| Exploratory specification | Adjusted R-squared | AIC | BIC | RMSE | OOS R-squared vs. AR(1) |
|---|---:|---:|---:|---:|---:|
| M3 AR(1) | 0.011967 | 72.80 | 103.60 | 0.236518 | 0.000000 |
| M3 AR(1), AR(2) | 0.021828 | 67.75 | 102.95 | 0.234830 | 0.014225 |
| M3 AR(1), AR(12) | 0.030330 | 62.49 | 97.70 | 0.242549 | -0.051641 |
| M3 AR(1), AR(2), AR(12) | 0.040809 | 56.94 | 96.54 | 0.240830 | -0.036793 |
| M3 AR(1)-AR(12) | 0.045259 | 62.93 | 142.14 | 0.245278 | -0.075441 |

Adding AR(2) produces a small reduction in RMSE (about 0.7%) and an OOS R-squared of 0.0142. The one-sided Clark-West p-value is 0.078953 before adjustment across the five exploratory comparisons. The Holm-adjusted p-value across those five comparisons is approximately 0.3469. This is suggestive at most, not confirmatory evidence. A descriptive decade split also shows that the AR(2) RMSE improvement is not uniform: it is marginally worse than AR(1) in the 1980s, 1990s and 2010s, and better in the 2000s and 2020s. These decade-specific comparisons are descriptive and were not separately tested.

Adding AR(12), alone or alongside AR(2), does not improve out-of-sample accuracy. The full AR(1)-through-AR(12) model has a lower AIC than the AR(1) and AR(1)+AR(2) specifications, but it does not have the lowest AIC overall. It has the highest BIC because of its parameter count and the worst RMSE of the five specifications. In-sample fit is not a sufficient selection criterion.

The residual diagnostics illustrate the trade-off. M3 AR(1) rejects the Breusch-Godfrey null at six and twelve lags (p-values 0.0013 and 0.00005). Adding AR(2) alone does not remove this evidence (p-values 0.0160 and 0.00041). The AR(1)+AR(2)+AR(12) model does not reject at six or twelve lags (p-values 0.1192 and 0.2204), but still has worse forecast accuracy than the AR(1) benchmark. The full AR(12) model also has much weaker residual serial-correlation diagnostics, but worse forecast accuracy and a substantial parameter penalty.

The dynamic Clark-West p-values are exploratory and were examined after viewing the model comparisons. They should be reported with the multiplicity adjustment and must not be treated as a new pre-specified confirmatory test.

## 5. Interpretation

The current evidence does not support the primary hypothesis that LMN financial uncertainty improves pseudo-out-of-sample forecasts of monthly changes in the 10-year ACM term premium beyond the AR/monetary/JLN benchmark. The same negative forecast conclusion appears in the VIX, 12-month uncertainty and Kim-Wright measurement exercises.

The expected-short-rate component offers a potentially interesting secondary signal, but its adjusted inference and forecast-accuracy results do not justify a strong claim. Exploratory dynamic specifications show that residual diagnostics and forecast performance can point in different directions: richer lag structures can whiten residuals while worsening forecasts.

These are meaningful empirical findings. They should not be converted into a claim that uncertainty is economically irrelevant, nor into a causal statement. The conclusion is limited to this outcome definition, predictor timing, sample, model hierarchy and pseudo-out-of-sample design.

## 6. Rolling stability

The supplementary stability script was run on the 602-observation primary ACM estimation sample (July 1976-August 2026).

The lagged LMN coefficient was re-estimated in 483 overlapping 120-month windows using OLS with six-lag HAC covariance estimates. The median rolling coefficient was 0.0764, the range was -0.3812 to 0.6397, and 66.7% of window estimates were positive. The coefficient therefore varies materially in magnitude and changes sign across windows. These overlapping estimates and their pointwise HAC intervals are descriptive; they are not independent tests of coefficient stability.

The existing recursive expanding-window forecasts were also compared in 363 overlapping 120-target-month windows. M3 had a lower RMSE than M2 in 22.3% of windows. The rolling comparison therefore does not indicate a persistent forecasting advantage from adding LMN.

| Forecast decade | Forecasts | M2 RMSE | M3 RMSE | OOS R-squared of M3 relative to M2 |
|---|---:|---:|---:|---:|
| 1980s | 42 | 0.222674 | 0.218376 | 0.038228 |
| 1990s | 120 | 0.192967 | 0.194123 | -0.012024 |
| 2000s | 120 | 0.297840 | 0.298729 | -0.005983 |
| 2010s | 120 | 0.218077 | 0.219587 | -0.013892 |
| 2020s | 80 | 0.222000 | 0.222027 | -0.000244 |

The decade comparison is descriptive. The 1980s and 2020s are partial decades, and no decade-specific significance tests were conducted. M3 performs slightly better in the first partial period, but its RMSE is marginally higher than M2 in every subsequent decade. This does not support a stable incremental forecast contribution from LMN.

## 7. Observation-influence sensitivity

The supplementary influence analysis was run on the same 602-observation M3 estimation sample.

- 84 months were flagged by at least one conventional OLS influence rule.
- February 1986 had the largest Cook's distance.
- Excluding December 2008 produced the largest absolute change in the LMN coefficient.
- The maximum absolute leave-one-month-out coefficient change was 0.027368.

The 84 flagged months are the union of several overlapping screening rules, not 84 confirmed data errors or grounds for deletion. The month with the largest Cook's distance differs from the month whose exclusion changes the focal coefficient most, illustrating that the diagnostics capture different forms of influence. The available console summary does not report the sign of the largest coefficient change or the resulting leave-one-out estimate, so no sign-reversal claim is made.

These are conventional OLS screening and point-estimate sensitivity measures. They do not use the HAC covariance estimator. No observations are removed, and no HAC inference is calculated on the gapped leave-one-month-out samples.

## 8. Decision on formal forecast-instability testing

The rolling results motivate attention to time variation, but the standard Giacomini-Rossi (2010) Fluctuation Test should not be applied directly to the current forecast series. The project's forecasts are generated recursively with an expanding estimation window. Rossi and Soupre (2018) describe the Giacomini-Rossi implementation as requiring fixed or rolling parameter-estimation windows of fixed size and explicitly rule out recursive estimation.

The current rolling M3-versus-M2 results therefore remain descriptive. If formal local forecast-comparison inference is later justified, it will require either a separately labelled fixed/rolling-estimation forecast exercise or a different procedure whose validity covers recursive estimation. Such an exercise must not replace the pre-specified expanding-window baseline or be selected because it produces a favorable result. Parameter-break tests are not a substitute for the project's relative forecast-performance question.

## 9. DFF aggregation sensitivity

The primary analysis uses the last valid daily DFF observation in each completed month. A supplementary sensitivity replaces that value with the arithmetic mean of daily DFF observations within the month. The alternative is validated against FRED's official monthly FEDFUNDS series; FEDFUNDS is not used as a model predictor.

### Validation of the monthly average

The daily-DFF monthly mean matches the official monthly FEDFUNDS series over 868 months, July 1954-October 2026. The mean absolute difference is 0.002404 percentage points, the maximum absolute difference is 0.005 percentage points, and the correlation is 0.9999997. All 868 matched months are within 0.01 percentage points, consistent with the published series' two-decimal rounding.

The absolute difference between month-end DFF and the monthly mean is not negligible in every month: across the same 868-month sample its mean is 0.2880 percentage points, median 0.10, 75th percentile 0.33, and maximum 7.44. This supports retaining month-end DFF as the primary convention when aligning predictors with the month-end ACM outcome, while reporting the monthly mean as a distinct sensitivity rather than treating the two measures as interchangeable.

### Estimation and forecast comparison

Both aggregation methods use the same 602-observation estimation sample (July 1976-August 2026) and the same 482 forecast target months (July 1986-August 2026). The M0 AR(1) forecasts are identical by construction because DFF does not enter M0.

| Aggregation | Model | RMSE | MAE | OOS R-squared vs. M0 |
|---|---|---:|---:|---:|
| Month-end | M0 AR(1) | 0.231417 | 0.169517 | 0.000000 |
| Month-end | M1 monetary | 0.233421 | 0.170520 | -0.017389 |
| Month-end | M2 + JLN | 0.236000 | 0.171723 | -0.039999 |
| Month-end | M3 + LMN | 0.236518 | 0.171133 | -0.044572 |
| Monthly mean | M0 AR(1) | 0.231417 | 0.169517 | 0.000000 |
| Monthly mean | M1 monetary | 0.233660 | 0.170215 | -0.019476 |
| Monthly mean | M2 + JLN | 0.236522 | 0.171645 | -0.044600 |
| Monthly mean | M3 + LMN | 0.236924 | 0.170498 | -0.048155 |

None of the one-sided Clark-West comparisons is statistically significant at conventional levels:

| Aggregation | Nested comparison | Clark-West p-value |
|---|---|---:|
| Month-end | M0 vs. M1 | 0.205646 |
| Month-end | M1 vs. M2 | 0.640734 |
| Month-end | M2 vs. M3 | 0.340455 |
| Monthly mean | M0 vs. M1 | 0.257830 |
| Monthly mean | M1 vs. M2 | 0.737262 |
| Monthly mean | M2 vs. M3 | 0.187645 |

The DFF aggregation choice does not change the substantive conclusion. The richer models do not improve the primary ACM term-premium forecasts relative to the AR(1) benchmark, and the LMN addition does not deliver a statistically significant nested forecast improvement. The month-end and monthly-mean DFF specifications are robustness alternatives, not competing models from which to select the more favorable result.

## 10. Remaining validation work

The rolling-stability and influence scripts have now been executed from the project author's local raw-data snapshots. Their console summaries are recorded above. The detailed CSV files and plots remain local and have not yet undergone a complete file-level review.

The remaining sequence is:

1. Re-run `scripts/03_data_audit.py`, `scripts/06_residual_diagnostics.py`, and `scripts/09_dynamic_specification_sensitivity.py` against the latest repository version. The current local audit and dynamic-sensitivity outputs were generated before the latest pull; the updated reports include matched-sample validation, Breusch-Godfrey diagnostics, and Holm/Bonferroni adjustments.
2. Confirm that the HAC and Clark-West sensitivity outputs in `scripts/07_hac_sensitivity.py` and `scripts/08_forecast_test_sensitivity.py` correspond to the current raw-data snapshots and latest code. The three-lag Clark-West results must reproduce the baseline files.
3. Review the detailed rolling coefficient, rolling forecast, influence, and leave-one-month-out CSVs and their black-and-white plots. Inspect flagged months against the original source series and economic context; do not remove genuine crisis or policy observations.
4. Verify source timing and data-vintage conventions. The two-month uncertainty-index lag remains a conservative convention, not a reconstruction of historical release dates.
5. Only consider a separate formal instability exercise after its estimation scheme and inferential assumptions have been justified. Do not apply the standard Giacomini-Rossi procedure to the existing recursive forecasts.
6. Update the empirical memo and final interpretation after the regenerated output files have been checked.

No automatic outlier deletion, baseline replacement, causal interpretation or broad novelty claim is warranted.
