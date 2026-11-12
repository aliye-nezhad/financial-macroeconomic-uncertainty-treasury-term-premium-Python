import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from term_premium.analysis import (
    breusch_godfrey_diagnostic_table,
    build_model_specs,
    clark_west_tests,
    common_complete_sample,
    expanding_window_forecasts,
    fit_hac_model_set,
    forecast_accuracy_table,
    residual_diagnostic_table,
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



def test_residual_diagnostics_report_acf_and_multiple_ljung_box_lags():
    panel = _synthetic_panel()
    specs = {"M0": ["y_lag1"], "M1": ["y_lag1", "x", "z"]}
    sample = common_complete_sample(panel, outcome="y", model_specs=specs)

    diagnostics = residual_diagnostic_table(
        sample,
        outcome="y",
        model_specs=specs,
        ljung_box_lags=(1, 3, 6, 12),
        acf_max_lag=12,
    )

    assert len(diagnostics) == 2 * 12
    assert set(diagnostics["model"]) == {"M0", "M1"}
    assert set(diagnostics["lag"]) == set(range(1, 13))
    tested = diagnostics.loc[diagnostics["lag"].isin([1, 3, 6, 12])]
    assert tested["ljung_box_q_stat"].notna().all()
    assert tested["ljung_box_pvalue"].between(0, 1).all()
    untested = diagnostics.loc[~diagnostics["lag"].isin([1, 3, 6, 12])]
    assert untested["ljung_box_pvalue"].isna().all()
    assert np.isfinite(diagnostics["residual_acf"]).all()


def test_breusch_godfrey_reports_lm_and_f_tests_for_each_model_and_lag():
    panel = _synthetic_panel()
    specs = {"M0": ["y_lag1"], "M1": ["y_lag1", "x", "z"]}
    sample = common_complete_sample(panel, outcome="y", model_specs=specs)

    diagnostics = breusch_godfrey_diagnostic_table(
        sample, outcome="y", model_specs=specs, lags=(6, 12)
    )

    assert len(diagnostics) == 4
    assert set(diagnostics["model"]) == {"M0", "M1"}
    assert set(diagnostics["lag"]) == {6, 12}
    assert diagnostics["nobs"].nunique() == 1
    assert np.isfinite(diagnostics[["lm_stat", "f_stat"]]).all().all()
    assert diagnostics["lm_pvalue"].between(0, 1).all()
    assert diagnostics["f_pvalue"].between(0, 1).all()


def test_breusch_godfrey_rejects_nonpositive_lags():
    panel = _synthetic_panel()
    specs = {"M0": ["y_lag1"]}
    sample = common_complete_sample(panel, outcome="y", model_specs=specs)

    with pytest.raises(ValueError, match="positive integers"):
        breusch_godfrey_diagnostic_table(
            sample, outcome="y", model_specs=specs, lags=(0, 6)
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


def test_first_expanding_forecast_uses_exact_initial_training_window():
    panel = _synthetic_panel(n=150)
    specs = {"M0_AR1": ["y_lag1"]}
    sample = common_complete_sample(panel, outcome="y", model_specs=specs)

    forecasts = expanding_window_forecasts(
        panel, outcome="y", model_specs=specs, min_train_size=100
    )

    train = sample.iloc[:100]
    target = sample.iloc[[100]]
    X_train = sm.add_constant(train[["y_lag1"]], has_constant="add")
    fitted = sm.OLS(train["y"], X_train).fit()
    X_target = sm.add_constant(target[["y_lag1"]], has_constant="add")
    expected_forecast = float(fitted.predict(X_target).iloc[0])

    assert forecasts.index[0] == sample.index[100]
    assert forecasts.iloc[0]["M0_AR1"] == pytest.approx(expected_forecast)


def test_forecast_at_origin_is_invariant_to_target_and_future_data():
    panel = _synthetic_panel(n=150)
    specs = {"M0_AR1": ["y_lag1"], "M1": ["y_lag1", "x"]}
    baseline = expanding_window_forecasts(
        panel, outcome="y", model_specs=specs, min_train_size=100
    )

    target_month = baseline.index[5]
    altered_panel = panel.copy()
    altered_panel.loc[target_month:, "y"] += 1_000_000
    future_months = altered_panel.index[altered_panel.index > target_month]
    altered_panel.loc[future_months, "x"] += 1_000_000

    altered = expanding_window_forecasts(
        altered_panel, outcome="y", model_specs=specs, min_train_size=100
    )

    np.testing.assert_allclose(
        baseline.loc[target_month, ["M0_AR1", "M1"]].to_numpy(dtype=float),
        altered.loc[target_month, ["M0_AR1", "M1"]].to_numpy(dtype=float),
    )


def test_clark_west_uses_the_adjusted_loss_differential():
    forecasts = pd.DataFrame(
        {
            "actual": [0.5, -0.2, 1.1, 0.3],
            "restricted": [0.2, -0.1, 0.4, 0.0],
            "unrestricted": [0.25, -0.05, 0.6, 0.1],
        }
    )
    result = clark_west_tests(
        forecasts,
        nested_pairs=[("restricted", "unrestricted")],
        hac_lags=0,
    )

    restricted_error = forecasts["actual"] - forecasts["restricted"]
    unrestricted_error = forecasts["actual"] - forecasts["unrestricted"]
    adjusted_difference = (
        restricted_error.pow(2)
        - unrestricted_error.pow(2)
        + (forecasts["restricted"] - forecasts["unrestricted"]).pow(2)
    )

    assert result.loc[0, "n_forecasts"] == len(forecasts)
    assert result.loc[0, "mean_adjusted_loss_difference"] == pytest.approx(
        adjusted_difference.mean()
    )
    assert 0 <= result.loc[0, "p_value_one_sided"] <= 1


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
    benchmark_r_squared = accuracy.loc[
        accuracy["model"] == "M0_AR1", "oos_r_squared_vs_ar1"
    ].iloc[0]
    assert benchmark_r_squared == pytest.approx(0.0)
    assert 0 <= cw.loc[0, "p_value_one_sided"] <= 1
