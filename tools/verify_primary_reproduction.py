"""Recompute and check the primary M0–M3 findings against published results.

Run only with the original audited raw snapshots and their manifest:
    python -m tools.verify_primary_reproduction

This command does not download data, rewrite reference CSVs, or save estimates.
It verifies source bytes against immutable published SHA-256 fingerprints before
fitting the primary regressions and generating recursive forecasts.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from collections.abc import Mapping

import numpy as np
import pandas as pd

from term_premium.analysis import (
    build_model_specs,
    clark_west_tests,
    common_complete_sample,
    expanding_window_forecasts,
    fit_hac_model_set,
    forecast_accuracy_table,
)
from term_premium.data import build_monthly_panel


ROOT = Path(__file__).resolve().parents[1]
OUTCOME = "target_acm_tp_change"
SOURCE_HASHES = ROOT / "docs" / "audited_source_hashes.json"
ACCURACY_CSV = ROOT / "outputs" / "forecasting" / "forecast_accuracy_acm_term_premium_1m.csv"
CW_CSV = ROOT / "outputs" / "forecasting" / "clark_west_acm_term_premium_1m.csv"
INFLUENCE_CSV = ROOT / "outputs" / "diagnostics" / "m3_influence_summary.csv"

# Allow only negligible floating-point variation from the reference environment.
REL_TOL = 1e-7
ABS_TOL = 1e-8


def verify_snapshot_hashes(raw_dir: Path, expected: Mapping[str, str]) -> None:
    """Check original source *bytes*, independently of the local manifest."""
    for identifier, fingerprint in expected.items():
        if identifier == "ACM":
            filename = raw_dir / "acm" / "ACMTermPremium.xls"
        elif identifier.startswith("FRED/"):
            series = identifier.removeprefix("FRED/")
            if not series.isalnum() or not series.isupper():
                raise ValueError(f"Invalid series identifier: {identifier}")
            filename = raw_dir / "fred" / f"{series}.csv"
        else:
            raise ValueError(f"Unexpected source identifier: {identifier}")
        if not filename.is_file():
            raise FileNotFoundError(f"Audited source file missing: {filename}")
        actual = sha256(filename.read_bytes()).hexdigest()
        if actual.lower() != fingerprint.lower():
            raise ValueError(
                f"Source differs from the audited snapshot: {identifier}. "
                "Restore the original file; do not refresh it."
            )


def load_audited_hashes(path: Path) -> dict[str, str]:
    """Read immutable source fingerprints, not a mutable local manifest."""
    document = json.loads(path.read_text(encoding="utf-8"))
    sources = document["sources"]
    if len(sources) != 11 or "ACM" not in sources:
        raise ValueError("The audited source list must contain 10 FRED series and ACM.")
    hashes = {key: row["sha256"] for key, row in sources.items()}
    if sum(key.startswith("FRED/") for key in hashes) != 10:
        raise ValueError("The audited source list must contain 10 FRED series.")
    if any(
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in "0123456789abcdefABCDEF" for char in value)
        for value in hashes.values()
    ):
        raise ValueError("Invalid audited SHA-256 fingerprint.")
    return hashes


def check_against_reference(
    calculated: pd.DataFrame,
    reference: pd.DataFrame,
    *,
    keys: tuple[str, ...],
) -> None:
    """Compare complete result tables, including all test statistics."""
    if set(calculated.columns) != set(reference.columns):
        raise ValueError(
            "Calculated and reference result columns differ: "
            f"{sorted(set(calculated.columns) ^ set(reference.columns))}"
        )
    if calculated.duplicated(list(keys)).any() or reference.duplicated(list(keys)).any():
        raise ValueError("Duplicated result-table identifiers.")
    new = calculated.set_index(list(keys)).sort_index()
    old = reference.set_index(list(keys)).sort_index()
    if not new.index.equals(old.index):
        raise ValueError("The model or comparison identifiers differ from the archive.")
    for field in old.columns:
        if pd.api.types.is_numeric_dtype(old[field]):
            np.testing.assert_allclose(
                new[field].astype(float).to_numpy(),
                old[field].astype(float).to_numpy(),
                rtol=REL_TOL,
                atol=ABS_TOL,
                err_msg=f"Recomputed {field} differs from the published result.",
            )
        elif not new[field].astype(str).equals(old[field].astype(str)):
            raise ValueError(f"Recomputed {field} differs from the published result.")


def reproduce_primary(root: Path = ROOT) -> dict[str, object]:
    """Read audited data, re-estimate M0–M3, and check published metrics."""
    hashes = load_audited_hashes(root / "docs" / "audited_source_hashes.json")
    raw_dir = root / "data" / "raw"
    verify_snapshot_hashes(raw_dir, hashes)

    # Panel construction checks the matching local manifest independently.
    panel = build_monthly_panel(raw_dir=raw_dir)
    panel[f"{OUTCOME}_lag1"] = panel[OUTCOME].shift(1)
    specs = build_model_specs(
        ar_lag=f"{OUTCOME}_lag1",
        uncertainty_horizon="1m",
        include_vix=False,
    )
    sample = common_complete_sample(panel, outcome=OUTCOME, model_specs=specs)
    if (
        len(sample) != 602
        or str(sample.index.min()) != "1976-07"
        or str(sample.index.max()) != "2026-08"
    ):
        raise ValueError("Primary common estimation sample differs from the archive.")

    summary, coefficients = fit_hac_model_set(
        sample, outcome=OUTCOME, model_specs=specs, hac_lags=6
    )
    if (
        summary["model"].tolist() != list(specs)
        or (summary["nobs"] != len(sample)).any()
        or not np.isfinite(coefficients["coefficient"]).all()
    ):
        raise ValueError("Primary full-sample regressions did not validate.")

    # The archived influence summary records the full-sample M3 LMN slope.
    influence = pd.read_csv(root / "outputs" / "diagnostics" / "m3_influence_summary.csv")
    focal = coefficients.loc[
        (coefficients["model"] == "M3_PLUS_LMN_1M")
        & (coefficients["variable"] == "lmnuf1m_lag2"),
        "coefficient",
    ]
    if len(focal) != 1 or len(influence) != 1:
        raise ValueError("Missing primary M3 LMN coefficient or reference.")
    np.testing.assert_allclose(
        float(focal.iloc[0]),
        float(influence["full_sample_lmn_coefficient"].iloc[0]),
        rtol=REL_TOL,
        atol=ABS_TOL,
    )

    forecasts = expanding_window_forecasts(
        panel, outcome=OUTCOME, model_specs=specs, min_train_size=120
    )
    if (
        len(forecasts) != 482
        or str(forecasts.index.min()) != "1986-07"
        or str(forecasts.index.max()) != "2026-08"
    ):
        raise ValueError("Primary recursive forecast span differs from the archive.")

    model_ids = list(specs)
    accuracy = forecast_accuracy_table(
        forecasts, model_ids=model_ids, benchmark_model="M0_AR1"
    )
    pairs = [(model_ids[i], model_ids[i + 1]) for i in range(len(model_ids) - 1)]
    cw = clark_west_tests(forecasts, nested_pairs=pairs, hac_lags=3)
    check_against_reference(
        accuracy, pd.read_csv(root / "outputs" / "forecasting" /
                              "forecast_accuracy_acm_term_premium_1m.csv"),
        keys=("model",),
    )
    check_against_reference(
        cw, pd.read_csv(root / "outputs" / "forecasting" /
                        "clark_west_acm_term_premium_1m.csv"),
        keys=("restricted_model", "unrestricted_model"),
    )
    return {
        "source_files": len(hashes),
        "estimation_months": len(sample),
        "recursive_forecasts": len(forecasts),
        "models": model_ids,
        "nested_tests": len(cw),
    }


def main() -> None:
    results = reproduce_primary()
    print("PRIMARY NUMERICAL REPRODUCTION: PASS")
    print(f"Audited raw source hashes: {results['source_files']}")
    print(f"Full-sample regression months: {results['estimation_months']}")
    print(f"Recursive forecasts per model: {results['recursive_forecasts']}")
    print(f"Nested Clark–West tests: {results['nested_tests']}")
    print("No source files or published outputs were modified.")


if __name__ == "__main__":
    main()
