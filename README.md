# Financial and Macroeconomic Uncertainty and the U.S. Treasury Term Premium

This study evaluates whether financial-sector uncertainty improves one-month-ahead forecasts of changes in the U.S. 10-year Treasury term premium, conditional on macroeconomic uncertainty, monetary conditions, and the yield curve. It also examines the expected-short-rate component and an alternative term-premium measure.

This is a **predictive macro-finance study**, not a causal analysis. The code covers source retrieval, monthly data construction, econometric estimation, forecast evaluation, and sensitivity checks in Python. Monetary-policy rates enter as controls; the study does **not** estimate the effects of an option-implied monetary-policy uncertainty measure. 

## Data and empirical design

The main outcome is the monthly change in the [New York Fed ACM](https://www.newyorkfed.org/research/data_indicators/term-premia-tabs) 10-year term premium. Financial and macroeconomic uncertainty are measured by the [LMN and JLN indexes](https://www.sydneyludvigson.com/macro-and-financial-uncertainty-indexes). Monetary and market controls come from FRED: the effective federal funds rate (`DFF`), its change, and the 10-year minus 2-year Treasury yield spread (`DGS10` and `DGS2`).

The nested forecasting models are:

| Model | Predictors |
| --- | --- |
| M0 | Lagged dependent variable (AR(1) benchmark) |
| M1 | M0 + federal funds rate, its change, and Treasury yield spread |
| M2 | M1 + JLN macroeconomic uncertainty |
| M3 | M2 + LMN financial uncertainty |
| M4 | M3 + VIX; estimated on a separate common sample |

Market predictors enter with one monthly lag and the JLN/LMN indexes with two monthly lags. The common M0–M3 sample runs from **July 1976 to August 2026** (602 months). Forecasts are produced recursively with an initial 120-month estimation window, yielding **482 monthly forecasts** from July 1986 to August 2026.

Models are estimated by OLS with Newey–West/HAC inference. Forecast performance is compared using RMSE, MAE, out-of-sample $R^2$, and one-sided Clark–West tests for nested specifications. Supplementary analyses consider the expected-short-rate component, the [Kim–Wright term premium](https://fred.stlouisfed.org/series/THREEFYTP10), VIX, 12-month uncertainty indexes, alternative federal-funds-rate aggregation, residual dynamics, rolling stability, and influential observations.

[Research design](docs/research_design.md) · [Data sources and timing](docs/data_plan.md) · [Literature review](docs/literature_review.md)

## Results

For the primary ACM term-premium outcome:

| Model | RMSE | MAE | Out-of-sample \(R^2\) vs. M0 |
| --- | ---: | ---: | ---: |
| M0: AR(1) | 0.231417 | 0.169517 | 0.000000 |
| M1: monetary controls | 0.233421 | 0.170520 | −0.017389 |
| M2: + JLN | 0.236000 | 0.171723 | −0.039999 |
| M3: + LMN | 0.236518 | 0.171133 | −0.044572 |

Adding LMN does not improve forecast accuracy relative to M2 or the AR(1) benchmark. The M2-to-M3 Clark–West test has a one-sided **p-value of 0.340455**. The main conclusion is also unchanged in the alternative term-premium, uncertainty-horizon, VIX, and federal-funds-rate aggregation comparisons.

The expected-short-rate component shows a negative LMN coefficient in the full-sample regression, but the richer model has a higher forecast RMSE than AR(1), and the nested comparisons do not remain significant after the reported family-wise multiple-testing adjustment. Rolling comparisons and influence diagnostics likewise do not establish a persistent forecasting advantage for LMN.

[Full results and interpretation](docs/empirical_results.md) · [Primary forecast accuracy](outputs/forecasting/forecast_accuracy_acm_term_premium_1m.csv) · [Primary Clark–West tests](outputs/forecasting/clark_west_acm_term_premium_1m.csv) · [Selected output files](outputs/README.md)

## Reproducing the analysis

The reference test environment is Python **3.11.18** with packages recorded in [requirements-locked.txt](requirements-locked.txt). From the repository root, create an environment, install the locked dependencies, and run the tests:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-locked.txt
python -m pip install --no-deps -e .
python -m pip check
python -m pytest -q
```

To build the data and run the analyses in order:

```powershell
Get-ChildItem scripts\*.py | Sort-Object Name | ForEach-Object {
    python $_.FullName
    if ($LASTEXITCODE -ne 0) { throw "Stopped at $($_.Name)" }
}
```

The first script downloads inputs when they are absent and verifies cached inputs against their original SHA-256 manifest when present. It stops rather than silently adopting changed or unrecorded cached files. Use `python scripts/01_download_data.py --refresh` only to deliberately acquire a **new** snapshot, which may change the empirical results. Raw files, the snapshot manifest, and most generated results remain local; selected aggregate results from the audited snapshot are committed under `outputs/`. The complete [reproduction guide](docs/REPRODUCIBILITY.md) includes Linux, macOS, and Windows commands. The audited source fingerprints are provided in [`docs/audited_source_hashes.json`](docs/audited_source_hashes.json). When the original preserved raw files and their manifest are available locally, `python -m tools.verify_primary_reproduction` checks all eleven source hashes, re-estimates M0–M3, regenerates the 482 recursive forecasts, and compares the numerical results to the published tables without overwriting them. This source-dependent check is not run by GitHub Actions.

**Reproduction limit:** The original 11 raw source snapshots are not redistributed. As a result, the public repository permits code execution and methodological inspection, but **does not by itself permit independent reproduction of the exact archived estimates**. Current downloads may differ because providers revise historical series. GitHub Actions runs the source-free test suite and validates selected archived outputs; it does not regenerate the full empirical analysis. The forecasting exercise is *pseudo-out-of-sample*, not a reconstruction of historical information vintages or publication calendars. The two-month uncertainty lag is an explicit timing convention. Source-data redistribution remains subject to provider terms.

## Repository structure

```text
├── .github/
│   └── workflows/
│       └── tests.yml
├── docs/
│   ├── audited_source_hashes.json
│   ├── data_plan.md
│   ├── empirical_results.md
│   ├── literature_review.md
│   ├── REPRODUCIBILITY.md
│   └── research_design.md
├── outputs/
│   ├── dff_aggregation_sensitivity/
│   │   ├── fedfunds_validation_summary.csv
│   │   └── forecast_accuracy.csv
│   ├── diagnostics/
│   │   └── m3_influence_summary.csv
│   ├── forecasting/
│   │   ├── clark_west_acm_term_premium_1m.csv
│   │   ├── forecast_accuracy_acm_expected_short_rate_1m.csv
│   │   ├── forecast_accuracy_acm_term_premium_1m.csv
│   │   └── forecast_accuracy_kim_wright_term_premium_1m.csv
│   └── README.md
├── scripts/
│   ├── 01_download_data.py
│   ├── 02_build_dataset.py
│   ├── 03_data_audit.py
│   ├── 04_estimate_models.py
│   ├── 05_forecast_evaluation.py
│   ├── 06_residual_diagnostics.py
│   ├── 07_hac_sensitivity.py
│   ├── 08_forecast_test_sensitivity.py
│   ├── 09_dynamic_specification_sensitivity.py
│   ├── 10_stability_analysis.py
│   ├── 11_influence_sensitivity.py
│   └── 12_dff_aggregation_sensitivity.py
├── src/
│   └── term_premium/
│       ├── __init__.py
│       ├── analysis.py
│       ├── data.py
│       └── diagnostics.py
├── tests/
│   ├── test_analysis.py
│   ├── test_data_audit.py
│   ├── test_data.py
│   ├── test_diagnostics.py
│   ├── test_panel_timing.py
│   ├── test_primary_reproduction.py
│   ├── test_published_results.py
│   └── test_review_bundle.py
├── tools/
│   ├── prepare_review_bundle.py
│   └── verify_primary_reproduction.py
├── .gitattributes
├── .gitignore
├── .python-version
├── LICENSE
├── pyproject.toml
├── README.md
├── requirements-locked.txt
└── requirements.txt
```

The `tools/prepare_review_bundle.py` command creates a local ZIP of selected existing outputs and their checksums after verifying the preserved raw-data manifest. The ZIP does not include source observations or estimation samples.

## Author

Aliye Nezhad

## License

The analysis code and original project documentation are available under the [MIT License](LICENSE). The source datasets and third-party material remain subject to their respective providers' terms.
