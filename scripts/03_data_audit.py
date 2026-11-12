"""Produce source coverage, model-variable, and matched-sample diagnostics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from term_premium.data import build_monthly_panel
from term_premium.diagnostics import missingness_profile, extreme_observation_table


def _pairwise_observation_counts(frame: pd.DataFrame) -> pd.DataFrame:
    """Return pairwise non-missing sample sizes for every variable pair."""
    indicators = frame.notna().astype("int64")
    return indicators.T.dot(indicators)


def _sample_record(
    panel: pd.DataFrame,
    name: str,
    outcome: str,
    predictors: list[str],
    sample_filters: list[str] | None = None,
) -> dict[str, object]:
    """Summarise a model sample, distinguishing regressors from sample filters."""
    sample_filters = sample_filters or []
    required = [outcome, *predictors, *sample_filters]
    missing_columns = [column for column in required if column not in panel.columns]
    if missing_columns:
        return {
            "sample": name,
            "outcome": outcome,
            "predictors": ";".join(predictors),
            "sample_filters": ";".join(sample_filters),
            "n_complete": 0,
            "first_month": None,
            "last_month": None,
            "missing_columns": ";".join(missing_columns),
        }

    complete = panel[required].dropna()
    return {
        "sample": name,
        "outcome": outcome,
        "predictors": ";".join(predictors),
        "sample_filters": ";".join(sample_filters),
        "n_complete": int(len(complete)),
        "first_month": str(complete.index.min()) if not complete.empty else None,
        "last_month": str(complete.index.max()) if not complete.empty else None,
        "missing_columns": "",
    }


def main() -> None:
    panel = build_monthly_panel()
    out = Path("outputs/diagnostics")
    out.mkdir(parents=True, exist_ok=True)

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
    coverage.to_csv(out / "source_coverage.csv")

    # Separate expected source-history gaps from missing values inside
    # each series' observed span. No values are imputed or removed.
    missingness = pd.DataFrame({
        variable: missingness_profile(panel[variable])
        for variable in source_available
    }).T
    missingness.to_csv(out / "missingness_profile.csv")

    expected_index = pd.period_range(
        panel.index.min(), panel.index.max(), freq="M"
    )
    index_audit = pd.DataFrame([{
        "n_rows": len(panel),
        "index_is_monthly_period": isinstance(panel.index, pd.PeriodIndex),
        "index_is_unique": bool(panel.index.is_unique),
        "index_is_monotonic": bool(panel.index.is_monotonic_increasing),
        "expected_months": len(expected_index),
        "observed_months": len(panel.index),
        "missing_calendar_months": len(expected_index.difference(panel.index)),
        "duplicate_months": int(panel.index.duplicated().sum()),
    }])
    index_audit.to_csv(out / "monthly_index_audit.csv", index=False)

    # Robust modified-z flags are for manual review, never automatic deletion.
    level_variables = [
        "acm_term_premium_10y", "acm_expected_short_rate_10y",
        "THREEFYTP10", "LMNUF1M", "JLNUM1M", "VIXCLS",
        "DFF", "DGS2", "DGS10",
    ]
    change_variables = [
        "acm_term_premium_change", "acm_expected_short_rate_change",
        "kim_wright_term_premium_change", "dff_change",
    ]
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
    uncertainty_frame.corr(min_periods=36).to_csv(
        out / "uncertainty_correlations.csv"
    )
    _pairwise_observation_counts(uncertainty_frame).to_csv(
        out / "uncertainty_pairwise_n.csv"
    )

    baseline_rhs = [
        "lmnuf1m_lag2",
        "jlnum1m_lag2",
        "dff_lag1",
        "yield_curve_slope_10y2y_lag1",
    ]
    alternative_horizon_rhs = [
        "lmnuf12m_lag2",
        "jlnum12m_lag2",
        "dff_lag1",
        "yield_curve_slope_10y2y_lag1",
    ]

    model_variables = [
        "target_acm_tp_change",
        "target_acm_expected_short_rate_change",
        "target_kim_wright_tp_change",
        *baseline_rhs,
        "lmnuf12m_lag2",
        "jlnum12m_lag2",
        "vixcls_lag1",
    ]
    model_available = [
        column for column in model_variables if column in panel.columns
    ]
    model_frame = panel[model_available]
    model_frame.describe().T.to_csv(
        out / "model_variable_descriptive_statistics.csv"
    )
    model_frame.corr(min_periods=36).to_csv(
        out / "model_variable_correlations.csv"
    )
    _pairwise_observation_counts(model_frame).to_csv(
        out / "model_variable_pairwise_n.csv"
    )

    # All comparisons use the same right-hand-side controls wherever possible.
    # The VIX-restricted baseline is deliberately estimated without VIX as a
    # regressor, so it can be compared with the VIX-augmented model on the
    # identical sample.
    sample_specs = [
        (
            "primary_acm_1m_full",
            "target_acm_tp_change",
            baseline_rhs,
            [],
        ),
        (
            "primary_acm_1m_vix_common_no_vix",
            "target_acm_tp_change",
            baseline_rhs,
            ["vixcls_lag1"],
        ),
        (
            "primary_acm_1m_vix_augmented",
            "target_acm_tp_change",
            [*baseline_rhs, "vixcls_lag1"],
            [],
        ),
        (
            "primary_acm_12m_full",
            "target_acm_tp_change",
            alternative_horizon_rhs,
            [],
        ),
        (
            "acm_expected_short_rate_same_rhs",
            "target_acm_expected_short_rate_change",
            baseline_rhs,
            [],
        ),
        (
            "kim_wright_same_rhs",
            "target_kim_wright_tp_change",
            baseline_rhs,
            [],
        ),
    ]

    sample_rows = [
        _sample_record(panel, name, outcome, predictors, filters)
        for name, outcome, predictors, filters in sample_specs
    ]
    samples = pd.DataFrame(sample_rows)
    samples.to_csv(out / "analysis_sample_audit.csv", index=False)

    print(f"Audit outputs written to {out}")
    print("\nSource coverage:")
    print(coverage.to_string())
    print("\nMatched analysis samples:")
    print(samples.to_string(index=False))
    print("\nUncertainty correlations:")
    print(uncertainty_frame.corr(min_periods=36).to_string())


if __name__ == "__main__":
    main()
