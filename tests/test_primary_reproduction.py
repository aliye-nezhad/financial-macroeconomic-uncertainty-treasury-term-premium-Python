"""Tests for the non-destructive, audited numerical reproduction check."""

import importlib.util
from hashlib import sha256
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "verify_primary_reproduction.py"
SPEC = importlib.util.spec_from_file_location("verify_primary_reproduction", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_audited_source_manifest_contains_eleven_valid_fingerprints():
    hashes = module.load_audited_hashes(
        ROOT / "docs" / "audited_source_hashes.json"
    )
    assert len(hashes) == 11
    assert "ACM" in hashes
    assert "FRED/VIXCLS" in hashes
    assert all(len(value) == 64 for value in hashes.values())


def test_verifier_detects_raw_source_tampering(tmp_path):
    path = tmp_path / "fred" / "TEST.csv"
    path.parent.mkdir(parents=True)
    payload = b"fixed historical observation bytes"
    path.write_bytes(payload)
    expected = {"FRED/TEST": sha256(payload).hexdigest()}

    module.verify_snapshot_hashes(tmp_path, expected)
    path.write_bytes(b"modified observation bytes")
    with pytest.raises(ValueError, match="differs from the audited snapshot"):
        module.verify_snapshot_hashes(tmp_path, expected)


def test_verifier_rejects_missing_audited_source(tmp_path):
    with pytest.raises(FileNotFoundError, match="Audited source file missing"):
        module.verify_snapshot_hashes(tmp_path, {"ACM": "0" * 64})


def test_reference_forecast_metrics_compare_successfully():
    path = ROOT / "outputs" / "forecasting" / "forecast_accuracy_acm_term_premium_1m.csv"
    original = pd.read_csv(path)
    module.check_against_reference(original.copy(), original, keys=("model",))


def test_reference_comparison_detects_modified_forecast_rmse():
    path = ROOT / "outputs" / "forecasting" / "forecast_accuracy_acm_term_premium_1m.csv"
    original = pd.read_csv(path)
    altered = original.copy()
    altered.loc[altered["model"] == "M3_PLUS_LMN_1M", "rmse"] += 0.01
    with pytest.raises(AssertionError, match="rmse"):
        module.check_against_reference(altered, original, keys=("model",))


def test_reference_comparison_detects_modified_clark_west_pvalue():
    path = ROOT / "outputs" / "forecasting" / "clark_west_acm_term_premium_1m.csv"
    original = pd.read_csv(path)
    altered = original.copy()
    altered.loc[
        altered["unrestricted_model"] == "M3_PLUS_LMN_1M",
        "p_value_one_sided",
    ] = 0.0001
    with pytest.raises(AssertionError, match="p_value_one_sided"):
        module.check_against_reference(
            altered, original, keys=("restricted_model", "unrestricted_model")
        )


def test_reference_comparison_rejects_missing_models():
    path = ROOT / "outputs" / "forecasting" / "forecast_accuracy_acm_term_premium_1m.csv"
    original = pd.read_csv(path)
    with pytest.raises(ValueError, match="identifiers differ"):
        module.check_against_reference(
            original.iloc[:-1].copy(), original, keys=("model",)
        )
