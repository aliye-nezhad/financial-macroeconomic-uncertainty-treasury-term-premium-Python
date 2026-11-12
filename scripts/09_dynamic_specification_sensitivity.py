"""Compare exploratory autoregressive specifications for the primary ACM outcome.

The pre-specified M0-M4 hierarchy is not changed. This script evaluates
whether adding selected autoregressive lags improves residual diagnostics
and recursive one-month-ahead forecasts for the primary M3 specification.
All candidate models use one identical complete monthly sample.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from term_premium.analysis import (
    build_model_specs,
    breusch_godfrey_diagnostic_table,
    common_complete_sample,
    expanding_window_forecasts,
    fit_hac_model_set,
    forecast_accuracy_table,
    clark_west_tests,
    residual_diagnostic_table,
)
from term_premium.data import build_monthly_panel


def main() -> None:
    outcome = "target_acm_tp_change"
    panel = build_monthly_panel()

    for lag in range(1, 13):
        panel[f"{outcome}_lag{lag}"] = panel[outcome].shift(lag)

    baseline = build_model_specs(
        ar_lag=f"{outcome}_lag1",
        uncertainty_horizon="1m",
    )["M3_PLUS_LMN_1M"]
    controls = [name for name in baseline if name != f"{outcome}_lag1"]

    specs = {
        "M3_AR1": baseline,
        "M3_AR1_AR2": [*baseline, f"{outcome}_lag2"],
        "M3_AR1_LAG12": [*baseline, f"{outcome}_lag12"],
        "M3_AR1_AR2_LAG12": [
            *baseline,
            f"{outcome}_lag2",
            f"{outcome}_lag12",
        ],
        "M3_AR12": [
            *controls,
            *[f"{outcome}_lag{lag}" for lag in range(1, 13)],
        ],
    }

    sample = common_complete_sample(
        panel,
        outcome=outcome,
        model_specs=specs,
    )
    summary, coefficients = fit_hac_model_set(
        sample,
        outcome=outcome,
        model_specs=specs,
        hac_lags=12,
    )
    residuals = residual_diagnostic_table(
        sample,
        outcome=outcome,
        model_specs=specs,
        ljung_box_lags=(1, 3, 6, 12),
        acf_max_lag=12,
    )
    bg = breusch_godfrey_diagnostic_table(
        sample,
        outcome=outcome,
        model_specs=specs,
        lags=(6, 12),
    )

    forecasts = expanding_window_forecasts(
        panel,
        outcome=outcome,
        model_specs=specs,
        min_train_size=120,
    )
    accuracy = forecast_accuracy_table(
        forecasts,
        model_ids=list(specs),
        benchmark_model="M3_AR1",
    )
    nested_pairs = [
        ("M3_AR1", "M3_AR1_AR2"),
        ("M3_AR1", "M3_AR1_LAG12"),
        ("M3_AR1_AR2", "M3_AR1_AR2_LAG12"),
        ("M3_AR1_LAG12", "M3_AR1_AR2_LAG12"),
        ("M3_AR1_AR2_LAG12", "M3_AR12"),
    ]
    cw = clark_west_tests(
        forecasts,
        nested_pairs=nested_pairs,
        hac_lags=3,
    )

    diagnostic_dir = Path("outputs/diagnostics")
    forecast_dir = Path("outputs/forecasting")
    diagnostic_dir.mkdir(parents=True, exist_ok=True)
    forecast_dir.mkdir(parents=True, exist_ok=True)

    summary.to_csv(diagnostic_dir / "dynamic_model_summary.csv", index=False)
    coefficients.to_csv(
        diagnostic_dir / "dynamic_model_coefficients.csv", index=False
    )
    residuals.to_csv(
        diagnostic_dir / "dynamic_residual_autocorrelation.csv", index=False
    )
    bg.to_csv(
        diagnostic_dir / "dynamic_breusch_godfrey.csv", index=False
    )
    forecasts.to_csv(
        forecast_dir / "dynamic_forecasts_primary_acm.csv"
    )
    accuracy.to_csv(
        forecast_dir / "dynamic_forecast_accuracy.csv", index=False
    )
    cw.to_csv(
        forecast_dir / "dynamic_clark_west.csv", index=False
    )

    dates = forecasts.index.to_timestamp()
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="white")
    ax.set_facecolor("white")
    ax.plot(
        dates, forecasts["actual"], color="black", linewidth=1.0,
        linestyle="-", label="Actual",
    )
    ax.plot(
        dates, forecasts["M3_AR1"], color="0.55", linewidth=0.9,
        linestyle="--", label="M3 AR(1)",
    )
    ax.plot(
        dates, forecasts["M3_AR1_AR2_LAG12"], color="0.25",
        linewidth=0.9, linestyle="-.", label="M3 AR(1), AR(2), AR(12)",
    )
    ax.plot(
        dates, forecasts["M3_AR12"], color="0.72", linewidth=0.9,
        linestyle=":", label="M3 AR(1)-AR(12)",
    )
    ax.axhline(0, color="0.35", linewidth=0.6, linestyle=":")
    ax.set_title(
        "Dynamic specification sensitivity: one-month-ahead forecasts",
        fontsize=11, fontweight="normal", loc="left",
    )
    ax.set_ylabel("Monthly change (percentage points)", fontsize=9)
    ax.set_xlabel("Forecast target month", fontsize=9)
    ax.grid(axis="y", color="0.88", linestyle=":", linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("0.25")
    ax.spines["bottom"].set_color("0.25")
    ax.tick_params(axis="both", colors="0.20", direction="out", labelsize=8)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(
        forecast_dir / "dynamic_forecast_comparison.png",
        dpi=300, bbox_inches="tight", facecolor="white",
    )
    plt.close(fig)

    print(
        f"Common estimation sample: {len(sample)} observations, "
        f"{sample.index.min()} to {sample.index.max()}"
    )
    print("\nMODEL SUMMARY")
    print(
        summary[
            [
                "model", "nobs", "adjusted_r_squared", "aic", "bic",
                "ljung_box_pvalue",
            ]
        ].to_string(index=False)
    )
    print("\nBREUSCH-GODFREY TESTS")
    print(bg[["model", "lag", "lm_pvalue", "f_pvalue"]].to_string(index=False))
    print("\nFORECAST ACCURACY")
    print(
        accuracy[
            ["model", "n_forecasts", "rmse", "mae", "oos_r_squared_vs_ar1"]
        ].to_string(index=False)
    )
    print("\nNESTED CLARK-WEST TESTS")
    print(
        cw[
            [
                "restricted_model", "unrestricted_model", "n_forecasts",
                "mean_adjusted_loss_difference", "clark_west_statistic",
                "p_value_one_sided",
            ]
        ].to_string(index=False)
    )
    print("\nSaved dynamic diagnostic and forecasting outputs.")


if __name__ == "__main__":
    main()
