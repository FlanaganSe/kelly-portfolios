# Factor product audit: what the retail shelf actually delivers, and what it costs

**Question.** Among US-listed factor ETFs selected by a predeclared mechanical
rule, does any product deliver its intended factor exposure — present, stable,
economically material — at a cost that leaves the exposure worth buying rather
than assembling from cheap broad funds?

**Decision it informs.** Whether any product may be used as an *implementation
proxy* in a later experiment. Out of scope: whether any factor earns a premium
(that is [Experiment 001](factor-persistence.md)), what an investor should hold,
and any allocation.

## Conclusion

**Nothing is promoted to a sleeve, and the reason is not that the products are
bad.** Fifteen of 44 reached `exploratory` — the lowest rung, which permits a
fund to be used as an implementation proxy in a later experiment and permits
nothing else. Twenty-four were `rejected` on the frozen falsifier and five are
`unresolved`.

Three results matter more than any individual fund.

**First: the screen selects survivors, and that is measurable.** Of 1,513
mandate-qualifying fund series filing Form N-PORT in 2019Q4, **358 (23.7%) had
stopped filing by 2025Q4**, holding **$333bn** at the frame date, while 751 new
ones launched. But **all 44 funds that passed the screen were still filing at the
end**. Survival is perfectly correlated with passing a size-and-fee screen, so a
universe assembled from today's large, cheap, listed products is not a sample of
the factor shelf — it is a sample of the part of it that worked or was at least
large enough to keep. This is a **lower bound**: public N-PORT filings begin in
2019, so any fund that closed before then is invisible to both censuses.

**Second: the shelf is value and size, and almost nothing else.** Of the 44 that
passed, **33 are graded on HML** (17 long value, 16 short it via a growth
mandate), **8 on SMB, 2 on RMW and 1 on UMD**. At $1bn of assets and a 0.60% fee
cap there is essentially no retail momentum or quality shelf at all: one momentum
product (MTUM) and two quality products (QUAL, SPHQ) in the entire regulatory
census. Whatever Experiment 001 concluded about UMD and RMW, a retail investor's
menu for acting on it is one fund and two funds respectively.

**Third: a static three-fund mix replicates most of the shelf, and beats about
half of it.** Against a long-only, fully invested combination of VTI, VUG, VTV and
VB fitted over the same window, the median product **lost 0.65 pp/yr**, and **22
of 44 lost more than their fee premium plus 0.50 pp/yr** — the frozen falsifier's
clause (c), and the single largest cause of rejection. Sixteen of 44 tracked their
own cheap replication within 0.50 pp/yr in the mean. The replication is fitted
**in sample**, so it is a best case for the combination and a deliberately hard
test for the product; that look-ahead is stated wherever the number appears.

**The most decision-relevant single result is MTUM.** It delivers genuine,
stable momentum exposure — a UMD loading of **+0.444**, 95% interval
`[+0.277, +0.562]`, +0.38 in the first half and +0.47 in the second — and it was
still **rejected**, because it lost **1.22 pp/yr** to a static mix of VTI, VUG and
VTV against a fee premium of only 0.12 pp/yr. Exposure delivery and implementation
value are different questions, and this is the fund where they separate most
cleanly.

**No alpha here means anything, and the page says why three separate ways.**

## The binding constraint is the data contract

Returns are the funds' **own filed monthly total returns**, Form N-PORT Item B.5,
taken from the filings themselves. That is a genuine improvement in provenance
over any price feed: a defined statistic, net of the fund's own fees, filed under
signature, permanently archived, with corrections filed as separate `NPORT-P/A`
documents so a revision is visible rather than silent, and with a liquidated
fund's filings surviving the disappearance of its ticker.

**It does not lift this experiment above `exploratory`, and
[decision 0002](../decisions/0002-no-research-grade-free-price-source.md) still
binds.** Public N-PORT filings begin with periods ending 2019-09-30, so the window
is 72 months. The figures are **unaudited**, and Form N-PORT's General Instruction
G permits each filer to use its own internal methodology, so the series is short,
self-reported and not methodologically uniform across funds. It reduces the
survivorship problem in one direction only: it can see funds that died after 2019
and cannot see funds that died before. Nothing here may promote a sleeve or appear
in the app as a finding.

The independent cross-check **could not be run**. The secondary source refused all
44 requests. That is recorded as an outcome rather than worked around, and it is
one more observation in favour of decision 0002 rather than against it.

### Three reasons no alpha on this page is interpretable

**The window cannot detect an alpha.** The median minimum detectable alpha at 80%
power is **4.02 pp/yr** (range 1.08 to 7.96). Against a true cross-sectional
dispersion of gross alpha of about 1.25 pp/yr
([Fama and French 2010](https://doi.org/10.1111/j.1540-6261.2010.01598.x)), the
window cannot see the effect it is looking for by roughly a factor of three. A
confidence interval containing zero here is a statement about 72 months, not about
a fund.

**Every alpha sits on a model-misfit pedestal, which is measured rather than
assumed.** VTI *is* the market portfolio, so under a correctly specified model its
alpha must be about minus its 0.03% fee. It is **−0.55 pp/yr** under FF5+UMD
(−0.40 CAPM, −0.51 FF3). Whatever that is, every fund carries it, because every
fund is priced by the same six factors over the same 72 months. **Fund alphas must
be read as distances from −0.55, never from zero.** ITOT (−0.60) and VOO (−0.29)
give the same picture. This is the calibration that turns "every cheap index fund
has a −3 pp/yr alpha" from an alarming result into a statement about how badly
FF5+UMD spans 2020–2025 for anything that is not mega-cap.

**Every alpha is shrunk, by its own factor.** With prior dispersion 1.25 pp/yr and
each fund's own HAC standard error, the median shrinkage factor here is **0.431**,
not the framework's reference **0.121**. The reference is the factor at a 3.36
pp/yr standard error, which is typical of an *active* fund; these are index funds
with R² between 0.89 and 0.998, so their alpha standard errors are far tighter and
hardcoding 0.121 would have over-shrunk every one of them. The annualisation trap
is enforced in code and in a test: an annual alpha is **twelve** times a monthly
intercept, so its standard error annualises by ×12 and never by √12 — using √12
would understate it by 3.46 and shrink five times too little, in the direction that
invents skill.

## The predeclared screening rule

Applied to a **regulatory census**, not a vendor list: every fund series that filed
an `NPORT-P` for the quarter ending September 2019 — **8,563 series**. The frame is
taken at the *start* of the observation window on purpose; screening the 2025Q4
census would silently drop every fund that died in between.

Criteria, applied in this fixed order, with each fund recording the **first**
criterion it failed:

| # | Criterion | Rule |
| --- | --- | --- |
| 1 | `mandate_regex` | Official series name matches the predeclared factor-mandate pattern (value, growth, momentum, quality, profitability, minimum/low volatility, multifactor, factor, small-cap, mid-cap) |
| 2 | `exclusion_regex` | Name does not match the predeclared exclusion pattern (leveraged, inverse, sector, thematic, single-country, non-US, ESG, bond, income, dividend, allocation, target-date, buffer, option) |
| 3 | `exchange_traded` | At least one share class flagged `ETF=Y` in the Nasdaq consolidated symbol directory — an exchange record, not a sponsor claim |
| 4 | `minimum_net_assets` | Net assets ≥ $1,000m at the 2019Q4 frame date |
| 5 | `maximum_expense_ratio` | Net expense ratio ≤ 0.60%/yr, read from the sponsor with a URL and a date |
| 6 | `inception_cutoff` | Inception on or before 2016-12-31 |
| 7 | `mandate_in_map` | Stated mandate appears in the predeclared intended-factor map |

### The full screen

**2,105 series matched the mandate pattern and every one is recorded**, passing or
failing, in
[`research/data-manifests/exp_002/product_universe.json`](../../research/data-manifests/exp_002/product_universe.json).
The complete list is committed rather than printed here because it is 2,105 rows;
the counts and every borderline case are below.

| Outcome | Count | Largest example |
| --- | ---: | --- |
| **Passed** | **44** | Vanguard Mid-Cap Index Fund (VO), $105.6bn |
| Failed `exchange_traded` | 1,374 | EuroPacific Growth Fund, $158.4bn — a mutual fund, never exchange-traded |
| Failed `exclusion_regex` | 592 | SMALLCAP World Fund, $43.9bn (non-US); Vanguard Dividend Growth, $39.5bn (dividend) |
| Failed `minimum_net_assets` | 92 | Invesco Dynamic Large Cap Value ETF, $973.7m |
| Failed `maximum_expense_ratio` | 1 | Invesco DWA Momentum ETF (PDP), 0.62% |
| Failed `inception_cutoff` | 1 | Principal U.S. Mega-Cap Multi-Factor ETF (USMC), inception 2017-10-11 |
| Failed `mandate_in_map` | 1 | iShares Morningstar Growth ETF (ILCG) — changed its objective mid-window |

Three cases need defending rather than asserting.

- **The $1bn threshold is the least comfortable criterion.** Three multifactor
  products sit within 10% of it and are excluded: Invesco Dynamic Large Cap Value
  ($973.7m), John Hancock Multifactor Large Cap ($911.7m) and iShares Edge MSCI
  Multifactor USA ($908.5m). The threshold was chosen from the *count* of funds at
  each level, which was visible before any return was downloaded, and never from
  performance — but it is arbitrary and it removes the multifactor tail
  specifically.
- **A fund that changed its stated objective inside the window is excluded and
  recorded, not dropped.** ILCG became a large-*and-mid* cap fund on a different
  index in March 2021; USMC stopped being an index fund in June 2022 (and fails on
  inception anyway); INTF's quality score absorbed carbon-intensity signals in June
  2022 (and fails the non-US clause anyway). A fund with no single stated mandate
  over the window has nothing to grade its exposure against.
- **Index and methodology changes that leave the mandate intact do *not* exclude a
  fund**, because excluding them would remove most of the shelf and hide exactly
  what the stability test exists to find. Eight are registered in
  [`product_facts.json`](../../research/data-manifests/exp_002/product_facts.json),
  and **four are invisible from the index name**: FTSE Russell added capping to the
  Russell style indexes on 2025-03-21 (IWF, IWO, IWY, and separately IWS/IWP/IWN on
  2024-03-21); S&P added capping to its style indexes on 2024-06-21 (IVW, IUSG,
  SPYG); SPMD and SPSM changed benchmark entirely on 2020-01-24; FTA and FTC changed
  base universe on 2023-12-01 with no announcement found.

**One correction to record.** Nine large-cap and small-cap growth ETFs (IWF, IVW,
IWO, IUSG, SPYG, RPG, IWY, ILCG, FTC) were initially failing criterion 5 only
because nobody had looked their fees up. That is a gathering gap, not a screen
result, and leaving it would have stripped growth mandates out of the universe
systematically — a selection effect in exactly the direction that makes a value
tilt look better. The fees were verified and the universe rebuilt **before any
return was downloaded**.

## The exposure table

Common period **2020-01…2025-12**, 72 months, FF5 plus momentum, Newey–West HAC at
6 lags. **Loading is sign-adjusted for the mandate**: a growth fund is graded on a
*negative* HML loading, so a positive number in this column always means "the
exposure the fund advertises is present". `H1`/`H2` are the fixed calendar halves.
Alpha is in percentage points per year; **`Shrunk` is the posterior after shrinking
by that fund's own factor**, and **`MDE80`** is the smallest alpha this window could
have detected at 80% power. `TD combo` is the mean annual return difference against
the fitted cheap replication.

| Ticker | Intended | Loading | HAC se | 95% bootstrap | H1 | H2 | Raw α | Shrunk α | MDE80 | TD combo | Status |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| EZM | +SMB | +0.554 | 0.055 | `[+0.456, +0.677]` | +0.49 | +0.53 | −3.43 | −1.31 | 4.45 | +0.71 | `exploratory` |
| SPMD | +SMB | +0.481 | 0.043 | `[+0.391, +0.582]` | +0.42 | +0.44 | −3.47 | −1.49 | 4.04 | +0.24 | `exploratory` |
| IJH | +SMB | +0.480 | 0.043 | `[+0.390, +0.582]` | +0.42 | +0.44 | −3.47 | −1.48 | 4.06 | +0.26 | `exploratory` |
| FTA | +HML | +0.452 | 0.040 | `[+0.354, +0.553]` | +0.40 | +0.62 | −3.85 | −1.49 | 4.40 | −0.22 | `exploratory` |
| MDYV | +HML | +0.411 | 0.048 | `[+0.288, +0.505]` | +0.44 | +0.50 | −2.90 | −0.89 | 5.26 | +0.45 | `exploratory` |
| IJJ | +HML | +0.411 | 0.049 | `[+0.287, +0.505]` | +0.43 | +0.50 | −2.96 | −0.91 | 5.26 | +0.41 | `exploratory` |
| VBR | +HML | +0.410 | 0.036 | `[+0.322, +0.480]` | +0.43 | +0.45 | −2.78 | −1.50 | 3.22 | +0.60 | `exploratory` |
| VLUE | +HML | +0.393 | 0.065 | `[+0.269, +0.539]` | +0.25 | +0.59 | −2.40 | −0.66 | 5.71 | +0.20 | `exploratory` |
| IWN | +HML | +0.392 | 0.031 | `[+0.330, +0.464]` | +0.37 | +0.44 | −2.55 | −1.79 | 2.28 | −0.70 | `exploratory` |
| IUSV | +HML | +0.310 | 0.050 | `[+0.184, +0.433]` | +0.29 | +0.42 | −2.18 | −0.93 | 4.07 | −0.07 | `exploratory` |
| SPYV | +HML | +0.303 | 0.051 | `[+0.175, +0.429]` | +0.28 | +0.41 | −2.14 | −0.89 | 4.14 | −0.24 | `exploratory` |
| IVE | +HML | +0.302 | 0.051 | `[+0.175, +0.429]` | +0.28 | +0.42 | −2.27 | −0.95 | 4.13 | −0.34 | `exploratory` |
| IWY | −HML | +0.302 | 0.044 | `[+0.207, +0.414]` | +0.26 | +0.45 | **+3.09** | +1.45 | 3.74 | +1.22 | `exploratory` |
| VUG | −HML | +0.284 | 0.039 | `[+0.207, +0.384]` | +0.22 | +0.44 | **+2.25** | +1.23 | 3.19 | +4.19 | `exploratory` |
| IWF | −HML | +0.278 | 0.039 | `[+0.200, +0.378]` | +0.23 | +0.42 | **+2.27** | +1.36 | 2.86 | +0.43 | `exploratory` |
| IVW | −HML | +0.224 | 0.038 | `[+0.141, +0.328]` | +0.19 | +0.37 | +0.93 | +0.40 | 4.05 | −0.08 | `unresolved` |
| SPYG | −HML | +0.223 | 0.038 | `[+0.140, +0.328]` | +0.19 | +0.37 | +1.06 | +0.45 | 4.05 | +0.04 | `unresolved` |
| JHMM | +HML | +0.212 | 0.041 | `[+0.127, +0.303]` | +0.23 | +0.34 | −3.60 | −1.66 | 3.78 | −0.27 | `unresolved` |
| IUSG | −HML | +0.207 | 0.035 | `[+0.129, +0.306]` | +0.18 | +0.34 | +0.72 | +0.34 | 3.73 | −0.19 | `unresolved` |
| SPHQ | +RMW | +0.176 | 0.048 | `[+0.079, +0.296]` | +0.14 | +0.31 | −0.56 | −0.26 | 3.75 | +0.01 | `unresolved` |
| SPSM | +SMB | +0.889 | 0.038 | `[+0.797, +0.953]` | +0.83 | +0.92 | −2.95 | −2.24 | 1.97 | −0.94 | `rejected` |
| IJR | +SMB | +0.889 | 0.039 | `[+0.796, +0.953]` | +0.83 | +0.92 | −2.99 | −2.26 | 2.00 | −0.98 | `rejected` |
| VB | +SMB | +0.599 | 0.037 | `[+0.516, +0.684]` | +0.53 | +0.58 | −2.97 | −1.63 | 3.16 | −2.89 | `rejected` |
| **MTUM** | **+UMD** | **+0.444** | 0.064 | `[+0.277, +0.562]` | +0.38 | +0.47 | −2.95 | −0.55 | 7.34 | **−1.22** | `rejected` |
| VOE | +HML | +0.434 | 0.056 | `[+0.278, +0.538]` | +0.45 | +0.54 | −4.38 | −1.87 | 4.06 | −0.59 | `rejected` |
| IWS | +HML | +0.392 | 0.051 | `[+0.256, +0.481]` | +0.42 | +0.46 | −4.91 | −2.30 | 3.73 | −0.83 | `rejected` |
| SLYV | +HML | +0.367 | 0.029 | `[+0.309, +0.435]` | +0.40 | +0.34 | −2.44 | −1.53 | 2.70 | −0.70 | `rejected` |
| IJS | +HML | +0.367 | 0.028 | `[+0.309, +0.435]` | +0.40 | +0.34 | −2.51 | −1.58 | 2.69 | −0.76 | `rejected` |
| IWD | +HML | +0.350 | 0.049 | `[+0.228, +0.472]` | +0.31 | +0.49 | −3.63 | −2.10 | 2.99 | −0.78 | `rejected` |
| VTV | +HML | +0.337 | 0.052 | `[+0.225, +0.471]` | +0.27 | +0.52 | −2.60 | −1.39 | 3.28 | −2.57 | `rejected` |
| IWR | +SMB | +0.293 | 0.055 | `[+0.172, +0.408]` | +0.20 | +0.27 | −3.86 | −1.67 | 4.00 | −0.89 | `rejected` |
| VO | +SMB | +0.232 | 0.061 | `[+0.103, +0.356]` | +0.16 | +0.16 | −3.78 | −1.44 | 4.46 | −1.18 | `rejected` |
| QUAL | +RMW | +0.186 | 0.036 | `[+0.101, +0.247]` | +0.20 | +0.20 | −2.15 | −1.19 | 3.13 | −1.26 | `rejected` |
| IWP | −HML | +0.168 | 0.079 | `[+0.020, +0.315]` | +0.13 | +0.21 | −2.74 | −0.48 | 7.58 | −2.39 | `rejected` |
| TILT | +HML | +0.148 | 0.014 | `[+0.113, +0.171]` | +0.15 | +0.16 | −0.95 | −0.86 | 1.08 | +0.99 | `rejected` |
| IWO | −HML | +0.134 | 0.038 | `[+0.054, +0.223]` | +0.16 | +0.06 | −2.55 | −1.15 | 3.87 | −1.82 | `rejected` |
| VBK | −HML | +0.125 | 0.044 | `[+0.041, +0.211]` | +0.09 | +0.05 | −3.49 | −1.35 | 4.41 | −2.86 | `rejected` |
| VOT | −HML | +0.121 | 0.075 | `[−0.032, +0.255]` | +0.11 | +0.02 | −3.22 | −0.58 | 7.48 | −2.62 | `rejected` |
| RPG | −HML | +0.084 | 0.089 | `[−0.124, +0.293]` | +0.03 | +0.10 | −4.99 | −0.81 | 7.96 | −2.82 | `rejected` |
| FTC | −HML | +0.059 | 0.058 | `[−0.069, +0.166]` | +0.08 | −0.06 | −1.03 | −0.34 | 4.95 | +0.14 | `rejected` |
| SLYG | −HML | −0.067 | 0.055 | `[−0.219, +0.034]` | −0.02 | −0.20 | −3.73 | −1.81 | 3.60 | −1.47 | `rejected` |
| IJT | −HML | −0.067 | 0.055 | `[−0.220, +0.034]` | −0.02 | −0.20 | −3.81 | −1.85 | 3.61 | −1.54 | `rejected` |
| IJK | −HML | −0.067 | 0.040 | `[−0.174, +0.003]` | −0.08 | −0.14 | −4.32 | −1.66 | 4.43 | −1.69 | `rejected` |
| MDYG | −HML | −0.068 | 0.040 | `[−0.174, +0.003]` | −0.08 | −0.14 | −4.31 | −1.66 | 4.42 | −1.69 | `rejected` |

### What the exposure column says

**Small- and mid-cap "growth" indexes deliver no growth tilt.** IJK, MDYG, IJT and
SLYG have sign-adjusted loadings of about **−0.07**, meaning their raw HML loading
is *positive*: the S&P 400 and 600 Growth indexes are, in Fama–French terms,
marginally *value* portfolios. RPG (+0.084), FTC (+0.059), VOT (+0.121) and VBK
(+0.125) are barely distinguishable from the market on the axis they advertise.
Large-cap growth is entirely different: VUG, IWF, IWY, IVW, SPYG and IUSG all carry
a genuine −0.21 to −0.30 HML loading. **The growth mandate means something at the
top of the market and almost nothing below it.**

**Exposure is stable where it exists, and unstable exactly where it is absent.**
Across 37 rolling 36-month windows, **41 of 44 funds never changed the sign of
their intended loading**, and only one — FTC — flipped between the fixed calendar
halves. The three exceptions are the three funds whose exposure was near zero to
begin with: RPG changes sign **12 times** (range −0.292 to +0.098), VOT twice and
FTC once. The median rolling range is 0.249. Instability is not what kills these
products; it is a symptom of the exposure not being there.

**Quality is the thinnest exposure on the shelf.** QUAL's RMW loading is +0.186 and
SPHQ's +0.176, both just above the 0.15 threshold and both with intervals that come
close to it. Two products, neither convincing.

## The multiple-testing correction, and what it actually did

The family is **every fund with usable returns times every specification
estimated**: 44 × 3 = **132 tests**, not the subset that looked interesting.

| Denominator | Tests | Uncorrected p ≤ 0.05 | Benjamini–Hochberg (0.10) | Holm–Bonferroni (0.10) |
| --- | ---: | ---: | ---: | ---: |
| Tests actually run | 132 | 56 | 54 | 5 |
| All funds that passed the screen | 132 | 56 | 54 | 5 |
| **Every mandate-matching series screened** | **6,315** | 56 | **2** | **0** |

Three readings, and the first is the one most likely to be misquoted.

- **Fifty-four "significant" alphas are almost all significantly *negative*.**
  Thirty-eight of the 44 primary-specification alphas are below zero, median
  **−2.92 pp/yr**. Benjamini–Hochberg is rejecting the hypothesis that these funds
  matched the factor model, in the direction of *under*performance. Not one of them
  is a discovery of skill, and after subtracting the −0.55 pp/yr model-misfit
  pedestal a large part of what remains is the model rather than the funds.
- **Holm–Bonferroni is the defensible correction and it leaves five.** These 132
  tests are nowhere near independent: the same six factors, the same 72 months, and
  three *nested* specifications per fund. Benjamini–Hochberg is valid under
  independence or positive regression dependence, so its count of 54 is an
  optimistic bound; Holm is valid under arbitrary dependence.
- **Widen the denominator to the whole search and it collapses.** Padding the
  family to all 2,105 screened series × 3 specifications with p = 1 — which cannot
  create a rejection and strictly tightens both corrections — leaves
  **2 under Benjamini–Hochberg and 0 under Holm**. That is the honest accounting of
  how much looking was done, and it is the number to quote.

## Hostile tests

| Test | Result |
| --- | --- |
| **Data-path gate** | VTI correlates **0.9993** with the market factor, beta **0.9968**, R² **0.9985**, worst month **2020-03** at **−13.80%**. The alignment of Item B.5's three returns to calendar months is confirmed against an independent series, not assumed — a reversed reading would shift every history by two months and leave every number plausible. |
| **Three specifications** | CAPM, FF3 and FF5+UMD estimated for every fund. No fund's intended loading appears in only one of them. |
| **Fixed calendar halves** | Reported for every fund above. One sign flip (FTC). |
| **Rolling 36-month windows** | 37 windows per fund. 41 of 44 never change sign; the three that do (RPG 12 times, VOT twice, FTC once) are the three whose loading was near zero anyway. |
| **Cash-rate substitution** | Substituting TB3MS, DGS3MO or DFF for the one-month bill moves **every alpha by −0.09, −0.20 and −0.09 pp/yr** respectively and **moves no loading at all**, because a constant shift in the dependent variable moves only the intercept. The choice of cash series did not make the answer. |
| **Widened multiple-testing denominator** | Above. BH 54 → 2, Holm 5 → 0. |
| **Replication by cheap broad funds** | Above. Median −0.65 pp/yr; 22 of 44 fire clause (c). |
| **Independent cross-source check** | **Could not be run.** The secondary source refused all 44 requests. |

## Verified facts, assumptions, open questions

### Verified

- The screening rule, the eras, the falsifier, the materiality threshold and the
  intended-factor map were frozen in the specification **before any return was
  downloaded**, and a fund that failed the screen never had its returns fetched.
  Every change made while turning placeholder fields into concrete ones is in the
  specification's `concretisation_log` with its date and reason, and all of them
  predate any result.
- The universe was screened against the census at the **start** of the window and
  is committed as a file the experiment reads and refuses to rebuild.
- Item B.5's ordering — `rtn1` is the earliest of the three months — is confirmed
  against a real filing: iShares MSCI USA Momentum Factor ETF, period ending
  2020-04-30, filed −7.36 / **−11.41** / +11.75, putting the COVID crash in March.
- Fund returns are **not** reduced by the expense ratio a second time; the filed
  total return is already net of it.
- The sample ends 2025-12. Later months exist in the filings and enter no
  statistic.

### Assumptions

- **The replicating weights are fitted in sample.** An investor could not have
  known them in advance, so every tracking difference against the combination is a
  best case for the combination.
- **The $1bn asset threshold**, chosen from fund counts before any return was seen,
  and the **0.60% fee cap**. Both are arbitrary and both are stated.
- **A size-and-style mandate is graded on its style leg**, because the plain size
  index is separately in the universe and the tilt is the only thing distinguishing
  them.
- **FF5+UMD spans these funds well enough for the intercept to mean something.** The
  −0.55 pp/yr pedestal on a total-market fund says it does not, entirely.

### Open questions

- **What is the exposure over a window long enough to matter?** 72 months is the
  whole constraint. A licensed source with pre-2019 fund history is the single
  highest-value purchase available to this repository.
- **What did the 358 disappeared funds do before they disappeared?** Their filings
  exist. This experiment counted them but did not read their returns, and doing so
  would turn a survivorship *bound* into a survivorship *measurement*.
- **Turnover and realised distributions are not in Form N-PORT** and are recorded as
  gaps, not estimated. They are in the annual report on Form N-CSR as unstructured
  HTML. No tax haircut is applied to any return anywhere.
- **Would the pedestal shrink under a model with a mega-cap or low-beta factor?**
  Untested, and it decides how much of the −2 to −5 pp/yr alphas is real.

## What this does not establish

- **Not that these funds are bad.** Twenty-four rejections are statements about
  *delivered exposure and cost over 72 months*, not about whether the underlying
  factor exists. Experiment 001 answers the second question and answered it
  `unresolved` for three factors and `rejected` for one.
- **Not manager skill, in either direction.** A positive alpha over a short history
  is not evidence of future skill; the three funds with positive alpha (IWY, IWF,
  VUG) are large-cap growth funds in a window that large-cap growth dominated.
- **Not investability in the future.** Four of the eight registered index changes
  are invisible from the index name, so a fund's mandate today is a weak guide to
  what it will track.

## Consequence for this repository

1. **Nothing is promoted to a sleeve.** Fifteen products may be used as
   implementation proxies in a later experiment and for nothing else.
2. **What would change this:** a licensed total-return source covering fund history
   before 2019. At the observed standard errors, extending the window from 72 to
   240 months would cut the minimum detectable alpha from about 4.0 pp/yr to about
   2.2, which is the first point at which a 1.25 pp/yr effect becomes arguable. No
   amount of care with the current data substitutes for it.
3. **A retail investor acting on Experiment 001's factors has almost no menu.** One
   momentum fund and two quality funds cleared a $1bn, 0.60% screen in the entire
   US regulatory census, and the momentum fund lost to a static three-fund mix.
4. **The cheap-combination comparison should be the default benchmark** for any
   future product question, not the market alone. It changed the verdict for 22 of
   44 funds.
5. **Any future fund-level result must report its model-misfit pedestal.** An alpha
   quoted against zero when a total-market fund prices at −0.55 pp/yr is not
   reportable.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_002_fund_exposure --build-universe
uv run python -m portfolio_edge.experiments.exp_002_fund_exposure --view-results
uv run pytest tests/unit/test_experiments_exp_002_fund_exposure.py
uv run pytest tests/unit/test_data_nport.py
uv run pytest tests/integration/test_exp_002_universe_committed.py   # offline
```

| Field | Value |
| --- | --- |
| Run | `fbe139abd9114abeb69e39fad8839f8e` |
| Status | `exploratory` |
| Specification hash | `b4c9a134e106e59bc290445f26eed25e4982660fc82e41accadfe914dc6035bc` |
| Specification | [`research/experiments/exp_002_fund_exposure.yaml`](../../research/experiments/exp_002_fund_exposure.yaml) |
| Code | [`exp_002_fund_exposure.py`](../../research/src/portfolio_edge/experiments/exp_002_fund_exposure.py), [`exp_002_universe.py`](../../research/src/portfolio_edge/experiments/exp_002_universe.py), [`data/nport.py`](../../research/src/portfolio_edge/data/nport.py) |
| Universe | [`data-manifests/exp_002/product_universe.json`](../../research/data-manifests/exp_002/product_universe.json), 2,105 screened series |
| Product facts | [`data-manifests/exp_002/product_facts.json`](../../research/data-manifests/exp_002/product_facts.json), 51 funds with a source URL and a date read |
| Return source | SEC Form N-PORT Item B.5: 1,205 filings across the 44 screened funds, of which 15 are `NPORT-P/A` amendments, plus the comparator series |
| Frame | N-PORT structured data sets `2019q4` and `2025q4` |
| Factors | FF5 + momentum, US, monthly, same French vintage as Experiment 001 |
| Cash | French one-month Treasury bill, from the same file as the factors |
| Seed | 20260812, declared in the specification |
| Bootstrap | Stationary block, 10 000 resamples, mean block 6 months (3 and 12 also computed) |
| Retrieval date | 2026-08-12 |

Four earlier attempts are in
[`research/ledger.jsonl`](../../research/ledger.jsonl) — one `failed` and three
`abandoned` — together with this run's `results_viewed` event. The abandoned
entries include a correction appended in the ledger about an abandonment that was
recorded prematurely and for the wrong reason; an append-only log whose mistakes
are quietly dropped is worth less than one whose mistakes are visible.
