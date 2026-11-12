import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "03_data_audit.py"
)
SPEC = importlib.util.spec_from_file_location("data_audit_script", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
DATA_AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DATA_AUDIT)


def test_sample_record_includes_ar_lag_in_exact_estimation_sample():
    index = pd.period_range("2000-01", periods=8, freq="M")
    y = pd.Series(np.arange(8, dtype=float), index=index)

    panel = pd.DataFrame(
        {
            "y": y,
            "y_lag1": y.shift(1),
            "x": np.linspace(0.0, 1.0, len(index)),
        },
        index=index,
    )
    model_specs = {
        "M0_AR1": ["y_lag1"],
        "M1": ["y_lag1", "x"],
    }

    result = DATA_AUDIT._sample_record(
        panel,
        "test_sample",
        "y",
        model_specs,
    )

    assert result["n_complete"] == 7
    assert result["first_month"] == "2000-02"
    assert result["last_month"] == "2000-08"
    assert "y_lag1" in result["predictors"]


def test_sample_record_rejects_internal_gaps_in_model_variables():
    index = pd.period_range("2000-01", periods=8, freq="M")
    y = pd.Series(np.arange(8, dtype=float), index=index)

    panel = pd.DataFrame(
        {
            "y": y,
            "y_lag1": y.shift(1),
            "x": np.linspace(0.0, 1.0, len(index)),
        },
        index=index,
    )
    panel.loc[pd.Period("2000-05", freq="M"), "x"] = np.nan

    with pytest.raises(ValueError, match="internal missing months"):
        DATA_AUDIT._sample_record(
            panel,
            "test_sample",
            "y",
            {"M0_AR1": ["y_lag1"], "M1": ["y_lag1", "x"]},
        )
