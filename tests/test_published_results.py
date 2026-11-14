"""Consistency checks for the aggregate results included in the repository."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FORECASTING = ROOT / "outputs" / "forecasting"
DFF = ROOT / "outputs" / "dff_aggregation_sensitivity"


def test_primary_forecast_metrics_are_internally_consistent():
    table = pd.read_csv(
        FORECASTING / "forecast_accuracy_acm_term_premium_1m.csv"
    ).set_index("model")

    assert set(table.index) == {
        "M0_AR1", "M1_MONETARY", "M2_PLUS_JLN_1M", "M3_PLUS_LMN_1M"
    }
    assert (table["n_forecasts"] == 482).all()
    assert (table["first_forecast_month"] == "1986-07").all()
    assert (table["last_forecast_month"] == "2026-08").all()

    benchmark_sse = table.loc["M0_AR1", "sse"]
    for _, record in table.iterrows():
        np.testing.assert_allclose(
            record["rmse"] ** 2,
            record["sse"] / record["n_forecasts"],
            rtol=0, atol=1e-12,
        )
        np.testing.assert_allclose(
            record["oos_r_squared_vs_ar1"],
            1 - record["sse"] / benchmark_sse,
            rtol=0, atol=1e-12,
        )


def test_primary_nested_comparisons_match_published_models():
    table = pd.read_csv(
        FORECASTING / "clark_west_acm_term_premium_1m.csv"
    )
    assert list(zip(table["restricted_model"], table["unrestricted_model"])) == [
        ("M0_AR1", "M1_MONETARY"),
        ("M1_MONETARY", "M2_PLUS_JLN_1M"),
        ("M2_PLUS_JLN_1M", "M3_PLUS_LMN_1M"),
    ]
    assert (table["n_forecasts"] == 482).all()
    assert (table["hac_maxlags"] == 3).all()
    np.testing.assert_allclose(
        table["p_value_one_sided"].iloc[2], 0.340455, atol=1e-6
    )


def test_dff_month_end_results_match_primary_forecasts():
    original = pd.read_csv(
        FORECASTING / "forecast_accuracy_acm_term_premium_1m.csv"
    ).sort_values("model").reset_index(drop=True)
    alternative = pd.read_csv(
        DFF / "forecast_accuracy.csv"
    )
    month_end = alternative.loc[
        alternative["aggregation"] == "month_end"
    ].drop(columns="aggregation").sort_values("model").reset_index(drop=True)

    pd.testing.assert_frame_equal(original, month_end)


def test_fedfunds_aggregation_validation_summary():
    table = pd.read_csv(DFF / "fedfunds_validation_summary.csv")
    assert len(table) == 1
    row = table.iloc[0]
    assert row["n_matched_months"] == 868
    assert row["n_within_0_01_percentage_points"] == 868
    assert row["n_outside_0_01_percentage_points"] == 0
    assert row["maximum_absolute_difference"] < 0.01
