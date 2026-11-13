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
    "FEDFUNDS": "Federal funds effective rate, monthly average (validation reference)",
    "DGS2": "2-year Treasury constant-maturity yield",
    "DGS10": "10-year Treasury constant-maturity yield",
}

MONTHLY_FRED_SERIES = {
    "LMNUF1M",
    "LMNUF12M",
    "JLNUM1M",
    "JLNUM12M",
    "FEDFUNDS",
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


def _snapshot_timestamp_for_entry(
    current_entry: dict[str, Any],
    previous_entry: dict[str, Any],
    previous_manifest: dict[str, Any],
    current_timestamp: str,
) -> str | None:
    """Preserve the acquisition time of the exact cached source snapshot."""
    if current_entry.get("retrieval") == "downloaded":
        return current_timestamp
    if current_entry.get("retrieval") != "cached":
        return None
    if current_entry.get("sha256") != previous_entry.get("sha256"):
        return None

    previous_timestamp = previous_entry.get("snapshot_retrieved_at_utc")
    if previous_timestamp is None and previous_entry.get("retrieval") == "downloaded":
        # Backward compatibility with manifests created before per-source
        # snapshot timestamps were recorded.
        previous_timestamp = previous_manifest.get("retrieved_at_utc")
    return previous_timestamp


def download_all(
    raw_dir: str | Path = "data/raw",
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    """Download/cache source files and preserve each snapshot's retrieval time."""
    raw_dir = Path(raw_dir)
    manifest_path = raw_dir / "download_manifest.json"
    previous_manifest: dict[str, Any] = {}
    if manifest_path.exists():
        previous_manifest = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )

    current_timestamp = datetime.now(timezone.utc).isoformat()
    manifest: dict[str, Any] = {
        "retrieved_at_utc": current_timestamp,
        "refresh_requested": refresh,
        "fred": {},
    }

    for series_id in FRED_SERIES:
        path = raw_dir / "fred" / f"{series_id}.csv"
        entry = _download_fred_series(
            series_id, path, refresh=refresh
        )
        previous_entry = previous_manifest.get("fred", {}).get(series_id, {})
        entry["snapshot_retrieved_at_utc"] = _snapshot_timestamp_for_entry(
            entry,
            previous_entry,
            previous_manifest,
            current_timestamp,
        )
        manifest["fred"][series_id] = entry

    acm_path = raw_dir / "acm" / "ACMTermPremium.xls"
    acm_entry = _download_acm_workbook(acm_path, refresh=refresh)
    acm_entry["snapshot_retrieved_at_utc"] = _snapshot_timestamp_for_entry(
        acm_entry,
        previous_manifest.get("acm", {}),
        previous_manifest,
        current_timestamp,
    )
    manifest["acm"] = acm_entry

    raw_dir.mkdir(parents=True, exist_ok=True)
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
    incomplete_month: pd.Period | str | None = None,
) -> pd.Series:
    """Map source observations to a monthly PeriodIndex.

    Daily observations are reduced to the last non-missing observation in
    each calendar month. When supplied, the incomplete month is excluded
    from daily data while remaining untouched in the raw source snapshot.
    """
    if incomplete_month is not None and source_frequency != "daily":
        raise ValueError("incomplete_month can only be applied to daily series.")

    series = series.dropna().sort_index()
    if source_frequency == "daily":
        # Group by calendar month directly. Reindex the full span so months
        # with no source observations remain explicit NaNs, as with resample.
        result = series.groupby(series.index.to_period("M")).last()
        if not result.empty:
            expected_months = pd.period_range(
                result.index.min(), result.index.max(), freq="M"
            )
            result = result.reindex(expected_months)
        if incomplete_month is not None:
            result = result.drop(
                index=pd.Period(str(incomplete_month), freq="M"),
                errors="ignore",
            )
    elif source_frequency == "monthly":
        result = series.copy()
        result.index = result.index.to_period("M")
        result = result.groupby(level=0).last()
    else:
        raise ValueError("source_frequency must be 'daily' or 'monthly'.")

    result.index.name = "month"
    return result.astype(float)


def monthly_average_period_series(
    series: pd.Series,
    *,
    incomplete_month: pd.Period | str | None = None,
) -> pd.Series:
    """Aggregate daily observations to arithmetic calendar-month means.

    Empty months remain explicit NaNs. When supplied, the incomplete month
    identified from the source snapshot metadata is excluded. This is a
    sensitivity transformation; it does not replace month-end aggregation
    in the primary forecasting specification.
    """
    if not isinstance(series.index, pd.DatetimeIndex):
        raise TypeError("Daily source series must use a DatetimeIndex.")

    series = series.dropna().sort_index()
    result = series.groupby(series.index.to_period("M")).mean()

    if not result.empty:
        expected_months = pd.period_range(
            result.index.min(), result.index.max(), freq="M"
        )
        result = result.reindex(expected_months)

    if incomplete_month is not None:
        result = result.drop(
            index=pd.Period(str(incomplete_month), freq="M"),
            errors="ignore",
        )

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


def _verify_snapshot_hash(
    path: Path,
    entry: dict[str, Any],
    *,
    source_label: str,
) -> None:
    """Confirm that a cached source file matches its recorded manifest hash."""
    expected_hash = entry.get("sha256")
    if not expected_hash:
        raise ValueError(
            f"The download manifest has no SHA-256 hash for {source_label}. "
            "Run scripts/01_download_data.py --refresh to rebuild source metadata."
        )

    actual_hash = sha256_bytes(path.read_bytes())
    if actual_hash != expected_hash:
        raise ValueError(
            f"Raw source hash mismatch for {source_label}. The file does not "
            "match the snapshot recorded in download_manifest.json. Restore "
            "the matching source file or run scripts/01_download_data.py --refresh."
        )


def _source_snapshot_timestamp(
    manifest: dict[str, Any],
    series_id: str,
) -> str | None:
    """Return a source file's original retrieval time from the download manifest."""
    entry = manifest.get("fred", {}).get(series_id, {})
    timestamp = entry.get("snapshot_retrieved_at_utc")
    if timestamp is None and entry.get("retrieval") == "downloaded":
        # Read manifests written before per-source timestamps were introduced.
        timestamp = manifest.get("retrieved_at_utc")
    return timestamp


def _incomplete_month_for_daily_source(
    series: pd.Series,
    snapshot_retrieved_at_utc: str | pd.Timestamp,
) -> pd.Period | None:
    """Identify a final daily-data month observed during its source snapshot month."""
    valid = series.dropna()
    if valid.empty:
        return None

    snapshot = pd.Timestamp(snapshot_retrieved_at_utc)
    if snapshot.tzinfo is None:
        snapshot = snapshot.tz_localize("UTC")
    else:
        snapshot = snapshot.tz_convert("UTC")
    snapshot_local = snapshot.tz_convert("America/New_York").tz_localize(None)
    snapshot_month = snapshot_local.to_period("M")
    last_observation_month = valid.index.max().to_period("M")

    if last_observation_month == snapshot_month:
        return last_observation_month
    return None


def build_monthly_panel(raw_dir: str | Path = "data/raw") -> pd.DataFrame:
    """Build a panel using completed daily-source months and published monthly data."""
    raw_dir = Path(raw_dir)
    manifest_path = raw_dir / "download_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Missing {manifest_path}. Run scripts/01_download_data.py first "
            "to create source-snapshot metadata."
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    series: list[pd.Series] = []
    excluded_partial_months: dict[str, str] = {}

    for series_id in FRED_SERIES:
        path = raw_dir / "fred" / f"{series_id}.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path}. Run scripts/01_download_data.py first."
            )
        _verify_snapshot_hash(
            path,
            manifest.get("fred", {}).get(series_id, {}),
            source_label=f"FRED {series_id}",
        )
        raw_series = read_fred_csv(path, series_id)
        frequency = (
            "monthly" if series_id in MONTHLY_FRED_SERIES else "daily"
        )
        incomplete_month = None
        if frequency == "daily":
            snapshot_timestamp = _source_snapshot_timestamp(
                manifest, series_id
            )
            if snapshot_timestamp is None:
                raise ValueError(
                    f"Missing snapshot retrieval timestamp for {series_id}. "
                    "Run python scripts/01_download_data.py --refresh to "
                    "establish source-snapshot provenance."
                )
            incomplete_month = _incomplete_month_for_daily_source(
                raw_series, snapshot_timestamp
            )
            if incomplete_month is not None:
                excluded_partial_months[series_id] = str(incomplete_month)

        monthly = monthly_period_series(
            raw_series,
            source_frequency=frequency,
            incomplete_month=incomplete_month,
        )
        series.append(monthly)

    acm_path = raw_dir / "acm" / "ACMTermPremium.xls"
    if not acm_path.exists():
        raise FileNotFoundError(
            f"Missing {acm_path}. Run scripts/01_download_data.py first."
        )
    _verify_snapshot_hash(
        acm_path,
        manifest.get("acm", {}),
        source_label="New York Fed ACM workbook",
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
    panel.attrs["excluded_partial_months"] = excluded_partial_months

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
