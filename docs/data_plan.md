# Data Plan and Source Registry

## Data acquisition principle
Download source data programmatically. Preserve unmodified raw snapshots locally, record per-source snapshot retrieval timestamps and SHA-256 hashes, and never silently overwrite a source snapshot. The analysis must be reproducible from saved raw files after the initial download. A normal run reuses cached files. An explicit `--refresh` replaces the cached source file and updates its manifest entry; the manifest records the replacement snapshot's timestamp and hash, but does not archive the previous file. Preserve a separate copy of any raw snapshot that must remain available for historical-vintage comparisons.

Do not commit raw data until redistribution and source terms have been checked. The code should support a local raw-data cache and an explicit refresh option.

## Core sources

| Concept | Source / series | Frequency | Role |
|---|---|---|---|
| 10-year ACM term premium | New York Fed ACM workbook | Monthly, end of month | Primary outcome |
| ACM expected average short rate | New York Fed ACM workbook | Monthly, end of month | Secondary outcome |
| 10-year Kim-Wright term premium | FRED THREEFYTP10 | Daily | Alternative outcome |
| Financial uncertainty | FRED LMNUF1M | Monthly | Main predictor |
| Macroeconomic uncertainty | FRED JLNUM1M | Monthly | Comparator |
| Equity-market implied volatility | FRED VIXCLS | Daily | Proxy / robustness |
| Effective federal funds rate | FRED DFF | Daily | Primary month-end monetary-policy control; monthly-mean sensitivity |
| Official monthly effective federal funds rate | FRED FEDFUNDS | Monthly average | Validation reference for the daily-DFF monthly-mean sensitivity; not a model predictor |
| 2-year Treasury yield | FRED DGS2 | Daily | Yield-curve control |
| 10-year Treasury yield | FRED DGS10 | Daily | Yield-curve slope construction |

## Source notes

### New York Fed ACM
Official landing page: https://www.newyorkfed.org/research/data_indicators/term-premia-tabs

The New York Fed provides daily and monthly estimates for maturities from one to ten years, including term premia, fitted yields, and expected average short rates. Monthly observations are end-of-month estimates. The data are model estimates and are not official estimates of the Federal Reserve System or FOMC.

The downloader must inspect the current workbook and verify sheet names and column names rather than assume them.

### Uncertainty indexes
- LMNUF1M: LMN 1-month-ahead financial uncertainty, from Ludvigson, Ma and Ng.
- JLNUM1M: JLN 1-month-ahead macroeconomic uncertainty, from Jurado, Ludvigson and Ng.

Both are monthly indexes. They have different underlying research frameworks and should not be interpreted as having directly comparable levels. FRED series pages provide definitions and current observations. Data are revised; the first project version will use current vintages and must be described as pseudo-out-of-sample.

### FRED daily series
- THREEFYTP10: Kim-Wright 10-year zero-coupon term premium.
- VIXCLS: CBOE VIX close.
- DFF: effective federal funds rate.
- FEDFUNDS: official monthly average of the effective federal funds rate; retained as a validation reference for the monthly mean computed from daily DFF, not as a model predictor.
- DGS2: 2-year Treasury constant-maturity yield.
- DGS10: 10-year Treasury constant-maturity yield.

For alignment with ACM month-end data, use the last valid observation in each calendar month for daily series. Month-end DFF is the primary monetary-policy measure. Do not replace it with a monthly average in the baseline. A monthly-average DFF aggregation is a supplementary sensitivity check and must be validated against the official monthly FEDFUNDS series. FEDFUNDS is not entered as an additional predictor.

FRED graph CSV endpoints can be used without a FRED API key for initial acquisition, subject to endpoint stability and series terms. The official FRED API may be added later with a key stored in an environment variable, never committed to the repository.

## Initial sample
A comparison that includes the Kim-Wright 10-year term-premium measure cannot begin before its available history, which starts in January 1990. This is not a global restriction on the primary ACM-only analysis: the M0-M3 ACM hierarchy uses its own longest common sample and can begin earlier. The initial empirical results accordingly report an ACM-only sample beginning in July 1976, while the Kim-Wright comparison uses its shorter available history. Each outcome and model hierarchy must report its own complete-case sample dates rather than imply that every exercise uses one global sample.

FRED metadata confirms that JLNUM1M and JLNUM12M are monthly JLN measures, while LMNUF1M and LMNUF12M are monthly LMN financial-uncertainty measures; the latter series is valid and is not a typo. The final start date and end date must be determined from actual downloaded data and complete-case availability.

## Frequency and timing rules
1. Parse all dates explicitly and use a month-end PeriodIndex internally.
2. For daily series, select the last non-missing observation in each completed calendar month. If the source snapshot was retrieved during the same month as its latest daily observation, exclude that incomplete month from the processed panel. Preserve the raw observation and its original snapshot timestamp; a later refreshed snapshot can make the month eligible.
3. For monthly series, preserve the observation month; do not silently shift dates.
4. Construct the yield-curve slope as month-end DGS10 minus DGS2.
5. Construct changes only after monthly alignment.
6. For the one-month-ahead forecast, predictors must be available at the forecast origin and the target must be the subsequent month's change.
7. Because current uncertainty-index data may be revised and are not necessarily available at the historical forecast origin, label the exercise pseudo-out-of-sample.

## Validation checks
- Unique, monotonic dates.
- Expected frequency and date range.
- Numeric values and missing-value codes handled explicitly.
- No duplicate months after aggregation.
- No accidental forward filling of missing observations.
- Month-end alignment verified against source data.
- ACM yield decomposition identity checked to the extent supported by workbook columns and definitions.
- Kim-Wright and ACM series not assumed to be numerically identical.
- Missingness table and common-sample dates saved to outputs.
- Raw source files hashed and recorded in a manifest; panel construction verifies each file against its recorded SHA-256 hash and stops if a file has changed or the manifest lacks its hash.

## Programmatic download implementation
Create separate functions for:
- Downloading FRED graph CSV series.
- Downloading the current ACM workbook.
- Saving raw files without modification.
- Recording metadata and SHA-256 hashes.
- Parsing each source into a standardized monthly format.

Do not mix downloading, cleaning, variable construction, and estimation in one script.
