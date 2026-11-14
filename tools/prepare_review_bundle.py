"""Package a verified, source-free subset of audited empirical outputs.

Run from any directory with:
    python tools/prepare_review_bundle.py

This utility does not download data, regenerate results, or alter source files.
It validates the existing source snapshots and selected archived-result values.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "docs/empirical_results.md",
    "outputs/forecasting/forecast_accuracy_acm_term_premium_1m.csv",
    "outputs/forecasting/clark_west_acm_term_premium_1m.csv",
    "outputs/forecasting/forecast_accuracy_acm_expected_short_rate_1m.csv",
    "outputs/forecasting/forecast_accuracy_kim_wright_term_premium_1m.csv",
    "outputs/forecasting/clark_west_hac_sensitivity.csv",
    "outputs/forecasting/forecast_plot_acm_term_premium_1m.png",
    "outputs/diagnostics/hac_sensitivity_coefficients.csv",
    "outputs/diagnostics/m3_influence_summary.csv",
    "outputs/forecasting/rolling_m3_vs_m2_performance.csv",
    "outputs/dff_aggregation_sensitivity/forecast_accuracy.csv",
    "outputs/dff_aggregation_sensitivity/fedfunds_validation_summary.csv",
)
EXPECTED_PRIMARY = {
    "M0_AR1": (0.231417, 0.169517, 0.0),
    "M1_MONETARY": (0.233421, 0.170520, -0.017389),
    "M2_PLUS_JLN_1M": (0.236000, 0.171723, -0.039999),
    "M3_PLUS_LMN_1M": (0.236518, 0.171133, -0.044572),
}
TOLERANCE = 0.000001


def file_hash(path: Path) -> str:
    """Return SHA-256 of an existing source or output file."""
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_primary_accuracy(path: Path) -> None:
    """Verify published baseline metrics against the original output CSV."""
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    observed = {}
    for row in rows:
        model = row.get("model")
        if model in observed:
            raise ValueError(f"Duplicate baseline model: {model}")
        observed[model] = row
    if set(observed) != set(EXPECTED_PRIMARY):
        raise ValueError(
            "Primary forecast models differ from the documented baseline: "
            f"{sorted(observed)}"
        )
    for model, (rmse, mae, r2) in EXPECTED_PRIMARY.items():
        row = observed[model]
        if int(row["n_forecasts"]) != 482:
            raise ValueError(f"{model}: unexpected forecast count.")
        if (
            row["first_forecast_month"] != "1986-07"
            or row["last_forecast_month"] != "2026-08"
        ):
            raise ValueError(f"{model}: forecast dates differ from the report.")
        for key, expected in (
            ("rmse", rmse),
            ("mae", mae),
            ("oos_r_squared_vs_ar1", r2),
        ):
            if abs(float(row[key]) - expected) > TOLERANCE:
                raise ValueError(f"{model}: documented {key} does not match CSV.")


def validate_primary_clark_west(path: Path) -> None:
    """Check the primary incremental-LMN test against the research memo."""
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    matched = [
        row for row in rows
        if row.get("restricted_model") == "M2_PLUS_JLN_1M"
        and row.get("unrestricted_model") == "M3_PLUS_LMN_1M"
    ]
    if len(matched) != 1:
        raise ValueError("Expected exactly one M2-to-M3 Clark-West comparison.")
    row = matched[0]
    if int(row["n_forecasts"]) != 482 or int(row["hac_maxlags"]) != 3:
        raise ValueError("Primary Clark-West sample or bandwidth differs.")
    if abs(float(row["p_value_one_sided"]) - 0.340455) > TOLERANCE:
        raise ValueError("Primary Clark-West p-value differs from the memo.")


def verify_raw_snapshots(root: Path) -> dict[str, dict[str, str]]:
    """Check local raw files against their manifest; return hashes, never bytes."""
    raw = root / "data" / "raw"
    path = raw / "download_manifest.json"
    if not path.is_file():
        raise FileNotFoundError(
            "Missing raw-data manifest. Use the preserved audited snapshots; "
            "do not refresh them merely to create this bundle."
        )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entries = manifest.get("fred", {})
    if len(entries) != 10 or not isinstance(manifest.get("acm"), dict):
        raise ValueError("Expected 10 FRED files and one ACM workbook.")
    checks = {}
    for identifier, entry in sorted(entries.items()):
        if not identifier.replace("_", "").isalnum():
            raise ValueError("Unexpected FRED series identifier in manifest.")
        source = raw / "fred" / f"{identifier}.csv"
        checks[f"FRED/{identifier}"] = (source, entry)
    checks["ACM"] = (raw / "acm" / "ACMTermPremium.xls", manifest["acm"])

    verified = {}
    for key, (source, entry) in checks.items():
        if not source.is_file():
            raise FileNotFoundError(f"Missing preserved snapshot: {key}")
        expected = entry.get("sha256")
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError(f"Missing or invalid source hash: {key}")
        actual = file_hash(source)
        if actual.lower() != expected.lower():
            raise ValueError(
                f"Preserved source hash mismatch: {key}. "
                "Restore the audited snapshot, rather than refreshing."
            )
        verified[key] = {
            "sha256": actual,
            "snapshot_retrieved_at_utc": entry.get(
                "snapshot_retrieved_at_utc", ""
            ),
        }
    return verified


def git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root,
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def build_bundle(root: Path, destination: Path) -> dict:
    """Validate archived results and write a curated ZIP without raw data."""
    root = root.resolve()
    destination = destination.resolve()
    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    if missing:
        raise FileNotFoundError(
            "Required reviewed outputs are missing. Run the existing pipeline "
            "against the preserved snapshots first:\n" + "\n".join(missing)
        )
    validate_primary_accuracy(
        root / "outputs/forecasting/forecast_accuracy_acm_term_premium_1m.csv"
    )
    validate_primary_clark_west(
        root / "outputs/forecasting/clark_west_acm_term_premium_1m.csv"
    )
    sources = verify_raw_snapshots(root)
    provenance = {
        "description": "Selected audited outputs, not a real-time data vintage",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_commit": git_head(root),
        "raw_snapshots_sha256": sources,
        "files_sha256": {
            name: file_hash(root / name) for name in REQUIRED_FILES
        },
        "limitations": [
            "Raw snapshots and processed observation-level data are excluded.",
            "The analysis is pseudo-out-of-sample, using revised source data.",
            "This bundle is an audited results excerpt, not full replication data.",
            "The original preserved snapshots are required for exact reproduction.",
        ],
    }
    note = (
        "# Reviewer output bundle\n\n"
        "Selected research tables, diagnostics and figures from the frozen "
        "macro-finance forecasting analysis. The code and complete documentation "
        "are maintained in the repository. The model hierarchy has not been "
        "changed to prepare this package.\n\n"
        "All included outputs were read from existing local files. Their SHA-256 "
        "hashes, the source snapshot checksums and the Git commit are recorded "
        "in provenance.json. No original raw data or observation-level "
        "estimation samples are included.\n\n"
        "These are pseudo-out-of-sample results based on revised source data, "
        "not historically available real-time forecast vintages.\n"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(
            f"Bundle exists: {destination}. Choose a new output path."
        )
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("REVIEW_BUNDLE_README.md", note)
        archive.writestr(
            "provenance.json", json.dumps(provenance, indent=2) + "\n"
        )
        for name in REQUIRED_FILES:
            archive.write(root / name, arcname=name)

    with ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Bundle failed ZIP CRC validation.")
    return provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "outputs_review_bundle.zip",
        help="ZIP destination (existing files are not overwritten)."
    )
    args = parser.parse_args()
    information = build_bundle(ROOT, args.output)
    print("REVIEW BUNDLE: PASS")
    print("Archive:", args.output.resolve())
    print("Git commit:", information["repository_commit"])
    print("Verified source snapshots:", len(information["raw_snapshots_sha256"]))
    print("Included repository outputs:", len(REQUIRED_FILES))
    print("Raw source files copied: 0")


if __name__ == "__main__":
    main()
