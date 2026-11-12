"""Generate residual ACF and multi-lag Ljung-Box diagnostics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from term_premium.analysis import (
    build_model_specs,
    common_complete_sample,
    residual_diagnostic_table,
)
from term_premium.data import build_monthly_panel


def main() -> None:
    panel = build_monthly_panel()
    panel["target_acm_tp_change_lag1"] = panel["target_acm_tp_change"].shift(1)
    panel["target_acm_expected_short_rate_change_lag1"] = (
        panel["target_acm_expected_short_rate_change"].shift(1)
    )
    panel["target_kim_wright_tp_change_lag1"] = (
        panel["target_kim_wright_tp_change"].shift(1)
    )

    specifications = [
        (
            "primary_acm_1m",
            "target_acm_tp_change",
            "1m",
            False,
        ),
        (
            "primary_acm_1m_vix_common",
            "target_acm_tp_change",
            "1m",
            True,
        ),
        (
            "primary_acm_12m",
            "target_acm_tp_change",
            "12m",
            False,
        ),
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

    results: list[pd.DataFrame] = []
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
        diagnostics = residual_diagnostic_table(
            sample,
            outcome=outcome,
            model_specs=model_specs,
            ljung_box_lags=(1, 3, 6, 12),
            acf_max_lag=12,
        )
        diagnostics.insert(0, "sample", label)
        diagnostics["first_month"] = str(sample.index.min())
        diagnostics["last_month"] = str(sample.index.max())
        results.append(diagnostics)

        print(
            f"\\n{label}: {len(sample)} observations, "
            f"{sample.index.min()} to {sample.index.max()}"
        )
        print(
            diagnostics.loc[
                diagnostics["lag"].isin([1, 3, 6, 12]),
                [
                    "model",
                    "lag",
                    "residual_acf",
                    "ljung_box_q_stat",
                    "ljung_box_pvalue",
                ],
            ].to_string(index=False)
        )

    combined = pd.concat(results, ignore_index=True)
    destination = output_dir / "residual_autocorrelation.csv"
    combined.to_csv(destination, index=False)
    print(f"\\nSaved: {destination}")


if __name__ == "__main__":
    main()
