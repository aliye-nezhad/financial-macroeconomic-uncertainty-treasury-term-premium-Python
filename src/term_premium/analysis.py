"""Reusable estimation and pseudo-out-of-sample forecasting routines.

The module keeps model definitions, common-sample construction, HAC inference,
expanding-window forecasts, and nested forecast-comparison tests in one place.
It deliberately makes no causal-identification claim.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm
from statsmodels.stats.diagnostic import (\n    acorr_breusch_godfrey,\n    acorr_ljungbox,\n)
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.stattools import acf


MONETARY_CONTROLS = [
    "dff_lag1",
    "dff_change_lag1",
    "yield_curve_slope_10y2y_lag1",
]


def build_model_specs(
    *,
    ar_lag: str,
    uncertainty_horizon: str = "1m",
    include_vix: bool = False,
) -> dict[str, list[str]]:
    """Return nested model specifications for a chosen outcome and horizon.

    M0 is an AR(1) benchmark. M1 adds monetary/yield-curve controls. M2 adds
    JLN macroeconomic uncertainty. M3 adds LMN financial uncertainty. M4 adds
    VIX and is only included when requested.

    The uncertainty horizon is either "1m" or "12m". The two horizons are
    estimated as separate model hierarchies, never entered together.
    """
    horizon = uncertainty_horizon.lower()
    if horizon not in {"1m", "12m"}:
        raise ValueError("uncertainty_horizon must be '1m' or '12m'.")

    jln = f"jlnum{horizon}_lag2"
    lmn = f"lmnuf{horizon}_lag2"

    specs: dict[str, list[str]] = {
        "M0_AR1": [ar_lag],
        "M1_MONETARY": [ar_lag, *MONETARY_CONTROLS],
        f"M2_PLUS_JLN_{horizon.upper()}": [
            ar_lag, *MONETARY_CONTROLS, jln
        ],
        f"M3_PLUS_LMN_{horizon.upper()}": [
            ar_lag, *MONETARY_CONTROLS, jln, lmn
        ],
    }
    if include_vix:
        specs["M4_PLUS_VIX"] = [
            ar_lag, *MONETARY_CONTROLS, jln, lmn, "vixcls_lag1"
        ]
    return specs


def common_complete_sample(
    panel: pd.DataFrame,
    *,
    outcome: str,
    model_specs: Mapping[str, Sequence[str]],
) -> pd.DataFrame:
    """Return one common, finite, consecutive monthly sample for all models.

    Enforcing a consecutive monthly index is important: otherwise an
    expanding-window forecast could silently skip a month and cease to be a
    one-month-ahead forecast.
    """
    predictors = list(
        dict.fromkeys(
            predictor
            for specification in model_specs.values()
            for predictor in specification
        )
    )
    required = list(dict.fromkeys([outcome, *predictors]))
    missing = [column for column in required if column not in panel.columns]
    if missing:
        raise KeyError(f"Panel is missing required model variables: {missing}")

    if not isinstance(panel.index, pd.PeriodIndex):
        raise TypeError("The panel must use a monthly pandas PeriodIndex.")
    if panel.index.freqstr not in {"M", "ME"}:
        raise ValueError("The panel PeriodIndex must have monthly frequency.")
    if not panel.index.is_unique or not panel.index.is_monotonic_increasing:
        raise ValueError("The panel monthly index must be unique and sorted.")

    sample = panel.loc[:, required].copy()
    for column in required:
        sample[column] = pd.to_numeric(sample[column], errors="coerce")
    sample = sample.replace([np.inf, -np.inf], np.nan).dropna()

    if sample.empty:
        raise ValueError("No complete observations remain for this model set.")

    expected = pd.period_range(
        start=sample.index.min(),
        end=sample.index.max(),
        freq="M",
    )
    if not sample.index.equals(expected):
        missing_months = expected.difference(sample.index)
        preview = [str(month) for month in missing_months[:5]]
        raise ValueError(
            "The common estimation sample contains internal missing months. "
            "Do not treat non-consecutive observations as one-month-ahead "
            f"forecasts. First missing months: {preview}"
        )
    return sample


def fit_hac_model_set(
    sample: pd.DataFrame,
    *,
    outcome: str,
    model_specs: Mapping[str, Sequence[str]],
    hac_lags: int = 6,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Estimate nested OLS models with Newey-West/HAC standard errors.

    All models must use the same preconstructed common sample. HAC inference
    affects reported standard errors and tests, not the OLS point estimates.
    """
    if hac_lags < 0:
        raise ValueError("hac_lags must be non-negative.")
    if outcome not in sample:
        raise KeyError(f"Outcome {outcome!r} is not in the supplied sample.")

    summary_rows: list[dict[str, object]] = []
    coefficient_rows: list[dict[str, object]] = []
    y = sample[outcome].astype(float)

    for model_id, predictors_sequence in model_specs.items():
        predictors = list(predictors_sequence)
        if not predictors:
            raise ValueError(f"{model_id} has no regressors.")
        X = sm.add_constant(sample[predictors].astype(float), has_constant="add")
        fitted = sm.OLS(y, X, missing="raise").fit(
            cov_type="HAC",
            cov_kwds={"maxlags": hac_lags},
            use_t=True,
        )

        residuals = pd.Series(fitted.resid, index=sample.index)
        ljung_lags = min(6, max(1, len(residuals) // 10))
        ljung_box = acorr_ljungbox(
            residuals,
            lags=[ljung_lags],
            return_df=True,
        )

        summary_rows.append(
            {
                "model": model_id,
                "outcome": outcome,
                "nobs": int(fitted.nobs),
                "first_month": str(sample.index.min()),
                "last_month": str(sample.index.max()),
                "predictors": ";".join(predictors),
                "r_squared": float(fitted.rsquared),
                "adjusted_r_squared": float(fitted.rsquared_adj),
                "aic": float(fitted.aic),
                "bic": float(fitted.bic),
                "durbin_watson": float(durbin_watson(residuals)),
                "ljung_box_lag": int(ljung_lags),
                "ljung_box_pvalue": float(ljung_box["lb_pvalue"].iloc[0]),
                "hac_maxlags": int(hac_lags),
            }
        )

        confidence_intervals = fitted.conf_int()
        for variable in fitted.params.index:
            coefficient_rows.append(
                {
                    "model": model_id,
                    "outcome": outcome,
                    "variable": variable,
                    "coefficient": float(fitted.params[variable]),
                    "hac_standard_error": float(fitted.bse[variable]),
                    "t_statistic": float(fitted.tvalues[variable]),
                    "p_value": float(fitted.pvalues[variable]),
                    "confidence_interval_low": float(
                        confidence_intervals.loc[variable, 0]
                    ),
                    "confidence_interval_high": float(
                        confidence_intervals.loc[variable, 1]
                    ),
                    "nobs": int(fitted.nobs),
                    "hac_maxlags": int(hac_lags),
                }
            )

    return pd.DataFrame(summary_rows), pd.DataFrame(coefficient_rows)



def residual_diagnostic_table(
    sample: pd.DataFrame,
    *,
    outcome: str,
    model_specs: Mapping[str, Sequence[str]],
    ljung_box_lags: Sequence[int] = (1, 3, 6, 12),
    acf_max_lag: int = 12,
) -> pd.DataFrame:
    """Report residual ACFs and Ljung-Box tests for a common model sample.

    The OLS residuals are used for diagnostics; HAC covariance estimation
    does not change fitted values or residuals. The ACF bands are approximate
    pointwise white-noise screening bands, not simultaneous confidence bands.
    """
    if not model_specs:
        raise ValueError("At least one model specification is required.")
    if acf_max_lag < 1:
        raise ValueError("acf_max_lag must be at least 1.")

    requested_lags = sorted({int(lag) for lag in ljung_box_lags})
    if not requested_lags or any(lag < 1 for lag in requested_lags):
        raise ValueError("Ljung-Box lags must be positive integers.")
    if max(requested_lags) > acf_max_lag:
        raise ValueError("acf_max_lag must cover every requested Ljung-Box lag.")

    validated = common_complete_sample(
        sample,
        outcome=outcome,
        model_specs=model_specs,
    )
    if len(validated) <= acf_max_lag:
        raise ValueError(
            "The sample must contain more observations than acf_max_lag."
        )

    band = 1.96 / np.sqrt(len(validated))
    rows: list[dict[str, object]] = []

    for model_id, predictors_sequence in model_specs.items():
        predictors = list(predictors_sequence)
        if not predictors:
            raise ValueError(f"{model_id} has no regressors.")

        X = sm.add_constant(
            validated[predictors].astype(float),
            has_constant="add",
        )
        fitted = sm.OLS(
            validated[outcome].astype(float),
            X,
            missing="raise",
        ).fit()
        residuals = np.asarray(fitted.resid, dtype=float)

        acf_values = acf(
            residuals,
            nlags=acf_max_lag,
            fft=False,
            missing="raise",
        )
        lb = acorr_ljungbox(
            residuals,
            lags=requested_lags,
            return_df=True,
        )
        lb_lookup = {
            int(lag): (
                float(lb.loc[lag, "lb_stat"]),
                float(lb.loc[lag, "lb_pvalue"]),
            )
            for lag in requested_lags
        }

        for lag in range(1, acf_max_lag + 1):
            q_stat, q_pvalue = lb_lookup.get(lag, (np.nan, np.nan))
            rho = float(acf_values[lag])
            rows.append(
                {
                    "model": model_id,
                    "outcome": outcome,
                    "nobs": int(fitted.nobs),
                    "lag": lag,
                    "residual_acf": rho,
                    "acf_95pct_lower": -float(band),
                    "acf_95pct_upper": float(band),
                    "acf_outside_95pct_band": bool(abs(rho) > band),
                    "ljung_box_q_stat": q_stat,
                    "ljung_box_pvalue": q_pvalue,
                }
            )

    return pd.DataFrame(rows)



def breusch_godfrey_diagnostic_table(
    sample: pd.DataFrame,
    *,
    outcome: str,
    model_specs: Mapping[str, Sequence[str]],
    lags: Sequence[int] = (6, 12),
) -> pd.DataFrame:
    """Run Breusch-Godfrey LM and F tests on each OLS model.

    The test is applied to the OLS residuals and original regressors. HAC
    covariance estimation is not used in this auxiliary serial-correlation
    test. Results are reported separately from the ACF/Ljung-Box screening
    diagnostics.
    """
    if not model_specs:
        raise ValueError("At least one model specification is required.")

    requested_lags = sorted({int(lag) for lag in lags})
    if not requested_lags or any(lag < 1 for lag in requested_lags):
        raise ValueError("Breusch-Godfrey lags must be positive integers.")

    validated = common_complete_sample(
        sample,
        outcome=outcome,
        model_specs=model_specs,
    )
    if max(requested_lags) >= len(validated):
        raise ValueError(
            "The sample must contain more observations than the largest "
            "Breusch-Godfrey lag."
        )

    y = validated[outcome].astype(float)
    rows: list[dict[str, object]] = []

    for model_id, predictors_sequence in model_specs.items():
        predictors = list(predictors_sequence)
        if not predictors:
            raise ValueError(f"{model_id} has no regressors.")

        X = sm.add_constant(
            validated[predictors].astype(float),
            has_constant="add",
        )
        fitted = sm.OLS(y, X, missing="raise").fit()

        for lag in requested_lags:
            lm_stat, lm_pvalue, f_stat, f_pvalue = (
                acorr_breusch_godfrey(
                    fitted,
                    nlags=lag,
                    result_object=False,
                )
            )
            rows.append(
                {
                    "model": model_id,
                    "outcome": outcome,
                    "nobs": int(fitted.nobs),
                    "lag": lag,
                    "lm_stat": float(lm_stat),
                    "lm_pvalue": float(lm_pvalue),
                    "f_stat": float(f_stat),
                    "f_pvalue": float(f_pvalue),
                }
            )

    return pd.DataFrame(rows)


def expanding_window_forecasts(
    panel: pd.DataFrame,
    *,
    outcome: str,
    model_specs: Mapping[str, Sequence[str]],
    min_train_size: int = 120,
) -> pd.DataFrame:
    """Generate recursive expanding-window, one-month-ahead OLS forecasts.

    The common sample is constructed using every variable in every model.
    At each forecast origin, models are estimated only on observations strictly
    before the target month. No future predictor or outcome is used.
    """
    sample = common_complete_sample(
        panel,
        outcome=outcome,
        model_specs=model_specs,
    )
    if min_train_size < 30:
        raise ValueError("min_train_size must be at least 30 monthly observations.")
    if min_train_size >= len(sample):
        raise ValueError(
            f"min_train_size={min_train_size} leaves no out-of-sample forecasts "
            f"from {len(sample)} complete observations."
        )

    forecast_rows: list[dict[str, float | str]] = []
    for forecast_position in range(min_train_size, len(sample)):
        train = sample.iloc[:forecast_position]
        target_row = sample.iloc[[forecast_position]]
        row: dict[str, float | str] = {
            "month": str(sample.index[forecast_position]),
            "actual": float(target_row[outcome].iloc[0]),
        }

        for model_id, predictors_sequence in model_specs.items():
            predictors = list(predictors_sequence)
            X_train = sm.add_constant(
                train[predictors].astype(float),
                has_constant="add",
            )
            X_target = sm.add_constant(
                target_row[predictors].astype(float),
                has_constant="add",
            )
            fitted = sm.OLS(
                train[outcome].astype(float),
                X_train,
                missing="raise",
            ).fit()
            row[model_id] = float(fitted.predict(X_target).iloc[0])
        forecast_rows.append(row)

    forecasts = pd.DataFrame(forecast_rows)
    forecasts["month"] = pd.PeriodIndex(forecasts["month"], freq="M")
    forecasts = forecasts.set_index("month")
    forecasts.index.name = "month"
    return forecasts


def forecast_accuracy_table(
    forecasts: pd.DataFrame,
    *,
    model_ids: Sequence[str],
    benchmark_model: str = "M0_AR1",
) -> pd.DataFrame:
    """Calculate OOS RMSE, MAE, bias and R-squared relative to an AR benchmark."""
    required = {"actual", benchmark_model, *model_ids}
    missing = sorted(required.difference(forecasts.columns))
    if missing:
        raise KeyError(f"Forecast table is missing columns: {missing}")

    actual = forecasts["actual"].astype(float)
    benchmark_sse = float(
        np.square(actual - forecasts[benchmark_model].astype(float)).sum()
    )
    if benchmark_sse <= 0:
        raise ValueError("Benchmark forecast SSE must be positive.")

    rows: list[dict[str, object]] = []
    for model_id in model_ids:
        errors = actual - forecasts[model_id].astype(float)
        sse = float(np.square(errors).sum())
        rows.append(
            {
                "model": model_id,
                "n_forecasts": int(len(errors)),
                "first_forecast_month": str(forecasts.index.min()),
                "last_forecast_month": str(forecasts.index.max()),
                "rmse": float(np.sqrt(np.mean(np.square(errors)))),
                "mae": float(np.mean(np.abs(errors))),
                "mean_forecast_error": float(errors.mean()),
                "oos_r_squared_vs_ar1": float(1.0 - sse / benchmark_sse),
                "sse": sse,
            }
        )
    return pd.DataFrame(rows)


def clark_west_tests(
    forecasts: pd.DataFrame,
    *,
    nested_pairs: Sequence[tuple[str, str]],
    hac_lags: int = 3,
) -> pd.DataFrame:
    """Run one-sided Clark-West tests for nested one-step-ahead forecasts.

    Each pair is (restricted_model, unrestricted_model). A positive adjusted
    loss differential favors the larger model. The reported p-value is the
    asymptotic one-sided normal p-value. HAC standard errors are used for the
    mean adjusted loss differential.
    """
    if hac_lags < 0:
        raise ValueError("hac_lags must be non-negative.")

    actual = forecasts["actual"].astype(float)
    rows: list[dict[str, object]] = []

    for restricted, unrestricted in nested_pairs:
        missing = [
            name
            for name in (restricted, unrestricted)
            if name not in forecasts.columns
        ]
        if missing:
            raise KeyError(f"Forecast table is missing nested models: {missing}")

        restricted_forecast = forecasts[restricted].astype(float)
        unrestricted_forecast = forecasts[unrestricted].astype(float)
        restricted_error = actual - restricted_forecast
        unrestricted_error = actual - unrestricted_forecast

        adjusted_loss_difference = (
            np.square(restricted_error)
            - np.square(unrestricted_error)
            + np.square(restricted_forecast - unrestricted_forecast)
        )
        test = sm.OLS(
            adjusted_loss_difference,
            np.ones((len(adjusted_loss_difference), 1)),
        ).fit(
            cov_type="HAC",
            cov_kwds={"maxlags": hac_lags},
            use_t=False,
        )
        statistic = float(test.tvalues.iloc[0])
        rows.append(
            {
                "restricted_model": restricted,
                "unrestricted_model": unrestricted,
                "n_forecasts": int(len(adjusted_loss_difference)),
                "mean_adjusted_loss_difference": float(
                    adjusted_loss_difference.mean()
                ),
                "clark_west_statistic": statistic,
                "p_value_one_sided": float(norm.sf(statistic)),
                "hac_maxlags": int(hac_lags),
            }
        )

    return pd.DataFrame(rows)
