# Reproducibility and data provenance

## Status and scope

The computational modules are tested in GitHub Actions against synthetic fixtures and consistency checks for the selected archived aggregate outputs. The original source data used for the archived estimates are not committed. Therefore, a fresh checkout **cannot independently regenerate the exact published numerical results** without the preserved source snapshots. The tests verify executable code and selected table integrity; they do not constitute a full-data replication.

The forecasting exercise is pseudo-out-of-sample. The raw inputs are preserved later-vintage series, not reconstructed releases available at each historical forecast origin. The two-month lag for uncertainty indexes is a declared timing convention, not a verified release calendar.

## Reference software

The tested environment is Python 3.11.18 on Ubuntu 24.04. [requirements-locked.txt](../requirements-locked.txt) records all installed runtime and test package versions from the November 14, 2026 successful CI run. [requirements.txt](../requirements.txt) gives more flexible compatibility ranges for development.

Package versions identify the execution environment, **not** the underlying observation vintage. Even a perfectly matched Python environment cannot recover revised historical source observations.

## Obtain and test the source code

Clone this repository and run the following from its root directory:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-locked.txt
python -m pip install --no-deps -e .
python -m pip check
python -m pytest -q
```

In Windows PowerShell, create and activate the environment using:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Then run the same four `python -m` commands shown above. Exact environment matching uses Python 3.11.18 and the locked package versions. Other compatible versions may work, but are not the reference installation.

## Raw data and manifest

The original analysis uses 11 files: ten FRED series and the New York Fed ACM monthly workbook. Source details and measurement definitions are recorded in [data_plan.md](data_plan.md). The local source manifest at `data/raw/download_manifest.json` records the SHA-256 hashes and acquisition metadata.

An ordinary execution of `scripts/01_download_data.py` downloads any missing file and verifies previously recorded cached sources against the manifest. If a cached file has changed, or its original recorded hash is absent, execution stops rather than rewriting the old hash as though the file were unchanged.

```bash
python scripts/01_download_data.py
```

For an intentionally new set of data, use `python scripts/01_download_data.py --refresh`. This refresh **replaces** the local source files and updates the manifest. Keep a separate copy of the original audited snapshots and manifest before refreshing; historical vintages cannot be reconstructed from the current download endpoints.

When neither the cached files nor their manifest are present, the first run retrieves the sources and records a new snapshot. This enables a new analysis, **not** exact replication of the archived 1976–2026 numerical results.

## Full empirical execution

After restoring the audited raw snapshots and their manifest, run the numbered programs from the repository root in order:

```bash
for script in scripts/[0-9][0-9]_*.py; do
    python "$script" || exit $?
done
```

In PowerShell:

```powershell
Get-ChildItem scripts\*.py | Sort-Object Name | ForEach-Object {
    python $_.FullName
    if ($LASTEXITCODE -ne 0) { throw "Stopped at $($_.Name)" }
}
```

The sequence covers source acquisition and validation, monthly panel construction, sample auditing, model estimation, recursive forecasts, residual checks, HAC sensitivity, forecasting test sensitivity, dynamic alternatives, stability, influence diagnostics, and federal-funds-rate aggregation sensitivity.

The complete pipeline writes additional diagnostic and regression outputs locally. The curated aggregate tables in [outputs/](../outputs/README.md) come from the preserved historical analysis and are not regenerated in GitHub Actions.

## What GitHub Actions verifies

The workflow on the default branch installs the locked environment, runs `pip check`, and executes the unit tests. The tests exercise data alignment, lag timing, model nesting, forecast comparisons, source-hash checking, influence diagnostics, and consistency of selected archived CSVs.

GitHub Actions cannot execute the full empirical workflow without the source files; it therefore makes **no claim of end-to-end reproduction of the archived estimates**. Full reproduction requires the original, matching snapshots and an execution of the complete pipeline.

## Interpretation

The reported estimates describe predictive relationships, not causal effects. Sample-endpoint and real-time-information restrictions are discussed in [research_design.md](research_design.md), and the original published aggregate results are described in [empirical_results.md](empirical_results.md).
