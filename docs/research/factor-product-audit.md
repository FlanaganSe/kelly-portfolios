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
ceiling: until a source with a documented total-return and corporate-action
contract is licensed, fund-level work may motivate further testing, may not promote
a sleeve, and may not appear in the app as a finding. Fifteen products reached the
per-fund status `exploratory`; that permits them to be used as implementation
proxies in a later experiment and permits nothing else.

## Conclusion

Of 8 563 fund series that filed a Form NPORT-P in the 2019Q4 SEC census, 2 105
matched the predeclared factor-mandate pattern, **44 passed the whole screen**, and
all 44 had a filed Item B.5 monthly total return for every one of the 72 months
from 2020-01 to 2025-12. **15 reached `exploratory`, 24 were `rejected` on the
frozen falsifier, 5 are `unresolved`.**

**The exposure question is answerable on this window and the alpha question is
not.** Those are different findings and they must not be merged.

1. **Exposure is largely delivered.** Across the 44-fund family of intended-loading
   tests, **38 survive Benjamini–Hochberg at 0.10** — the only family on this page
   where a correction leaves most of its members standing. A large-cap value fund
   loads on HML, a small-cap fund loads on SMB, and the loadings are stable across
   the fixed calendar split. This is a manufacturing result, not a return result.
2. **Alpha is negative almost everywhere and measurable almost nowhere.** 38 of the
   44 shrunk alphas are negative; the median is **−1.33 pp/yr**. Only **8 of 44**
   raw alphas exceed the minimum alpha their own window could detect at 80% power,
   and **every one of those eight is negative**. The median minimum detectable
   alpha across the 132 fund-by-specification tests is **4.52 pp/yr**, which is
   larger than any plausible true alpha. An interval containing zero here is a
   statement about 72 months, not about a fund.
3. **The six positive shrunk alphas are all the same trade.** VUG, IWF, IWY, IVW,
   IUSG and SPYG — every one a large-cap growth product, over a window in which
   large-cap growth beat the market. That is a factor-model misfit shared by every
   fund priced by the same six factors over the same 72 months, and it is the
   reason no fund is promoted on a residual return in either direction.

**Nothing here is alpha in the sense of skill, and nothing here is validated.** The
only defensible reading of a positive residual over 72 months is that the model did
not span the window.

### What decided the 24 rejections

| Clause | What it tests | Fired on |
| --- | --- | ---: |
| (a) intended loading below 0.15 | the exposure is absent | 10 |
| (b) intended loading flips sign across the fixed halves | the exposure is not an exposure | 1 |
| (c) shortfall to the cheap replication above 0.50 pp/yr | implementation value | 22 |
| (d) total cost above 1.0 pp/yr with no corresponding exposure | cost without exposure | 8 |

Clauses overlap; 24 distinct funds fired at least one. **Clause (c) did most of the
work, and clause (c) is decided against a comparator fitted in sample** (§7). Read
every (c) rejection as "a look-ahead combination of four cheap funds beat this
product over these 72 months", never as "this product is badly run".

**A *t*-statistic below 2 is not a falsifier here, and the specification says so in
its own text.** It usually means the sample cannot identify a small residual
return. The frozen falsifier tests four things, none of which is a *t*-statistic on
alpha: whether the intended loading is present, whether it is stable, whether a
cheap replication beat the product by more than its fee premium explains, and
whether the total cost of ownership exceeds 1.0 pp/yr without a corresponding
exposure. No fund was promoted on residual alpha and none was rejected for one.

---

## 1. What was run

| Field | Value |
| --- | --- |
| Specification | [`research/experiments/exp_002_fund_exposure.yaml`](../../research/experiments/exp_002_fund_exposure.yaml), hash `b4c9a134e106e59bc290445f26eed25e4982660fc82e41accadfe914dc6035bc` |
| Run kind | **exploratory**; does not consume the final holdout |
| Ledger `run_id` | `e95932d2236d48668a566a9a9c079b8f`, `succeeded` and `results_viewed` |
| Frame | SEC N-PORT structured data set **2019Q4**, 8 563 series, sha256 `f8e10bce83ac…`, retrieved 2026-08-12T08:09:23Z |
| Follow-up frame | 2025Q4, 12 552 series, sha256 `4ebb169e6cc0…`, used **only** to measure attrition |
| Returns | Form N-PORT Item B.5 monthly total return per share class, 1 205 filings across 44 funds, already net of the expense ratio and of reinvested distributions |
| Window | 2020-01…2025-12, **72 months**; nothing after 2025-12 was read |
| Factor model | FF5 + UMD, US monthly, French vintage pinned by raw sha256 `cbc3724812132654fbbe8daae3c46e0f90e70008434f94a7986fe49f1db6ad3b` (FF5) and `f405ee2d47a5c75ce05025f789733d0599879361e9836a553504240b89159871` (momentum), retrieved 2026-08-12T06:19:22Z |
| Cash rate | the one-month bill distributed **in the same French file as the factors**, so the intercept is interpretable as alpha |
| Inference | Newey–West HAC at 6 lags; stationary block bootstrap, mean block **6 months frozen not tuned**, 10 000 resamples, resampling the return and the whole design jointly |
| Seed | 20260812 |
| Product facts | [`research/data-manifests/exp_002/product_facts.json`](../../research/data-manifests/exp_002/product_facts.json), each fee, index and inception with its own URL and date read, `as of 2026-08-12` |
| Universe | [`research/data-manifests/exp_002/product_universe.json`](../../research/data-manifests/exp_002/product_universe.json), sha256 `549b3a8ce777a0ab045bd68d84626be8a950c600760084ea1bb09255b54babf3`, built 2026-08-12T08:56:39Z **before any return was downloaded** |

### The data path was gated before anything was believed

Item B.5 reports `rtn1` as the *first* month of the reporting period. Reading it
backwards would shift every history by two months and leave every number looking
plausible, so the alignment is checked rather than assumed. The broad-market
comparator VTI, reconstructed from its own filings, correlates **0.99926** with the
French market total return, regresses on `Mkt-RF` with beta **0.9968** and
R² **0.99852**, and has its worst month in **2020-03** at **−13.80%**. That is the
gate passing, and it is the reason the loadings below can be read at all.

### The run history, including what did not finish

Five executions of this family are in [`research/ledger.jsonl`](../../research/ledger.jsonl).
Reporting only the one that produced numbers is the failure the ledger exists to
prevent.

| Run | Spec hash | Terminal event | Why |
| --- | --- | --- | --- |
| `8b37318c…` | `0f4095f7…` | `failed` | `KeyError: no table 'french_us_ff5_monthly'` — a reader bug, not a data problem. No result. |
| `24c2c919…` | `0f4095f7…` | `abandoned` | Killed while still downloading filings: the committed universe and product-facts files had been moved to `data-manifests/exp_002/` after it started, so it was executing against paths that no longer existed. |
| `c7d2024b…` | `b4c9a134…` | `abandoned` | Killed after ~45 minutes; every filing was cached but it was stalled in retry backoff against the secondary cross-source endpoint, which was answering HTTP 429 to every request. Superseded by a run whose retry budget for that best-effort diagnostic is one attempt. |
| `2645817b…` | `b4c9a134…` | `abandoned`, then **superseded by a correction** | The first entry was appended **while the run was still executing**, on the mistaken belief it was already dead, and it recorded a reason belonging to a different run. The correction is a new line rather than a repair, and it records that the run was then killed *to make the premature entry true*. Mid-download; nothing was viewed. |
| `e95932d2…` | `b4c9a134…` | `succeeded` | The run reported here. |

Two further facts about that history belong in the record.

- **The universe was rebuilt between `c7d2024b` and `2645817b`,** at
  2026-08-12T08:56:39Z, to add nine large- and small-cap growth ETFs (IWF, IVW,
  IWO, IUSG, SPYG, RPG, IWY, ILCG, FTC). They had been failing the expense-ratio
  criterion only because nobody had looked their fees up — a gathering gap, not a
  screen result, and leaving it would have stripped growth mandates out of the
  universe systematically, which is a selection effect in exactly the direction
  that makes a value tilt look better. The rebuild happened **before any return was
  examined**. Six of those nine are in the final 44 and three of the six positive
  alphas above are among them.
- **A sixth execution, `f02d06f7ab1648f88d157a740f8499f3`, was started at
  2026-08-12T09:05:53Z against the same specification hash and has no terminal
  entry.** It is neither `succeeded`, `failed` nor `abandoned`. Until it is
  terminated the ledger is open.

---

## 2. The screen, and the funnel from 2 105 to 44

The rule was frozen before any return series was read, is mechanical, and has no
"and peers" clause. Criteria are applied in a fixed order and only the **first**
failure is recorded, which is what makes the funnel add up.

1. **`mandate_regex`** — the official series name matches
   `\b(value|growth|momentum|quality|profitab\w*|min(?:imum)?\s+volatility|low\s+volatility|multi-?factor|factor|small[- ]?cap|mid[- ]?cap)\b`, case-insensitively.
2. **`exclusion_regex`** — the name does **not** match the predeclared exclusion
   pattern, which removes leveraged and inverse, sector and thematic, single-country
   and non-US, ESG-primary, bond, income, dividend, allocation, target-date, buffer
   and option funds.
3. **`exchange_traded`** — at least one share class carries a ticker flagged `ETF=Y`
   in the Nasdaq consolidated symbol directory, which is an exchange record rather
   than a sponsor claim.
4. **`minimum_net_assets`** — at least 1 000 million USD at the 2019Q4 frame date.
5. **`maximum_expense_ratio`** — net expense ratio at or below 0.60%/yr, read from
   the sponsor's own prospectus or fund page, with the URL and date recorded.
6. **`inception_cutoff`** — inception on or before 2016-12-31, so the audit is not
   measuring a launch.
7. **`mandate_in_map`** — the stated mandate is in the predeclared intended-factor
   map. The reserved value `mandate_changed` is deliberately absent from that map.
8. **`complete_return_coverage`** — a filed Item B.5 return for every month of the
   window, with no gap. A gap excludes; it is never interpolated.

| Stage | Removed | Remaining | What was removed |
| --- | ---: | ---: | --- |
| 2019Q4 census | — | 8 563 | every series that filed a Form NPORT-P |
| `mandate_regex` | 6 458 | **2 105** | everything whose name names no factor mandate |
| `exclusion_regex` | 592 | 1 513 | 185 international, 82 global, 67 income, 60 allocation, 51 emerging, 47 dividend, 16 bond, 10 ESG, 7 developed, 7 "Intl", and the long tail of single-country, sector, leveraged and inverse names |
| `exchange_traded` | 1 374 | 139 | open-end mutual funds and insurance separate accounts with no listed share class — including the largest series in the frame, EuroPacific Growth Fund (158.4 bn), T. Rowe Price Blue Chip Growth (63.5 bn) and "THE U.S. LARGE CAP VALUE SERIES" (29.9 bn) |
| `minimum_net_assets` | 92 | 47 | sub-billion ETFs; the largest excluded is PWV at 973.7 m, then JHML 911.7 m, LRGF 908.5 m, RPV 890.9 m |
| `maximum_expense_ratio` | 1 | 46 | **PDP**, Invesco DWA Momentum, at 0.62% |
| `inception_cutoff` | 1 | 45 | **USMC**, Principal U.S. Mega-Cap Multi-Factor, inception 2017-10-11 |
| `mandate_in_map` | 1 | **44** | **ILCG**, which changed objective inside the window and so has no single stated mandate to be graded against |
| `complete_return_coverage` | 0 | **44** | nothing; all 44 had all 72 months |

**The exchange-traded criterion is by far the largest filter and it is a decision
about investability, not about quality.** It removes 1 374 of the 2 105
mandate-matching series, including every large actively managed mutual fund in the
frame. Whatever this page concludes, it concludes about the *listed* factor shelf.

Two structural facts about what survived:

- **The 44 funds are not 44 independent products.** Six pairs track the identical
  index under two sponsors — IVW/SPYG, IVE/SPYV, IJK/MDYG, IJJ/MDYV, IJS/SLYV,
  IJT/SLYG — and IJH/SPMD both track the S&P MidCap 400 while IJR/SPSM both track
  the S&P SmallCap 600. Sixteen of the 44 funds are eight indices. Each pair's
  loadings agree to about 0.001 and each pair received the same status, which is a
  useful consistency check and a serious problem for any correction that assumes
  independence (§6).
- **The shelf is thin outside value and size.** By stated mandate: 8 growth,
  7 value, 5 mid-cap, 4 each small value, small growth, mid value, mid growth,
  3 small-cap, 2 quality, 2 multifactor and **1 momentum**. MTUM is the entire
  momentum shelf that clears a billion dollars, a 0.60% fee and a 2016 inception.

The 44 also carry index changes that a name-matching check would miss and that the
specification deliberately retains rather than excludes: FTSE Russell added
issuer capping to the Russell style indexes in March 2025 (IWF, IWO, IWY) and to
the mid-cap indexes in March 2024 (IWS, IWP, IWN); S&P added capping to its style
indexes in June 2024 (IVW, IUSG, SPYG); MTUM's index became the "SR Variant" in
December 2020; FTA's and FTC's base universes changed in December 2023; SPMD and
SPSM changed index entirely in January 2020, inside the window. Every one is
recorded in the product facts with a source URL, `as of 2026-08-12`.

---

## 3. The exposure table

Every row is the frozen primary specification: OLS of the fund's monthly excess
return on `Mkt-RF`, `SMB`, `HML`, `RMW`, `CMA` and `UMD`, HAC at 6 lags, 72
observations. **Loading is sign-adjusted for the mandate**: a growth mandate is
graded on a *negative* HML loading of the same magnitude, marked `HML (−)`, because
growth is the short leg of value and not an independent factor. The interval is the
stationary block bootstrap at the frozen 6-month mean block. Alpha, its HAC standard
error and MDE₈₀ are in percentage points per year. **Shrunk** is the posterior mean
under the fixed Fama–French (2010) prior with each fund's own shrinkage factor in
brackets. **Shortfall** is positive when the product lost more to its cheap
replication than its fee premium explains, and it carries no interval (§7). Ordered
by net assets at the frame date, which selects nothing.

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

Two readings of the table that the sorted columns hide.

**Four "growth" products delivered a positive HML loading.** IJK, IJT, SLYG and
MDYG — the S&P MidCap 400 Growth and SmallCap 600 Growth indexes under two sponsors
— have sign-adjusted loadings of −0.067, meaning a raw HML loading of **+0.067**.
They are graded against the short leg of value and they tilted, weakly, to value.
That is an exposure-delivery failure and it is what clause (a) exists to catch.

**Rolling loadings are stable almost everywhere.** Thirty-seven 36-month windows per
fund. Only three funds change the sign of their rolling intended loading at all:
RPG twelve times over a range of 0.39, VOT twice, FTC once. TILT's rolling loading
moves over a range of 0.058 across six years, the tightest on the shelf; RPG's is
the widest.

---

## 4. Statistical alpha versus implementation value

These are two different questions with two different answers, and the specification
forbids collapsing them. **A fund can be worth owning with zero alpha if it delivers
a wanted exposure cheaply; a positive alpha over a short history is not evidence of
skill.** Four cases on this page make the distinction concrete.

**VUG — positive alpha, no implementation finding.** Shrunk alpha **+1.23 pp/yr**,
the second largest on the page, and a shortfall of **−4.19 pp/yr**, meaning it beat
its cheap replication by 4.19 pp/yr. Both numbers are the same fact and neither is
skill. Because a fund is never part of the basis that replicates it, VUG's
replication degenerates to **VTI at weight 1.000**, so its "shortfall" is the
realised excess return of large-cap growth over the total market from 2020 to 2025.
Its `exploratory` status rests on delivering a −0.284 HML loading stably, which it
did. **Statistical conclusion: none. Implementation conclusion: VUG delivered its
intended exposure at 3 bp.**

**TILT — the only genuinely powered alpha on the page, and it is negative.** HAC
standard error **0.38 pp/yr** against a median of 1.44, minimum detectable alpha
**1.08 pp/yr** against a median of 4.02, shrinkage factor **0.913** — the estimate
is barely shrunk because it barely needs to be. Raw alpha **−0.95 pp/yr** on a
0.25% expense ratio, and it *beat* its cheap replication by 1.21 pp/yr. It is
`rejected` anyway, on clause (a): its HML loading is **+0.148** against a threshold
of 0.15, a miss of 0.002, on a bootstrap interval `[+0.113, +0.171]` that contains
the threshold. **Statistical conclusion: a small negative residual, and it is the
one alpha here that the window could actually see. Implementation conclusion: a
market-tilt product that does what it says, too weakly to clear a threshold set
before anyone looked.**

**IJH and SPMD — the same index, and the cleanest implementation finding here.**
Both track the S&P MidCap 400; loadings +0.480 and +0.481; alphas −3.47 both;
shortfalls −0.28 and −0.24; expense ratios 0.05% and 0.03%. Two sponsors,
indistinguishable delivery, and the audit separates them by three basis points.
**Statistical conclusion: none — a −3.47 pp/yr alpha against a 4.05 pp/yr detection
threshold is an unmeasured quantity. Implementation conclusion: mid-cap exposure is
available at 3 bp with no measurable shortfall.**

**EZM, FTA and JHMM — expensive and still ahead of their replication.** Net expense
ratios of 0.38%, 0.58% and 0.41%, the three dearest funds that were not rejected,
with shortfalls of −1.06, −0.33 and −0.11 pp/yr. **A fee comparison is not a cost
comparison**, and this is the direction that is usually forgotten: the cheap fund
can lose more to a replication than the expensive one.

The reverse case is more common. **27 of 44 products have a positive shortfall and
22 exceed the 0.50 pp/yr clause,** while the largest fee premium any product carries
over its own replicating basis is **0.55 pp/yr** and the median is far below that.
The biggest shortfalls — VB +2.89, VBK +2.84, VOT +2.60, VTV +2.57, RPG +2.50 — are
five to a hundred times any fee difference in the table. **Whatever separates these
products from cheap broad funds over this window, it is not the expense ratio.**

---

## 5. The frozen falsifier, and why a *t*-statistic is not part of it

Verbatim from the specification, frozen before any return was read:

> A fund is rejected as an implementation candidate when ANY of: (a) the point
> estimate of its loading on its intended factor is below 0.15 over the common
> period; (b) the intended loading's sign flips between the first and second half of
> the fund's common-period history; (c) its tracking difference versus a cheap
> broad-market fund plus the same combination of broad funds that approximates its
> exposures is worse than its stated expense ratio advantage by more than 0.50
> percentage points per year; or (d) its total realised cost of ownership, including
> expense ratio, tracking difference and realised taxable distributions, exceeds the
> materiality threshold of 1.0 percentage point per year above the broad-market
> comparator without a corresponding exposure. **A t-statistic on residual alpha
> below 2 is NOT a falsifier: it usually means the sample cannot identify a small
> residual return, not that the fund is useless.**

Every clause is about exposure or cost. None is about a residual return, and the
reason is arithmetic rather than taste: **the median minimum detectable alpha across
the 132 fund-by-specification tests is 4.52 pp/yr**, and only 8 of the 44 primary
alphas exceed their own detection threshold.

A *t*-rule would not even be conservative here, which is the point people miss.
**26 of the 44 primary alphas already have |*t*| ≥ 2, and 24 of those 26 are
negative** — the two positives are IWF and IWY, both large-cap growth. Reading a
*t*-statistic as the verdict would therefore not "kill the retail factor shelf" for
being unmeasurable; it would convict most of it of a large negative residual that a
72-month window cannot separate from model misfit. The detection threshold is the
honest bar, and at 80% power it corresponds to |*t*| > 2.80, which 8 funds clear.

Three boundary cases decide how the statuses read.

- **`unresolved` is a statement about the interval, `rejected` about the point
  estimate.** Clause (a) fires on the point estimate; the `unresolved` rule applies
  when no clause fires and the 95% interval *contains* 0.15. So TILT at +0.148 with
  interval `[+0.113, +0.171]` is `rejected`, while IVW at +0.224 with interval
  `[+0.141, +0.328]` is `unresolved` — both intervals contain the threshold, and the
  point estimate breaks the tie in opposite directions. Applied exactly as frozen,
  and reported here because it is the least robust classification on the page.
- **Clause (b) fired once,** on FTC: +0.077 in the first half, −0.060 in the second.
  Its 95% interval `[−0.069, +0.166]` contains zero, so this is a sign flip in a
  loading that cannot be distinguished from no loading at all.
- **Clause (d) never fired alone.** All eight (d) firings are on funds that had
  already fired (a) and (c), because (d) requires a missing exposure by
  construction. It changes no status; it quantifies the cost of the ones already
  rejected: VBK 2.91, RPG 3.17, VOT 2.67, IWO 2.06, IJK 1.85, MDYG 1.84, IJT 1.72,
  SLYG 1.62 pp/yr.

The 5 `unresolved` funds are IVW, IUSG, SPYG (all large-cap growth, all graded on a
negative HML loading of about 0.21–0.22), SPHQ (quality, RMW +0.176) and JHMM
(multifactor, HML +0.212). In every case the interval straddles 0.15 and 72 months
cannot say more.

---

## 6. The multiple-testing family

**The family is 44 funds × 3 specifications = 132 alpha tests**, not the funds or
the specification anyone chose to report. CAPM, FF3 and FF5+UMD are all estimated
for all 44 funds and all 132 *p*-values enter the correction, because a loading or a
residual that appears in one specification and not the others is not a finding.

| Correction | Rejections of 132 |
| --- | ---: |
| Uncorrected at 0.05 | 56 |
| Uncorrected at 0.10 | 65 |
| **Benjamini–Hochberg at 0.10** | **54** |
| **Holm–Bonferroni** | **5** |
| BH, family padded to every mandate-matching series × 3 = 6 315 | 2 |
| Holm, same padded family | 0 |

Four things this table says.

**BH at 0.10 is barely different from no correction at all here** — 54 against 56 at
an uncorrected 0.05 — because the *p*-value distribution is dominated by a mass of
genuinely small values. Of the 54 survivors, **50 are negative alphas and 4 are
positive**; they span 26 distinct tickers and 26 FF5+UMD, 24 FF3 and 4 CAPM fits.

**Benjamini–Hochberg assumes independence and this family has almost none.** Three
nested specifications per fund, the same six factors, the same 72 months, and eight
pairs of funds tracking an identical index. The specification's own note says so:
"the Benjamini-Hochberg count is an OPTIMISTIC bound and Holm is the defensible
one." **Holm, valid under arbitrary dependence, leaves five tests: IJR and SPSM
(FF5+UMD), IWS (FF3 and FF5+UMD) and IWD (FF5+UMD) — every one a negative alpha, and
IJR and SPSM are the same index, so five tests are three products.**

**The declared hostile denominator collapses it further.** Padding the family to
every mandate-matching series screened, at *p* = 1.0 for the 6 183 that were never
regressed, leaves **2 BH rejections and 0 Holm rejections**. Padding with *p* = 1
cannot create a rejection and strictly tightens both corrections, so this is the
most pessimistic honest denominator, and the two survivors are IJR and SPSM — the
S&P SmallCap 600, twice.

**Exposure is the family that survives.** The intended-loading tests are a separate
44-member family: 37 reject uncorrected and **38 survive Benjamini–Hochberg**. That
asymmetry — 38 of 44 loadings, against 5 of 132 alphas under a defensible correction
— is the whole result of this experiment in two numbers.

One naming hazard: the artifact's `estimates` list also has 132 entries, being three
reported numbers for each of the 44 funds. It is a coincidence of arithmetic and not
the same 132.

---

## 7. Shrinkage, and the annualisation trap

Every alpha is shrunk before it means anything. Taking true gross alpha as normal
with mean zero and cross-sectional standard deviation `sigma_true = 1.25%/yr`
([Fama and French 2010](https://doi.org/10.1111/j.1540-6261.2010.01598.x)), the
posterior mean is

```
shrunk = observed × sigma_true² / (sigma_true² + SE²)
```

with **each fund's own HAC standard error**, never the framework's reference factor
of 0.121. That reference is the factor at the reference standard error of 3.36%/yr;
reusing it would be wrong for every fund on this page in both directions. The
realised factors run from **0.162** (RPG, SE 2.84) to **0.913** (TILT, SE 0.38),
median **0.431**.

**The trap: an annual alpha is twelve times a monthly intercept, so its standard
error annualises by ×12 and never by ×√12.** Both the intercept and its standard
error are scaled by `MONTHS_PER_YEAR = 12` in the code. Using √12 would divide every
standard error by 3.46 and shrink far too little. The arithmetic, on this page's own
numbers:

| Fund | Raw alpha | HAC SE ×12 | Factor | Shrunk | SE if ×√12 | Factor | Shrunk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| VO | −3.78 | 1.59 | 0.381 | **−1.44** | 0.46 | 0.881 | −3.33 |
| RPG | −4.99 | 2.84 | 0.162 | **−0.81** | 0.82 | 0.699 | −3.49 |
| IJR | −2.99 | 0.71 | 0.755 | **−2.26** | 0.21 | 0.974 | −2.91 |
| TILT | −0.95 | 0.38 | 0.913 | **−0.86** | 0.11 | 0.992 | −0.94 |

The right-hand block is arithmetic, not a result: it is what this page would print
if the error were made. On RPG the mistake would quadruple the reported posterior.
Note also that the mistake matters least exactly where it matters least anyway — on
TILT, whose estimate is precise enough that the prior barely moves it.

**The shrunk alpha carries no interval, by construction.** A posterior mean under a
fixed prior is not a sampling estimate and has no sampling distribution of its own.
The raw alpha, its HAC standard error and the minimum detectable alpha are printed
beside every shrunk figure, and the shrunk figure must never be quoted alone.

---

## 8. The cheap replication, and why its shortfall has no interval

The secondary comparator is a combination of **VTI, VUG, VTV and VB** with
non-negative weights summing to one, fitted by constrained least squares on the
**same 72 months** as the exposure regression. That is deliberate and it is stated
as what it is: **an investor could not have known those weights in advance, so the
comparison is a best case for the replication and therefore a hard test for the
product.** A sampling interval around a look-ahead quantity would imply a precision
the construction does not have, so none is reported for any shortfall on this page.

Two structural facts a reader needs before using clause (c).

**Three of the four building blocks are themselves audited products, and a fund is
never in its own basis.** So the replication degenerates for exactly those three.
VUG is replicated by VTI at weight 1.000, tracking error 7.36 pp/yr. VB is
replicated by 0.733 VTI + 0.267 VTV, tracking error 8.31. VTV by 0.784 VTI + 0.216
VB, tracking error 7.48. For these three the "implementation shortfall" is the
realised style return of 2020–2025, not an implementation cost, and VB's and VTV's
rejections should be read as "small-cap and value underperformed the market over
these 72 months" — which is a return finding this page is not entitled to make.

**Tracking error against the combination ranges from 1.38 pp/yr (TILT) to 8.65
(MTUM), median about 5.** Clause (c)'s threshold is 0.50 pp/yr. A difference of
means with that much dispersion over 72 months is not resolvable at 0.50 pp/yr, and
the quantity carries no interval by design. **Clause (c) is a decision rule applied
as frozen, not a measurement**, and 22 of the 24 rejections rest on it.

---

## 9. Attrition, survivorship, and a defect in the attrition number

The frame is taken at the **start** of the window, not the end, precisely so that
attrition is measurable rather than invisible. Screening the 2025Q4 census would
select on survival: a fund that liquidated in 2022 would simply be absent.

| Quantity | As reported in the artifact | Recomputed from the committed screen list |
| --- | ---: | ---: |
| Mandate-qualifying series in the 2019Q4 frame | 1 513 | 1 513 |
| Mandate-qualifying series in the 2025Q4 frame | 1 906 | — |
| Present in frame, absent at follow-up | **358 (23.66%)** | **312 (20.62%)** |
| Frame-date net assets of that set | **333.5 bn USD** | **138.7 bn USD** |
| Absent from frame, present at follow-up | 751 | — |

**The two columns disagree because the reported figure counts renames as deaths.**
The "disappeared" set is a difference of two sets that are each built by running the
mandate and exclusion patterns over that census's *own* series names, so a series
that renamed out of the mandate pattern, or into the exclusion pattern, between 2019
and 2025 is counted as gone even though it is still filing. The committed file
contradicts itself on this: **four of its own fifteen largest "disappeared" series
are recorded elsewhere in the same file as still filing at the follow-up quarter,
with net assets** — EuroPacific Growth Fund (136.3 bn at follow-up), T. Rowe Price
New America Growth (17.3 bn), Spectrum Growth (4.4 bn) and AST T. Rowe Price Growth
Opportunities (2.6 bn). Counting only series absent from the 2025Q4 census
altogether gives 312 and 138.7 bn. **The 46-series difference carries 194.8 bn, 58%
of the headline asset figure, and one fund is most of it.** The same error runs in
reverse through the 751 "launched" count, which will include renames.

**The direction of the finding is unchanged and the caveat still holds.** Even at
20.6%, a fifth of the 2019 factor shelf is gone in six years, and this is a **lower
bound** on survivorship contamination: public N-PORT filings begin in 2019, so any
fund that closed before 2019Q4 is invisible to both censuses. A universe assembled
from today's listings would contain the 751 and none of the 312. Four of the 1 513
carry a final-filing flag. None of the 44 audited funds is absent at follow-up,
which is true by construction: 72 months of filed returns were required.

---

## 10. Hostile tests: what ran, what did not, and one that is wrong

Eight were declared. Their status:

| Declared test | Status |
| --- | --- |
| Re-estimate under CAPM, FF3 and FF5+UMD and report all three | **Run.** 132 fits; the correction consumes all of them. |
| Re-estimate on fixed calendar halves and rolling 36-month windows | **Run.** 37 windows per fund; only RPG, VOT and FTC change sign at all. |
| Substitute DGS3MO and DFF for TB3MS and show the effect | **Run, and the printed number is wrong.** See below. |
| Include every screened fund and specification in the denominator | **Run.** 6 315-member padded family: 2 BH, 0 Holm. |
| Compare against a fitted combination of cheap broad funds, and state the look-ahead | **Run**, with the look-ahead stated. §8. |
| Cross-check every N-PORT return against an independent source | **Did not run at all.** |
| Report MDE₈₀ beside every alpha | **Run.** |
| Measure attrition between the two censuses | **Run**, with the defect in §9. |

**The cross-source check produced nothing.** All 44 tickers are in the artifact's
`unavailable` list with `HTTPError` and the `compared` list is empty — the Yahoo
chart endpoint refused every request, which is exactly the behaviour
[Decision 0002](../decisions/0002-no-research-grade-free-price-source.md) recorded.
**Form N-PORT Item B.5 is therefore the sole measurement of every return on this
page, with no independent corroboration of any kind.** The specification's stated
reason for having a secondary source — "two independent measurements of the same
quantity make a silent adjustment error visible" — is unmet. The run's own summary
does not say this; it is visible only in the diagnostics.

**The cash-rate sensitivity diagnostic has a unit error.** It reports the French
one-month bill at **2.665** (percent per year) beside TB3MS at **0.02755**, DGS3MO
at **0.02860** and DFF at **0.02753** — which are *decimals* per year, because the
FRED reader converts published percent to decimal with `value / 100`. The reported
"alpha shift" of about **2.637 pp/yr** for each alternative is a percent minus a
decimal. On a like-for-like basis the shifts are **−0.09, −0.20 and −0.09 pp/yr**.
No result on this page depends on it: the diagnostic is consumed nowhere, and a
constant shift in the dependent variable moves only the intercept, so every loading
is invariant by construction. But as printed it asserts that the cash-series choice
moves every alpha by 2.6 pp/yr, which would be the largest single quantity in the
audit and is not true. The corrected figures support the specification's claim that
the choice did not make the answer; the printed ones would refute it.

**One diagnostic the committed code produces and this artifact does not have.** The
code at commit `d22cb607` computes a *model-misfit pedestal*: the alpha the factor
model assigns to VTI, a fund that by construction *is* the market and whose alpha
under a correctly specified model should be about minus its three-basis-point fee.
Every fund on this page carries whatever that number is, because every fund is
priced by the same six factors over the same 72 months. **It is absent from this
artifact,** which was produced from an earlier working tree (`git_commit c486a054`
with `diff_sha256 260f8b22…`). Two consequences: re-running the committed code will
not reproduce this `result.json` exactly, and the single most useful calibration for
the alpha column is missing from the evidence. VTI's beta (0.9968) and R² (0.99852)
are in the validation gate; its alpha is not recorded anywhere.

**Amendments are counted but their content is not.** 15 of the 1 205 filings are
`NPORT-P/A` amendments, across 11 funds (IWR, QUAL, IWP, IWN, MTUM, IWO, IJK, IJJ,
IJT, VLUE, FTA). Where two filings report the same month the later filing date wins
and the reader raises a warning rather than averaging. Which months disagreed, and
by how much, is not in the artifact.

---

## 11. Verified facts, assumptions, open questions

### Verified

- The screen was frozen, mechanical and applied **before any return was
  downloaded**; returns were never fetched for a fund that failed it, so no screen
  decision could be revised after seeing performance. Every one of the 2 105
  mandate-matching series is committed with its outcome and the first criterion it
  failed.
- The Item B.5 month alignment is **checked, not assumed**: VTI reconstructed from
  its own filings correlates 0.99926 with the French market total return, betas
  0.9968 on `Mkt-RF` with R² 0.99852, and its worst month is 2020-03 at −13.80%.
- All 44 funds have 72 of 72 months with no gap, no interpolation and no fetch
  failure.
- The expense ratio is **not** subtracted twice. Item B.5 is the fund's own total
  return, already net of fees and already assuming reinvested distributions.
- Every excess return is taken over the one-month bill distributed in the same
  French file as the factors, which is the rate `Mkt-RF` is defined against, so the
  intercept is interpretable as alpha.
- Both French files are pinned by the sha256 of their raw bytes; a new vintage
  aborts the run rather than reporting numbers.
- The HML/RMW volatility band inherited from the
  [Phase 1 gate](fama-french-reproduction.md) does **not** propagate here. Every
  figure on this page is a loading, a mean or a difference of means, and nothing
  divides by those volatilities.

### Assumptions

- **`sigma_true = 1.25%/yr` is transferred, not measured.** It comes from Fama and
  French's bootstrap of US active equity mutual funds over 1984–2006. It is applied
  here to index-tracking ETFs over 2020–2025, and it decides every shrunk number on
  the page. A different prior gives different posteriors and the same raw alphas.
- **The intended-factor map is a declaration.** Growth graded on negative HML,
  size-and-style graded on its style leg, multifactor graded on HML because every
  multifactor product in this universe names value first in its own objective. All
  written into the specification before any regression, so no fund could be graded
  against whichever loading turned out largest.
- **The thresholds are a priori and none is tuned**: loading 0.15, materiality
  1.0 pp/yr, shortfall 0.50 pp/yr, HAC 6 lags, bootstrap mean block 6 months. The
  predeclared 3- and 12-month neighbour blocks are named in the specification but
  their intervals are not in the artifact, so the block-length sensitivity is
  **unreported**, not zero.
- **Benjamini–Hochberg treats the 132 tests as independent.** They are not, and the
  BH count is stated in the artifact itself as an optimistic bound.
- **Every figure is PRETAX**, and no tax haircut is applied to any return anywhere.

### Open questions

1. **What is VTI's own alpha under this model over this window?** The cheapest
   evidence that would change how the alpha column is read, and it is not in the
   artifact. Until it exists, "positive alpha" here cannot be distinguished from
   "the model does not span 2020–2025".
2. **Does any N-PORT return agree with an independent measurement?** Unanswered; the
   cross-check failed for all 44 funds.
3. **What do realised taxable distributions and turnover do to the cost ranking?**
   Neither is in Form N-PORT. Both live in the annual report on Form N-CSR as
   unstructured HTML, and both are recorded as **gaps** rather than estimated.
   Clause (d) is therefore evaluated without the distribution term the falsifier
   names.
4. **Would an out-of-sample replication change clause (c)?** Weights fitted on a
   prior window would remove the look-ahead and would be a fairer test in one
   direction and a harder one in another. Not run, and not runnable on 72 months
   without shortening the estimation window further.
5. **What did the 15 amendments change?**

---

## 12. What this does not establish

- **Not skill, in any direction.** Six positive shrunk alphas, all large-cap growth,
  none exceeding its own detection threshold. A positive alpha over a short
  inception history is not evidence of future manager skill, and this window is
  short by any standard.
- **Not investable cost.** Bid-ask spreads, brokerage, taxes, realised distributions
  and portfolio turnover are all absent. Nothing here is a net-of-everything return
  to a shareholder.
- **Not a survivorship-free universe.** N-PORT begins in 2019; a fund that closed
  before 2019Q4 is invisible to both censuses. The measured attrition is a lower
  bound and the true rate is higher.
- **Not audited data.** Item B.5 returns are fund-reported and unaudited, and Form
  N-PORT General Instruction G permits each filer to use its own internal
  methodology, so two funds' returns are not guaranteed to be computed identically.
  With the cross-source check dead, that assumption is untested.
- **Not the whole shelf.** Exchange-traded only, at least 1 bn USD in 2019, at most
  0.60% net expense ratio, inception on or before 2016-12-31. The 1 374 series
  removed for having no listed share class include every large active mutual fund in
  the frame.
- **Not a return finding.** Where a product's shortfall is really the realised style
  return of 2020–2025 (§8), this page is measuring the window, not the product.

**The binding constraint is the data contract and the length of the window, not the
evidence.** Seventy-two months of unaudited, self-reported, per-filer-methodology
returns from a source that begins after the deaths that matter most is what limits
every conclusion here. Decision 0002 is not overturned by having found a better
source than a price feed; Form N-PORT is a stronger contract than any price feed
tested and is still not enough to promote anything.

---

## 13. How this composes with Experiment 001

[Experiment 001](factor-persistence.md) left HML, UMD and RMW `unresolved` and CMA
`rejected`. **No factor reached `exploratory`, so no premium is established for any
exposure audited here.** The two experiments answer different halves of one product
and they multiply rather than add: what a shareholder receives is
`premium × delivered loading − cost`. Experiment 001 could not sign the first term
for any factor. This page measures the second and finds it delivered. The third is
positive — a cost, not a credit — for 27 of 44 products against a look-ahead
replication.

**A product audit cannot rescue an exposure whose premium is not established.** Two
instances make that concrete.

- **Sixteen of the 44 funds are graded on a *negative* HML loading, and three of
  them reached `exploratory`** (VUG, IWF, IWY). "Delivering the intended exposure"
  there means reliably holding the *short* leg of a premium whose post-publication
  estimate in Experiment 001 is +1.57 pp/yr on a 90% interval of `[−2.28, +5.54]` —
  unresolved in sign. A product that manufactures the short leg of an unresolved
  premium precisely and cheaply is not a candidate for anything; it is a well-made
  bet on a coin whose bias nobody has measured.
- **The two factors Experiment 001 singled out have almost no shelf.** RMW was
  prioritised there on the narrow grounds that it alone did not decay (96%
  retained); its entire investable shelf here is two funds, QUAL (`rejected` on
  clause (c)) and SPHQ (`unresolved`). UMD was ruled out there as a standalone
  sleeve on cost; its entire shelf here is MTUM, which **does** deliver its exposure
  — UMD loading +0.444, `[+0.277, +0.562]` — and is `rejected` on clause (c) after
  losing 1.22 pp/yr to a three-fund combination with a 0.12 pp/yr fee premium. That
  is the cost result Experiment 001 predicted, showing up in a product.

The one place the two experiments are consistent and quiet: Experiment 001's
HML/RMW volatility band was flagged as something Experiment 002 must carry. It does
not apply, because nothing here divides by a factor volatility.

---

## Consequence for this repository

1. **Nothing is promoted, and Decision 0002 is not the only reason.** Even with a
   licensed source, no product on this page would qualify: the exposures that are
   cleanly delivered belong to factors with no established premium, the alpha column
   is unmeasurable, and the cost comparison that rejected 22 products is decided by
   a look-ahead comparator. The 15 `exploratory` products may be used as
   implementation proxies in a later experiment and for nothing else.
2. **Exactly what would change that.** A licensed, point-in-time, survivorship-free
   total-return source with a documented corporate-action and delisting contract —
   Decision 0002's deferred alternative — covering the listed shelf from at least
   2003, so the window is **240 months rather than 72**. Re-freeze the specification
   against it and run **confirmatory**, not exploratory. Promotion then requires all
   of: intended loading at or above 0.15 with a 95% interval excluding 0.15 from
   below; the same on both fixed halves; shortfall at or below **0 pp/yr** against a
   replication whose weights are fitted on a **prior** window rather than the test
   window; total cost of ownership including realised distributions and turnover at
   or below **1.0 pp/yr**; and the underlying factor at `exploratory` or better in
   Experiment 001, which no factor currently is. **A residual alpha of any sign or
   size remains inadmissible as a promotion criterion.**
3. **The cheapest step that would improve *this* page rather than the next one is
   the model-misfit pedestal.** Publishing VTI's own alpha under CAPM, FF3 and
   FF5+UMD over the same 72 months would tell a reader whether the six positive
   alphas are anything at all. The committed code already computes it; this artifact
   predates it.
4. **The edge budget's fund-cost line survives, with an addition.**
   [Expected edge decomposition](expected-edge-decomposition.md) books fund cost
   reduction at 49 bp/yr central against an investor's own counterfactual, which is
   a statement about replacing an expensive fund with a cheap one and is untouched
   here — the 44 audited funds have a median net expense ratio of 0.15%. What this
   page adds is the quantity that line does not carry: **for most of this shelf the
   gap to a cheap replication is larger than the fee.** 22 of 44 products lost more
   than 0.50 pp/yr to a four-fund combination whose fee premium over them was at
   most 0.32 pp/yr and typically 0.12, and the five largest shortfalls are 2.5 to
   2.9 pp/yr — against a look-ahead comparator, so a best case for it. A fee
   comparison is not a cost comparison, and any tool that shows an expense ratio as
   the cost of owning a factor fund would be understating it by an order of
   magnitude on this evidence.
5. **Three defects to fix before this family is run again**, none of which changes a
   status: the cash-rate sensitivity unit error (§10), the attrition rename count
   (§9), and the degenerate replication for the three basis funds that are
   themselves audited (§8). The dangling run `f02d06f7ab1648f88d157a740f8499f3` has
   no terminal ledger entry and should get one.
6. **The listed factor shelf is thinner than it looks.** After a mechanical screen,
   44 products, of which 16 are eight indices sold twice, one is the entire momentum
   shelf, and two each are quality and multifactor. Any later work that needs a
   momentum or quality proxy has a single candidate and no fallback.

## Reproduce it

```sh
cd research
uv run python -m portfolio_edge.experiments.exp_002_fund_exposure --build-universe
uv run python -m portfolio_edge.experiments.exp_002_fund_exposure --view-results
uv run pytest tests/unit/test_experiments_exp_002_fund_exposure.py
uv run pytest tests/unit/test_exp_002_universe_committed.py
```

The run, its git commit, working-tree diff hash, dataset-manifest hashes, artifact
hashes and the `results_viewed` event are in
[`research/ledger.jsonl`](../../research/ledger.jsonl). Artifacts are under
`research/artifacts/e95932d2236d48668a566a9a9c079b8f/`: `result.json`
(sha256 `d13ee330937c14b5…`), `summary.md`, and five parquet frames — `screen`
(all 2 105 screened series), `coverage`, `exposures`, `outcomes` and `replication`.
**The committed code produces one diagnostic this artifact does not contain (§10),
so a re-run will not be byte-identical.** Retrieval dates for every source:
**2026-08-12**. Seed 20260812.
