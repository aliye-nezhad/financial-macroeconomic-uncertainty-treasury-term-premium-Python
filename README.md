# Financial and Macroeconomic Uncertainty and the U.S. Treasury Term Premium

**Python | Macro-finance | Monetary economics | Term structure | Forecast evaluation**

## Project status

Research-design and data-feasibility stage. No empirical results have been produced.

## Research question

Does financial-sector uncertainty contain incremental predictive information for changes in the U.S. 10-year Treasury term premium, beyond macroeconomic uncertainty and conventional monetary-policy and yield-curve indicators? Is that predictive information concentrated in the term-premium component rather than the expected-short-rate component of long-term yields?

## Economic motivation

Long-term nominal Treasury yields can be decomposed into an expected-short-rate component and a term-premium component. The former is closely related to the expected path of monetary policy; the latter reflects compensation for bearing interest-rate risk and other model-dependent risk-premium components.

Financial uncertainty can affect both components through competing channels. It may raise required compensation for bearing duration risk, but it may also increase demand for safe Treasury assets. It can also change expectations about future monetary easing. The direction of the relationship is therefore an empirical question.

The project compares broad financial-sector uncertainty with macroeconomic uncertainty and a market-based proxy for equity volatility. It evaluates whether these measures add predictive information for Treasury term-premium movements.

## Empirical design

- **Primary outcome:** one-month-ahead change in the U.S. 10-year ACM term premium.
- **Secondary outcome:** change in the ACM expected-average-short-rate component.
- **Alternative outcome measurement:** 10-year Kim-Wright term premium.
- **Primary uncertainty measure:** Ludvigson-Ma-Ng financial uncertainty index.
- **Comparison measure:** Ludvigson-Ma-Ng macroeconomic uncertainty index.
- **Market-based proxy:** CBOE VIX, interpreted specifically as option-implied near-term equity-market volatility, not as a comprehensive uncertainty measure.
- **Monetary/market controls:** changes in the effective federal funds rate and the 2-year Treasury yield, with timing and alternative specifications documented.

The main exercise is a nested forecasting comparison: an autoregressive benchmark, a benchmark augmented with macroeconomic uncertainty and monetary/market controls, and a model that additionally includes financial uncertainty. VIX is used in a separate proxy/robustness specification.

The common-sample analysis is expected to begin in 1990, subject to a final source and missing-data audit. The ACM-only sample may be extended further back where the predictors permit.

## Interpretation and claims

This is a predictive empirical exercise, not a causal identification design. Observed policy rates and uncertainty indexes are not exogenous shocks. The analysis will not claim that financial uncertainty causes term-premium changes.

The project does not claim a new discovery that uncertainty affects the yield curve. Existing literature studies this relationship, including recent work using dynamic term-structure models. The intended portfolio contribution is an independently implemented, transparent out-of-sample comparison of financial versus macroeconomic uncertainty, with attention to the expectations/term-premium decomposition and alternative published term-premium estimates.

The initial forecasting exercise will use the latest available data vintage. Unless historical vintages and release dates are reconstructed, it will be described as pseudo-out-of-sample rather than a genuine real-time forecasting exercise.

## Data sources

- [New York Fed Treasury Term Premia (ACM)](https://www.newyorkfed.org/research/data_indicators/term-premia-tabs): monthly end-of-month and daily estimates for maturities from one to ten years, including term premia, fitted yields, and expected average short rates.
- [JLN Macro and Financial Uncertainty Indexes](https://www.sydneyludvigson.com/macro-and-financial-uncertainty-indexes): downloadable macro, real, and financial uncertainty indexes, with vintage files.
- [FRED Kim-Wright 10-year term premium (THREEFYTP10)](https://fred.stlouisfed.org/series/THREEFYTP10): daily 10-year term premium estimates from the Kim-Wright three-factor model.
- [FRED VIXCLS](https://fred.stlouisfed.org/series/VIXCLS): daily CBOE VIX close.
- [FRED DFF](https://fred.stlouisfed.org/series/DFF): daily effective federal funds rate.
- [FRED DGS2](https://fred.stlouisfed.org/series/DGS2): daily 2-year Treasury constant-maturity yield.

Data will be retrieved programmatically where permitted. Raw files will not be committed until source terms and redistribution conditions have been reviewed. Download timestamps, URLs, file hashes, and processing metadata will be recorded.

## Planned workflow

1. Literature map and research-design audit.
2. Automated source downloads and raw-data validation.
3. Frequency alignment, transformations, and common-sample construction.
4. Descriptive analysis and benchmark time-series specifications.
5. Nested predictive models.
6. Expanding-window one-month-ahead forecasts.
7. Forecast evaluation and robustness.
8. Comparison of ACM and Kim-Wright estimates.
9. Research note, reproducibility report, and final repository audit.

See [research_design.md](docs/research_design.md), [literature_review.md](docs/literature_review.md), and [data_plan.md](docs/data_plan.md).


## Initial implementation

The first data-pipeline scaffold is now in the repository:

- `src/term_premium/data.py`: FRED and New York Fed downloads, raw-file manifest and hashes, source parsing, month-end alignment, ACM decomposition check, and panel construction.
- `scripts/01_download_data.py`: downloads/caches all source files.
- `scripts/02_build_dataset.py`: constructs the monthly panel.
- `tests/test_data.py`: initial date-alignment and FRED parsing tests.
- `requirements.txt` and `pyproject.toml`: Python dependencies and package configuration.

### Run locally

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
pytest
python scripts/01_download_data.py
python scripts/02_build_dataset.py
```

Use `python scripts/01_download_data.py --refresh` to refresh cached source snapshots.

**Verification status:** The code has been committed, but it has not yet been executed against live source downloads or run through pytest in this environment. The first local run is a data-source and parser validation step, not a reproduction of empirical results.

The constructed panel uses one-month lags for daily market predictors and two-month lags for monthly JLN/LMN uncertainty indexes. This is a conservative publication-delay convention, not an exact historical release calendar. The use of currently revised uncertainty-index observations means the exercise remains pseudo-out-of-sample rather than real-time.
