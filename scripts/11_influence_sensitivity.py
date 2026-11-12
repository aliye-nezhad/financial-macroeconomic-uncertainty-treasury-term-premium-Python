"""Assess whether individual months disproportionately influence the M3 LMN estimate.

The script reports conventional OLS influence diagnostics and exact
leave-one-month-out changes in the focal OLS coefficient. It does not delete
observations, recompute HAC inference on gapped samples, or change the
pre-specified M0-M4 hierarchy.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from term_premium.analysis import build_model_specs, common_complete_sample
from term_premium.data import build_monthly_panel
from term_premium.diagnostics import (
    leave_one_month_out_coefficient_table,
    regression_influence_table,
)


OUTCOME = "target_acm_tp_change"
FOCAL_PREDICTOR = "lmnuf1m_lag2"
MODEL_ID = "M3_PLUS_LMN_1M"


def _save_leave_one_out_plot(
    results: pd.DataFrame,
    destination: Path,
) -> None:
    months = pd.PeriodIndex(results["excluded_month"], freq="M").to_timestamp()
    full_coefficient = float(results["full_sample_coefficient"].iloc[0])

    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="white")
    ax.set_facecolor("white")
    ax.plot(
        months,
        results["leave_one_month_out_coefficient"],
        color="black",
        linewidth=0.9,
        label="Coefficient after excluding month",
    )
    ax.axhline(
        full_coefficient,
        color="0.40",
        linewidth=1.0,
        linestyle="--",
        label="Full-sample coefficient",
    )
    ax.set_title(
        "Single-month influence on the M3 LMN coefficient",
        fontsize=11,
        fontweight="normal",
        loc="left",
    )
    ax.set_ylabel("OLS coefficient on lagged LMN uncertainty", fontsize=9)
    ax.set_xlabel("Excluded month", fontsize=9)
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

    model_specs = build_model_specs(
        ar_lag=f"{OUTCOME}_lag1",
        uncertainty_horizon="1m",
    )
    predictors = model_specs[MODEL_ID]
    sample = common_complete_sample(
        panel,
        outcome=OUTCOME,
        model_specs={MODEL_ID: predictors},
    )

    influence = regression_influence_table(
        sample,
        outcome=OUTCOME,
        predictors=predictors,
        focal_predictor=FOCAL_PREDICTOR,
    )
    leave_one_out = leave_one_month_out_coefficient_table(
        sample,
        outcome=OUTCOME,
        predictors=predictors,
        focal_predictor=FOCAL_PREDICTOR,
    )

    diagnostic_dir = Path("outputs/diagnostics")
    diagnostic_dir.mkdir(parents=True, exist_ok=True)

    influence_path = diagnostic_dir / "m3_influence_diagnostics.csv"
    leave_one_out_path = diagnostic_dir / "m3_leave_one_month_out_lmn.csv"
    summary_path = diagnostic_dir / "m3_influence_summary.csv"
    plot_path = diagnostic_dir / "m3_leave_one_month_out_lmn.png"

    influence.to_csv(influence_path, index=False)
    leave_one_out.to_csv(leave_one_out_path, index=False)
    _save_leave_one_out_plot(leave_one_out, plot_path)

    maximum_influence = influence.loc[influence["cooks_distance"].idxmax()]
    maximum_coefficient_change = leave_one_out.loc[
        leave_one_out["absolute_coefficient_change"].idxmax()
    ]
    summary = pd.DataFrame(
        [
            {
                "model": MODEL_ID,
                "outcome": OUTCOME,
                "focal_predictor": FOCAL_PREDICTOR,
                "nobs": len(sample),
                "first_month": str(sample.index.min()),
                "last_month": str(sample.index.max()),
                "full_sample_lmn_coefficient": float(
                    leave_one_out["full_sample_coefficient"].iloc[0]
                ),
                "n_flagged_by_any_influence_rule": int(
                    influence["flagged_by_any_rule"].sum()
                ),
                "n_high_leverage": int(influence["leverage_flag"].sum()),
                "n_large_studentized_residual": int(
                    influence["studentized_residual_flag"].sum()
                ),
                "n_high_cooks_distance": int(
                    influence["cooks_distance_flag"].sum()
                ),
                "n_high_dffits": int(influence["dffits_flag"].sum()),
                "n_high_focal_dfbetas": int(influence["dfbetas_flag"].sum()),
                "month_with_max_cooks_distance": maximum_influence["month"],
                "maximum_cooks_distance": float(
                    maximum_influence["cooks_distance"]
                ),
                "month_with_max_abs_leave_one_out_change": (
                    maximum_coefficient_change["excluded_month"]
                ),
                "maximum_absolute_leave_one_out_coefficient_change": float(
                    maximum_coefficient_change["absolute_coefficient_change"]
                ),
                "minimum_leave_one_out_coefficient": float(
                    leave_one_out["leave_one_month_out_coefficient"].min()
                ),
                "maximum_leave_one_out_coefficient": float(
                    leave_one_out["leave_one_month_out_coefficient"].max()
                ),
                "interpretation": (
                    "Screening and point-estimate sensitivity only. "
                    "No observation is automatically excluded; no HAC "
                    "inference is calculated on gapped deletion samples."
                ),
            }
        ]
    )
    summary.to_csv(summary_path, index=False)

    print(
        f"Common M3 estimation sample: {len(sample)} observations, "
        f"{sample.index.min()} to {sample.index.max()}"
    )
    print(
        "Months flagged by at least one conventional influence rule: "
        f"{int(influence['flagged_by_any_rule'].sum())}"
    )
    print(
        "Month with largest Cook's distance: "
        f"{maximum_influence['month']}"
    )
    print(
        "Month whose exclusion changes the LMN coefficient most: "
        f"{maximum_coefficient_change['excluded_month']}"
    )
    print(
        "Maximum absolute leave-one-month-out coefficient change: "
        f"{maximum_coefficient_change['absolute_coefficient_change']:.6f}"
    )
    print("\nSaved influence diagnostics and leave-one-month-out outputs.")
    print("These are screening results, not instructions to delete observations.")


if __name__ == "__main__":
    main()
