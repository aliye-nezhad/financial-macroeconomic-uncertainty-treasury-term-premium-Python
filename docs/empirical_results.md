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

Adding AR(12), alone or alongside AR(2), does not improve out-of-sample accuracy. The full AR(1)-through-AR(12) model has the lowest AIC among some alternatives only in a limited sense, but its BIC is much higher because of the parameter count and its RMSE is the worst of the five specifications. In-sample fit is not a sufficient selection criterion.

The residual diagnostics illustrate the trade-off. M3 AR(1) rejects the Breusch-Godfrey null at six and twelve lags (p-values 0.0013 and 0.00005). Adding AR(2) alone does not remove this evidence (p-values 0.0160 and 0.00041). The AR(1)+AR(2)+AR(12) model does not reject at six or twelve lags (p-values 0.1192 and 0.2204), but still has worse forecast accuracy than the AR(1) benchmark. The full AR(12) model also has much weaker residual serial-correlation diagnostics, but worse forecast accuracy and a substantial parameter penalty.

The dynamic Clark-West p-values are exploratory and were examined after viewing the model comparisons. They should be reported with the multiplicity adjustment and must not be treated as a new pre-specified confirmatory test.

## 5. Interpretation

The current evidence does not support the primary hypothesis that LMN financial uncertainty improves pseudo-out-of-sample forecasts of monthly changes in the 10-year ACM term premium beyond the AR/monetary/JLN benchmark. The same negative forecast conclusion appears in the VIX, 12-month uncertainty and Kim-Wright measurement exercises.

The expected-short-rate component offers a potentially interesting secondary signal, but its adjusted inference and forecast-accuracy results do not justify a strong claim. Exploratory dynamic specifications show that residual diagnostics and forecast performance can point in different directions: richer lag structures can whiten residuals while worsening forecasts.

These are meaningful empirical findings. They should not be converted into a claim that uncertainty is economically irrelevant, nor into a causal statement. The conclusion is limited to this outcome definition, predictor timing, sample, model hierarchy and pseudo-out-of-sample design.

## 6. Remaining validation work

Before treating the results as final:

1. Verify the timing and data-vintage conventions against the exact source snapshots and the code that constructs lagged variables.
2. Inspect the flagged extreme observations against their source series. The diagnostic flags are screening aids; no observation should be deleted mechanically.
3. Consider whether a forecast comparison robust to structural breaks or changing forecast performance over time is warranted. Any such exercise must be pre-specified before implementation and labelled as an additional robustness analysis.
4. Re-run the updated script 09 after the latest documentation/output changes. The current uploaded output archive predates the latest script 09 reporting changes, which add Ljung-Box output and Holm/Bonferroni adjustments for its five exploratory comparisons.
5. Update this memo only after regenerated outputs have been checked.

No automatic outlier deletion, baseline replacement, causal interpretation or novelty claim is warranted.
