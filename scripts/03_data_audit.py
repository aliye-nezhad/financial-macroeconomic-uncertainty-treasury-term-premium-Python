"""Produce descriptive data, coverage, and predictor-dependence audits."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from term_premium.data import build_monthly_panel


def main() -> None:
    panel = build_monthly_panel()
    out = Path("outputs/diagnostics")
    out.mkdir(parents=True, exist_ok=True)

    key = [
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
    available = [column for column in key if column in panel.columns]

    coverage = pd.DataFrame({
        "first_valid_month": {
            c: str(panel[c].first_valid_index()) for c in available
        },
        "last_valid_month": {
            c: str(panel[c].last_valid_index()) for c in available
        },
        "n_observations": {c: int(panel[c].notna().sum()) for c in available},
        "n_missing": {c: int(panel[c].isna().sum()) for c in available},
        "missing_share": {c: float(panel[c].isna().mean()) for c in available},
    })
    coverage.to_csv(out / "source_coverage.csv")

    panel[available].describe().T.to_csv(out / "descriptive_statistics.csv")
    panel[available].corr(min_periods=36).to_csv(
        out / "contemporaneous_correlations.csv"
    )

    # Correlations between the uncertainty indexes are especially important:
    # raw index levels are not directly comparable, but overlap in information
    # can affect incremental predictive content.
    uncertainty = [
        "LMNUF1M", "LMNUF12M", "JLNUM1M", "JLNUM12M", "VIXCLS"
    ]
    panel[uncertainty].corr(min_periods=36).to_csv(
        out / "uncertainty_correlations.csv"
    )

    # Report common samples separately; don't force all robustness measures
    # into one complete-case sample.
    samples = {
        "primary_acm_1m": [
            "target_acm_tp_change", "lmnu f1m_lag2".replace(" ", ""),
            "jlnum1m_lag2", "dff_lag1", "yield_curve_slope_10y2y_lag1",
        ],
        "acm_component": [
            "target_acm_expected_short_rate_change",
            "lmnu f1m_lag2".replace(" ", ""), "jlnum1m_lag2",
        ],
        "kim_wright": [
            "target_kim_wright_tp_change",
            "lmnu f1m_lag2".replace(" ", ""), "jlnum1m_lag2",
        ],
    }
    sample_rows = []
    for sample_name, columns in samples.items():
        valid_columns = [c for c in columns if c in panel.columns]
        n = int(panel[valid_columns].dropna().shape[0])
        sample_rows.append({
            "sample": sample_name,
            "n_complete": n,
            "first_month": (
                str(panel[valid_columns].dropna().index.min()) if n else None
            ),
            "last_month": (
                str(panel[valid_columns].dropna().index.max()) if n else None
            ),
            "missing_columns": ";".join(set(columns) - set(valid_columns)),
        })
    pd.DataFrame(sample_rows).to_csv(
        out / "analysis_sample_audit.csv", index=False
    )

    print(f"Audit outputs written to {out}")
    print("\nSource coverage:")
    print(coverage.to_string())


if __name__ == "__main__":
    main()
