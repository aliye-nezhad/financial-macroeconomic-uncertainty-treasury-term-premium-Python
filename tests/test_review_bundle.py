"""Tests for the offline reviewer bundle and its integrity checks."""

import csv
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from zipfile import ZipFile

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "prepare_review_bundle.py"
SPEC = importlib.util.spec_from_file_location("prepare_review_bundle", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _fake_repo(root: Path) -> None:
    for name in bundle.REQUIRED_FILES:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"sample reviewed output\n")
    rows = []
    for model, (rmse, mae, r2) in bundle.EXPECTED_PRIMARY.items():
        rows.append({
            "model": model,
            "n_forecasts": 482,
            "first_forecast_month": "1986-07",
            "last_forecast_month": "2026-08",
            "rmse": rmse,
            "mae": mae,
            "oos_r_squared_vs_ar1": r2,
        })
    _write_csv(
        root / "outputs/forecasting/forecast_accuracy_acm_term_premium_1m.csv",
        rows,
    )
    _write_csv(
        root / "outputs/forecasting/clark_west_acm_term_premium_1m.csv",
        [{
            "restricted_model": "M2_PLUS_JLN_1M",
            "unrestricted_model": "M3_PLUS_LMN_1M",
            "n_forecasts": 482,
            "hac_maxlags": 3,
            "p_value_one_sided": 0.340455,
        }],
    )
    raw = root / "data/raw"
    (raw / "fred").mkdir(parents=True, exist_ok=True)
    (raw / "acm").mkdir(parents=True, exist_ok=True)
    manifest = {"fred": {}, "acm": {}}
    for i in range(10):
        name = f"FAKE{i}"
        contents = f"source snapshot {i}".encode()
        (raw / "fred" / f"{name}.csv").write_bytes(contents)
        manifest["fred"][name] = {
            "sha256": sha256(contents).hexdigest(),
            "snapshot_retrieved_at_utc": "2026-11-13T10:00:00+00:00",
        }
    acm_bytes = b"source snapshot ACM"
    (raw / "acm" / "ACMTermPremium.xls").write_bytes(acm_bytes)
    manifest["acm"] = {
        "sha256": sha256(acm_bytes).hexdigest(),
        "snapshot_retrieved_at_utc": "2026-11-13T10:00:00+00:00",
    }
    (raw / "download_manifest.json").write_text(json.dumps(manifest))


def test_review_bundle_verifies_and_excludes_raw_data(tmp_path, monkeypatch):
    _fake_repo(tmp_path)
    monkeypatch.setattr(bundle, "git_head", lambda root: "abc123")
    destination = tmp_path / "outputs_review_bundle.zip"
    manifest = bundle.build_bundle(tmp_path, destination)

    assert manifest["repository_commit"] == "abc123"
    assert len(manifest["raw_snapshots_sha256"]) == 11
    assert len(manifest["files_sha256"]) == len(bundle.REQUIRED_FILES)
    with ZipFile(destination) as archive:
        names = set(archive.namelist())
        assert names == set(bundle.REQUIRED_FILES) | {
            "provenance.json", "REVIEW_BUNDLE_README.md"
        }
        assert archive.testzip() is None
        saved = json.loads(archive.read("provenance.json"))
        assert saved["files_sha256"] == manifest["files_sha256"]
        assert not any(name.startswith("data/") for name in names)


def test_review_bundle_rejects_modified_primary_metrics(tmp_path, monkeypatch):
    _fake_repo(tmp_path)
    monkeypatch.setattr(bundle, "git_head", lambda root: "abc123")
    path = tmp_path / (
        "outputs/forecasting/forecast_accuracy_acm_term_premium_1m.csv"
    )
    path.write_text(path.read_text().replace("0.236518", "0.136518"))
    output = tmp_path / "outputs_review_bundle.zip"
    with pytest.raises(ValueError, match="documented rmse"):
        bundle.build_bundle(tmp_path, output)
    assert not output.exists()


def test_review_bundle_rejects_changed_snapshot(tmp_path, monkeypatch):
    _fake_repo(tmp_path)
    monkeypatch.setattr(bundle, "git_head", lambda root: "abc123")
    (tmp_path / "data/raw/fred/FAKE0.csv").write_bytes(b"unverified edit")
    output = tmp_path / "outputs_review_bundle.zip"
    with pytest.raises(ValueError, match="hash mismatch"):
        bundle.build_bundle(tmp_path, output)
    assert not output.exists()


def test_review_bundle_requires_all_selected_outputs(tmp_path):
    _fake_repo(tmp_path)
    (tmp_path / "outputs/diagnostics/m3_influence_summary.csv").unlink()
    with pytest.raises(FileNotFoundError, match="m3_influence_summary"):
        bundle.build_bundle(tmp_path, tmp_path / "outputs_review_bundle.zip")


def test_review_bundle_does_not_overwrite_existing_archive(tmp_path, monkeypatch):
    _fake_repo(tmp_path)
    monkeypatch.setattr(bundle, "git_head", lambda root: "abc123")
    destination = tmp_path / "outputs_review_bundle.zip"
    destination.write_bytes(b"keep existing archive")
    with pytest.raises(FileExistsError, match="exists"):
        bundle.build_bundle(tmp_path, destination)
    assert destination.read_bytes() == b"keep existing archive"
