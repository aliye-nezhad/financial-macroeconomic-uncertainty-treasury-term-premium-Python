from io import StringIO

import pandas as pd

from term_premium.data import monthly_period_series, read_fred_csv


def test_monthly_fred_series_preserves_month_identity():
    source = pd.Series(
        [0.5, 0.7],
        index=pd.to_datetime(["2020-01-01", "2020-02-01"]),
        name="JLNUM1M",
    )

    result = monthly_period_series(source, source_frequency="monthly")

    assert list(result.index.astype(str)) == ["2020-01", "2020-02"]
    assert result.loc[pd.Period("2020-01", freq="M")] == 0.5


def test_daily_series_uses_last_non_missing_observation_of_month():
    source = pd.Series(
        [1.0, 2.0, 3.0],
        index=pd.to_datetime(["2020-01-30", "2020-01-31", "2020-02-03"]),
        name="VIXCLS",
    )

    result = monthly_period_series(source, source_frequency="daily")

    assert result.loc[pd.Period("2020-01", freq="M")] == 2.0
    assert result.loc[pd.Period("2020-02", freq="M")] == 3.0


def test_fred_csv_parser_handles_dot_missing_values(tmp_path):
    csv = (
        "observation_date,TESTSERIES\n"
        "2020-01-01,1.25\n"
        "2020-02-01,.\n"
        "2020-03-01,2.50\n"
    )
    path = tmp_path / "test.csv"
    path.write_text(csv, encoding="utf-8")

    result = read_fred_csv(path, "TESTSERIES")

    assert result.loc[pd.Timestamp("2020-01-01")] == 1.25
    assert pd.isna(result.loc[pd.Timestamp("2020-02-01")])
    assert result.loc[pd.Timestamp("2020-03-01")] == 2.50
