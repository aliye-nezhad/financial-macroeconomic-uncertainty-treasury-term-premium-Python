"""Check regression-inference sensitivity to HAC bandwidth choices.

The baseline regressions use six monthly lags. This script re-estimates the
same pre-specified models on exactly the same samples with HAC bandwidths of
6, 12, and 18 months. OLS coefficients and fitted values are unchanged;
only estimated covariance matrices, standard errors, tests, and confidence
intervals vary with the bandwidth.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from term_premium.analysis import (
    build_model_specs,
    common_complete_sample,
    fit_hac_model_set,
)
from term_premium.data import build_monthly_panel


HAC_LAGS = (6, 12, 18)


def main() -> None:
    panel = build_monthly_panel()
    outcomes = [
        "target_acm_tp_change",
        "target_acm_expected_short_rate_change",
        "target_kim_wright_tp_change",
    ]
    for outcome in outcomes:
        panel[f"{outcome}_lag1"] = panel[outcome].shift(1)

    specifications = [
        ("primary_acm_1m", "target_acm_tp_change", "1m", False),
        ("primary_acm_1m_vix_common", "target_acm_tp_change", "1m", True),
        ("primary_acm_12m", "target_acm_tp_change", "12m", False),
        (
            "acm_expected_short_rate_1m",
            "target_acm_expected_short_rate_change",
            "1m",
            False,
        ),
        (
            "kim_wright_term_premium_1m",
            "target_kim_wright_tp_change",
            "1m",
            False,
        ),
    ]

    output_dir = Path("outputs/diagnostics")
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_results: list[pd.DataFrame] = []
    coefficient_results: list[pd.DataFrame] = []

    for label, outcome, horizon, include_vix in specifications:
        model_specs = build_model_specs(
            ar_lag=f"{outcome}_lag1",
            uncertainty_horizon=horizon,
            include_vix=include_vix,
        )
        sample = common_complete_sample(
            panel,
            outcome=outcome,
            model_specs=model_specs,
        )

        for hac_lags in HAC_LAGS:
            summary, coefficients = fit_hac_model_set(
                sample,
                outcome=outcome,
                model_specs=model_specs,
                hac_lags=hac_lags,
            )
            summary.insert(0, "sample", label)
            coefficients.insert(0, "sample", label)
            summary_results.append(summary)
            coefficient_results.append(coefficients)

        print(
            f"\n{label}: {len(sample)} observations, "
            f"{sample.index.min()} to {sample.index.max()}"
        )

    summaries = pd.concat(summary_results, ignore_index=True)
    coefficients = pd.concat(coefficient_results, ignore_index=True)

    summary_path = output_dir / "hac_sensitivity_model_summary.csv"
    coefficient_path = output_dir / "hac_sensitivity_coefficients.csv"
    summaries.to_csv(summary_path, index=False)
    coefficients.to_csv(coefficient_path, index=False)

    print(f"\nSaved: {summary_path}")
    print(f"Saved: {coefficient_path}")
    print("\nCoefficient inference by HAC bandwidth:")
    print(
        coefficients[
            [
                "sample",
                "model",
                "variable",
                "coefficient",
                "hac_standard_error",
                "p_value",
                "confidence_interval_low",
                "confidence_interval_high",
                "hac_maxlags",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
