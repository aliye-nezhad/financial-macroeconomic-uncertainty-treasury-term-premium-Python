# Literature Review and Research Positioning

## Purpose and status

This is a focused review of the closest literature relevant to the project's question. It is not a systematic review of every paper on uncertainty and the yield curve. The sources below are sufficient to rule out broad novelty claims, but the literature search should be extended before this project is presented as an original research contribution.

The project asks whether financial-sector uncertainty contains incremental **pseudo-out-of-sample predictive information** for monthly changes in the U.S. 10-year Treasury term premium, conditional on macroeconomic uncertainty and conventional monetary/market controls. It also examines the ACM expected-short-rate component and an alternative Kim-Wright term-premium estimate.

The project is predictive, not causal. The distinction between forecasting a model-estimated term-premium change and identifying the response of yields or term premia to an uncertainty shock is central to the positioning below.

## Measuring macroeconomic and financial uncertainty

**Jurado, Kyle, Sydney C. Ludvigson, and Serena Ng (2015). "Measuring Uncertainty." American Economic Review, 105(3), 1177–1216.**

Develops econometric measures of macroeconomic uncertainty from a large information set. It motivates distinguishing conditional uncertainty from simple observed volatility proxies.

- Paper: https://www.aeaweb.org/articles?id=10.1257/aer.20131193
- JLN data: https://fred.stlouisfed.org/series/JLNUM1M

**Ludvigson, Sydney C., Sai Ma, and Serena Ng (2021). "Uncertainty and Business Cycles: Exogenous Impulse or Endogenous Response?" American Economic Journal: Macroeconomics, 13(4), 369–410.**

Develops macroeconomic, real, and financial uncertainty measures and studies their business-cycle relationships. The LMN financial uncertainty index is a central predictor in this project.

- Article: https://www.aeaweb.org/articles?id=10.1257/mac.20190029
- Author data page: https://www.sydneyludvigson.com/macro-and-financial-uncertainty-indexes
- LMN data: https://fred.stlouisfed.org/series/LMNUF1M

## Term-premium measurement

**Adrian, Tobias, Richard K. Crump, and Emanuel Moench (2013). "Pricing the Term Structure with Linear Regressions." Journal of Financial Economics, 110(1), 110–138.**

Provides the affine term-structure approach used by the New York Fed to estimate fitted yields, expected average short rates, and term premia. The ACM estimates are model-dependent latent components, not directly observed prices.

- New York Fed data and model information: https://www.newyorkfed.org/research/data_indicators/term-premia-tabs

**Kim, Don H. and Jonathan H. Wright (2005). "An Arbitrage-Free Three-Factor Term Structure Model and the Recent Behavior of Long-Term Yields and Distant-Horizon Forward Rates." Federal Reserve Board Finance and Economics Discussion Series 2005-33.**

Provides an alternative model-based term-premium estimate distributed through FRED as THREEFYTP10. It is a distinct measurement, not an interchangeable version of ACM.

- FRED series: https://fred.stlouisfed.org/series/THREEFYTP10

## Closest related empirical studies

### Castelnuovo (2019): financial uncertainty and the yield curve

**Castelnuovo, Efrem (2019). "Yield Curve and Financial Uncertainty: Evidence Based on US Data." Australian Economic Review, 52(3), 323–335.**

The study uses U.S. monthly data from 1962–2018 and local projections to estimate the response of Treasury rates at several maturities to a one-standard-deviation increase in the LMN financial uncertainty measure. The maturities include 3-month, 6-month, 1-year, 5-year, and 10-year rates. The specification controls for inflation, industrial-production growth, and lagged interest rates. The estimated responses are negative across maturities, with a larger response at the short end and a temporary steepening of the yield curve.

**Overlap:** It already establishes a close empirical relationship between LMN financial uncertainty and U.S. interest rates across the yield curve. The use of LMN uncertainty and Treasury-rate outcomes is therefore not new.

**Difference from this project:** Castelnuovo studies impulse responses of yields using local projections. This project evaluates one-month-ahead predictive performance for changes in model-estimated 10-year term-premium components, comparing LMN with JLN and conventional controls. It does not estimate causal or structural responses to uncertainty shocks.

- Working paper and PDF: https://melbourneinstitute.unimelb.edu.au/publications/working-papers/search/result?paper=3095815
- Published article: https://doi.org/10.1111/1467-8462.12341

### Kumar, Mallick, Mohanty, and Zampolli (2023): market volatility and the term premium

**Kumar, Abhishek, Sushanta Mallick, Madhusudan Mohanty, and Fabrizio Zampolli (2023). "Market Volatility, Monetary Policy and the Term Premium." Oxford Bulletin of Economics and Statistics, 85(1), 208–237.**

Uses time-varying VAR models to study option-implied equity and bond-market volatility, monetary policy, macroeconomic variables, and the government-bond term premium. It emphasizes the need to jointly identify VIX and MOVE shocks because the two volatility measures are highly correlated. The paper reports that a positive VIX shock reduces the term premium, while a positive MOVE shock raises it.

**Overlap:** The paper directly studies market volatility, monetary policy, and the term premium. It also shows why different forms of financial-market uncertainty should not be treated as equivalent.

**Difference from this project:** Its focus is structural shock dynamics using option-implied VIX and MOVE measures. This project uses the LMN financial-uncertainty index as its main financial measure, JLN as a macroeconomic comparator, and VIX as an additional proxy. Its target is forecast performance, not structural impulse responses.

- Published article: https://doi.org/10.1111/obes.12518
- Earlier BIS working-paper version: https://www.bis.org/publ/work606.htm

### Cross, Poon, and Zhu (2026): uncertainty and the term structure of interest rates

**Cross, Jamie L., Aubrey Poon, and Dan Zhu (2026). "Uncertainty and the Term Structure of Interest Rates." European Economic Review, 187, 105352.**

This is the closest and most important recent reference for the project's broad research area.

The paper uses U.S. Treasury yield-curve data from 1971M8 to 2020M12 and a Bayesian Yields-Macro Dynamic Nelson–Siegel model. It studies three uncertainty measures: LMN financial uncertainty, JLN macroeconomic uncertainty, and Baker-Bloom-Davis economic policy uncertainty. The macroeconomic controls include capacity utilization, unemployment, CPI inflation, and the shadow federal funds rate. The uncertainty measure is placed first in the recursively identified macroeconomic block.

The paper finds that unexpected increases in uncertainty are associated with a lower, steeper, and less curved yield curve. It also examines the expectations and term-premium components through counterfactual exercises for the Great Recession and COVID-19 episodes. Those counterfactuals imply lower expected future short rates and higher term premia under heightened uncertainty.

**Overlap:** The paper studies the same broad U.S. Treasury/uncertainty nexus, uses both LMN and JLN uncertainty measures, examines the yield-curve decomposition, and directly discusses expected short rates and term premia. It rules out any claim that the broad relationship or the use of these uncertainty measures to study the term structure is new.

**Difference from this project:** Cross, Poon, and Zhu estimate a structural yield-curve system and study uncertainty shocks, factor responses, and episode-specific counterfactual decompositions. They do not present the same nested one-month-ahead pseudo-out-of-sample forecasting exercise comparing the incremental forecast value of LMN relative to JLN and monetary/market controls for changes in the ACM term premium. Their term-premium decomposition is based on the expectations-hypothesis counterfactual within their model, rather than a direct forecasting comparison across ACM and Kim-Wright term-premium estimates.

The distinction is methodological and empirical, not a claim that the underlying economic relationship is undiscovered.

- Published article: https://doi.org/10.1016/j.euroecorev.2026.105352
- Open-access publisher PDF in the University of Kent repository: https://kar.kent.ac.uk/113848/19/1-s2.0-S0014292126000966-main.pdf
- Repository record: https://kar.kent.ac.uk/113848/

### Additional term-structure studies on policy and macroeconomic uncertainty

**Creal, Drew D., and Jing Cynthia Wu (2017). "Monetary Policy Uncertainty and Economic Fluctuations." International Economic Review, 58(4), 1317–1354.**

Creal and Wu develop a no-arbitrage term-structure model in which latent yield-volatility factors can affect the conditional means of macroeconomic variables and yield factors. The accessible earlier NBER working-paper version describes two dimensions of interest-rate uncertainty, short-term and long-term, and estimates the nonlinear, non-Gaussian state-space model using Bayesian MCMC and particle-filter methods. The published 2017 version is titled *Monetary Policy Uncertainty and Economic Fluctuations*. This is a model-based treatment of uncertainty embedded in yield volatility, not the externally constructed LMN/JLN index comparison used here.

**Overlap:** The paper places uncertainty directly inside a macro-finance term-structure framework and distinguishes uncertainty dimensions.

**Difference:** Its focus is a model-based term-structure and macroeconomic-fluctuation analysis, not the incremental pseudo-out-of-sample predictive value of LMN financial uncertainty relative to JLN macroeconomic uncertainty in monthly ACM term-premium changes.

- Article: https://doi.org/10.1111/iere.12253
- NBER working-paper version: https://www.nber.org/papers/w20594

**Tillmann, Peter (2020). "Monetary Policy Uncertainty and the Response of the Yield Curve to Policy Shocks." Journal of Money, Credit and Banking, 52(4), 803–833.**

Tillmann uses interacted local projections to estimate yield-curve responses to monetary-policy shocks conditional on several monetary-policy-uncertainty measures. The baseline sample is monthly, January 1994-November 2015. The paper uses ACM fitted yields and their expectations/term-premium components, with Kim-Wright estimates as an alternative measurement check. Its primary shock is the daily change in the 2-year Treasury yield on FOMC meeting days, with an alternative high-frequency shock series. The uncertainty measures include a newspaper-based monetary-policy uncertainty index, survey-based interest-rate uncertainty, and squared monetary-policy surprises. Long-term yields rise less after a tightening when policy uncertainty is high, with the weaker response attributed to a stronger fall in term premia.

**Overlap:** It directly examines the term-premium component and shows that uncertainty conditions can alter the yield-curve response to monetary-policy shocks.

**Difference:** The uncertainty concept is monetary-policy uncertainty, and the design studies conditional responses to identified policy shocks rather than the monthly forecast contribution of LMN financial uncertainty. Because Tillmann already uses both ACM and Kim-Wright term-premium measurements, this project must not present the use of those two measurement families itself as novel; the distinction must rest on the LMN-versus-JLN incremental forecasting question and its evaluation design.

- Article: https://doi.org/10.1111/jmcb.12657
- Earlier working-paper version: https://www.cb.cityu.edu.hk/ef/doc/GRU/WPS/GRU%232018-004%20Tillmann(1).pdf

**Leippold, Markus, and Felix Matthys (2022). "Economic Policy Uncertainty and the Yield Curve." Review of Finance, 26(4), 751–797.**

The paper combines a general-equilibrium model with empirical analysis of economic-policy uncertainty and the nominal yield curve. It reports that higher policy uncertainty is associated with lower yield levels and higher yield volatility, predicts future short rates, and has an ambiguous effect on term premia; the response of bond risk premia differs by maturity.

**Overlap:** It explicitly links policy uncertainty, expected short rates, yield volatility and bond risk premia.

**Difference:** Its focus is economic-policy uncertainty and a structural/theoretical term-structure framework, not LMN-versus-JLN incremental forecast evaluation for monthly changes in the ACM 10-year term premium.

- Article: https://doi.org/10.1093/rof/rfac031
- Earlier working-paper version (2015): https://www.frbsf.org/economic-research/wp-content/uploads/sites/4/S02_P1_Felix-Matthys.pdf

**Shang, Fei (2022). "The Effect of Uncertainty on the Sensitivity of the Yield Curve to Monetary Policy Surprises." Journal of Economic Dynamics and Control, 137, 104355.**

Shang uses a threshold factor-augmented VAR built around a dynamic Nelson-Siegel representation of U.S. Treasury yields. The regime shifts are linked to macroeconomic uncertainty, and the model studies how the yield-curve level, slope and curvature respond to monetary-policy surprises. The monthly sample covers 1991-2016, with separate attention to the pre-zero-lower-bound and zero-lower-bound periods. The results show that uncertainty changes the sensitivity to policy surprises particularly during the zero-lower-bound period; the paper does not evaluate the incremental forecast value of LMN for ACM term-premium changes.

**Overlap:** It studies uncertainty-dependent yield-curve dynamics and monetary-policy transmission across regimes.

**Difference:** Its outcome is the conditional response of yield-curve factors to monetary-policy surprises, not pseudo-out-of-sample forecasts of monthly ACM term-premium changes.

- Article: https://doi.org/10.1016/j.jedc.2022.104355

## Forecast comparison under instability

**Giacomini, Raffaella, and Barbara Rossi (2010). "Forecast Comparisons in Unstable Environments." Journal of Applied Econometrics, 25(4), 595–620.**

This paper develops formal procedures for evaluating how the relative forecasting performance of two models evolves over time. Its Fluctuation test examines local relative forecast performance across rolling windows; its One-Time Reversal test is designed for a large change in which model forecasts better. The central motivation is that a full-sample average can conceal time variation in relative forecast performance.

- Article: https://doi.org/10.1002/jae.1177

**Rossi, Barbara (2021). "Forecasting in the Presence of Instabilities: How We Know Whether Models Predict Well and How to Improve Them." Journal of Economic Literature, 59(4), 1135–1190.**

This review emphasizes robust evaluation of forecasting performance under instability. An important distinction is that parameter breaks are neither necessary nor sufficient for time variation in forecast performance. The researcher should therefore assess forecast performance directly, with local measures where appropriate, rather than automatically treating a parameter-break test as the answer to a forecasting-instability question.

- Article: https://doi.org/10.1257/jel.20201479
- AEA article page: https://www.aeaweb.org/articles?id=10.1257/jel.20201479

**Rossi, Barbara, and Matthieu Soupre (2018). "Implementing Tests for Forecast Evaluation in the Presence of Instabilities." The Stata Journal, 17(4).**

This article reviews procedures for relative and absolute forecast evaluation under instability and documents the Giacomini-Rossi Fluctuation Test implementation. It states that the standard implementation assumes model parameters are estimated either with a fixed sample or a rolling sample of fixed size, and that this excludes recursive expanding-window estimation. This restriction matters for the present project because its primary forecasts use an expanding estimation window.

- Article: https://doi.org/10.1177/1536867X1801700405

**Implication for this project:** The 120-month rolling M3-versus-M2 results in `scripts/10_stability_analysis.py` are descriptive diagnostics, not a formal instability test. The standard Giacomini-Rossi Fluctuation Test should not be applied directly to the project's existing recursive expanding-window forecasts. If formal local forecast-comparison inference is later warranted, it requires a separately labelled fixed/rolling-estimation forecast exercise or a different procedure whose validity covers recursive estimation. An Andrews or Bai-Perron parameter-break test is not the default next step because the primary research question concerns forecast performance, not structural parameter breaks.

## Research positioning and claims

The following claims are **not defensible**:

- That the relationship between financial uncertainty and the U.S. yield curve or term premium is unexplored.
- That using LMN and JLN measures in a Treasury-yield application is itself novel.
- That VIX is a new or comprehensive measure of financial uncertainty.
- That the project's predictive regressions identify causal effects of uncertainty.

The defensible scope is narrower:

1. A transparent, reproducible pseudo-out-of-sample comparison of whether LMN financial uncertainty adds predictive information beyond JLN macroeconomic uncertainty and conventional monetary/yield-curve controls.
2. A focus on monthly changes in the 10-year ACM term premium, rather than only Treasury yields or latent yield-curve factors.
3. A component comparison using the ACM expected-average-short-rate change.
4. Measurement robustness using the distinct Kim-Wright term-premium estimate.
5. Explicit forecast evaluation using an expanding window, common target-month samples, RMSE, MAE, out-of-sample R-squared, and Clark-West tests for nested forecasts.

This is best described as a **reproducible macro-finance forecasting assessment**. Its value for a computational research portfolio lies in the quality of the data pipeline, timing discipline, econometric implementation, diagnostics, forecast evaluation, and honest interpretation. It should not be presented as a novel causal paper.

## Implications for interpreting the current results

The project's current forecast results do not show improved term-premium forecast accuracy from adding JLN, LMN, or VIX to the AR/monetary benchmark. This is a substantive null finding, not a reason to alter the pre-specified model hierarchy after observing the results.

The expected-short-rate exercise contains a Clark-West comparison that merits careful reporting, but it must be interpreted alongside raw forecast errors and out-of-sample R-squared. No single p-value should determine the conclusion.

The next research tasks are to complete the pre-specified robustness and stability checks, verify all empirical outputs, and document the results. Any subsequent model extensions should be clearly labelled exploratory and should not replace the original pre-specified baseline.

## Remaining literature-review work

This focused review is not exhaustive. The four studies above have been screened and their broad designs compared. Publicly accessible earlier working-paper text was also inspected for Creal and Wu, Tillmann, and Leippold and Matthys; the accessible Shang article preview includes its introduction, model description, data overview, and conclusion. Earlier drafts and article previews are not substitutes for checking the final published versions, and differences across versions may matter. Before making a formal originality claim, compare the final published versions and inspect additional work on monetary-policy uncertainty, term premia, and forecast evaluation cited in their references and in Cross, Poon, and Zhu (2026).

The final review should compare exact outcomes, uncertainty measures, samples, identification or forecasting designs, and evaluation methods. A title or abstract match alone is not enough to establish either overlap or novelty.
