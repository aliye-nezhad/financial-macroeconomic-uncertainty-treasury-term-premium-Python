# Financial and Macroeconomic Uncertainty and the U.S. Treasury Term Premium

I examine whether financial-sector uncertainty improves one-month-ahead forecasts of changes in the U.S. 10-year Treasury term premium, after accounting for macroeconomic uncertainty, monetary conditions, and the yield curve. I also compare the expected-short-rate component and an alternative estimate of the term premium.

This is a **predictive macro-finance study**, not a causal analysis. The code covers source retrieval, monthly data construction, econometric estimation, forecast evaluation, and sensitivity checks in Python.

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

I estimate the regressions by OLS with Newey–West/HAC inference and compare forecasts using RMSE, MAE, out-of-sample \(R^2\), and one-sided Clark–West tests for nested specifications. The supplementary checks examine the expected-short-rate component, the [Kim–Wright term premium](https://fred.stlouisfed.org/series/THREEFYTP10), VIX, 12-month uncertainty indexes, alternative federal-funds-rate aggregation, residual dynamics, rolling stability, and influential observations.

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

The workflow is tested with Python 3.11. From the repository root, create an environment, install the dependencies, and run the tests:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q
```

To build the data and run the analyses in order:

```powershell
Get-ChildItem scripts\*.py | Sort-Object Name | ForEach-Object {
    python $_.FullName
    if ($LASTEXITCODE -ne 0) { throw "Stopped at $($_.Name)" }
}
```

The first script downloads the source files **only if they are not already cached**. Normal runs do not refresh existing snapshots; `python scripts/01_download_data.py --refresh` explicitly replaces them. Raw files, their SHA-256 manifest, and most generated results are kept locally. Selected aggregate results from the audited snapshot are committed under `outputs/`.

**Reproduction limit:** the preserved raw snapshots behind the reported numbers are not redistributed here. Running from newly downloaded data can yield different results because source series are revised. The exercise is *pseudo-out-of-sample*: it does not reconstruct the exact information vintages available to forecasters at each historical date. The two-month uncertainty lag is a conservative timing convention, not a historical publication-calendar reconstruction. The raw-data licenses and redistribution terms remain with their original providers.

## Repository structure

```text
├── .github/workflows/tests.yml
├── docs/
│   ├── data_plan.md
│   ├── empirical_results.md
│   ├── literature_review.md
│   └── research_design.md
├── outputs/
│   ├── README.md
│   ├── diagnostics/
│   ├── dff_aggregation_sensitivity/
│   └── forecasting/
├── scripts/                     # 01–12: download, build, estimate, forecast, check
├── src/term_premium/            # Source handling, models, and diagnostics
├── tests/                       # Data, timing, inference, and forecast tests
├── tools/prepare_review_bundle.py
├── requirements.txt
├── pyproject.toml
└── LICENSE
```

The `tools/prepare_review_bundle.py` command creates a local ZIP of selected existing outputs and their checksums after verifying the preserved raw-data manifest. The ZIP does not include source observations or estimation samples.

## Author

Aliye Nezhad

## License

The analysis code and original project documentation are available under the [MIT License](LICENSE). The source datasets and third-party material remain subject to their respective providers' terms.
