import pandas as pd

from term_premium.data import monthly_period_series


def test_daily_month_end_aggregation_does_not_use_future_observations():
    source = pd.Series(
        [10.0, 12.0, 14.0],
        index=pd.to_datetime(["2020-01-30", "2020-01-31", "2020-02-03"]),
    )
    result = monthly_period_series(source, source_frequency="daily")

    assert result.loc[pd.Period("2020-01", freq="M")] == 12.0
    assert result.loc[pd.Period("2020-02", freq="M")] == 14.0


def test_monthly_uncertainty_lag_two_is_prior_to_target_month():
    uncertainty = pd.Series(
        [1.0, 2.0, 3.0, 4.0],
        index=pd.period_range("2020-01", periods=4, freq="M"),
    )
    target_month = pd.Period("2020-03", freq="M")

    assert uncertainty.shift(2).loc[target_month] == 1.0


def test_monthly_index_uses_period_index():
    source = pd.Series(
        [0.2, 0.3],
        index=pd.to_datetime(["2020-01-01", "2020-02-01"]),
    )
    result = monthly_period_series(source, source_frequency="monthly")

    assert isinstance(result.index, pd.PeriodIndex)
    assert result.index.freqstr == "M"
