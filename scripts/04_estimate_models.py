"""Estimate the pre-specified nested OLS models with HAC inference."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from term_premium.analysis import build_model_specs, common_complete_sample, fit_hac_model_set
from term_premium.data import build_monthly_panel


def _run_outcome(
    panel: pd.DataFrame,
    *,
    outcome: str,
    outcome_label: str,
    horizon: str,
    include_vix: bool,
    output_dir: Path,
) -> None:
    ar_lag = f"{outcome}_lag1"
    specs = build_model_specs(
        ar_lag=ar_lag,
        uncertainty_horizon=horizon,
        include_vix=include_vix,
    )
    sample = common_complete_sample(
        panel,
        outcome=outcome,
        model_specs=specs,
    )
    summary, coefficients = fit_hac_model_set(
        sample,
        outcome=outcome,
        model_specs=specs,
        hac_lags=6,
    )

    suffix = f"{outcome_label}_{horizon}"
    if include_vix:
        suffix += "_vix_common"
    summary.to_csv(output_dir / f"regression_summary_{suffix}.csv", index=False)
    coefficients.to_csv(
        output_dir / f"regression_coefficients_{suffix}.csv",
        index=False,
    )
    sample.reset_index().to_csv(
        output_dir / f"estimation_sample_{suffix}.csv",
        index=False,
    )
    print(f"\n{suffix}: {len(sample)} observations, "
          f"{sample.index.min()} to {sample.index.max()}")
    print(summary[["model", "nobs", "r_squared", "adjusted_r_squared",
                   "ljung_box_pvalue"]].to_string(index=False))


def main() -> None:
    panel = build_monthly_panel()
    panel["target_acm_tp_change_lag1"] = panel["target_acm_tp_change"].shift(1)
    panel["target_acm_expected_short_rate_change_lag1"] = (
        panel["target_acm_expected_short_rate_change"].shift(1)
    )
    panel["target_kim_wright_tp_change_lag1"] = (
        panel["target_kim_wright_tp_change"].shift(1)
    )

    output_dir = Path("outputs/estimation")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Main 1-month uncertainty hierarchy, using the longest common sample.
    _run_outcome(
        panel,
        outcome="target_acm_tp_change",
        outcome_label="acm_term_premium",
        horizon="1m",
        include_vix=False,
        output_dir=output_dir,
    )

    # VIX comparison is a separate matched-sample hierarchy.
    _run_outcome(
        panel,
        outcome="target_acm_tp_change",
        outcome_label="acm_term_premium",
        horizon="1m",
        include_vix=True,
        output_dir=output_dir,
    )

    # Pre-specified alternative uncertainty horizon.
    _run_outcome(
        panel,
        outcome="target_acm_tp_change",
        outcome_label="acm_term_premium",
        horizon="12m",
        include_vix=False,
        output_dir=output_dir,
    )

    # Component and alternative-measure robustness.
    _run_outcome(
        panel,
        outcome="target_acm_expected_short_rate_change",
        outcome_label="acm_expected_short_rate",
        horizon="1m",
        include_vix=False,
        output_dir=output_dir,
    )
    _run_outcome(
        panel,
        outcome="target_kim_wright_tp_change",
        outcome_label="kim_wright_term_premium",
        horizon="1m",
        include_vix=False,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    main()
