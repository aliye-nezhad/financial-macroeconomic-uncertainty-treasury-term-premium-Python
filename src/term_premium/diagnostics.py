"""Non-destructive data-quality diagnostics for monthly macro-financial panels.

Extreme-observation flags are screening aids only. They never modify, winsorize,
or delete observations.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


MODIFIED_Z_CUTOFF = 3.5
_MAD_NORMAL_CONSISTENCY = 0.6744897501960817


def missingness_profile(series: pd.Series) -> dict[str, int | float | str | None]:
    """Separate leading, interior, and trailing missingness in a time series."""
    observed_positions = np.flatnonzero(series.notna().to_numpy())
    n_total = int(len(series))
    n_missing = int(series.isna().sum())

    if len(observed_positions) == 0:
        return {
            "first_valid": None,
            "last_valid": None,
            "n_observations": 0,
            "n_missing": n_missing,
            "leading_missing": n_total,
            "interior_missing": 0,
            "trailing_missing": 0,
            "missing_share": 1.0 if n_total else 0.0,
        }

    first = int(observed_positions[0])
    last = int(observed_positions[-1])
    return {
        "first_valid": str(series.index[first]),
        "last_valid": str(series.index[last]),
        "n_observations": int(len(observed_positions)),
        "n_missing": n_missing,
        "leading_missing": first,
        "interior_missing": int(series.iloc[first : last + 1].isna().sum()),
        "trailing_missing": n_total - last - 1,
        "missing_share": float(n_missing / n_total) if n_total else 0.0,
    }


def modified_z_scores(series: pd.Series) -> pd.Series:
    """Calculate robust modified z-scores using the median absolute deviation.

    If the MAD is zero or undefined, scores are returned as NaN rather than
    substituting a fragile scale estimate.
    """
    numeric = pd.to_numeric(series, errors="coerce").astype(float)
    numeric = numeric.where(np.isfinite(numeric))
    median = numeric.median()
    mad = (numeric - median).abs().median()

    if not np.isfinite(mad) or mad <= 0:
        return pd.Series(np.nan, index=series.index, name="modified_z")

    scores = _MAD_NORMAL_CONSISTENCY * (numeric - median) / mad
    scores.name = "modified_z"
    return scores


def extreme_observation_table(
    panel: pd.DataFrame,
    *,
    level_variables: list[str],
    change_variables: list[str],
    threshold: float = MODIFIED_Z_CUTOFF,
) -> pd.DataFrame:
    """List robust-z extreme observations without changing the source panel.

    Level variables are screened both in levels and first differences.
    Variables already expressed as monthly changes are screened as stored.
    The conventional absolute modified-z threshold is 3.5; flags require
    manual review because crisis episodes and regime changes can be genuine.
    """
    if threshold <= 0:
        raise ValueError("threshold must be positive.")

    rows: list[dict[str, object]] = []
    specifications: list[tuple[str, str, pd.Series]] = []

    for variable in level_variables:
        if variable not in panel:
            continue
        source = panel[variable]
        specifications.append((variable, "level", source))
        specifications.append((variable, "first_difference", source.diff()))

    for variable in change_variables:
        if variable not in panel:
            continue
        specifications.append((variable, "monthly_change", panel[variable]))

    for variable, transformation, values in specifications:
        numeric = pd.to_numeric(values, errors="coerce").astype(float)
        numeric = numeric.where(np.isfinite(numeric))
        scores = modified_z_scores(numeric)
        flagged = scores.abs().gt(threshold).fillna(False)
        if not flagged.any():
            continue

        median = float(numeric.median())
        mad = float((numeric - median).abs().median())
        for date in numeric.index[flagged]:
            score = float(scores.loc[date])
            rows.append(
                {
                    "variable": variable,
                    "transformation": transformation,
                    "month": str(date),
                    "value": float(numeric.loc[date]),
                    "median": median,
                    "mad": mad,
                    "modified_z": score,
                    "absolute_modified_z": abs(score),
                    "threshold": float(threshold),
                    "review_note": (
                        "Flag for inspection only; do not delete automatically."
                    ),
                }
            )

    columns = [
        "variable",
        "transformation",
        "month",
        "value",
        "median",
        "mad",
        "modified_z",
        "absolute_modified_z",
        "threshold",
        "review_note",
    ]
    result = pd.DataFrame(rows, columns=columns)
    if not result.empty:
        result = result.sort_values(
            "absolute_modified_z", ascending=False
        ).reset_index(drop=True)
    return result
