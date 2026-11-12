"""Download, validate, and align public macro-financial source data.

The module deliberately separates raw source retrieval from transformations.
Raw downloads are cached locally and are not intended to be committed to Git.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

FRED_GRAPH_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
ACM_WORKBOOK_URL = (
    "https://www.newyorkfed.org/medialibrary/media/research/"
    "data_indicators/ACMTermPremium.xls"
)

# Both one-month and twelve-month uncertainty horizons are downloaded.
# The one-month horizon is the initial baseline; the twelve-month horizon
# is a pre-specified horizon sensitivity, not a result-selected alternative.
FRED_SERIES: dict[str, str] = {
    "LMNUF1M": "LMN one-month-ahead financial uncertainty",
    "LMNUF12M": "LMN twelve-month-ahead financial uncertainty",
    "JLNUM1M": "JLN one-month-ahead macroeconomic uncertainty",
    "JLNUM12M": "JLN twelve-month-ahead macroeconomic uncertainty",
    "THREEFYTP10": "Kim-Wright 10-year term premium",
    "VIXCLS": "CBOE VIX close",
    "DFF": "Effective federal funds rate",
    "DGS2": "2-year Treasury constant-maturity yield",
    "DGS10": "10-year Treasury constant-maturity yield",
}

MONTHLY_FRED_SERIES = {
    "LMNUF1M",
    "LMNUF12M",
    "JLNUM1M",
    "JLNUM12M",
}
DAILY_FRED_SERIES = set(FRED_SERIES) - MONTHLY_FRED_SERIES


def sha256_bytes(payload: bytes) -> str:
    """Return the SHA-256 digest of a byte sequence."""
    return hashlib.sha256(payload).hexdigest()


def _request_bytes(url: str, *, params: dict[str, str] | None = None) -> bytes:
    """Retrieve a source payload with a tested User-Agent and transient retries.

    The curl-style User-Agent is used because it succeeded in a direct
    comparison against FRED from the project's Windows environment, whereas
    the previous project-specific User-Agent repeatedly timed out. This is an
    operational compatibility choice, not a claim that FRED requires curl.
    """
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)

    with requests.Session() as session:
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        response = session.get(
            url,
            params=params,
            timeout=(20, 45),
            headers={
                "User-Agent": "curl/8.10.1",
                "Accept": "text/csv,application/vnd.ms-excel,application/octet-stream,*/*;q=0.8",
            },
        )
        response.raise_for_status()
        return response.content


def _write_bytes_atomically(destination: Path, payload: bytes) -> None:
    """Write a completed payload to disk without exposing partial files."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_name(destination.name + ".part")
    temporary_path.write_bytes(payload)
    temporary_path.replace(destination)


def _fred_payload_is_valid(payload: bytes, series_id: str) -> None:
    """Fail early if FRED returns an HTML error page or malformed CSV."""
    try:
        frame = pd.read_csv(BytesIO(payload), nrows=3)
    except Exception as exc:  # pragma: no cover - defensive network boundary
        raise ValueError(f"FRED returned unreadable data for {series_id}.") from exc

    if frame.empty or len(frame.columns) < 2:
        raise ValueError(f"FRED returned no usable observations for {series_id}.")

    columns = [str(column).strip().lower() for column in frame.columns]
    if not any("date" in column for column in columns):
        raise ValueError(f"FRED response for {series_id} has no date column.")


def _download_fred_series(
    series_id: str,
    destination: Path,
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and not refresh:
        payload = destination.read_bytes()
        _fred_payload_is_valid(payload, series_id)
        retrieval = "cached"
    else:
        payload = _request_bytes(FRED_GRAPH_URL, params={"id": series_id})
        _fred_payload_is_valid(payload, series_id)
        _write_bytes_atomically(destination, payload)
        retrieval = "downloaded"

    return {
        "source": "FRED graph CSV",
        "series_id": series_id,
        "description": FRED_SERIES[series_id],
        "url": f"{FRED_GRAPH_URL}?id={series_id}",
        "file": str(destination),
        "retrieval": retrieval,
        "sha256": sha256_bytes(payload),
        "bytes": len(payload),
    }


def _download_acm_workbook(
    destination: Path,
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and not refresh:
        payload = destination.read_bytes()
        retrieval = "cached"
    else:
        payload = _request_bytes(ACM_WORKBOOK_URL)
        retrieval = "downloaded"

    # The official endpoint currently distributes an Excel .xls workbook.
    # Parse it now so an HTML error page or changed file is not cached as data.
    try:
        workbook = pd.ExcelFile(BytesIO(payload), engine="xlrd")
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise ValueError(
            "The New York Fed ACM endpoint did not return a readable .xls "
            "workbook. Check the official download page and update the parser "
            "only after verifying the new source format."
        ) from exc

    required_sheet = "ACM Monthly"
    if required_sheet not in workbook.sheet_names:
        raise ValueError(
            f"ACM workbook is missing the expected sheet {required_sheet!r}. "
            f"Available sheets: {workbook.sheet_names}"
        )

    if retrieval == "downloaded":
        _write_bytes_atomically(destination, payload)

    return {
        "source": "Federal Reserve Bank of New York ACM workbook",
        "url": ACM_WORKBOOK_URL,
        "file": str(destination),
        "retrieval": retrieval,
        "sha256": sha256_bytes(payload),
        "bytes": len(payload),
        "sheet_names": workbook.sheet_names,
    }


def download_all(
    raw_dir: str | Path = "data/raw",
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    """Download/cache all FRED series and the official New York Fed ACM file."""
    raw_dir = Path(raw_dir)
    manifest: dict[str, Any] = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "refresh_requested": refresh,
        "fred": {},
    }

    for series_id in FRED_SERIES:
        path = raw_dir / "fred" / f"{series_id}.csv"
        manifest["fred"][series_id] = _download_fred_series(
            series_id, path, refresh=refresh
        )

    acm_path = raw_dir / "acm" / "ACMTermPremium.xls"
    manifest["acm"] = _download_acm_workbook(acm_path, refresh=refresh)

    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = raw_dir / "download_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return manifest


def read_fred_csv(path: str | Path, series_id: str) -> pd.Series:
    """Read a cached FRED graph CSV as a numeric, date-indexed Series."""
    frame = pd.read_csv(path, na_values=[".", ""])
    if frame.shape[1] < 2:
        raise ValueError(f"Expected date and value columns in {path}.")

    date_column = next(
        (column for column in frame.columns if "date" in str(column).lower()),
        frame.columns[0],
    )
    value_column = next(
        (column for column in frame.columns if column != date_column),
        None,
    )
    if value_column is None:
        raise ValueError(f"Could not identify the value column in {path}.")

    dates = pd.to_datetime(frame[date_column], errors="coerce")
    values = pd.to_numeric(frame[value_column], errors="coerce")
    series = pd.Series(values.to_numpy(), index=dates, name=series_id)
    series = series.loc[series.index.notna()].sort_index()
    series = series.loc[~series.index.duplicated(keep="last")]
    return series.astype(float)


def monthly_period_series(
    series: pd.Series,
    *,
    source_frequency: str,
) -> pd.Series:
    """Map a monthly or daily series to a PeriodIndex at calendar-month level.

    Monthly FRED observations are labelled by the first day of the month;
    daily observations are reduced to the last non-missing observation in
    each month. The returned index is a monthly PeriodIndex.
    """
    series = series.dropna().sort_index()
    if source_frequency == "daily":
        result = series.resample("ME").last()
        result.index = result.index.to_period("M")
    elif source_frequency == "monthly":
        result = series.copy()
        result.index = result.index.to_period("M")
        result = result.groupby(level=0).last()
    else:
        raise ValueError("source_frequency must be 'daily' or 'monthly'.")

    result.index.name = "month"
    return result.astype(float)


def _parse_acm_monthly_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Parse an already-read ACM Monthly worksheet and validate its contents.

    Convert source columns to NumPy arrays before constructing the DataFrame.
    Passing a Series together with a separate DatetimeIndex makes pandas align
    by the Series' original integer labels and can silently produce all-NaN
    columns. The arrays ensure positional pairing with the parsed dates.
    """
    frame = frame.copy()
    frame.columns = [str(column).strip().upper() for column in frame.columns]

    required = ["DATE", "ACMY10", "ACMTP10", "ACMRNY10"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(
            f"ACM Monthly sheet is missing columns {missing}. "
            f"Available columns: {list(frame.columns)}"
        )

    dates = pd.to_datetime(
        frame["DATE"].astype(str).str.strip(),
        format="%d-%b-%Y",
        errors="coerce",
    )
    if dates.isna().any():
        bad_rows = frame.loc[dates.isna(), "DATE"].head(5).tolist()
        raise ValueError(
            "ACM Monthly sheet contains unparseable DATE values. "
            f"Examples: {bad_rows}"
        )

    values = {
        "acm_fitted_yield_10y": pd.to_numeric(
            frame["ACMY10"], errors="coerce"
        ).to_numpy(),
        "acm_term_premium_10y": pd.to_numeric(
            frame["ACMTP10"], errors="coerce"
        ).to_numpy(),
        "acm_expected_short_rate_10y": pd.to_numeric(
            frame["ACMRNY10"], errors="coerce"
        ).to_numpy(),
    }
    result = pd.DataFrame(
        values,
        index=pd.DatetimeIndex(dates).to_period("M"),
    )
    result = result.sort_index()
    result = result.groupby(level=0).last()
    result.index.name = "month"

    if result.empty:
        raise ValueError("ACM Monthly sheet contains no valid monthly observations.")

    for column in result.columns:
        if not result[column].notna().any():
            raise ValueError(
                f"ACM Monthly variable {column!r} contains no numeric observations."
            )

    # The published decomposition should hold up to workbook rounding.
    decomposition_error = (
        result["acm_fitted_yield_10y"]
        - result["acm_term_premium_10y"]
        - result["acm_expected_short_rate_10y"]
    ).abs()
    valid_errors = decomposition_error.dropna()
    if valid_errors.empty:
        raise ValueError(
            "ACM yield decomposition cannot be checked because there are "
            "no overlapping non-missing observations."
        )

    max_error = float(valid_errors.max())
    if max_error > 0.03:
        raise ValueError(
            "ACM yield decomposition identity failed validation: "
            f"maximum absolute discrepancy is {max_error:.4f} percentage points."
        )

    return result


def read_acm_monthly(path: str | Path) -> pd.DataFrame:
    """Read and validate the New York Fed's published ACM monthly workbook."""
    frame = pd.read_excel(
        path,
        sheet_name="ACM Monthly",
        engine="xlrd",
    )
    return _parse_acm_monthly_frame(frame)


def build_monthly_panel(raw_dir: str | Path = "data/raw") -> pd.DataFrame:
    """Build a month-end panel from cached ACM and FRED source snapshots."""
    raw_dir = Path(raw_dir)
    series: list[pd.Series] = []

    for series_id in FRED_SERIES:
        path = raw_dir / "fred" / f"{series_id}.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path}. Run scripts/01_download_data.py first."
            )
        raw_series = read_fred_csv(path, series_id)
        frequency = (
            "monthly" if series_id in MONTHLY_FRED_SERIES else "daily"
        )
        monthly = monthly_period_series(
            raw_series,
            source_frequency=frequency,
        )
        series.append(monthly)

    acm_path = raw_dir / "acm" / "ACMTermPremium.xls"
    if not acm_path.exists():
        raise FileNotFoundError(
            f"Missing {acm_path}. Run scripts/01_download_data.py first."
        )
    acm = read_acm_monthly(acm_path)

    panel = pd.concat(series + [acm], axis=1).sort_index()
    panel.index.name = "month"

    panel["yield_curve_slope_10y2y"] = panel["DGS10"] - panel["DGS2"]
    panel["dff_change"] = panel["DFF"].diff()
    panel["acm_term_premium_change"] = panel["acm_term_premium_10y"].diff()
    panel["acm_expected_short_rate_change"] = (
        panel["acm_expected_short_rate_10y"].diff()
    )
    panel["kim_wright_term_premium_change"] = panel["THREEFYTP10"].diff()

    # Forecasting information set:
    # - Market series are observed daily and aggregated to month-end. Use t-1.
    # - JLN/LMN monthly indexes are lagged by two months as a conservative
    #   publication-delay convention. This is not a reconstruction of exact
    #   historical release dates or ALFRED vintages.
    uncertainty_predictors = [
        "LMNUF1M", "LMNUF12M", "JLNUM1M", "JLNUM12M"
    ]
    market_predictors = [
        "VIXCLS", "DFF", "dff_change", "DGS2", "DGS10",
        "yield_curve_slope_10y2y",
        "acm_term_premium_change",
        "acm_expected_short_rate_change",
        "kim_wright_term_premium_change",
    ]

    for column in uncertainty_predictors:
        panel[f"{column.lower()}_lag2"] = panel[column].shift(2)

    for column in market_predictors:
        panel[f"{column.lower()}_lag1"] = panel[column].shift(1)

    # Row t contains the change realised during month t. Its predictors are
    # restricted to values dated t-1 (market data) and t-2 (monthly
    # uncertainty indexes). Thus the row is a one-month-ahead forecast target
    # relative to the end-of-month t-1 information set.
    panel["target_acm_tp_change"] = panel["acm_term_premium_change"]
    panel["target_acm_expected_short_rate_change"] = (
        panel["acm_expected_short_rate_change"]
    )
    panel["target_kim_wright_tp_change"] = (
        panel["kim_wright_term_premium_change"]
    )

    return panel


def save_monthly_panel(
    panel: pd.DataFrame,
    destination: str | Path = "data/processed/monthly_macro_finance_panel.csv",
) -> Path:
    """Save the processed panel with an explicit month-end date column."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    output = panel.copy()
    output.insert(
        0,
        "month_end",
        output.index.to_timestamp(how="end").normalize(),
    )
    output.to_csv(destination, index=False, date_format="%Y-%m-%d")
    return destination
