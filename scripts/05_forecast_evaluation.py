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

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.plot(forecasts.index.to_timestamp(), forecasts["actual"],
            label="Actual", linewidth=1.2)
    ax.plot(forecasts.index.to_timestamp(), forecasts["M0_AR1"],
            label="AR(1) benchmark", linewidth=1.0, alpha=0.85)
    final_model = model_ids[-1]
    ax.plot(forecasts.index.to_timestamp(), forecasts[final_model],
            label=final_model, linewidth=1.0, alpha=0.85)
    ax.axhline(0, linewidth=0.7, alpha=0.5)
    ax.set_title(f"One-month-ahead forecasts: {label.replace('_', ' ')}")
    ax.set_ylabel("Monthly change (percentage points)")
    ax.set_xlabel("Forecast target month")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(
        output_dir / f"forecast_plot_{suffix}.png",
        dpi=300,
        bbox_inches="tight",
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
