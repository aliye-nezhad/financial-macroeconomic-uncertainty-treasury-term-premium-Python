"""Assess rolling coefficient and forecast-performance stability.

This is a descriptive stability exercise for the pre-specified M2/M3 models.
It does not change the baseline hierarchy or add post-hoc break dates.
Rolling windows overlap, so their coefficient intervals and forecast metrics
must not be interpreted as independent repeated hypothesis tests.
"""

from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from term_premium.analysis import (
    build_model_specs,
    common_complete_sample,
    expanding_window_forecasts,
)
from term_premium.data import build_monthly_panel


ROLLING_WINDOW = 120
INITIAL_TRAIN_SIZE = 120
HAC_LAGS = 6
OUTCOME = "target_acm_tp_change"
FOCAL_PREDICTOR = "lmnuf1m_lag2"
RESTRICTED_MODEL = "M2_PLUS_JLN_1M"
UNRESTRICTED_MODEL = "M3_PLUS_LMN_1M"

def _validate_monthly_index(index: pd.Index, *, label: str) -> None:
    """Require a unique, sorted, consecutive monthly PeriodIndex."""
    if not isinstance(index, pd.PeriodIndex):
        raise TypeError(f"{label} must use a monthly PeriodIndex.")
    if index.freqstr not in {"M", "ME"}:
        raise ValueError(f"{label} must have monthly frequency.")
    if len(index) == 0:
        raise ValueError(f"{label} cannot be empty.")
    if not index.is_unique or not index.is_monotonic_increasing:
        raise ValueError(f"{label} must be unique and sorted.")
    expected = pd.period_range(index.min(), index.max(), freq="M")
    if not index.equals(expected):
        raise ValueError(
            f"{label} must contain consecutive months; gaps cannot be "
            "treated as rolling monthly windows."
        )



def rolling_lmn_coefficients(
    sample: pd.DataFrame,
    *,
    outcome: str,
    model_specs: Mapping[str, Sequence[str]],
    model_id: str,
    focal_predictor: str,
    window_size: int = ROLLING_WINDOW,
    hac_lags: int = HAC_LAGS,
) -> pd.DataFrame:
    """Estimate the focal coefficient in overlapping rolling OLS-HAC windows.

    Confidence intervals use the model's HAC covariance estimate. Because
    windows overlap, the sequence is descriptive and is not a collection of
    independent significance tests.
    """
    if model_id not in model_specs:
        raise KeyError(f"Unknown model {model_id!r}.")
    predictors = list(model_specs[model_id])
    if focal_predictor not in predictors:
        raise ValueError(
            f"{focal_predictor!r} is not a predictor in {model_id!r}."
        )
    if window_size <= len(predictors) + 1:
        raise ValueError("window_size must exceed the number of model parameters.")
    if hac_lags < 0 or hac_lags >= window_size:
        raise ValueError("hac_lags must be non-negative and smaller than window_size.")
    if len(sample) < window_size:
        raise ValueError("The sample is shorter than the requested rolling window.")
    _validate_monthly_index(sample.index, label="The estimation sample")
    required_columns = [outcome, *predictors]
    missing_columns = [
        column for column in required_columns if column not in sample.columns
    ]
    if missing_columns:
        raise KeyError(f"Estimation sample is missing columns: {missing_columns}.")
    numeric_sample = sample[required_columns].apply(
        pd.to_numeric,
        errors="coerce",
    )
    if not np.isfinite(numeric_sample.to_numpy(dtype=float)).all():
        raise ValueError("The estimation sample contains missing or non-finite values.")

    rows: list[dict[str, object]] = []
    for end_position in range(window_size, len(sample) + 1):
        window = sample.iloc[end_position - window_size : end_position]
        X = sm.add_constant(
            window[predictors].astype(float),
            has_constant="add",
        )
        if np.linalg.matrix_rank(X.to_numpy(dtype=float)) < X.shape[1]:
            raise ValueError(
                "Rolling estimation design is rank deficient for window "
                f"{window.index.min()} to {window.index.max()}."
            )
        fitted = sm.OLS(
            window[outcome].astype(float),
            X,
            missing="raise",
        ).fit(
            cov_type="HAC",
            cov_kwds={"maxlags": hac_lags},
            use_t=True,
        )
        confidence_interval = fitted.conf_int(alpha=0.05).loc[focal_predictor]
        rows.append(
            {
                "model": model_id,
                "focal_predictor": focal_predictor,
                "window_start": str(window.index.min()),
                "window_end": str(window.index.max()),
                "nobs": int(fitted.nobs),
                "coefficient": float(fitted.params[focal_predictor]),
                "hac_standard_error": float(fitted.bse[focal_predictor]),
                "confidence_interval_low": float(confidence_interval.iloc[0]),
                "confidence_interval_high": float(confidence_interval.iloc[1]),
                "hac_maxlags": int(hac_lags),
            }
        )
    return pd.DataFrame(rows)


def _forecast_metrics(
    window: pd.DataFrame,
    *,
    restricted_model: str,
    unrestricted_model: str,
) -> dict[str, float | int]:
    actual = window["actual"].astype(float)
    restricted_error = actual - window[restricted_model].astype(float)
    unrestricted_error = actual - window[unrestricted_model].astype(float)
    restricted_sse = float(np.square(restricted_error).sum())
    unrestricted_sse = float(np.square(unrestricted_error).sum())
    if restricted_sse <= 0:
        raise ValueError("Restricted-model SSE must be positive.")

    restricted_rmse = float(np.sqrt(np.mean(np.square(restricted_error))))
    unrestricted_rmse = float(np.sqrt(np.mean(np.square(unrestricted_error))))
    return {
        "n_forecasts": int(len(window)),
        "restricted_rmse": restricted_rmse,
        "unrestricted_rmse": unrestricted_rmse,
        "rmse_difference_unrestricted_minus_restricted": (
            unrestricted_rmse - restricted_rmse
        ),
        "oos_r_squared_vs_restricted": (
            1.0 - unrestricted_sse / restricted_sse
        ),
        "restricted_mean_error": float(restricted_error.mean()),
        "unrestricted_mean_error": float(unrestricted_error.mean()),
    }


def rolling_forecast_performance(
    forecasts: pd.DataFrame,
    *,
    restricted_model: str,
    unrestricted_model: str,
    window_size: int = ROLLING_WINDOW,
) -> pd.DataFrame:
    """Compare M3 with M2 over overlapping 120-target-month forecast windows.

    The forecast sequence itself remains recursive and expanding-window.
    This function only groups already-generated one-step-ahead forecasts.
    No repeated p-values are calculated for the overlapping windows.
    """
    required = {"actual", restricted_model, unrestricted_model}
    missing = sorted(required.difference(forecasts.columns))
    if missing:
        raise KeyError(f"Forecast table is missing columns: {missing}.")
    _validate_monthly_index(forecasts.index, label="Forecasts")
    if window_size < 2 or len(forecasts) < window_size:
        raise ValueError("At least window_size forecast observations are required.")

    numeric = forecasts[["actual", restricted_model, unrestricted_model]].astype(float)
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("Forecasts contain missing or non-finite values.")

    rows: list[dict[str, object]] = []
    for end_position in range(window_size, len(numeric) + 1):
        window = numeric.iloc[end_position - window_size : end_position]
        rows.append(
            {
                "window_start": str(window.index.min()),
                "window_end": str(window.index.max()),
                "restricted_model": restricted_model,
                "unrestricted_model": unrestricted_model,
                **_forecast_metrics(
                    window,
                    restricted_model=restricted_model,
                    unrestricted_model=unrestricted_model,
                ),
            }
        )
    return pd.DataFrame(rows)


def forecast_performance_by_decade(
    forecasts: pd.DataFrame,
    *,
    restricted_model: str,
    unrestricted_model: str,
) -> pd.DataFrame:
    """Report descriptive forecast metrics by calendar decade.

    The first and last decades can be partial. These groups are descriptive;
    no decade-specific significance tests are performed.
    """
    required = {"actual", restricted_model, unrestricted_model}
    missing = sorted(required.difference(forecasts.columns))
    if missing:
        raise KeyError(f"Forecast table is missing columns: {missing}.")
    _validate_monthly_index(forecasts.index, label="Forecasts")

    rows: list[dict[str, object]] = []
    decade_labels = (forecasts.index.year // 10) * 10
    for decade in sorted(pd.unique(decade_labels)):
        window = forecasts.loc[decade_labels == decade]
        numeric = window[["actual", restricted_model, unrestricted_model]].astype(float)
        if not np.isfinite(numeric.to_numpy()).all():
            raise ValueError("Forecasts contain missing or non-finite values.")
        rows.append(
            {
                "calendar_decade": f"{decade}s",
                "first_forecast_month": str(window.index.min()),
                "last_forecast_month": str(window.index.max()),
                **_forecast_metrics(
                    numeric,
                    restricted_model=restricted_model,
                    unrestricted_model=unrestricted_model,
                ),
            }
        )
    return pd.DataFrame(rows)


def _save_rolling_coefficient_plot(
    coefficients: pd.DataFrame,
    destination: Path,
) -> None:
    dates = pd.PeriodIndex(coefficients["window_end"], freq="M").to_timestamp()
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="white")
    ax.set_facecolor("white")
    ax.fill_between(
        dates,
        coefficients["confidence_interval_low"].to_numpy(dtype=float),
        coefficients["confidence_interval_high"].to_numpy(dtype=float),
        color="0.88",
        linewidth=0,
        label="95% HAC confidence interval",
    )
    ax.plot(
        dates,
        coefficients["coefficient"],
        color="black",
        linewidth=1.0,
        label="LMN coefficient",
    )
    ax.axhline(0, color="0.35", linewidth=0.7, linestyle=":")
    ax.set_title(
        "Rolling 10-year estimates of the LMN coefficient",
        fontsize=11,
        fontweight="normal",
        loc="left",
    )
    ax.set_ylabel("Coefficient on lagged LMN uncertainty", fontsize=9)
    ax.set_xlabel("End of 120-month estimation window", fontsize=9)
    ax.grid(axis="y", color="0.88", linestyle=":", linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("0.25")
    ax.spines["bottom"].set_color("0.25")
    ax.tick_params(axis="both", colors="0.20", direction="out", labelsize=8)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(destination, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _save_rolling_forecast_plot(
    performance: pd.DataFrame,
    destination: Path,
) -> None:
    dates = pd.PeriodIndex(performance["window_end"], freq="M").to_timestamp()
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="white")
    ax.set_facecolor("white")
    ax.plot(
        dates,
        performance["oos_r_squared_vs_restricted"],
        color="black",
        linewidth=1.0,
        label="M3 relative to M2",
    )
    ax.axhline(0, color="0.35", linewidth=0.7, linestyle=":")
    ax.set_title(
        "Rolling 10-year forecast performance: M3 relative to M2",
        fontsize=11,
        fontweight="normal",
        loc="left",
    )
    ax.set_ylabel("Out-of-sample R-squared relative to M2", fontsize=9)
    ax.set_xlabel("End of 120-month forecast window", fontsize=9)
    ax.grid(axis="y", color="0.88", linestyle=":", linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("0.25")
    ax.spines["bottom"].set_color("0.25")
    ax.tick_params(axis="both", colors="0.20", direction="out", labelsize=8)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(destination, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    panel = build_monthly_panel()
    panel[f"{OUTCOME}_lag1"] = panel[OUTCOME].shift(1)
    specs = build_model_specs(
        ar_lag=f"{OUTCOME}_lag1",
        uncertainty_horizon="1m",
    )
    sample = common_complete_sample(
        panel,
        outcome=OUTCOME,
        model_specs=specs,
    )

    rolling_coefficients = rolling_lmn_coefficients(
        sample,
        outcome=OUTCOME,
        model_specs=specs,
        model_id=UNRESTRICTED_MODEL,
        focal_predictor=FOCAL_PREDICTOR,
        window_size=ROLLING_WINDOW,
        hac_lags=HAC_LAGS,
    )
    forecasts = expanding_window_forecasts(
        panel,
        outcome=OUTCOME,
        model_specs=specs,
        min_train_size=INITIAL_TRAIN_SIZE,
    )
    rolling_performance = rolling_forecast_performance(
        forecasts,
        restricted_model=RESTRICTED_MODEL,
        unrestricted_model=UNRESTRICTED_MODEL,
        window_size=ROLLING_WINDOW,
    )
    decade_performance = forecast_performance_by_decade(
        forecasts,
        restricted_model=RESTRICTED_MODEL,
        unrestricted_model=UNRESTRICTED_MODEL,
    )

    diagnostic_dir = Path("outputs/diagnostics")
    forecast_dir = Path("outputs/forecasting")
    diagnostic_dir.mkdir(parents=True, exist_ok=True)
    forecast_dir.mkdir(parents=True, exist_ok=True)

    rolling_coefficients.to_csv(
        diagnostic_dir / "rolling_lmn_coefficient.csv",
        index=False,
    )
    rolling_performance.to_csv(
        forecast_dir / "rolling_m3_vs_m2_performance.csv",
        index=False,
    )
    decade_performance.to_csv(
        forecast_dir / "decade_m3_vs_m2_performance.csv",
        index=False,
    )
    _save_rolling_coefficient_plot(
        rolling_coefficients,
        diagnostic_dir / "rolling_lmn_coefficient.png",
    )
    _save_rolling_forecast_plot(
        rolling_performance,
        forecast_dir / "rolling_m3_vs_m2_performance.png",
    )

    positive_coefficient_share = float(
        (rolling_coefficients["coefficient"] > 0).mean()
    )
    coefficient_median = float(rolling_coefficients["coefficient"].median())
    coefficient_min = float(rolling_coefficients["coefficient"].min())
    coefficient_max = float(rolling_coefficients["coefficient"].max())
    positive_forecast_share = float(
        (rolling_performance["oos_r_squared_vs_restricted"] > 0).mean()
    )

    print(
        f"Common estimation sample: {len(sample)} observations, "
        f"{sample.index.min()} to {sample.index.max()}"
    )
    print(
        f"Rolling coefficient windows: {len(rolling_coefficients)}; "
        f"median coefficient: {coefficient_median:.4f}; "
        f"range: [{coefficient_min:.4f}, {coefficient_max:.4f}]; "
        f"share of windows with positive coefficient: "
        f"{positive_coefficient_share:.3f}"
    )
    print(
        f"Rolling forecast windows: {len(rolling_performance)}; "
        f"share where M3 beats M2 by RMSE: {positive_forecast_share:.3f}"
    )
    print("\nForecast performance by calendar decade (descriptive):")
    print(decade_performance.to_string(index=False))
    print("\nSaved rolling coefficient and forecast-stability outputs.")


if __name__ == "__main__":
    main()
