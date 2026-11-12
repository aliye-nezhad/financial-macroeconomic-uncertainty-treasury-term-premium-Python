"""Non-destructive data-quality diagnostics for monthly macro-financial panels.

Extreme-observation flags are screening aids only. They never modify, winsorize,
or delete observations.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence


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


def _validated_regression_design(
    sample: pd.DataFrame,
    *,
    outcome: str,
    predictors: list[str],
    focal_predictor: str,
) -> tuple[pd.Series, pd.DataFrame, int]:
    """Validate a consecutive monthly regression sample and return its design."""
    if not predictors or len(set(predictors)) != len(predictors):
        raise ValueError("predictors must be a non-empty list without duplicates.")
    if focal_predictor not in predictors:
        raise ValueError("focal_predictor must be included in predictors.")

    required = [outcome, *predictors]
    missing = [column for column in required if column not in sample.columns]
    if missing:
        raise KeyError(f"Sample is missing regression variables: {missing}.")
    if not isinstance(sample.index, pd.PeriodIndex):
        raise TypeError("The regression sample must use a monthly PeriodIndex.")
    if sample.index.freqstr not in {"M", "ME"}:
        raise ValueError("The regression sample must use monthly frequency.")
    if not sample.index.is_unique or not sample.index.is_monotonic_increasing:
        raise ValueError("The monthly index must be unique and sorted.")

    expected = pd.period_range(sample.index.min(), sample.index.max(), freq="M")
    if not sample.index.equals(expected):
        raise ValueError("The regression sample must contain consecutive months.")

    numeric = sample[required].apply(pd.to_numeric, errors="coerce")
    values = numeric.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("The regression sample contains missing or non-finite values.")

    y = numeric[outcome].astype(float)
    X = sm.add_constant(numeric[predictors].astype(float), has_constant="add")
    nobs, n_parameters = X.shape
    if nobs <= n_parameters + 1:
        raise ValueError("The sample must exceed the number of parameters by at least two.")
    if np.linalg.matrix_rank(X.to_numpy(dtype=float)) < n_parameters:
        raise ValueError("The regression design matrix is rank deficient.")
    return y, X, int(X.columns.get_loc(focal_predictor))


def regression_influence_table(
    sample: pd.DataFrame,
    *,
    outcome: str,
    predictors: list[str],
    focal_predictor: str,
) -> pd.DataFrame:
    """Calculate conventional OLS influence diagnostics for a monthly model.

    Cook's distance, leverage, externally studentized residuals, DFFITS and
    DFBETAS are screening diagnostics. Their common rules of thumb are not
    formal outlier tests, do not account for HAC covariance estimation, and
    must never trigger automatic observation deletion.
    """
    y, X, focal_position = _validated_regression_design(
        sample,
        outcome=outcome,
        predictors=predictors,
        focal_predictor=focal_predictor,
    )
    fitted = sm.OLS(y, X, missing="raise").fit()
    influence = OLSInfluence(fitted)

    nobs, n_parameters = X.shape
    cooks_distance = np.asarray(influence.cooks_distance[0], dtype=float)
    leverage = np.asarray(influence.hat_matrix_diag, dtype=float)
    studentized_residual = np.asarray(
        influence.resid_studentized_external,
        dtype=float,
    )
    dffits = np.asarray(influence.dffits[0], dtype=float)
    focal_dfbetas = np.asarray(
        influence.dfbetas[:, focal_position],
        dtype=float,
    )

    leverage_cutoff = 2.0 * n_parameters / nobs
    cooks_cutoff = 4.0 / (nobs - n_parameters)
    studentized_cutoff = 3.0
    dffits_cutoff = 2.0 * np.sqrt(n_parameters / nobs)
    dfbetas_cutoff = 2.0 / np.sqrt(nobs)

    leverage_flag = leverage > leverage_cutoff
    cooks_flag = cooks_distance > cooks_cutoff
    studentized_flag = np.abs(studentized_residual) > studentized_cutoff
    dffits_flag = np.abs(dffits) > dffits_cutoff
    dfbetas_flag = np.abs(focal_dfbetas) > dfbetas_cutoff

    return pd.DataFrame(
        {
            "month": sample.index.astype(str),
            "outcome": outcome,
            "focal_predictor": focal_predictor,
            "nobs": nobs,
            "n_parameters_including_constant": n_parameters,
            "leverage": leverage,
            "leverage_cutoff": leverage_cutoff,
            "leverage_flag": leverage_flag,
            "studentized_residual": studentized_residual,
            "absolute_studentized_residual": np.abs(studentized_residual),
            "studentized_residual_cutoff": studentized_cutoff,
            "studentized_residual_flag": studentized_flag,
            "cooks_distance": cooks_distance,
            "cooks_distance_cutoff": cooks_cutoff,
            "cooks_distance_flag": cooks_flag,
            "dffits": dffits,
            "absolute_dffits": np.abs(dffits),
            "dffits_cutoff": dffits_cutoff,
            "dffits_flag": dffits_flag,
            "focal_predictor_dfbetas": focal_dfbetas,
            "absolute_focal_predictor_dfbetas": np.abs(focal_dfbetas),
            "dfbetas_cutoff": dfbetas_cutoff,
            "dfbetas_flag": dfbetas_flag,
            "flagged_by_any_rule": (
                leverage_flag
                | studentized_flag
                | cooks_flag
                | dffits_flag
                | dfbetas_flag
            ),
            "review_note": (
                "Screening flag only; inspect the observation and its economic "
                "context. Do not delete automatically."
            ),
        }
    )


def leave_one_month_out_coefficient_table(
    sample: pd.DataFrame,
    *,
    outcome: str,
    predictors: list[str],
    focal_predictor: str,
) -> pd.DataFrame:
    """Re-estimate the focal OLS coefficient after omitting each month in turn.

    This is a point-estimate influence exercise only. Omitting an interior
    month creates a gap, so the resulting rows must not be treated as an
    equally spaced time series for HAC inference or forecast evaluation.
    No standard errors or p-values are calculated for these deletion samples.
    """
    y, X, focal_position = _validated_regression_design(
        sample,
        outcome=outcome,
        predictors=predictors,
        focal_predictor=focal_predictor,
    )
    design = X.to_numpy(dtype=float)
    dependent = y.to_numpy(dtype=float)
    full_coefficients, _, full_rank, _ = np.linalg.lstsq(
        design,
        dependent,
        rcond=None,
    )
    if full_rank < design.shape[1]:
        raise ValueError("The full-sample regression design is rank deficient.")

    full_coefficient = float(full_coefficients[focal_position])
    rows: list[dict[str, object]] = []
    for position, month in enumerate(sample.index):
        retained = np.ones(len(sample), dtype=bool)
        retained[position] = False
        deleted_design = design[retained]
        deleted_dependent = dependent[retained]
        coefficients, _, rank, _ = np.linalg.lstsq(
            deleted_design,
            deleted_dependent,
            rcond=None,
        )
        deleted_coefficient = (
            float(coefficients[focal_position])
            if rank == design.shape[1]
            else np.nan
        )
        change = deleted_coefficient - full_coefficient
        relative_change = (
            100.0 * change / abs(full_coefficient)
            if np.isfinite(change) and abs(full_coefficient) > 1e-12
            else np.nan
        )
        rows.append(
            {
                "excluded_month": str(month),
                "outcome": outcome,
                "focal_predictor": focal_predictor,
                "nobs_after_exclusion": len(sample) - 1,
                "full_sample_coefficient": full_coefficient,
                "leave_one_month_out_coefficient": deleted_coefficient,
                "coefficient_change": change,
                "absolute_coefficient_change": (
                    abs(change) if np.isfinite(change) else np.nan
                ),
                "relative_change_percent_of_absolute_full_sample_coefficient": (
                    relative_change
                ),
                "rank_preserved": bool(rank == design.shape[1]),
                "inference_note": (
                    "Point estimate only; no HAC standard error or p-value."
                ),
            }
        )
    return pd.DataFrame(rows)
