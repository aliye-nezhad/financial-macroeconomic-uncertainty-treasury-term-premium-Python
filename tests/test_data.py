from io import StringIO

import pandas as pd
import pytest

from term_premium.data import (
    _parse_acm_monthly_frame,
    monthly_period_series,
    read_fred_csv,
)


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


def test_daily_series_preserves_calendar_months_without_observations():
    source = pd.Series(
        [1.0, 3.0],
        index=pd.to_datetime(["2020-01-31", "2020-03-02"]),
        name="VIXCLS",
    )

    result = monthly_period_series(source, source_frequency="daily")

    assert list(result.index.astype(str)) == ["2020-01", "2020-02", "2020-03"]
    assert result.loc[pd.Period("2020-01", freq="M")] == 1.0
    assert pd.isna(result.loc[pd.Period("2020-02", freq="M")])
    assert result.loc[pd.Period("2020-03", freq="M")] == 3.0


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


def test_acm_parser_pairs_values_positionally_with_dates():
    frame = pd.DataFrame(
        {
            "date": ["30-Jun-1961", "31-Jul-1961"],
            "acmy10": [3.8, 3.9],
            "acmtp10": [0.2, 0.3],
            "acmrny10": [3.6, 3.6],
        }
    )

    result = _parse_acm_monthly_frame(frame)

    june = pd.Period("1961-06", freq="M")
    july = pd.Period("1961-07", freq="M")
    assert result.loc[june, "acm_term_premium_10y"] == pytest.approx(0.2)
    assert result.loc[july, "acm_term_premium_10y"] == pytest.approx(0.3)
    assert result.loc[june, "acm_fitted_yield_10y"] == pytest.approx(3.8)


def test_acm_parser_rejects_entirely_missing_series():
    frame = pd.DataFrame(
        {
            "DATE": ["30-Jun-1961", "31-Jul-1961"],
            "ACMY10": [3.8, 3.9],
            "ACMTP10": [float("nan"), float("nan")],
            "ACMRNY10": [3.6, 3.6],
        }
    )

    with pytest.raises(ValueError, match="no numeric observations"):
        _parse_acm_monthly_frame(frame)


def test_acm_parser_rejects_failed_yield_decomposition():
    frame = pd.DataFrame(
        {
            "DATE": ["30-Jun-1961", "31-Jul-1961"],
            "ACMY10": [3.8, 3.9],
            "ACMTP10": [0.2, 0.3],
            "ACMRNY10": [3.2, 3.2],
        }
    )

    with pytest.raises(ValueError, match="decomposition identity failed"):
        _parse_acm_monthly_frame(frame)
