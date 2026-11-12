"""Run expanding-window forecasts and nested forecast comparisons."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from term_premium.analysis import (
    build_model_specs,
    clark_west_tests,
    expanding_window_forecasts,
    forecast_accuracy_table,
)
from term_premium.data import build_monthly_panel


def _run_forecast_set(
    panel: pd.DataFrame,
    *,
    outcome: str,
    label: str,
    horizon: str,
    include_vix: bool,
    output_dir: Path,
) -> None:
    specs = build_model_specs(
        ar_lag=f"{outcome}_lag1",
        uncertainty_horizon=horizon,
        include_vix=include_vix,
    )
    forecasts = expanding_window_forecasts(
        panel,
        outcome=outcome,
        model_specs=specs,
        min_train_size=120,
    )
    model_ids = list(specs)
    accuracy = forecast_accuracy_table(
        forecasts,
        model_ids=model_ids,
        benchmark_model="M0_AR1",
    )

    nested_pairs = [
        (model_ids[i], model_ids[i + 1])
        for i in range(len(model_ids) - 1)
    ]
    cw = clark_west_tests(
        forecasts,
        nested_pairs=nested_pairs,
        hac_lags=3,
    )

    suffix = f"{label}_{horizon}"
    if include_vix:
        suffix += "_vix_common"

    forecasts.to_csv(output_dir / f"forecasts_{suffix}.csv")
    accuracy.to_csv(output_dir / f"forecast_accuracy_{suffix}.csv", index=False)
    cw.to_csv(output_dir / f"clark_west_{suffix}.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="white")
    ax.set_facecolor("white")
    dates = forecasts.index.to_timestamp()
    ax.plot(dates, forecasts["actual"], label="Actual", color="black",
            linestyle="-", linewidth=1.15)
    ax.plot(dates, forecasts["M0_AR1"], label="AR(1) benchmark",
            color="0.40", linestyle="--", linewidth=0.95)
    final_model = model_ids[-1]
    ax.plot(dates, forecasts[final_model], label=final_model,
            color="0.68", linestyle="-.", linewidth=0.95)
    ax.axhline(0, color="0.25", linewidth=0.7, linestyle=":")
    ax.set_title(
        f"One-month-ahead forecasts: {label.replace('_', ' ')}",
        fontsize=11, fontweight="normal", loc="left", pad=10,
    )
    ax.set_ylabel("Monthly change (percentage points)", fontsize=9)
    ax.set_xlabel("Forecast target month", fontsize=9)
    ax.grid(axis="y", color="0.88", linestyle=":", linewidth=0.6)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("0.25")
    ax.spines["bottom"].set_color("0.25")
    ax.tick_params(axis="both", colors="0.20", direction="out",
                   length=3, width=0.6, labelsize=8)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(
        output_dir / f"forecast_plot_{suffix}.png",
        dpi=300, bbox_inches="tight", facecolor="white",
    )
    plt.close(fig)

    print(f"\n{suffix}: {len(forecasts)} forecasts, "
          f"{forecasts.index.min()} to {forecasts.index.max()}")
    print(accuracy[["model", "n_forecasts", "rmse", "mae",
                    "oos_r_squared_vs_ar1"]].to_string(index=False))
    print("\nClark-West tests:")
    print(cw.to_string(index=False))


def main() -> None:
    panel = build_monthly_panel()
    panel["target_acm_tp_change_lag1"] = panel["target_acm_tp_change"].shift(1)
    panel["target_acm_expected_short_rate_change_lag1"] = (
        panel["target_acm_expected_short_rate_change"].shift(1)
    )
    panel["target_kim_wright_tp_change_lag1"] = (
        panel["target_kim_wright_tp_change"].shift(1)
    )

    output_dir = Path("outputs/forecasting")
    output_dir.mkdir(parents=True, exist_ok=True)

    _run_forecast_set(
        panel,
        outcome="target_acm_tp_change",
        label="acm_term_premium",
        horizon="1m",
        include_vix=False,
        output_dir=output_dir,
    )
    _run_forecast_set(
        panel,
        outcome="target_acm_tp_change",
        label="acm_term_premium",
        horizon="1m",
        include_vix=True,
        output_dir=output_dir,
    )
    _run_forecast_set(
        panel,
        outcome="target_acm_tp_change",
        label="acm_term_premium",
        horizon="12m",
        include_vix=False,
        output_dir=output_dir,
    )
    _run_forecast_set(
        panel,
        outcome="target_acm_expected_short_rate_change",
        label="acm_expected_short_rate",
        horizon="1m",
        include_vix=False,
        output_dir=output_dir,
    )
    _run_forecast_set(
        panel,
        outcome="target_kim_wright_tp_change",
        label="kim_wright_term_premium",
        horizon="1m",
        include_vix=False,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    main()
