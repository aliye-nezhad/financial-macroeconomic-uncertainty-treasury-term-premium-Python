"""Compare month-end and monthly-average DFF aggregation.

The month-end DFF series remains the primary specification because the ACM
outcome is observed at month-end. The monthly-average alternative is a
supplementary aggregation sensitivity. Its construction is checked against
FRED's official monthly FEDFUNDS series, which is used only as a validation
reference and is not included as a model predictor.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from term_premium.analysis import (
    build_model_specs,
    clark_west_tests,
    common_complete_sample,
    expanding_window_forecasts,
    fit_hac_model_set,
    forecast_accuracy_table,
)
from term_premium.data import (
    build_monthly_panel,
    monthly_average_period_series,
    monthly_period_series,
    read_fred_csv,
)


OUT = Path("outputs/dff_aggregation_sensitivity")
OUTCOME = "target_acm_tp_change"
AR_LAG = f"{OUTCOME}_lag1"
FEDFUNDS_TOLERANCE = 0.01


def _fedfunds_validation(
    daily_dff: pd.Series,
    official_fedfunds: pd.Series,
    *,
    incomplete_month: str | None,
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """Compare daily-DFF monthly means with FRED's official monthly series."""
    excluded = (
        pd.Period(incomplete_month, freq="M")
        if incomplete_month is not None
        else None
    )
    monthly_mean = monthly_average_period_series(
        daily_dff,
        incomplete_month=excluded,
    )
    official_monthly = monthly_period_series(
        official_fedfunds,
        source_frequency="monthly",
    )

    comparison = pd.DataFrame(
        {
            "DFF_monthly_mean": monthly_mean,
            "FEDFUNDS_official": official_monthly,
        }
    ).sort_index()
    comparison["absolute_difference"] = (
        comparison["DFF_monthly_mean"] - comparison["FEDFUNDS_official"]
    ).abs()

    matched = comparison.dropna(
        subset=["DFF_monthly_mean", "FEDFUNDS_official"]
    )
    if matched.empty:
        raise ValueError(
            "No overlapping observations are available to validate "
            "the DFF monthly average against FEDFUNDS."
        )

    within_tolerance = matched["absolute_difference"].le(
        FEDFUNDS_TOLERANCE
    )
    summary = pd.DataFrame(
        [
            {
                "n_matched_months": int(len(matched)),
                "first_month": str(matched.index.min()),
                "last_month": str(matched.index.max()),
                "mean_absolute_difference": float(
                    matched["absolute_difference"].mean()
                ),
                "maximum_absolute_difference": float(
                    matched["absolute_difference"].max()
                ),
                "correlation": float(
                    matched[
                        ["DFF_monthly_mean", "FEDFUNDS_official"]
                    ].corr().iloc[0, 1]
                ),
                "n_within_0_01_percentage_points": int(
                    within_tolerance.sum()
                ),
                "n_outside_0_01_percentage_points": int(
                    (~within_tolerance).sum()
                ),
                "tolerance_percentage_points": FEDFUNDS_TOLERANCE,
            }
        ]
    )
    return monthly_mean, comparison, summary


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # Retain the existing month-end construction as the baseline.
    baseline = build_monthly_panel()

    # Validate the alternative aggregation against the official monthly series.
    daily_dff = read_fred_csv("data/raw/fred/DFF.csv", "DFF")
    official_fedfunds = read_fred_csv(
        "data/raw/fred/FEDFUNDS.csv",
        "FEDFUNDS",
    )
    excluded_month = (
        baseline.attrs.get("excluded_partial_months", {}).get("DFF")
    )
    monthly_mean, validation, validation_summary = _fedfunds_validation(
        daily_dff,
        official_fedfunds,
        incomplete_month=excluded_month,
    )

    validation.to_csv(OUT / "fedfunds_validation.csv")
    validation_summary.to_csv(
        OUT / "fedfunds_validation_summary.csv",
        index=False,
    )
    if validation_summary.loc[
        0, "n_outside_0_01_percentage_points"
    ]:
        raise ValueError(
            "The daily-DFF monthly mean differs from official FEDFUNDS "
            "by more than 0.01 percentage points in at least one month. "
            "Inspect fedfunds_validation.csv before interpreting the "
            "aggregation sensitivity."
        )

    # Replace only DFF and its derived lagged terms in the alternative panel.
    alternative = baseline.copy()
    alternative["DFF"] = monthly_mean.reindex(alternative.index)
    alternative["dff_change"] = alternative["DFF"].diff()
    alternative["dff_lag1"] = alternative["DFF"].shift(1)
    alternative["dff_change_lag1"] = (
        alternative["dff_change"].shift(1)
    )

    panels = {
        "month_end": baseline,
        "monthly_mean": alternative,
    }
    model_specs = build_model_specs(
        ar_lag=AR_LAG,
        uncertainty_horizon="1m",
        include_vix=False,
    )
    nested_pairs = [
        ("M0_AR1", "M1_MONETARY"),
        ("M1_MONETARY", "M2_PLUS_JLN_1M"),
        ("M2_PLUS_JLN_1M", "M3_PLUS_LMN_1M"),
    ]

    summaries = []
    coefficients = []
    accuracies = []
    clark_west = []
    sample_records = []
    reference_index = None
    reference_forecasts = None

    for aggregation, panel in panels.items():
        panel[AR_LAG] = panel[OUTCOME].shift(1)
        sample = common_complete_sample(
            panel,
            outcome=OUTCOME,
            model_specs=model_specs,
        )

        if reference_index is None:
            reference_index = sample.index
        elif not sample.index.equals(reference_index):
            raise RuntimeError(
                "Month-end and monthly-mean aggregation produced different "
                "estimation samples."
            )

        summary, coef = fit_hac_model_set(
            sample,
            outcome=OUTCOME,
            model_specs=model_specs,
            hac_lags=6,
        )
        forecasts = expanding_window_forecasts(
            panel,
            outcome=OUTCOME,
            model_specs=model_specs,
            min_train_size=120,
        )

        if reference_forecasts is None:
            reference_forecasts = forecasts
            maximum_m0_difference = 0.0
        else:
            if not forecasts.index.equals(reference_forecasts.index):
                raise RuntimeError(
                    "Month-end and monthly-mean aggregation produced "
                    "different forecast target months."
                )
            maximum_m0_difference = float(
                (
                    reference_forecasts["M0_AR1"]
                    - forecasts["M0_AR1"]
                ).abs().max()
            )
            if maximum_m0_difference > 1e-12:
                raise RuntimeError(
                    "The AR(1) forecasts should be identical because M0 "
                    "does not contain DFF."
                )

        accuracy = forecast_accuracy_table(
            forecasts,
            model_ids=list(model_specs),
            benchmark_model="M0_AR1",
        )
        cw = clark_west_tests(
            forecasts,
            nested_pairs=nested_pairs,
            hac_lags=3,
        )

        for frame in (summary, coef, accuracy, cw):
            frame.insert(0, "aggregation", aggregation)

        summaries.append(summary)
        coefficients.append(coef)
        accuracies.append(accuracy)
        clark_west.append(cw)
        sample_records.append(
            {
                "aggregation": aggregation,
                "nobs": len(sample),
                "first_month": str(sample.index.min()),
                "last_month": str(sample.index.max()),
                "n_forecasts": len(forecasts),
                "first_forecast": str(forecasts.index.min()),
                "last_forecast": str(forecasts.index.max()),
                "maximum_M0_forecast_difference": maximum_m0_difference,
            }
        )

    summary_all = pd.concat(summaries, ignore_index=True)
    coefficient_all = pd.concat(coefficients, ignore_index=True)
    accuracy_all = pd.concat(accuracies, ignore_index=True)
    clark_west_all = pd.concat(clark_west, ignore_index=True)
    sample_all = pd.DataFrame(sample_records)

    summary_all.to_csv(OUT / "model_summary.csv", index=False)
    coefficient_all.to_csv(OUT / "coefficients.csv", index=False)
    accuracy_all.to_csv(OUT / "forecast_accuracy.csv", index=False)
    clark_west_all.to_csv(OUT / "clark_west.csv", index=False)
    sample_all.to_csv(OUT / "sample_comparison.csv", index=False)

    print("\n=== FEDFUNDS VALIDATION ===")
    print(validation_summary.to_string(index=False))

    print("\n=== SAMPLE COMPARISON ===")
    print(sample_all.to_string(index=False))

    print("\n=== MODEL SUMMARY ===")
    print(
        summary_all[
            [
                "aggregation",
                "model",
                "nobs",
                "adjusted_r_squared",
                "aic",
                "bic",
                "ljung_box_pvalue",
            ]
        ].to_string(index=False)
    )

    print("\n=== FOCAL COEFFICIENTS ===")
    focus_columns = [
        "aggregation",
        "model",
        "variable",
        "coefficient",
        "hac_standard_error",
        "p_value",
    ]
    focus_variables = [
        "dff_lag1",
        "dff_change_lag1",
        "lmnuf1m_lag2",
    ]
    focus = coefficient_all.loc[
        coefficient_all["variable"].isin(focus_variables),
        focus_columns,
    ]
    print(focus.to_string(index=False))

    print("\n=== FORECAST ACCURACY ===")
    print(
        accuracy_all[
            [
                "aggregation",
                "model",
                "n_forecasts",
                "rmse",
                "mae",
                "oos_r_squared_vs_ar1",
            ]
        ].to_string(index=False)
    )

    print("\n=== CLARK-WEST TESTS ===")
    print(clark_west_all.to_string(index=False))

    print(f"\nAll sensitivity outputs saved to: {OUT}")


if __name__ == "__main__":
    main()
