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
