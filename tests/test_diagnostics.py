import numpy as np
import pandas as pd

from term_premium.diagnostics import (
    extreme_observation_table,
    missingness_profile,
    modified_z_scores,
)


def test_missingness_profile_separates_edges_from_internal_gaps():
    index = pd.period_range("2000-01", periods=6, freq="M")
    series = pd.Series([np.nan, 1.0, np.nan, 2.0, 3.0, np.nan], index=index)
    result = missingness_profile(series)
    assert result["leading_missing"] == 1
    assert result["interior_missing"] == 1
    assert result["trailing_missing"] == 1
    assert result["n_observations"] == 3


def test_modified_z_scores_flag_extreme_value_without_mutating_series():
    series = pd.Series([0.0, 0.1, -0.1, 0.05, -0.05, 20.0])
    original = series.copy()
    scores = modified_z_scores(series)
    assert abs(scores.iloc[-1]) > 3.5
    pd.testing.assert_series_equal(series, original)


def test_extreme_observation_table_flags_level_and_change_only():
    index = pd.period_range("2000-01", periods=8, freq="M")
    panel = pd.DataFrame(
        {"level": [0.0, 0.1, -0.1, 0.05, -0.05, 0.02, 0.0, 20.0],
         "change": [0.0, 0.1, -0.1, 0.05, -0.05, 0.02, 0.0, 15.0]},
        index=index,
    )
    flags = extreme_observation_table(
        panel,
        level_variables=["level"],
        change_variables=["change"],
    )
    assert not flags.empty
    assert set(flags["transformation"]).issubset(
        {"level", "first_difference", "monthly_change"}
    )
    assert flags["review_note"].str.contains("do not delete").all()



def test_regression_influence_and_leave_one_month_out_diagnostics():
    from term_premium.diagnostics import (
        leave_one_month_out_coefficient_table,
        regression_influence_table,
    )

    rng = np.random.default_rng(2026)
    index = pd.period_range("2000-01", periods=120, freq="M")
    x = rng.normal(size=len(index))
    z = rng.normal(size=len(index))
    noise = rng.normal(scale=0.5, size=len(index))
    y = 0.4 + 0.25 * x + 0.8 * z + noise
    z[-1] = 4.0
    y[-1] += 12.0
    sample = pd.DataFrame({"y": y, "x": x, "z": z}, index=index)
    original = sample.copy(deep=True)

    influence = regression_influence_table(
        sample,
        outcome="y",
        predictors=["x", "z"],
        focal_predictor="z",
    )
    leave_one_out = leave_one_month_out_coefficient_table(
        sample,
        outcome="y",
        predictors=["x", "z"],
        focal_predictor="z",
    )

    assert len(influence) == len(sample)
    assert len(leave_one_out) == len(sample)
    assert influence["flagged_by_any_rule"].iloc[-1]
    assert influence["cooks_distance"].iloc[-1] > 0
    assert leave_one_out["excluded_month"].iloc[-1] == str(index[-1])
    assert leave_one_out["rank_preserved"].all()
    assert leave_one_out["absolute_coefficient_change"].max() > 0
    assert "p_value" not in leave_one_out.columns
    pd.testing.assert_frame_equal(sample, original)


def test_influence_diagnostics_reject_internal_month_gaps():
    import pytest

    from term_premium.diagnostics import regression_influence_table

    index = pd.period_range("2000-01", periods=80, freq="M")
    rng = np.random.default_rng(11)
    sample = pd.DataFrame(
        {
            "y": rng.normal(size=len(index)),
            "x": rng.normal(size=len(index)),
        },
        index=index,
    ).drop(index[20])

    with pytest.raises(ValueError, match="consecutive months"):
        regression_influence_table(
            sample,
            outcome="y",
            predictors=["x"],
            focal_predictor="x",
        )
