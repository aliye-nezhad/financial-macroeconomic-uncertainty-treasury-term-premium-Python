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




def test_hac_bandwidth_changes_inference_not_ols_coefficients():
    panel = _synthetic_panel()
    specs = {"M0": ["y_lag1"], "M1": ["y_lag1", "x", "z"]}
    sample = common_complete_sample(panel, outcome="y", model_specs=specs)

    _, coefficients_6 = fit_hac_model_set(
        sample, outcome="y", model_specs=specs, hac_lags=6
    )
    _, coefficients_12 = fit_hac_model_set(
        sample, outcome="y", model_specs=specs, hac_lags=12
    )

    left = coefficients_6.sort_values(["model", "variable"]).reset_index(drop=True)
    right = coefficients_12.sort_values(["model", "variable"]).reset_index(drop=True)

    assert left[["model", "variable", "nobs"]].equals(
        right[["model", "variable", "nobs"]]
    )
    np.testing.assert_allclose(
        left["coefficient"].to_numpy(),
        right["coefficient"].to_numpy(),
        rtol=0,
        atol=1e-12,
    )
    assert (left["hac_maxlags"] == 6).all()
    assert (right["hac_maxlags"] == 12).all()
    assert np.isfinite(left["hac_standard_error"]).all()
    assert np.isfinite(right["hac_standard_error"]).all()

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


def test_clark_west_hac_bandwidth_changes_inference_not_adjusted_loss_mean():
    rng = np.random.default_rng(20261112)
    n = 240
    actual = rng.normal(size=n)
    restricted = 0.25 * actual + rng.normal(scale=0.9, size=n)
    unrestricted = 0.30 * actual + rng.normal(scale=0.8, size=n)
    forecasts = pd.DataFrame(
        {
            "actual": actual,
            "restricted": restricted,
            "unrestricted": unrestricted,
        }
    )

    results = pd.concat(
        [
            clark_west_tests(
                forecasts,
                nested_pairs=[("restricted", "unrestricted")],
                hac_lags=bandwidth,
            )
            for bandwidth in (3, 6, 12, 18)
        ],
        ignore_index=True,
    )

    assert results["hac_maxlags"].tolist() == [3, 6, 12, 18]
    assert results["n_forecasts"].nunique() == 1
    np.testing.assert_allclose(
        results["mean_adjusted_loss_difference"].to_numpy(),
        results["mean_adjusted_loss_difference"].iloc[0],
        rtol=0,
        atol=1e-12,
    )
    assert np.isfinite(
        results[["clark_west_statistic", "p_value_one_sided"]]
    ).all().all()
    assert results["p_value_one_sided"].between(0, 1).all()


def test_clark_west_multiple_testing_adjustments_are_grouped_by_hac_bandwidth():
    from term_premium.analysis import adjust_clark_west_pvalues_by_bandwidth

    results = pd.DataFrame(
        {
            "hac_maxlags": [3, 3, 6, 6],
            "p_value_one_sided": [0.01, 0.04, 0.01, 0.04],
        }
    )
    adjusted = adjust_clark_west_pvalues_by_bandwidth(results)

    np.testing.assert_allclose(
        adjusted["p_value_holm"].to_numpy(),
        [0.02, 0.04, 0.02, 0.04],
    )
    np.testing.assert_allclose(
        adjusted["p_value_bonferroni"].to_numpy(),
        [0.02, 0.08, 0.02, 0.08],
    )
    assert adjusted["multiple_test_family_size"].tolist() == [2, 2, 2, 2]


def test_forecast_test_sensitivity_script_is_importable():
    import importlib.util
    from pathlib import Path

    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "08_forecast_test_sensitivity.py"
    )
    spec = importlib.util.spec_from_file_location(
        "forecast_test_sensitivity",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.HAC_LAGS == (3, 6, 12, 18)


def test_dynamic_specification_sensitivity_script_is_importable():
    import importlib.util
    from pathlib import Path

    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "09_dynamic_specification_sensitivity.py"
    )
    spec = importlib.util.spec_from_file_location(
        "dynamic_specification_sensitivity",
        script_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(module.main)


def test_rolling_lmn_coefficients_use_fixed_monthly_windows():
    import importlib.util
    from pathlib import Path

    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "10_stability_analysis.py"
    )
    spec = importlib.util.spec_from_file_location(
        "stability_analysis",
        script_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    panel = _synthetic_panel(n=180)
    panel["y_lag2"] = pd.Series(panel["y"].to_numpy(), index=panel.index).shift(2)
    specs = {"M2": ["y_lag1", "x"], "M3": ["y_lag1", "x", "z"]}
    sample = common_complete_sample(panel, outcome="y", model_specs=specs)
    result = module.rolling_lmn_coefficients(
        sample,
        outcome="y",
        model_specs=specs,
        model_id="M3",
        focal_predictor="z",
        window_size=60,
        hac_lags=3,
    )
    assert len(result) == len(sample) - 60 + 1
    assert result["nobs"].eq(60).all()
    assert result["window_start"].iloc[0] == str(sample.index[0])
    assert result["window_end"].iloc[-1] == str(sample.index[-1])
    assert np.isfinite(
        result[
            [
                "coefficient",
                "hac_standard_error",
                "confidence_interval_low",
                "confidence_interval_high",
            ]
        ]
    ).all().all()


def test_rolling_forecast_performance_and_decade_summaries():
    import importlib.util
    from pathlib import Path

    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "10_stability_analysis.py"
    )
    spec = importlib.util.spec_from_file_location(
        "stability_analysis",
        script_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    index = pd.period_range("1980-01", periods=150, freq="M")
    rng = np.random.default_rng(123)
    actual = rng.normal(size=150)
    forecasts = pd.DataFrame(
        {
            "actual": actual,
            "M2": actual + rng.normal(scale=1.0, size=150),
            "M3": actual + rng.normal(scale=0.9, size=150),
        },
        index=index,
    )
    rolling = module.rolling_forecast_performance(
        forecasts,
        restricted_model="M2",
        unrestricted_model="M3",
        window_size=60,
    )
    decades = module.forecast_performance_by_decade(
        forecasts,
        restricted_model="M2",
        unrestricted_model="M3",
    )
    assert len(rolling) == 91
    assert rolling["n_forecasts"].eq(60).all()
    assert set(decades["calendar_decade"]) == {"1980s", "1990s"}
    assert decades["n_forecasts"].sum() == len(forecasts)
    assert np.isfinite(
        rolling[
            [
                "restricted_rmse",
                "unrestricted_rmse",
                "oos_r_squared_vs_restricted",
            ]
        ]
    ).all().all()


def test_stability_functions_reject_gapped_monthly_indexes():
    import importlib.util
    from pathlib import Path

    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "10_stability_analysis.py"
    )
    spec = importlib.util.spec_from_file_location(
        "stability_analysis_validation",
        script_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    panel = _synthetic_panel(n=180)
    specs = {"M2": ["y_lag1", "x"], "M3": ["y_lag1", "x", "z"]}
    sample = common_complete_sample(panel, outcome="y", model_specs=specs)
    gapped_sample = sample.drop(sample.index[70])

    with pytest.raises(ValueError, match="consecutive months"):
        module.rolling_lmn_coefficients(
            gapped_sample,
            outcome="y",
            model_specs=specs,
            model_id="M3",
            focal_predictor="z",
            window_size=60,
            hac_lags=3,
        )

    index = pd.period_range("1980-01", periods=150, freq="M")
    rng = np.random.default_rng(456)
    actual = rng.normal(size=150)
    forecasts = pd.DataFrame(
        {
            "actual": actual,
            "M2": actual + rng.normal(size=150),
            "M3": actual + rng.normal(size=150),
        },
        index=index,
    ).drop(index[70])

    with pytest.raises(ValueError, match="consecutive months"):
        module.rolling_forecast_performance(
            forecasts,
            restricted_model="M2",
            unrestricted_model="M3",
            window_size=60,
        )

    with pytest.raises(ValueError, match="consecutive months"):
        module.forecast_performance_by_decade(
            forecasts,
            restricted_model="M2",
            unrestricted_model="M3",
        )


def test_rolling_lmn_coefficients_reject_rank_deficient_windows():
    import importlib.util
    from pathlib import Path

    script_path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "10_stability_analysis.py"
    )
    spec = importlib.util.spec_from_file_location(
        "stability_analysis_rank",
        script_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    panel = _synthetic_panel(n=100)
    panel["z"] = 1.0
    specs = {"M3": ["y_lag1", "x", "z"]}
    sample = common_complete_sample(panel, outcome="y", model_specs=specs)

    with pytest.raises(ValueError, match="rank deficient"):
        module.rolling_lmn_coefficients(
            sample,
            outcome="y",
            model_specs=specs,
            model_id="M3",
            focal_predictor="z",
            window_size=60,
            hac_lags=3,
        )
