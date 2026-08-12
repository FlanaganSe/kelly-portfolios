# Investable factor products: the exposure is delivered, the value is not

**Question.** Do any exchange-traded products deliver the factor exposure they
advertise, stably, at a cost that leaves the exposure worth buying — and can a
residual return be separated from that exposure on the data available?

**Decision it informs.** Whether any retail factor product may be used as an
implementation proxy in a later experiment, and what the
[edge budget](expected-edge-decomposition.md) may book for the fund-cost line. Out
of scope: allocation, sizing, after-tax outcomes, and whether any factor premium
exists at all — that is [Experiment 001](factor-persistence.md).

**Status: `exploratory`, and nothing is promoted.**
[Decision 0002](../decisions/0002-no-research-grade-free-price-source.md) fixes the
ceiling: until a source with a documented total-return and corporate-action contract
is licensed, fund-level work may motivate further testing, may not promote a sleeve,
and may not appear in the app as a finding. Fifteen products reached the *per-fund*
status `exploratory`, which permits them to be used as implementation proxies in a
later experiment and permits nothing else.

## Conclusion

Of 8 563 series that filed a Form NPORT-P in the 2019Q4 SEC census, 2 105 matched
the predeclared factor-mandate pattern, **44 passed the whole screen**, and all 44
had a filed Item B.5 monthly total return for every one of the 72 months from
2020-01 to 2025-12. **15 reached `exploratory`, 24 were `rejected` on the frozen
falsifier, 5 are `unresolved`.**

**The exposure question is answerable on this window and the alpha question is not.**
Those are different findings and merging them is the error this page exists to
prevent.

1. **Exposure is largely delivered.** In the separate 44-member family of
   intended-loading tests, **38 reject a zero loading in the mandate's own direction
   under Benjamini–Hochberg at 0.10** — the only family here where a correction leaves
   most of its members standing. Value funds load on HML, small-cap funds on SMB, and
   the loadings hold across the fixed calendar split. That is a manufacturing result,
   not a return result, and "not zero" is a weaker bar than the falsifier's 0.15.
2. **Alpha is negative almost everywhere and measurable almost nowhere.** 38 of the
   44 shrunk alphas are negative, median **−1.33 pp/yr**. Only **8 of 44** raw alphas
   exceed the alpha their own window could detect at 80% power, and **all eight are
   negative**. The median minimum detectable alpha across the 132
   fund-by-specification tests is **4.52 pp/yr**, larger than any plausible true
   alpha. An interval containing zero here is a statement about 72 months.
3. **The six positive shrunk alphas are one trade.** VUG, IWF, IWY, IVW, IUSG and
   SPYG — every one a large-cap growth product, over a window in which large-cap
   growth beat the market. **Nothing here is alpha in the sense of skill.**
4. **The model itself has a measurable offset, and every alpha must be read against
   it.** VTI is a cap-weighted total-market fund: it *is* the market portfolio, so
   under a correctly specified model its alpha should be about minus its
   three-basis-point fee. Under FF5+UMD over these 72 months it is
   **−0.55 pp/yr with a HAC *t* of −3.41** (CAPM −0.40, FF3 −0.51). That
   **0.52 pp/yr of model misfit is carried by every fund in the audit**, because
   every fund is priced by the same six factors over the same window. It reframes
   the alpha column without rescuing it: subtracting the pedestal moves the median
   *raw* alpha from −2.92 to **−2.38 pp/yr**, still negative, leaves the same six
   funds above it and 38 below, and cuts the number of funds whose distance from it
   exceeds their own detection threshold from 8 to **4**.

### What decided the 24 rejections

| Clause | What it tests | Fired on |
| --- | --- | ---: |
| (a) intended loading below 0.15 | the exposure is absent | 10 |
| (b) intended loading flips sign across the fixed halves | the exposure is not an exposure | 1 |
| (c) shortfall to the cheap replication above 0.50 pp/yr | implementation value | 22 |
| (d) total cost above 1.0 pp/yr with no corresponding exposure | cost without exposure | 8 |

Clauses overlap; 24 distinct funds fired at least one. **Clause (c) did most of the
work and is decided against a comparator fitted in sample** (§7). Read every (c)
rejection as "a look-ahead combination of four cheap funds beat this product over
these 72 months", never as "this product is badly run".

---

## 1. What was run

| Field | Value |
| --- | --- |
| Specification | [`research/experiments/exp_002_fund_exposure.yaml`](../../research/experiments/exp_002_fund_exposure.yaml), hash `b4c9a134e106e59bc290445f26eed25e4982660fc82e41accadfe914dc6035bc` |
| Run kind | **exploratory**; does not consume the final holdout |
| Ledger `run_id` | `fbe139abd9114abeb69e39fad8839f8e`, `succeeded` and `results_viewed`. Every outcome, exposure, replication, correction and universe figure is **byte-identical** to the two earlier successful runs of the same specification hash; the differences are two added diagnostics (§9) |
| Frame | SEC N-PORT data set **2019Q4**, 8 563 series, sha256 `f8e10bce83ac…`, retrieved 2026-08-12T08:09:23Z. Follow-up 2025Q4, 12 552 series, sha256 `4ebb169e6cc0…`, used **only** to measure attrition |
| Returns | Form N-PORT Item B.5 monthly total return per share class; 1 205 filings across 44 funds; already net of the expense ratio and of reinvested distributions |
| Window | 2020-01…2025-12, **72 months**; nothing after 2025-12 was read |
| Factor model | FF5 + UMD, US monthly, French vintage pinned by raw sha256 `cbc3724812132654fbbe8daae3c46e0f90e70008434f94a7986fe49f1db6ad3b` and `f405ee2d47a5c75ce05025f789733d0599879361e9836a553504240b89159871`, retrieved 2026-08-12T06:19:22Z |
| Cash rate | the one-month bill from the **same French file as the factors**, so the intercept is interpretable as alpha |
| Inference | Newey–West HAC at 6 lags; stationary block bootstrap, mean block **6 months frozen not tuned**, 10 000 resamples, resampling the return and the whole design jointly |
| Seed | 20260812 |
| Committed inputs | [`product_universe.json`](../../research/data-manifests/exp_002/product_universe.json) sha256 `549b3a8ce777a0ab045bd68d84626be8a950c600760084ea1bb09255b54babf3`, built 2026-08-12T08:56:39Z before any return was downloaded; [`product_facts.json`](../../research/data-manifests/exp_002/product_facts.json), each fee, index and inception with its own URL and date, `as of 2026-08-12` |

**The data path was gated before anything was believed.** Item B.5 reports `rtn1` as
the *first* month of the reporting period; reading it backwards would shift every
history by two months and leave every number looking plausible. So VTI, reconstructed
from its own filings, must correlate at least 0.99 with the French market total
return and show its worst month in 2020-03. It correlates **0.99926**, betas
**0.9968** on `Mkt-RF` with R² **0.99852**, worst month **2020-03 at −13.80%**.

### The run history, not only the run that worked

Seven executions of this family are in [`research/ledger.jsonl`](../../research/ledger.jsonl):
one `failed`, three `abandoned` and three `succeeded`.

| Run | Spec | Terminal event | Why |
| --- | --- | --- | --- |
| `8b37318c…` | `0f4095f7…` | `failed` | `KeyError: no table 'french_us_ff5_monthly'` — a reader bug. No result. |
| `24c2c919…` | `0f4095f7…` | `abandoned` | Killed mid-download: the committed universe and facts files had been moved to `data-manifests/exp_002/` after it started, so it was running against paths that no longer existed. |
| `c7d2024b…` | `b4c9a134…` | `abandoned` | Killed after ~45 minutes; every filing cached but stalled in retry backoff against the secondary cross-source endpoint, which answered HTTP 429 to every request. Superseded by a run whose retry budget for that best-effort diagnostic is one attempt. |
| `2645817b…` | `b4c9a134…` | `abandoned`, then **corrected** | The first entry was appended **while the run was still executing**, on the mistaken belief it was dead, and recorded a reason belonging to a different run. The correction is a new line rather than a repair, and records that the run was then killed *to make the premature entry true*. Nothing was viewed. |
| `e95932d2…` | `b4c9a134…` | `succeeded` | First complete result. No pedestal; cash-rate diagnostic wrong. |
| `f02d06f7…` | `b4c9a134…` | `succeeded` | Adds the model-misfit pedestal. Cash-rate diagnostic still wrong. |
| `fbe139ab…` | `b4c9a134…` | `succeeded` | **The run reported here.** Cash-rate unit error fixed. |

**The three successful runs agree on every number that decides anything.** Same
specification hash, same seed, same pinned inputs; the outcomes, exposures,
replication, multiple-testing and universe blocks are byte-identical across all
three. What changed between them is diagnostic coverage, and both changes are
reported in §9 rather than folded silently into the reported run.

One further fact belongs in the record. **The universe was rebuilt at
2026-08-12T08:56:39Z**, between the third and fourth runs, to add nine large- and
small-cap growth ETFs (IWF, IVW, IWO, IUSG, SPYG, RPG, IWY, ILCG, FTC) that had been
failing the expense-ratio criterion only because nobody had looked their fees up — a
gathering gap, not a screen result, and leaving it would have stripped growth mandates
out systematically, a selection effect in exactly the direction that makes a value
tilt look better. It happened **before any return was examined**; six of the nine are
in the final 44, and three of the six positive alphas are among them.

---

## 2. The screen, and the funnel from 2 105 to 44

Frozen before any return series was read, mechanical, with no "and peers" clause.
Criteria apply in a fixed order and only the **first** failure is recorded, which is
what makes the funnel add up.

1. **`mandate_regex`** — the official series name matches
   `\b(value|growth|momentum|quality|profitab\w*|min(?:imum)?\s+volatility|low\s+volatility|multi-?factor|factor|small[- ]?cap|mid[- ]?cap)\b`, case-insensitively.
2. **`exclusion_regex`** — the name does **not** match the predeclared exclusion
   pattern: leveraged and inverse, sector and thematic, single-country and non-US,
   ESG-primary, bond, income, dividend, allocation, target-date, buffer and option.
3. **`exchange_traded`** — at least one share class flagged `ETF=Y` in the Nasdaq
   consolidated symbol directory, an exchange record rather than a sponsor claim.
4. **`minimum_net_assets`** — at least 1 000 million USD at the 2019Q4 frame date.
5. **`maximum_expense_ratio`** — net expense ratio at or below 0.60%/yr, read from the
   sponsor's own prospectus or fund page with the URL and date recorded.
6. **`inception_cutoff`** — inception on or before 2016-12-31, so the audit is not
   measuring a launch.
7. **`mandate_in_map`** — the stated mandate is in the predeclared intended-factor
   map. The reserved value `mandate_changed` is deliberately absent from that map.
8. **`complete_return_coverage`** — a filed Item B.5 return for every month of the
   window. A gap excludes; it is never interpolated.

| Stage | Removed | Remaining | What was removed |
| --- | ---: | ---: | --- |
| 2019Q4 census | — | 8 563 | every series that filed a Form NPORT-P |
| `mandate_regex` | 6 458 | **2 105** | everything whose name names no factor mandate |
| `exclusion_regex` | 592 | 1 513 | 185 international, 82 global, 67 income, 60 allocation, 51 emerging, 47 dividend, 16 bond, 10 ESG, 7 developed, 7 "Intl", then the tail of single-country, sector, leveraged and inverse names |
| `exchange_traded` | 1 374 | 139 | open-end mutual funds and insurance separate accounts with no listed share class — including the three largest series in the frame, EuroPacific Growth Fund (158.4 bn), T. Rowe Price Blue Chip Growth (63.5 bn) and "THE U.S. LARGE CAP VALUE SERIES" (29.9 bn) |
| `minimum_net_assets` | 92 | 47 | sub-billion ETFs; largest excluded PWV 973.7 m, then JHML 911.7 m, LRGF 908.5 m, RPV 890.9 m |
| `maximum_expense_ratio` | 1 | 46 | **PDP**, Invesco DWA Momentum, at 0.62% |
| `inception_cutoff` | 1 | 45 | **USMC**, Principal U.S. Mega-Cap Multi-Factor, inception 2017-10-11 |
| `mandate_in_map` | 1 | **44** | **ILCG**, which changed objective inside the window and so has no single mandate to be graded against |
| `complete_return_coverage` | 0 | **44** | nothing; all 44 had all 72 months |

**The exchange-traded criterion is by far the largest filter, and it is a decision
about investability rather than quality.** Whatever this page concludes, it concludes
about the *listed* shelf.

Two structural facts about what survived. **The 44 are not 44 independent products**:
IVW/SPYG, IVE/SPYV, IJK/MDYG, IJJ/MDYV, IJS/SLYV and IJT/SLYG each track one index
under two sponsors, IJH/SPMD both track the S&P MidCap 400 and IJR/SPSM the S&P
SmallCap 600. Sixteen funds are eight indices; each pair's loadings agree to about
0.001 and each pair received the same status. **And the shelf is thin outside value
and size**: by stated mandate, 8 growth, 7 value, 5 mid-cap, 4 each small value,
small growth, mid value and mid growth, 3 small-cap, 2 quality, 2 multifactor, and
**1 momentum**. MTUM is the entire momentum shelf clearing a billion dollars, a 0.60%
fee and a 2016 inception.

Fourteen of the 44 carry an index methodology change inside the window that a
name-matching check would miss — issuer capping added to the Russell and S&P style
indexes in 2024–2025, MTUM's move to the "SR Variant" in 2020, FTA's and FTC's base
universes in 2023, SPMD's and SPSM's outright index change in January 2020. The
specification records them rather than excluding them, because excluding them would
remove most of the shelf and hide what the rolling-loading test exists to find. Each
is in the product facts with a source URL.

---

## 3. The exposure table

Every row is the frozen primary specification: OLS of the fund's monthly excess
return on `Mkt-RF`, `SMB`, `HML`, `RMW`, `CMA` and `UMD`, HAC at 6 lags, 72
observations. **Loading is sign-adjusted for the mandate** — a growth mandate is
graded on a *negative* HML loading of the same magnitude, marked `HML (−)`, because
growth is the short leg of value and not an independent factor. The interval is the
stationary block bootstrap at the frozen 6-month mean block. Alpha, its HAC standard
error and MDE₈₀ are percentage points per year; **shrunk** is the posterior mean under
the fixed Fama–French (2010) prior with each fund's own factor in brackets;
**shortfall** is positive when the product lost more to its cheap replication than its
fee premium explains, and carries no interval (§7). Ordered by frame-date net assets,
which selects nothing.

| Ticker | Mandate | ER % | Intended | Loading | 95% interval | Raw alpha | HAC SE | Shrunk (factor) | MDE₈₀ | Shortfall | Status |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| VO | mid cap | 0.03 | SMB | +0.232 | `[+0.103, +0.356]` | −3.78 | 1.59 | −1.44 (0.381) | 4.46 | +1.18 | `rejected` |
| VUG | growth | 0.03 | HML (−) | +0.284 | `[+0.207, +0.384]` | +2.25 | 1.14 | +1.23 (0.546) | 3.19 | −4.19 | `exploratory` |
| VB | small cap | 0.03 | SMB | +0.599 | `[+0.516, +0.684]` | −2.97 | 1.13 | −1.63 (0.551) | 3.16 | +2.89 | `rejected` |
| VTV | value | 0.03 | HML | +0.337 | `[+0.225, +0.471]` | −2.60 | 1.17 | −1.39 (0.533) | 3.28 | +2.57 | `rejected` |
| IJH | mid cap | 0.05 | SMB | +0.480 | `[+0.390, +0.582]` | −3.47 | 1.45 | −1.48 (0.427) | 4.06 | −0.28 | `exploratory` |
| IWF | growth | 0.18 | HML (−) | +0.278 | `[+0.200, +0.378]` | +2.27 | 1.02 | +1.36 (0.600) | 2.86 | −0.58 | `exploratory` |
| IJR | small cap | 0.06 | SMB | +0.889 | `[+0.796, +0.953]` | −2.99 | 0.71 | −2.26 (0.755) | 2.00 | +0.95 | `rejected` |
| IWD | value | 0.18 | HML | +0.350 | `[+0.228, +0.472]` | −3.63 | 1.07 | −2.10 (0.578) | 2.99 | +0.63 | `rejected` |
| VBR | small value | 0.05 | HML | +0.410 | `[+0.322, +0.480]` | −2.78 | 1.15 | −1.50 (0.541) | 3.22 | −0.62 | `exploratory` |
| VBK | small growth | 0.05 | HML (−) | +0.125 | `[+0.041, +0.211]` | −3.49 | 1.57 | −1.35 (0.387) | 4.41 | +2.84 | `rejected` |
| IVW | growth | 0.18 | HML (−) | +0.224 | `[+0.141, +0.328]` | +0.93 | 1.45 | +0.40 (0.428) | 4.05 | −0.07 | `unresolved` |
| IWR | mid cap | 0.18 | SMB | +0.293 | `[+0.172, +0.408]` | −3.86 | 1.43 | −1.67 (0.434) | 4.00 | +0.74 | `rejected` |
| VOE | mid value | 0.05 | HML | +0.434 | `[+0.278, +0.538]` | −4.38 | 1.45 | −1.87 (0.426) | 4.06 | +0.57 | `rejected` |
| IVE | value | 0.18 | HML | +0.302 | `[+0.175, +0.429]` | −2.27 | 1.47 | −0.95 (0.418) | 4.13 | +0.19 | `exploratory` |
| VOT | mid growth | 0.05 | HML (−) | +0.121 | `[−0.032, +0.255]` | −3.22 | 2.67 | −0.58 (0.180) | 7.48 | +2.60 | `rejected` |
| QUAL | quality | 0.15 | RMW | +0.186 | `[+0.101, +0.247]` | −2.15 | 1.12 | −1.19 (0.555) | 3.13 | +1.14 | `rejected` |
| IWS | mid value | 0.23 | HML | +0.392 | `[+0.256, +0.481]` | −4.91 | 1.33 | −2.30 (0.468) | 3.73 | +0.63 | `rejected` |
| IWP | mid growth | 0.23 | HML (−) | +0.168 | `[+0.020, +0.315]` | −2.74 | 2.71 | −0.48 (0.176) | 7.58 | +2.19 | `rejected` |
| IWN | small value | 0.24 | HML | +0.392 | `[+0.330, +0.464]` | −2.55 | 0.81 | −1.79 (0.702) | 2.28 | +0.49 | `exploratory` |
| MTUM | momentum | 0.15 | UMD | +0.444 | `[+0.277, +0.562]` | −2.95 | 2.62 | −0.55 (0.185) | 7.34 | +1.10 | `rejected` |
| IWO | small growth | 0.24 | HML (−) | +0.134 | `[+0.054, +0.223]` | −2.55 | 1.38 | −1.15 (0.450) | 3.87 | +1.61 | `rejected` |
| IJK | mid growth | 0.16 | HML (−) | −0.067 | `[−0.174, +0.003]` | −4.32 | 1.58 | −1.66 (0.384) | 4.43 | +1.56 | `rejected` |
| IUSG | growth | 0.04 | HML (−) | +0.207 | `[+0.129, +0.306]` | +0.72 | 1.33 | +0.34 (0.469) | 3.73 | +0.18 | `unresolved` |
| IJS | small value | 0.18 | HML | +0.367 | `[+0.309, +0.435]` | −2.51 | 0.96 | −1.58 (0.628) | 2.69 | +0.61 | `rejected` |
| IJJ | mid value | 0.18 | HML | +0.411 | `[+0.287, +0.505]` | −2.96 | 1.88 | −0.91 (0.307) | 5.26 | −0.56 | `exploratory` |
| IUSV | value | 0.04 | HML | +0.310 | `[+0.184, +0.433]` | −2.18 | 1.45 | −0.93 (0.425) | 4.07 | +0.06 | `exploratory` |
| IJT | small growth | 0.18 | HML (−) | −0.067 | `[−0.220, +0.034]` | −3.81 | 1.29 | −1.85 (0.485) | 3.61 | +1.39 | `rejected` |
| SPYG | growth | 0.04 | HML (−) | +0.223 | `[+0.140, +0.328]` | +1.06 | 1.45 | +0.45 (0.428) | 4.05 | −0.05 | `unresolved` |
| VLUE | value | 0.15 | HML | +0.393 | `[+0.269, +0.539]` | −2.40 | 2.04 | −0.66 (0.273) | 5.71 | −0.32 | `exploratory` |
| SPYV | value | 0.04 | HML | +0.303 | `[+0.175, +0.429]` | −2.14 | 1.48 | −0.89 (0.417) | 4.14 | +0.23 | `exploratory` |
| RPG | growth | 0.35 | HML (−) | +0.084 | `[−0.124, +0.293]` | −4.99 | 2.84 | −0.81 (0.162) | 7.96 | +2.50 | `rejected` |
| SLYV | small value | 0.15 | HML | +0.367 | `[+0.309, +0.435]` | −2.44 | 0.96 | −1.53 (0.627) | 2.70 | +0.58 | `rejected` |
| SLYG | small growth | 0.15 | HML (−) | −0.067 | `[−0.219, +0.034]` | −3.73 | 1.28 | −1.81 (0.486) | 3.60 | +1.35 | `rejected` |
| SPMD | mid cap | 0.03 | SMB | +0.481 | `[+0.391, +0.582]` | −3.47 | 1.44 | −1.49 (0.429) | 4.04 | −0.24 | `exploratory` |
| MDYG | mid growth | 0.15 | HML (−) | −0.068 | `[−0.174, +0.003]` | −4.31 | 1.58 | −1.66 (0.385) | 4.42 | +1.57 | `rejected` |
| SPHQ | quality | 0.15 | RMW | +0.176 | `[+0.079, +0.296]` | −0.56 | 1.34 | −0.26 (0.466) | 3.75 | −0.13 | `unresolved` |
| IWY | growth | 0.20 | HML (−) | +0.302 | `[+0.207, +0.414]` | +3.09 | 1.33 | +1.45 (0.468) | 3.74 | −1.39 | `exploratory` |
| TILT | multifactor | 0.25 | HML | +0.148 | `[+0.113, +0.171]` | −0.95 | 0.38 | −0.86 (0.913) | 1.08 | −1.21 | `rejected` |
| JHMM | multifactor | 0.41 | HML | +0.212 | `[+0.127, +0.303]` | −3.60 | 1.35 | −1.66 (0.462) | 3.78 | −0.11 | `unresolved` |
| SPSM | small cap | 0.03 | SMB | +0.889 | `[+0.797, +0.953]` | −2.95 | 0.70 | −2.24 (0.759) | 1.97 | +0.94 | `rejected` |
| MDYV | mid value | 0.15 | HML | +0.411 | `[+0.288, +0.505]` | −2.90 | 1.88 | −0.89 (0.307) | 5.26 | −0.57 | `exploratory` |
| EZM | mid cap | 0.38 | SMB | +0.554 | `[+0.456, +0.677]` | −3.43 | 1.59 | −1.31 (0.382) | 4.45 | −1.06 | `exploratory` |
| FTA | value | 0.58 | HML | +0.452 | `[+0.354, +0.553]` | −3.85 | 1.57 | −1.49 (0.388) | 4.40 | −0.33 | `exploratory` |
| FTC | growth | 0.58 | HML (−) | +0.059 | `[−0.069, +0.166]` | −1.03 | 1.77 | −0.34 (0.334) | 4.95 | −0.69 | `rejected` |

**Four "growth" products delivered a positive HML loading.** IJK, IJT, SLYG and MDYG
— the S&P MidCap 400 Growth and SmallCap 600 Growth indexes under two sponsors — have
sign-adjusted loadings of −0.067, meaning a raw HML loading of **+0.067**. They are
graded against the short leg of value and tilted, weakly, towards value. That is an
exposure-delivery failure, and it is what clause (a) exists to catch.

**Rolling loadings are stable almost everywhere.** Thirty-seven 36-month windows per
fund; only RPG (twelve sign changes, range 0.39), VOT (two) and FTC (one) change sign
at all. TILT's rolling loading moves over a range of 0.058 across six years, the
tightest on the shelf.

---

## 4. Statistical alpha versus implementation value

These are two questions with two answers and the specification forbids collapsing
them. **A fund can be worth owning with zero alpha if it delivers a wanted exposure
cheaply; a positive alpha over a short history is not evidence of skill.**

Before any of it can be read, the **model-misfit pedestal**. VTI holds the market
portfolio at a three-basis-point fee, so under a correctly specified model its alpha
should be about −0.03 pp/yr. Measured:

| Specification | VTI alpha, pp/yr | HAC SE | *t* | Market beta | R² |
| --- | ---: | ---: | ---: | ---: | ---: |
| CAPM | −0.396 | 0.377 | −1.05 | 0.9968 | 0.9985 |
| FF3 | −0.513 | 0.185 | −2.77 | 1.0001 | 0.9991 |
| **FF5+UMD** | **−0.547** | 0.161 | **−3.41** | 0.9967 | 0.9992 |

**Read every alpha in §3 as a distance from −0.55, not from zero.** The misfit is
0.52 pp/yr, significant on its own standard error, and it is common to all 44 funds.
It does not rescue the column: the median raw alpha moves from −2.92 to −2.38
against the pedestal, the same six remain above it and 38 below, and the number of funds
whose distance from the pedestal exceeds their own detection threshold falls from 8 to
**4**. The pedestal makes the alphas smaller and less measurable, not more real.

Four cases make the statistical/implementation distinction concrete.

- **VUG.** Shrunk alpha **+1.23 pp/yr**, and it beat its cheap replication by
  **4.19 pp/yr**. Both numbers are the same fact and neither is skill: because a fund
  is never part of the basis that replicates it, VUG's replication degenerates to
  **VTI at weight 1.000**, so its "shortfall" is the realised excess return of
  large-cap growth over the total market from 2020 to 2025. *Statistical conclusion:
  none. Implementation conclusion: VUG delivered a −0.284 HML loading stably at 3 bp.*
- **TILT.** The only genuinely powered alpha here: HAC standard error **0.38 pp/yr**
  against a median of 1.44, MDE₈₀ **1.08** against a median of 4.02, shrinkage factor
  **0.913** — barely shrunk because it barely needs to be. Raw alpha **−0.95 pp/yr**
  on a 0.25% fee, and it beat its replication by 1.21. `rejected` anyway, on clause
  (a): HML loading **+0.148** against a 0.15 threshold, a miss of 0.002, on an
  interval `[+0.113, +0.171]` that contains the threshold. *Statistical conclusion: a
  small negative residual, the one alpha this window could see. Implementation
  conclusion: a market-tilt product that does what it says, too weakly to clear a
  threshold set before anyone looked.*
- **IJH and SPMD.** The same index; loadings +0.480 and +0.481, alphas −3.47 both,
  shortfalls −0.28 and −0.24, fees 0.05% and 0.03%. Indistinguishable delivery,
  separated by three basis points. *Statistical conclusion: none — a −3.47 alpha
  against a 4.05 detection threshold is an unmeasured quantity. Implementation
  conclusion: mid-cap exposure is available at 3 bp with no measurable shortfall.*
- **EZM, FTA, JHMM.** Fees of 0.38%, 0.58% and 0.41%, the three dearest funds not
  rejected, with shortfalls of −1.06, −0.33 and −0.11. **A fee comparison is not a
  cost comparison**, and this is the direction usually forgotten: the cheap fund can
  lose more to a replication than the expensive one.

The reverse case is the common one. **27 of 44 products have a positive shortfall and
22 exceed the 0.50 pp/yr clause**, while the largest fee premium any product carries
over its own replicating basis is 0.55 pp/yr and the median is 0.12. The biggest
shortfalls — VB +2.89, VBK +2.84, VOT +2.60, VTV +2.57, RPG +2.50 — are five to a
hundred times any fee difference in the table. **Whatever separates these products
from cheap broad funds over this window, it is not the expense ratio.**

---

## 5. The frozen falsifier, and why a *t*-statistic is not part of it

Verbatim, frozen before any return was read:

> A fund is rejected as an implementation candidate when ANY of: (a) the point
> estimate of its loading on its intended factor is below 0.15 over the common
> period; (b) the intended loading's sign flips between the first and second half of
> the fund's common-period history; (c) its tracking difference versus a cheap
> broad-market fund plus the same combination of broad funds that approximates its
> exposures is worse than its stated expense ratio advantage by more than 0.50
> percentage points per year; or (d) its total realised cost of ownership, including
> expense ratio, tracking difference and realised taxable distributions, exceeds the
> materiality threshold of 1.0 percentage point per year above the broad-market
> comparator without a corresponding exposure. **A t-statistic on residual alpha below
> 2 is NOT a falsifier: it usually means the sample cannot identify a small residual
> return, not that the fund is useless.**

Every clause is about exposure or cost; none is about a residual return. **A *t*-rule
would not even be conservative here, which is what is usually missed: 26 of the 44
primary alphas already have |*t*| ≥ 2, and 24 of those 26 are negative** (the
positives are IWF and IWY). Reading *t* as the verdict would not kill the shelf for
being unmeasurable; it would convict most of it of a large negative residual that 72
months cannot separate from model misfit. The detection threshold is the honest bar:
at 80% power it corresponds to |*t*| > 2.80, which 8 of 44 clear, all negative.

Three boundary cases decide how the statuses read.

- **`unresolved` is a statement about the interval, `rejected` about the point
  estimate.** Clause (a) fires on the point estimate; `unresolved` applies when no
  clause fires and the 95% interval *contains* 0.15. So TILT at +0.148,
  `[+0.113, +0.171]`, is `rejected`, while IVW at +0.224, `[+0.141, +0.328]`, is
  `unresolved` — both intervals contain the threshold and the point estimate breaks
  the tie in opposite directions. Applied exactly as frozen, and reported because it
  is the least robust classification on the page.
- **Clause (b) fired once**, on FTC: +0.077 then −0.060, on an interval
  `[−0.069, +0.166]` that contains zero. That is a sign flip in a loading
  indistinguishable from no loading.
- **Clause (d) never fired alone.** All eight firings are on funds that had already
  fired (a) and (c), because (d) requires a missing exposure by construction. It
  changes no status; it prices the ones already rejected: RPG 3.17, VBK 2.91, VOT
  2.67, IWO 2.06, IJK 1.85, MDYG 1.84, IJT 1.72, SLYG 1.62 pp/yr.

The 5 `unresolved` funds are IVW, IUSG and SPYG (large-cap growth, HML (−) around
0.21), SPHQ (quality, RMW +0.176) and JHMM (multifactor, HML +0.212). In each the
interval straddles 0.15 and 72 months cannot say more.

---

## 6. The multiple-testing family

**The family is 44 funds × 3 specifications = 132 alpha tests**, not the funds or the
specification anyone chose to report. CAPM, FF3 and FF5+UMD are estimated for all 44
and all 132 *p*-values enter the correction, because a residual that appears in one
specification and not the others is not a finding.

| Correction | Rejections of 132 |
| --- | ---: |
| Uncorrected at 0.05 | 56 |
| Uncorrected at 0.10 | 65 |
| **Benjamini–Hochberg at 0.10** | **54** |
| **Holm–Bonferroni** | **5** |
| BH, family padded to every mandate-matching series × 3 = 6 315 | 2 |
| Holm, same padded family | 0 |

**BH at 0.10 is barely different from no correction here** — 54 against 56 at an
uncorrected 0.05 — because the *p*-value distribution is dominated by a mass of
genuinely small values. Of the 54 survivors, **50 are negative and 4 positive**,
spanning 26 tickers and 26 FF5+UMD, 24 FF3 and 4 CAPM fits.

**BH assumes independence and this family has almost none**: three nested
specifications per fund, the same six factors, the same 72 months, eight pairs of
funds on an identical index. The artifact says so itself — the BH count is "an
OPTIMISTIC bound and Holm is the defensible one". **Holm, valid under arbitrary
dependence, leaves five tests: IJR and SPSM (FF5+UMD), IWS (FF3 and FF5+UMD) and IWD
(FF5+UMD) — all negative, and IJR and SPSM are the same index, so five tests are three
products.** The declared hostile denominator collapses it further: padding the family
to every mandate-matching series screened, at *p* = 1.0 for the 6 183 never regressed,
leaves **2 BH rejections and 0 Holm** — and the two are IJR and SPSM, the S&P
SmallCap 600 twice. Padding with *p* = 1 cannot create a rejection and strictly
tightens both corrections, so that is the most pessimistic honest denominator.

**Exposure is the family that survives.** The intended-loading tests are a separate
44-member family, each a one-sided test that the sign-adjusted loading exceeds zero:
37 reject uncorrected and **38 reject under BH**. That asymmetry — 38 of 44 loadings
against 5 of 132 alphas under a defensible correction — is the whole result in two
numbers. It is also a weaker claim than the falsifier's, which asks for a loading of
0.15 rather than merely for one distinguishable from zero.

One naming hazard: the artifact's `estimates` list also has 132 entries, being three
reported numbers for each of 44 funds. Coincidence of arithmetic, not the same 132.

---

## 7. Shrinkage, the annualisation trap, and the look-ahead replication

Every alpha is shrunk before it means anything. Taking true gross alpha as normal with
mean zero and cross-sectional standard deviation `sigma_true = 1.25%/yr`
([Fama and French 2010](https://doi.org/10.1111/j.1540-6261.2010.01598.x)), the
posterior mean is `observed × sigma_true² / (sigma_true² + SE²)`, computed with **each
fund's own HAC standard error** and never the framework's reference factor of 0.121 —
that is the factor at the reference standard error of 3.36%/yr and would be wrong for
every fund here in both directions. Realised factors run **0.162** (RPG, SE 2.84) to
**0.913** (TILT, SE 0.38), median **0.431**.

**The trap: an annual alpha is twelve times a monthly intercept, so its standard error
annualises by ×12 and never by ×√12.** Both are scaled by 12 in the code. Using √12
would divide every standard error by 3.46 and shrink far too little:

| Fund | Raw alpha | HAC SE ×12 | Factor | Shrunk | SE if ×√12 | Factor | Shrunk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| VO | −3.78 | 1.59 | 0.381 | **−1.44** | 0.46 | 0.881 | −3.33 |
| RPG | −4.99 | 2.84 | 0.162 | **−0.81** | 0.82 | 0.699 | −3.49 |
| IJR | −2.99 | 0.71 | 0.755 | **−2.26** | 0.21 | 0.974 | −2.91 |
| TILT | −0.95 | 0.38 | 0.913 | **−0.86** | 0.11 | 0.992 | −0.94 |

The right-hand block is arithmetic, not a result: it is what this page would print if
the error were made, and on RPG it would quadruple the posterior. **The shrunk alpha
carries no interval by construction** — a posterior mean under a fixed prior is not a
sampling estimate — so the raw alpha, its HAC standard error and MDE₈₀ are printed
beside it, and it must never be quoted alone.

**The cheap replication has the same no-interval property, for a different reason.**
The general rule that this comparator, not the market, is the control a candidate must
beat is [decision 0003](../decisions/0003-cheap-broad-market-control.md).
The secondary comparator is a combination of **VTI, VUG, VTV and VB** with non-negative
weights summing to one, fitted by constrained least squares on the **same 72 months**
as the exposure regression. An investor could not have known those weights in advance,
so **the comparison is a best case for the replication and therefore a hard test for
the product**, and a sampling interval around a look-ahead quantity would imply a
precision the construction does not have.

Two structural facts a reader needs before using clause (c). **Three of the four
building blocks are themselves audited products, and a fund is never in its own
basis**, so the replication degenerates for exactly those three: VUG is replicated by
VTI at weight 1.000 (tracking error 7.36 pp/yr), VB by 0.733 VTI + 0.267 VTV (8.31),
VTV by 0.784 VTI + 0.216 VB (7.48). For these three the "implementation shortfall" is
the realised style return of 2020–2025 rather than an implementation cost, and VB's
and VTV's rejections should be read as "small-cap and value underperformed the market
over these 72 months" — a return finding this page is not entitled to make. And
**tracking error against the combination ranges 1.38 pp/yr (TILT) to 8.65 (MTUM),
median about 5**, against a clause-(c) threshold of 0.50. A difference of means with
that much dispersion over 72 months is not resolvable at 0.50 pp/yr. **Clause (c) is a
decision rule applied as frozen, not a measurement**, and 22 of 24 rejections rest on
it.

---

## 8. Attrition, survivorship, and a defect in the attrition number

The frame is taken at the **start** of the window so that attrition is measurable
rather than invisible: screening the 2025Q4 census would select on survival.

| Quantity | Reported in the artifact | Recomputed from the committed screen list |
| --- | ---: | ---: |
| Mandate-qualifying series in the 2019Q4 frame | 1 513 | 1 513 |
| Mandate-qualifying series in the 2025Q4 frame | 1 906 | — |
| Present in frame, absent at follow-up | **358 (23.66%)** | **312 (20.62%)** |
| Frame-date net assets of that set | **333.5 bn USD** | **138.7 bn USD** |
| Absent from frame, present at follow-up | 751 | — |

**The columns disagree because the reported figure counts renames as deaths.** The
"disappeared" set is a difference of two sets each built by running the mandate and
exclusion patterns over that census's *own* series names, so a series that renamed out
of the mandate pattern, or into the exclusion pattern, is counted as gone even though
it is still filing. The committed file contradicts itself on this: **four of its own
fifteen largest "disappeared" series are recorded elsewhere in the same file as still
filing at the follow-up quarter, with net assets** — EuroPacific Growth Fund, T. Rowe
Price New America Growth, Spectrum Growth and AST T. Rowe Price Growth Opportunities,
holding 136.3, 17.3, 4.4 and 2.6 bn USD respectively **at the follow-up quarter they
are recorded as having disappeared from**. Counting only series absent from
the 2025Q4 census altogether gives 312 and 138.7 bn. **The 46-series difference carries
194.8 bn, 58% of the headline asset figure, and one fund is most of it.** The same
error runs in reverse through the 751 "launched" count.

**The direction of the finding is unchanged and the caveat still holds.** Even at
20.6%, a fifth of the 2019 listed factor shelf is gone in six years, and this is a
**lower bound**: public N-PORT filings begin in 2019, so a fund that closed before
2019Q4 is invisible to both censuses. A universe assembled from today's listings would
contain the launches and none of the 312. None of the 44 audited funds is
absent at follow-up, which is true by construction — 72 months of filed returns were
required.

---

## 9. Hostile tests: what ran, what did not, and what was wrong on the way

| Declared test | Status |
| --- | --- |
| Re-estimate under CAPM, FF3 and FF5+UMD and report all three | **Run.** 132 fits; the correction consumes all of them. |
| Fixed calendar halves and rolling 36-month windows | **Run.** 37 windows per fund; only RPG, VOT and FTC change sign. |
| Substitute DGS3MO and DFF for TB3MS and show the effect | **Run.** Wrong in the first two successful runs; fixed in this one. |
| Every screened fund and specification in the denominator | **Run.** 6 315-member padded family: 2 BH, 0 Holm. |
| Compare against a fitted combination of cheap broad funds, stating the look-ahead | **Run**, §7. |
| Cross-check every N-PORT return against an independent source | **Did not run at all.** |
| Report MDE₈₀ beside every alpha | **Run.** |
| Measure attrition between the two censuses | **Run**, with the defect in §8. |

**The cross-source check produced nothing.** All 44 tickers are in the artifact's
`unavailable` list with `HTTPError` and the `compared` list is empty — the Yahoo chart
endpoint refused every request, which is the behaviour
[Decision 0002](../decisions/0002-no-research-grade-free-price-source.md) recorded.
**Form N-PORT Item B.5 is therefore the sole measurement of every return here, with no
independent corroboration of any kind**, and the specification's stated reason for
having a secondary source — "two independent measurements of the same quantity make a
silent adjustment error visible" — is unmet. The run's own summary does not say this;
it is visible only in the diagnostics.

**The cash-rate sensitivity diagnostic was wrong in the first two successful runs, and
the error is worth recording because it was large and it pointed the wrong way.** Both
printed the French one-month bill at **2.665** (percent per year) beside TB3MS
**0.02755**, DGS3MO **0.02860** and DFF **0.02753** — *decimals* per year, because the
FRED reader converts published percent with `value / 100`. The printed "alpha shift"
of about **2.637 pp/yr** for each alternative was a percent minus a decimal, and as
printed it asserted that the cash-series choice moves every alpha by 2.6 pp/yr — which
would have been the largest single quantity in the audit and would have refuted the
specification's claim that the choice did not make the answer. Corrected in this run,
with a unit guard that now refuses a series whose declared units are not
`decimal_per_year`, the shifts are **−0.09 (TB3MS), −0.20 (DGS3MO) and −0.09 (DFF)
pp/yr**. No conclusion ever depended on it: the diagnostic is consumed nowhere, and a
constant shift in the dependent variable moves only the intercept, so every loading is
invariant by construction.

**The model-misfit pedestal was added between the first and second successful runs**
and is the one addition that changes how the page reads (§4). Without it the audit
reports that a three-basis-point index fund carries a −3 pp/yr alpha and leaves the
reader to guess how much of that is the model; with it, 0.52 pp/yr of the answer is
measured. It is a control, not a result, and it makes the alpha column *less*
informative rather than more.

**Amendments are counted but their content is not.** 15 of the 1 205 filings are
`NPORT-P/A` amendments across 11 funds. Where two filings report the same month the
later filing date wins and the reader warns rather than averaging; which months
disagreed, and by how much, is not in the artifact.

---

## 10. Verified facts, assumptions, open questions

**Verified.** The screen was frozen, mechanical and applied before any return was
downloaded; returns were never fetched for a fund that failed it, so no screen decision
could be revised after seeing performance, and all 2 105 mandate-matching series are
committed with their outcome and first failing criterion. The Item B.5 month alignment
is checked, not assumed. All 44 funds have 72 of 72 months with no gap, no
interpolation and no fetch failure. The expense ratio is **not** subtracted twice —
Item B.5 is already net of fees and assumes reinvested distributions. Every excess
return is taken over the rate `Mkt-RF` is defined against. Both French files are pinned
by raw sha256 and a new vintage aborts the run. The HML/RMW volatility band from the
[Phase 1 gate](fama-french-reproduction.md) does **not** propagate here: every figure
is a loading, a mean or a difference of means, and nothing divides by those
volatilities.

**Assumptions.** `sigma_true = 1.25%/yr` is *transferred, not measured*: it comes from
a bootstrap of US active equity mutual funds over 1984–2006 and is applied here to
index-tracking ETFs over 2020–2025, and it decides every shrunk number on the page. The
intended-factor map is a declaration — growth graded on negative HML, size-and-style on
its style leg, multifactor on HML — written down before any regression so no fund could
be graded against whichever loading turned out largest. The thresholds are a priori and
none is tuned: loading 0.15, materiality 1.0 pp/yr, shortfall 0.50 pp/yr, HAC 6 lags,
bootstrap mean block 6 months; the predeclared 3- and 12-month neighbour blocks are
named in the specification but their intervals are **not in the artifact**, so block
sensitivity is unreported rather than zero. Benjamini–Hochberg treats the 132 tests as
independent and they are not. Every figure is PRETAX.

**Open questions.**

1. **How much of the remaining −2.38 pp/yr median is still model misfit?** The pedestal
   measures the misfit a fund with *market* exposure carries. A small-cap value fund is
   not the market, and nothing here measures the misfit at its corner of the factor
   space. A pedestal per style — the same control run on a passive index at each corner
   — would bound it, and does not exist.
2. **Does any N-PORT return agree with an independent measurement?** Unanswered; the
   cross-check failed for all 44.
3. **What do realised taxable distributions and turnover do to the cost ranking?**
   Neither is in Form N-PORT; both are in Form N-CSR as unstructured HTML and are
   recorded as **gaps** rather than estimated. Clause (d) is therefore evaluated
   without the distribution term the falsifier names.
4. **Would an out-of-sample replication change clause (c)?** Weights fitted on a prior
   window would remove the look-ahead. Not run, and not runnable on 72 months without
   shortening the estimation window further.

---

## 11. What this does not establish

- **Not skill, in any direction.** Six positive shrunk alphas, all large-cap growth,
  none exceeding its own detection threshold, and all measured against a model that
  charges the market portfolio itself −0.55 pp/yr. A positive alpha over a short
  inception history is not evidence of future manager skill.
- **Not investable cost.** Bid-ask spreads, brokerage, taxes, realised distributions
  and portfolio turnover are all absent. Nothing here is a net-of-everything return.
- **Not a survivorship-free universe.** N-PORT begins in 2019; a fund that closed
  before 2019Q4 is invisible to both censuses, so the measured attrition is a lower
  bound and the true rate is higher.
- **Not audited data.** Item B.5 returns are fund-reported and unaudited, and Form
  N-PORT General Instruction G lets each filer use its own internal methodology, so two
  funds' returns are not guaranteed to be computed identically. With the cross-source
  check dead, that assumption is untested.
- **Not the whole shelf.** Exchange-traded only, ≥1 bn USD in 2019, ≤0.60% net expense
  ratio, inception on or before 2016-12-31.
- **Not a return finding.** Where a product's shortfall is really the realised style
  return of 2020–2025 (§7), this page is measuring the window, not the product.

**The binding constraint is the data contract and the length of the window, not the
evidence.** Seventy-two months of unaudited, self-reported, per-filer-methodology
returns from a source that begins after the deaths that matter most is what limits
every conclusion here. Form N-PORT is a materially stronger contract than any price
feed Decision 0002 tested, and it is still not enough to promote anything.

---

## 12. How this composes with Experiment 001

[Experiment 001](factor-persistence.md) left HML, UMD and RMW `unresolved` and CMA
`rejected`. **No factor reached `exploratory`, so no premium is established for any
exposure audited here.** The two experiments answer different halves of one product and
they multiply rather than add: what a shareholder receives is
`premium × delivered loading − cost`. Experiment 001 could not sign the first term for
any factor; this page measures the second and finds it delivered; the third is a cost
for 27 of 44 products against a look-ahead replication. **A product audit cannot rescue
an exposure whose premium is not established.**

Two instances make that concrete.

- **Sixteen of the 44 funds are graded on a *negative* HML loading and three reached
  `exploratory`** (VUG, IWF, IWY). "Delivering the intended exposure" there means
  reliably holding the *short* leg of a premium whose post-publication estimate in
  Experiment 001 is +1.57 pp/yr on a 90% interval of `[−2.28, +5.54]` — unresolved in
  sign. A product that manufactures the short leg of an unresolved premium precisely
  and cheaply is not a candidate for anything.
- **The two factors Experiment 001 singled out have almost no shelf.** RMW was
  prioritised there because it alone did not decay (96% retained); its entire
  investable shelf here is QUAL (`rejected` on clause (c)) and SPHQ (`unresolved`). UMD
  was ruled out there as a standalone sleeve on cost; its entire shelf here is MTUM,
  which **does** deliver its exposure — UMD loading +0.444, `[+0.277, +0.562]` — and is
  `rejected` on clause (c) after losing 1.22 pp/yr to a three-fund combination whose
  fee premium over it was 0.12. That is the cost result Experiment 001 predicted,
  showing up in a product.

---

## Consequence for this repository

1. **Nothing is promoted, and Decision 0002 is not the only reason.** Even with a
   licensed source, no product here would qualify: the exposures that are cleanly
   delivered belong to factors with no established premium, the alpha column is
   unmeasurable, and the cost comparison that rejected 22 products is decided by a
   look-ahead comparator. The 15 `exploratory` products may be used as implementation
   proxies in a later experiment and for nothing else; the programme-wide statement of
   what that leaves is [decision 0004](../decisions/0004-no-sleeve-promoted.md).
2. **Exactly what would change that.** A licensed, point-in-time, survivorship-free
   total-return source with a documented corporate-action and delisting contract —
   Decision 0002's deferred alternative — covering the listed shelf from at least 2003,
   so the window is **240 months rather than 72**. Re-freeze the specification against
   it and run **confirmatory**. Promotion then requires all of: intended loading at or
   above 0.15 with a 95% interval excluding 0.15 from below; the same on both fixed
   halves; shortfall at or below **0 pp/yr** against a replication whose weights are
   fitted on a **prior** window; total cost of ownership including realised
   distributions and turnover at or below **1.0 pp/yr**; and the underlying factor at
   `exploratory` or better in Experiment 001, which no factor currently is. **A residual
   alpha of any sign or size remains inadmissible as a promotion criterion.**
3. **Any future page that prints a fund alpha must print its pedestal beside it.** A
   factor model that charges the market portfolio −0.55 pp/yr over a window is not a
   zero-mean measuring instrument on that window, and an alpha quoted as a distance
   from zero is that much overstated. The control costs one extra regression and it is
   the difference between "this index fund destroyed 3 pp/yr" and "this model does not
   span 2020–2025 to better than half a point".
4. **The edge budget's fund-cost line survives, with an addition.**
   [Expected edge decomposition](expected-edge-decomposition.md) books fund cost
   reduction at 49 bp/yr central against an investor's own counterfactual — a statement
   about replacing an expensive fund with a cheap one, untouched here, and the 44
   audited funds have a median net expense ratio of 0.15%. What this page adds is the
   quantity that line does not carry: **for most of this shelf the gap to a cheap
   replication is larger than the fee.** 22 of 44 lost more than 0.50 pp/yr to a
   four-fund combination whose fee premium over them was at most 0.32 pp/yr and
   typically 0.12, with the five largest shortfalls at 2.5 to 2.9 — against a
   look-ahead comparator, so a best case for it. **A fee comparison is not a cost
   comparison.**
5. **Two defects remain open**, neither of which changes a status: the attrition rename
   count (§8), and the degenerate replication for the three basis funds that are
   themselves audited (§7). The cash-rate unit error is fixed and its history is
   recorded in §9 rather than erased.
6. **The listed factor shelf is thinner than it looks.** After a mechanical screen, 44
   products, of which 16 are eight indices sold twice, one is the entire momentum
   shelf, and two each are quality and multifactor. Any later work needing a momentum
   or quality proxy has a single candidate and no fallback.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_002_fund_exposure --build-universe
uv run python -m portfolio_edge.experiments.exp_002_fund_exposure --view-results
uv run pytest tests/unit/test_experiments_exp_002_fund_exposure.py
uv run pytest tests/unit/test_exp_002_universe_committed.py
```

Every run above — its git commit, working-tree diff hash, dataset-manifest hashes,
artifact hashes and `results_viewed` event — is in
[`research/ledger.jsonl`](../../research/ledger.jsonl). Artifacts for the reported run
are under `research/artifacts/fbe139abd9114abeb69e39fad8839f8e/`: `result.json`
(sha256 `e99a8de84f60bdd2…`), `summary.md`, and five parquet frames — `screen` (all
2 105 screened series), `coverage`, `exposures`, `outcomes`, `replication`. The two
superseded successful runs are kept rather than deleted, because the difference
between them is the record of what §9 describes. Retrieval date for every source:
**2026-08-12**. Seed 20260812.
