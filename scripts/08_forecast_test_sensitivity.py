"""Assess Clark-West forecast-test sensitivity to HAC bandwidth choices.

This script reuses the expanding-window forecast files created by
scripts/05_forecast_evaluation.py. It does not re-estimate the forecasting
models. The original three-lag Clark-West results are recomputed and checked
against the saved baseline files before the wider bandwidth sensitivity
results are written.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from term_premium.analysis import (\n    adjust_clark_west_pvalues_by_bandwidth,\n    clark_west_tests,\n)


HAC_LAGS = (3, 6, 12, 18)

FORECAST_SETS = (
    (
        "acm_term_premium_1m",
        "acm_term_premium_1m",
        (
            "M0_AR1",
            "M1_MONETARY",
            "M2_PLUS_JLN_1M",
            "M3_PLUS_LMN_1M",
        ),
    ),
    (
        "acm_term_premium_1m_vix_common",
        "acm_term_premium_1m_vix_common",
        (
            "M0_AR1",
            "M1_MONETARY",
            "M2_PLUS_JLN_1M",
            "M3_PLUS_LMN_1M",
            "M4_PLUS_VIX",
        ),
    ),
    (
        "acm_term_premium_12m",
        "acm_term_premium_12m",
        (
            "M0_AR1",
            "M1_MONETARY",
            "M2_PLUS_JLN_12M",
            "M3_PLUS_LMN_12M",
        ),
    ),
    (
        "acm_expected_short_rate_1m",
        "acm_expected_short_rate_1m",
        (
            "M0_AR1",
            "M1_MONETARY",
            "M2_PLUS_JLN_1M",
            "M3_PLUS_LMN_1M",
        ),
    ),
    (
        "kim_wright_term_premium_1m",
        "kim_wright_term_premium_1m",
        (
            "M0_AR1",
            "M1_MONETARY",
            "M2_PLUS_JLN_1M",
            "M3_PLUS_LMN_1M",
        ),
    ),
)


def _read_forecasts(
    path: Path,
    *,
    expected_models: tuple[str, ...],
) -> pd.DataFrame:
    """Read and validate one saved monthly forecast panel."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Forecast file not found: {path}. "
            "Run scripts/05_forecast_evaluation.py first."
        )

    forecasts = pd.read_csv(path, index_col=0)
    if "actual" not in forecasts.columns:
        raise ValueError(f"{path} does not contain an 'actual' column.")

    observed_models = tuple(
        column for column in forecasts.columns if column != "actual"
    )
    if observed_models != expected_models:
        raise ValueError(
            f"Unexpected model columns in {path}. "
            f"Expected {expected_models}, found {observed_models}."
        )

    try:
        forecasts.index = pd.PeriodIndex(
            forecasts.index.astype(str),
            freq="M",
            name="month",
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Could not interpret the forecast index in {path} as monthly."
        ) from exc

    if not forecasts.index.is_unique or not forecasts.index.is_monotonic_increasing:
        raise ValueError(f"The forecast index in {path} must be unique and sorted.")

    expected_index = pd.period_range(
        forecasts.index.min(),
        forecasts.index.max(),
        freq="M",
    )
    if not forecasts.index.equals(expected_index):
        raise ValueError(f"The forecast index in {path} contains missing months.")

    numeric = forecasts[["actual", *expected_models]].apply(
        pd.to_numeric,
        errors="coerce",
    )
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError(f"The forecast values in {path} contain missing or non-finite values.")

    return numeric


def _verify_three_lag_baseline(
    sensitivity: pd.DataFrame,
    baseline_path: Path,
) -> None:
    """Confirm that recomputed three-lag tests reproduce the saved baseline."""
    if not baseline_path.is_file():
        raise FileNotFoundError(
            f"Baseline Clark-West file not found: {baseline_path}. "
            "Run scripts/05_forecast_evaluation.py first."
        )

    baseline = pd.read_csv(baseline_path)
    keys = ["restricted_model", "unrestricted_model"]
    metrics = [
        "n_forecasts",
        "mean_adjusted_loss_difference",
        "clark_west_statistic",
        "p_value_one_sided",
    ]
    required = set(keys + metrics)
    missing = sorted(required.difference(baseline.columns))
    if missing:
        raise ValueError(
            f"Baseline file {baseline_path} is missing columns: {missing}"
        )

    recalculated = sensitivity.loc[
        sensitivity["hac_maxlags"] == 3,
        keys + metrics,
    ].sort_values(keys).reset_index(drop=True)
    baseline = baseline[keys + metrics].sort_values(keys).reset_index(drop=True)

    if len(recalculated) != len(baseline):
        raise RuntimeError(
            f"The three-lag result count does not match {baseline_path}."
        )
    if not recalculated[keys].equals(baseline[keys]):
        raise RuntimeError(
            f"The nested model pairs do not match {baseline_path}."
        )
    if not np.array_equal(
        recalculated["n_forecasts"].to_numpy(),
        baseline["n_forecasts"].to_numpy(),
    ):
        raise RuntimeError(
            f"The forecast counts do not match {baseline_path}."
        )

    for column in metrics[1:]:
        if not np.allclose(
            recalculated[column].to_numpy(dtype=float),
            baseline[column].to_numpy(dtype=float),
            rtol=1e-10,
            atol=1e-12,
        ):
            raise RuntimeError(
                f"Recomputed three-lag values do not reproduce "
                f"{baseline_path} ({column})."
            )


def main() -> None:
    output_dir = Path("outputs/forecasting")
    all_results: list[pd.DataFrame] = []

    for label, suffix, model_ids in FORECAST_SETS:
        forecast_path = output_dir / f"forecasts_{suffix}.csv"
        baseline_path = output_dir / f"clark_west_{suffix}.csv"
        forecasts = _read_forecasts(
            forecast_path,
            expected_models=model_ids,
        )
        nested_pairs = list(zip(model_ids[:-1], model_ids[1:]))

        bandwidth_results: list[pd.DataFrame] = []
        for hac_lags in HAC_LAGS:
            result = clark_west_tests(
                forecasts,
                nested_pairs=nested_pairs,
                hac_lags=hac_lags,
            )
            result.insert(0, "forecast_set", label)
            result["first_forecast_month"] = str(forecasts.index.min())
            result["last_forecast_month"] = str(forecasts.index.max())
            bandwidth_results.append(result)

        sensitivity = pd.concat(bandwidth_results, ignore_index=True)
        _verify_three_lag_baseline(sensitivity, baseline_path)
        sensitivity["baseline_3lag_verified"] = True
        all_results.append(sensitivity)

        print(
            f"{label}: {len(forecasts)} forecasts, "
            f"{forecasts.index.min()} to {forecasts.index.max()}; "
            "three-lag baseline verified."
        )

    combined = pd.concat(all_results, ignore_index=True)
    combined = adjust_clark_west_pvalues_by_bandwidth(combined)
    columns = [
        "forecast_set",
        "restricted_model",
        "unrestricted_model",
        "n_forecasts",
        "first_forecast_month",
        "last_forecast_month",
        "mean_adjusted_loss_difference",
        "clark_west_statistic",
        "p_value_one_sided",
        "p_value_holm",
        "p_value_bonferroni",
        "multiple_test_family_size",
        "hac_maxlags",
        "baseline_3lag_verified",
    ]
    combined = combined[columns]

    destination = output_dir / "clark_west_hac_sensitivity.csv"
    combined.to_csv(destination, index=False)

    print("\nClark-West HAC bandwidth sensitivity:")
    print(
        combined[
            [
                "forecast_set",
                "restricted_model",
                "unrestricted_model",
                "hac_maxlags",
                "mean_adjusted_loss_difference",
                "clark_west_statistic",
                "p_value_one_sided",
                "p_value_holm",
            ]
        ].to_string(index=False)
    )
    print(f"\nSaved: {destination}")


if __name__ == "__main__":
    main()
