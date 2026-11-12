"""Produce source coverage, model-variable, and matched-sample diagnostics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from term_premium.analysis import build_model_specs, common_complete_sample
from term_premium.data import build_monthly_panel
from term_premium.diagnostics import (
    extreme_observation_table,
    missingness_profile,
)


def _pairwise_observation_counts(frame: pd.DataFrame) -> pd.DataFrame:
    """Return pairwise non-missing sample sizes for every variable pair."""
    indicators = frame.notna().astype("int64")
    return indicators.T.dot(indicators)


def _sample_record(
    panel: pd.DataFrame,
    name: str,
    outcome: str,
    model_specs: dict[str, list[str]],
    *,
    sample_filters: list[str] | None = None,
    reported_predictors: list[str] | None = None,
) -> dict[str, object]:
    """Summarise the exact common, consecutive sample used by a model set.

    The sample is constructed from the union of every model's regressors,
    including the outcome's autoregressive lag. Optional sample filters are
    recorded separately for transparency, but are also required to be present
    in the supplied model specifications.
    """
    sample_filters = sample_filters or []
    required_predictors = list(
        dict.fromkeys(
            [
                *(
                    predictor
                    for specification in model_specs.values()
                    for predictor in specification
                ),
                *sample_filters,
            ]
        )
    )
    displayed_predictors = (
        reported_predictors
        if reported_predictors is not None
        else required_predictors
    )
    required_columns = [outcome, *required_predictors]
    missing_columns = [
        column for column in required_columns if column not in panel.columns
    ]

    if missing_columns:
        return {
            "sample": name,
            "outcome": outcome,
            "predictors": ";".join(displayed_predictors),
            "sample_filters": ";".join(sample_filters),
            "n_complete": 0,
            "first_month": None,
            "last_month": None,
            "missing_columns": ";".join(missing_columns),
        }

    # Reuse the estimation-sample constructor so the audit applies the same
    # finite-value and consecutive-month requirements as model estimation.
    complete = common_complete_sample(
        panel,
        outcome=outcome,
        model_specs={"audit_sample": required_predictors},
    )

    return {
        "sample": name,
        "outcome": outcome,
        "predictors": ";".join(displayed_predictors),
        "sample_filters": ";".join(sample_filters),
        "n_complete": int(len(complete)),
        "first_month": str(complete.index.min()),
        "last_month": str(complete.index.max()),
        "missing_columns": "",
    }


def main() -> None:
    panel = build_monthly_panel()
    out = Path("outputs/diagnostics")
    out.mkdir(parents=True, exist_ok=True)

    outcomes = [
        "target_acm_tp_change",
        "target_acm_expected_short_rate_change",
        "target_kim_wright_tp_change",
    ]
    for outcome in outcomes:
        panel[f"{outcome}_lag1"] = panel[outcome].shift(1)

    acm_1m_specs = build_model_specs(
        ar_lag="target_acm_tp_change_lag1",
        uncertainty_horizon="1m",
    )
    acm_1m_vix_specs = build_model_specs(
        ar_lag="target_acm_tp_change_lag1",
        uncertainty_horizon="1m",
        include_vix=True,
    )
    acm_12m_specs = build_model_specs(
        ar_lag="target_acm_tp_change_lag1",
        uncertainty_horizon="12m",
    )
    expected_short_rate_specs = build_model_specs(
        ar_lag="target_acm_expected_short_rate_change_lag1",
        uncertainty_horizon="1m",
    )
    kim_wright_specs = build_model_specs(
        ar_lag="target_kim_wright_tp_change_lag1",
        uncertainty_horizon="1m",
    )

    source_variables = [
        "acm_fitted_yield_10y",
        "acm_term_premium_10y",
        "acm_expected_short_rate_10y",
        "THREEFYTP10",
        "LMNUF1M",
        "LMNUF12M",
        "JLNUM1M",
        "JLNUM12M",
        "VIXCLS",
        "DFF",
        "DGS2",
        "DGS10",
        "yield_curve_slope_10y2y",
    ]
    source_available = [
        column for column in source_variables if column in panel.columns
    ]

    coverage = pd.DataFrame(
        {
            "first_valid_month": {
                c: str(panel[c].first_valid_index()) for c in source_available
            },
            "last_valid_month": {
                c: str(panel[c].last_valid_index()) for c in source_available
            },
            "n_observations": {
                c: int(panel[c].notna().sum()) for c in source_available
            },
            "n_missing": {
                c: int(panel[c].isna().sum()) for c in source_available
            },
            "missing_share": {
                c: float(panel[c].isna().mean()) for c in source_available
            },
        }
    )
    coverage.index.name = "variable"
    coverage.to_csv(out / "source_coverage.csv", index_label="variable")

    # Separate expected source-history gaps from missing values inside
    # each series' observed span. No values are imputed or removed.
    missingness = pd.DataFrame(
        {
            variable: missingness_profile(panel[variable])
            for variable in source_available
        }
    ).T
    missingness.index.name = "variable"
    missingness.to_csv(out / "missingness_profile.csv", index_label="variable")

    expected_index = pd.period_range(
        panel.index.min(), panel.index.max(), freq="M"
    )
    index_audit = pd.DataFrame(
        [
            {
                "n_rows": len(panel),
                "index_is_monthly_period": isinstance(
                    panel.index, pd.PeriodIndex
                ),
                "index_is_unique": bool(panel.index.is_unique),
                "index_is_monotonic": bool(panel.index.is_monotonic_increasing),
                "expected_months": len(expected_index),
                "observed_months": len(panel.index),
                "missing_calendar_months": len(
                    expected_index.difference(panel.index)
                ),
                "duplicate_months": int(panel.index.duplicated().sum()),
            }
        ]
    )
    index_audit.to_csv(out / "monthly_index_audit.csv", index=False)

    # Robust modified-z flags are for manual review, never automatic deletion.
    level_variables = [
        "acm_term_premium_10y",
        "acm_expected_short_rate_10y",
        "THREEFYTP10",
        "LMNUF1M",
        "LMNUF12M",
        "JLNUM1M",
        "JLNUM12M",
        "VIXCLS",
        "DFF",
        "DGS2",
        "DGS10",
    ]
    # The panel's *_change variables are mechanically generated with .diff()
    # from level series already screened below. Re-screening those aliases
    # would duplicate the same extreme dates. Add only independently sourced
    # change series here if the data design later introduces any.
    change_variables: list[str] = []
    extremes = extreme_observation_table(
        panel,
        level_variables=level_variables,
        change_variables=change_variables,
    )
    extremes.to_csv(out / "extreme_observation_flags.csv", index=False)

    uncertainty = ["LMNUF1M", "LMNUF12M", "JLNUM1M", "JLNUM12M", "VIXCLS"]
    uncertainty_available = [
        column for column in uncertainty if column in panel.columns
    ]
    uncertainty_frame = panel[uncertainty_available]

    uncertainty_correlations = uncertainty_frame.corr(min_periods=36)
    uncertainty_correlations.index.name = "variable"
    uncertainty_correlations.to_csv(
        out / "uncertainty_correlations.csv",
        index_label="variable",
    )

    uncertainty_pairwise_n = _pairwise_observation_counts(uncertainty_frame)
    uncertainty_pairwise_n.index.name = "variable"
    uncertainty_pairwise_n.to_csv(
        out / "uncertainty_pairwise_n.csv",
        index_label="variable",
    )

    all_model_specs = [
        acm_1m_specs,
        acm_1m_vix_specs,
        acm_12m_specs,
        expected_short_rate_specs,
        kim_wright_specs,
    ]
    model_variables = list(
        dict.fromkeys(
            [
                *outcomes,
                *[
                    predictor
                    for specification_set in all_model_specs
                    for specification in specification_set.values()
                    for predictor in specification
                ],
            ]
        )
    )
    model_available = [
        column for column in model_variables if column in panel.columns
    ]
    model_frame = panel[model_available]

    model_descriptives = model_frame.describe().T
    model_descriptives.index.name = "variable"
    model_descriptives.to_csv(
        out / "model_variable_descriptive_statistics.csv",
        index_label="variable",
    )

    model_correlations = model_frame.corr(min_periods=36)
    model_correlations.index.name = "variable"
    model_correlations.to_csv(
        out / "model_variable_correlations.csv",
        index_label="variable",
    )

    model_pairwise_n = _pairwise_observation_counts(model_frame)
    model_pairwise_n.index.name = "variable"
    model_pairwise_n.to_csv(
        out / "model_variable_pairwise_n.csv",
        index_label="variable",
    )

    sample_specs = [
        (
            "primary_acm_1m_full",
            "target_acm_tp_change",
            acm_1m_specs,
            acm_1m_specs["M3_PLUS_LMN_1M"],
            [],
        ),
        (
            "primary_acm_1m_vix_common_no_vix",
            "target_acm_tp_change",
            acm_1m_vix_specs,
            acm_1m_specs["M3_PLUS_LMN_1M"],
            ["vixcls_lag1"],
        ),
        (
            "primary_acm_1m_vix_augmented",
            "target_acm_tp_change",
            acm_1m_vix_specs,
            acm_1m_vix_specs["M4_PLUS_VIX"],
            [],
        ),
        (
            "primary_acm_12m_full",
            "target_acm_tp_change",
            acm_12m_specs,
            acm_12m_specs["M3_PLUS_LMN_12M"],
            [],
        ),
        (
            "acm_expected_short_rate_same_rhs",
            "target_acm_expected_short_rate_change",
            expected_short_rate_specs,
            expected_short_rate_specs["M3_PLUS_LMN_1M"],
            [],
        ),
        (
            "kim_wright_same_rhs",
            "target_kim_wright_tp_change",
            kim_wright_specs,
            kim_wright_specs["M3_PLUS_LMN_1M"],
            [],
        ),
    ]

    sample_rows = [
        _sample_record(
            panel,
            name,
            outcome,
            model_specs,
            sample_filters=filters,
            reported_predictors=reported_predictors,
        )
        for (
            name,
            outcome,
            model_specs,
            reported_predictors,
            filters,
        ) in sample_specs
    ]
    samples = pd.DataFrame(sample_rows)
    samples.to_csv(out / "analysis_sample_audit.csv", index=False)

    print(f"Audit outputs written to {out}")
    print("\nSource coverage:")
    print(coverage.to_string())
    print("\nMatched analysis samples:")
    print(samples.to_string(index=False))
    print("\nUncertainty correlations:")
    print(uncertainty_correlations.to_string())


if __name__ == "__main__":
    main()
