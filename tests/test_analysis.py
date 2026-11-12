import numpy as np
import pandas as pd
import pytest

from term_premium.analysis import (
    build_model_specs,
    clark_west_tests,
    common_complete_sample,
    expanding_window_forecasts,
    fit_hac_model_set,
    forecast_accuracy_table,
)


def _synthetic_panel(n=180):
    rng = np.random.default_rng(20261112)
    index = pd.period_range("2000-01", periods=n, freq="M")
    x = rng.normal(size=n)
    z = rng.normal(size=n)
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = 0.35 * y[t - 1] + 0.25 * x[t - 1] + 0.15 * z[t - 1] + rng.normal()
    return pd.DataFrame(
        {
            "y": y,
            "y_lag1": pd.Series(y, index=index).shift(1),
            "x": x,
            "z": z,
            "vix": rng.normal(size=n),
        },
        index=index,
    )


def test_model_hierarchy_is_nested_and_horizon_specific():
    specs = build_model_specs(ar_lag="y_lag1", uncertainty_horizon="1m")
    ids = list(specs)
    assert ids == ["M0_AR1", "M1_MONETARY", "M2_PLUS_JLN_1M", "M3_PLUS_LMN_1M"]
    assert specs[ids[0]] == ["y_lag1"]
    assert set(specs[ids[0]]).issubset(specs[ids[1]])
    assert set(specs[ids[1]]).issubset(specs[ids[2]])
    assert set(specs[ids[2]]).issubset(specs[ids[3]])


def test_12m_model_hierarchy_retains_ar1_benchmark():
    specs = build_model_specs(ar_lag="y_lag1", uncertainty_horizon="12m")
    ids = list(specs)
    assert ids == [
        "M0_AR1",
        "M1_MONETARY",
        "M2_PLUS_JLN_12M",
        "M3_PLUS_LMN_12M",
    ]
    assert specs["M0_AR1"] == ["y_lag1"]


def test_common_sample_rejects_internal_missing_month():
    panel = _synthetic_panel()
    panel = panel.drop(pd.Period("2005-01", freq="M"))
    specs = {"M0": ["y_lag1"], "M1": ["y_lag1", "x"]}
    with pytest.raises(ValueError, match="internal missing months"):
        common_complete_sample(panel, outcome="y", model_specs=specs)


def test_hac_model_set_returns_coefficients_and_model_summary():
    panel = _synthetic_panel()
    specs = {"M0": ["y_lag1"], "M1": ["y_lag1", "x", "z"]}
    sample = common_complete_sample(panel, outcome="y", model_specs=specs)
    summary, coefficients = fit_hac_model_set(
        sample, outcome="y", model_specs=specs, hac_lags=4
    )
    assert list(summary["model"]) == ["M0", "M1"]
    assert summary["nobs"].nunique() == 1
    assert {"coefficient", "hac_standard_error", "p_value"}.issubset(
        coefficients.columns
    )


def test_expanding_forecasts_are_one_step_ahead_and_complete():
    panel = _synthetic_panel()
    specs = {"M0_AR1": ["y_lag1"], "M1": ["y_lag1", "x"]}
    forecasts = expanding_window_forecasts(
        panel, outcome="y", model_specs=specs, min_train_size=100
    )
    assert len(forecasts) == len(panel.dropna(subset=["y", "y_lag1", "x"])) - 100
    assert forecasts.index.is_monotonic_increasing
    assert {"actual", "M0_AR1", "M1"}.issubset(forecasts.columns)


def test_forecast_accuracy_and_clark_west_outputs():
    panel = _synthetic_panel()
    specs = {"M0_AR1": ["y_lag1"], "M1": ["y_lag1", "x"]}
    forecasts = expanding_window_forecasts(
        panel, outcome="y", model_specs=specs, min_train_size=100
    )
    accuracy = forecast_accuracy_table(
        forecasts, model_ids=list(specs), benchmark_model="M0_AR1"
    )
    cw = clark_west_tests(
        forecasts, nested_pairs=[("M0_AR1", "M1")], hac_lags=2
    )
    assert len(accuracy) == 2
    assert len(cw) == 1
    assert np.isfinite(accuracy["rmse"]).all()
    assert 0 <= cw.loc[0, "p_value_one_sided"] <= 1
