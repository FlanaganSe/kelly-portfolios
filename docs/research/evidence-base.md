# The evidence base: what this repository can measure, and what it cannot

**Question.** What sources of truth does this repository actually hold, what can each
one resolve, and what is foreclosed until something is acquired?

**Decision it informs.** What a new experiment may be commissioned to ask. A question
whose answer sits below the measured resolution of every instrument here should not be
asked again until the instrument changes — that is the mistake
[decision 0005](../decisions/0005-factor-premia-closed-on-public-data.md) exists to stop
repeating.

**Out of scope.** Whether any return source is real
([framework](portfolio-edge-research-framework.md)); what to hold
([recommendation](portfolio-recommendation.md)).

`as of 2026-08-17`. Every hash below is pinned in a committed manifest under
`research/data-manifests/`, and every experiment aborts rather than reporting numbers
if a hash moves.

---

## 1. The resolution table — read this before proposing an experiment

For each question the repository has asked, the smallest effect its instrument could
detect at 80% power, against the effect size that would matter. **Where the floor
exceeds the bar, a null result carries almost no information.**

| Question | Instrument | Measured floor (MDE₈₀) | Bar that matters | Can it answer? |
| --- | --- | ---: | ---: | --- |
| Closed-form identities (Kelly, `gamma_star`, ERC, costs) | none — algebra | machine precision | — | **yes** |
| Reproducing a published factor table | French file vs printed table | ±0.005 pp/mo rounding | first moments | **yes**, first moments only |
| US post-publication factor premium | 384 months, one region | 5.0 pp/yr (HML) | 2.0 pp/yr | **no**, by ~2.5× |
| Same, pooled over three regions | + 2 regional files | **2.62** best of twelve cells | 2.0 pp/yr | **no**, narrowly and measured |
| Same, momentum pooled | 3 regional momentum files | **4.98**, the worst here | 2.0 pp/yr | **no**, by ~2.5× |
| Long-only capture fraction | 6 sorted portfolios, 750 mo | interval width ≈ 0.29 | a factor of 2 | **yes**, once a benchmark is named |
| Size premium | quintile/decile sorts, 750 mo | 4.7 pp/yr | 2.0 pp/yr | **no** |
| Fund **factor loading** | N-PORT, 46–78 months | interval half-width ≈ 0.10 | 0.15 loading | **yes** |
| Fund **alpha**, US factor shelf | N-PORT, 72 months | median **4.52** pp/yr | ≈1.25 pp/yr true dispersion | **no**, by ~3.6× |
| Fund alpha, ex-US shelf | N-PORT, 27–78 months | median 3.23 pp/yr | ≈1.25 pp/yr | **no** |
| Fund alpha, managed futures | N-PORT, 46–78 months | median **12.75** pp/yr | ≈1.25 pp/yr | **no**, by ~10× |
| Rebalancing policy difference | 420 months, 3 sleeves | — | 0.25 pp/yr | **yes** — the effect is large and negative |
| Marginal sleeve growth at 10% weight | 420 months | ≈0.58 pp/yr typical | 0.30 pp/yr | **no** — see [search coverage](search-coverage.md) |
| Crisis-conditional trend benefit | 53 crisis months | ≈4.4 effective observations | — | **no** |
| Financed 50% trend overlay, vendor leg | 485 months | 2.82 pp/yr | 0.30 pp/yr | gap +4.79, but the leg's decay exceeds its break-even |
| Same, **live fund leg** | N-PORT, 78 months | **4.76** pp/yr | 0.30 pp/yr | **no** — the window, not the series, now binds |
| **Vendor index against live funds** | 78 paired months, ρ = 0.72 | interval half-width ≈ 8.3 pp/yr | the 7.7 pp/yr bias bound | **yes, narrowly** — 7.7 is outside the interval |
| **BAB full-sample premium** | AQR US leg, 1,146 mo | 3.45 pp/yr | 2.0 pp/yr | **yes** — measured +7.77, `[+5.05, +10.48]` |
| Same, **post-2015 publication** | 137 mo | **5.86** pp/yr | 2.0 pp/yr | **no**, by ~2.9× |
| Short-term reversal, full sample | French, 1,205 mo | 3.20 pp/yr | 2.0 pp/yr | **yes** — +7.46 |
| Same, **post-1991 publication** | 426 mo | 4.39 pp/yr | 2.0 pp/yr | **no** — +1.71, well inside the floor |
| Accruals / net issuance, post-publication | 354 and 210 mo | 5.36 and 9.00 pp/yr | 2.0 pp/yr | **no**, by 2.7–4.5× |
| **Correlation among candidate engines** | 497 aligned months | SE ≈ 0.045 on ρ ≈ 0 | 0.3 for breadth | **yes** — this is the resolvable question |
| **Marginal gold sleeve at 10% weight, pro rata** | 618–658 months | **0.94–1.04 pp/yr** | 0.30 pp/yr | **no**, by ~3× — the measured effect is +0.04 to −0.42 |
| Same, **financed overlay** — the rule that matters | 618 months | **0.63–0.73 pp/yr** | 0.30 pp/yr | **no**, by ~2× — the measured effect is +0.18 to +0.22 and **the funding rule flips its sign** |
| **Gold added to a 30% trend overlay** | 605 joint months | **1.67–1.68 pp/yr** | 0.30 pp/yr | **no**, by ~5× — the measured increment is +0.09 to +0.10 |
| **Correlation between trend and gold** | 605 joint months | SE ≈ 0.041 on ρ ≈ 0.1 | 0.3 for breadth | **yes** — measured +0.072 to +0.141, so they are distinct engines |
| **Gold's correlation to equity, unconditional** | 658 months | SE ≈ 0.039 on ρ ≈ 0 | 0.3 for breadth | **yes** — measured −0.03 to +0.03 |
| **Gold's correlation to equity, inside drawdowns** | 294 crisis months | SE ≈ 0.058 on ρ ≈ 0 | **+0.20**, the falsifier in [capital efficiency](capital-efficiency-and-breadth.md) §5b | **yes** — measured −0.011 to +0.084; the bar sits 3.4 SEs above zero and 2.0 above the worst reading |

Three entries in that table are the whole shape of the programme's results. **Exposure is
measurable and alpha is not** — 38 of 44 US funds reject a zero intended loading under
Benjamini–Hochberg, while 5 of 132 alpha tests survive Holm and all five are negative.
**The public factor library has a floor above this repository's own materiality
threshold**, so a premium between zero and about 2.6 pp/yr is invisible in it however
the regions are pooled. And **a correlation is not a mean**: the same files that cannot
sign a post-publication premium resolve a correlation to two decimal places, which is
why the breadth question is answerable here and the return question is not.

### The model-misfit pedestals

Any alpha quoted here is a distance from these, never from zero. A cap-weighted market
fund *is* its region's market portfolio, so under a correctly specified model its alpha
should be about minus its fee.

| Region | Fund | Fee | FF5+UMD alpha | Window |
| --- | --- | ---: | ---: | --- |
| US | VTI | 0.03% | **−0.55 pp/yr** (HAC *t* = −3.41) | 2020-01…2025-12 |
| Developed ex-US | VEA | 0.03% | −0.31 pp/yr | 2019-07…2025-12 |
| Emerging | VWO | 0.06% | **+1.50 pp/yr** | 2019-07…2025-12 |

The emerging pedestal is the uncomfortable one: the standard six-factor model misprices
a cap-weighted emerging index fund by a percentage and a half a year, which is larger
than any alpha anyone would claim.

---

## 2. What is held

### Ken French data library — factors and sorted portfolios

Free, monthly, USD, gross, and **not investable**. The long-short files are
zero-net-investment academic spreads with no fee, spread, borrow, capacity or tax. Ken
French rebuilds the entire history from the current CRSP or Bloomberg vintage on every
release and **publishes no vintage archive**, so a sha256 identifies which file was used
and makes no point-in-time claim.

| File | Coverage | sha256 (prefix) | Second moment gated? |
| --- | --- | --- | --- |
| `F-F_Research_Data_5_Factors_2x3` | 1963-07…2026-06 | `cbc37248` | **`unresolved`** — HML −3.03%, RMW +5.09% |
| `F-F_Research_Data_Factors` (3-factor) | 1926-07…2026-06 | `cd6d8e0d` | no |
| `F-F_Momentum_Factor` | 1927-01…2026-06 | `f405ee2d` | **never gated** |
| `Developed_ex_US_5_Factors` | 1990-07…2026-06 | `54ffd319` | **never gated** |
| `Emerging_5_Factors` | 1989-07…2026-06 | `ea71c1f5` | **never gated** |
| `Developed_ex_US_Mom_Factor` | 1990-11…2026-06 | `ca8297c3` | **never gated** |
| `Emerging_MOM_Factor` | 1990-01…2026-06 | `5e684176` | **never gated** |
| `Developed_Mom_Factor` | 1990-11…2026-06 | `2bee31ed` | registered, **excluded** — includes the US |
| `6_Portfolios_2x3` | 1926-07…2026-06 | `06108313` | — |
| `25_Portfolios_5x5` | 1926-07…2026-06 | `43cfc360` | — |
| `6_Portfolios_ME_Prior_12_2` | 1927-01…2026-06 | `8c3ae277` | — |
| `Portfolios_Formed_on_ME` | 1926-07…2026-06 | `d731dea9` | — |
| `Developed_ex_US_6_Portfolios_ME_BE-ME` | 1990-07…2026-06 | `2b79a263` | — |
| `Emerging_Markets_6_Portfolios_ME_BE-ME` | 1989-07…2026-06 | `2b5fa424` | — |
| `F-F_ST_Reversal_Factor` | 1926-02…2026-06 | `dc40286c` | **never gated** |
| `F-F_LT_Reversal_Factor` | 1931-01…2026-06 | `48d8615e` | **never gated** |
| `Portfolios_Formed_on_NI` (net share issues) | 1963-07…2026-06 | `f9b9f25b` | — |
| `Portfolios_Formed_on_AC` (accruals) | 1963-07…2026-06 | `df8ec2d2` | — |
| `Portfolios_Formed_on_BETA` | 1963-07…2026-06 | `39ee17df` | — |

**The library publishes no long-short factor file for net issuance, accruals or prior
beta.** Only sorted legs exist, so any spread built from them is *this repository's*
construction and inherits no external replication. Two further traps in the new files:
`Portfolios_Formed_on_NI` carries `< 0` (net repurchasers) and `ZERO` buckets that sit
**outside** its quintile and decile splits, so `Lo 10` is not the buyback portfolio;
and the `F-F_LT_Reversal_Factor` preamble says "It contains a momentum factor" — Ken
French reused the momentum file's header text and the first line is simply wrong.

Three traps this library has already set here, each caught and each cheap to reset:

- **`Developed_5_Factors` includes the United States** at roughly half its weight
  (measured: 0.460 US + 0.549 developed-ex-US, summing to 1.009). Use the `ex_US` files
  in anything that also holds a US sleeve.
- **The five-factor `SMB` is not the three-factor `SMB`.** It averages size legs across
  three sorts and is not rebuildable from the six 2×3 portfolios; attempting it leaves a
  3.5 pp/month residual.
- **Emerging sorted portfolios are published under the prefix `Emerging_Markets_`**, not
  the `Emerging_` prefix the emerging *factor* files use. There is **no emerging
  small-value 5×5 corner in the library at all**.

**The Phase 1 systematic band.** Thirteen of fifteen gating cells reproduce Fama and
French (2015) Table 4; the standard deviations of HML and RMW do not, by variance ratios
of 0.940 and 1.104, against two independently typeset vintages
([Phase 1](fama-french-reproduction.md)). That is a vintage disagreement, not sampling
error: it does not shrink with more data and appears in no bootstrap interval. **Anything
that divides by an HML or RMW volatility carries ±3–5% systematically.** Five of the
series above carry no measured band at all, which is weaker than a band of zero.

### SEC filings — the only fund-level source held

| Source | What it gives | What it cannot give |
| --- | --- | --- |
| **N-PORT structured data sets**, 2019Q4 (8,563 series, `f8e10bce`) and 2025Q4 (12,552, `4ebb169e`) | The fund census, net assets, and Item B.5 **monthly total return per share class**, already net of fees and reinvested distributions | Anything before 2019. Audited figures — these are unaudited and General Instruction G lets each filer use its own methodology. Any independent corroboration: the cross-source check returned an HTTP error for **all 44 US and all 25 ex-US tickers** |
| **N-PORT Item B.6** | nothing usable | Distributions *reinvested in shares*. Identically zero across 321 ETF fund-months, because ETF distributions are paid in cash. **This field cannot measure distributions for an exchange-traded product** |
| **Form 497K summary prospectus** | Fee tables and SEC-standardised **after-tax returns**, read by hand with the accession committed | Anything at scale — unstructured, read per fund |
| **Form N-CSR** | Securities-lending income, capital-gain distributions from Financial Highlights, foreign taxes passed through | Anything at scale — unstructured HTML |
| **Form N-CEN**, acquired 2026-08-17. 110 filings, 25 core funds, 8 fiscal years (`data-manifests/core_beta_shelf/`) | The only **structured** fund-cost source held: Item C.3.b tracking difference against the fund's own index, Item C.6 securities lending, Item C.8 **recoupable** waiver flags — per series, per fiscal year, as XML | Treat as audited. Every figure is filer-reported: BlackRock filed the before- and after-expense tracking difference *identically* for eight funds; Item C.3.b never says which share class a multi-class fund answered for; and Schwab's Item C.8 recoupment flag contradicts its own prospectus |
| **N-PORT holdings** | Position-level holdings, **not yet used by any experiment** | — |

The 2019 start is the binding limitation and it selects on survival in the direction
that flatters: a fund that closed before 2019Q4 is invisible to both censuses, so every
attrition figure here is a **lower bound**. Measured, separating a death from a rename:
**312 of 1,513 US mandate-qualifying series (20.6%, $138.7bn)** and **88 of 322 ex-US
(27.3%, $19.5bn)** vanished between the censuses, against naive rates of 23.7% and 32.3%
that count renames as deaths.

**A second hole, found while building [Experiment 012](live-managed-futures.md) and worse
than the first for anything that follows funds through time: a fund that both launched
after 2019Q4 and closed before 2025Q4 appears in *neither* census, so a union frame drops
it entirely.** It removes funds from *inside* the window rather than before it. Closing it
needs the intermediate quarterly data sets, which no experiment reads yet, and it is the
cheapest single improvement available to this source.

**Item B.5 is more than an audit input: it is a usable live return series.** Experiment 012
assembles 46 managed-futures funds' monthly net total returns into an equal-weight index
over 78 months and finds **52% of the opening cohort stopped filing** inside the window —
again a lower bound. That is the only survivorship-bounded, net-of-fee, backfill-free return
series this repository holds for any strategy.

### FRED, AQR, and modelled series

| Source | Series | Status |
| --- | --- | --- |
| FRED | `TB3MS` (used as cash), `DGS3MO`, `DFF` (registered, not interchangeable) | measured |
| FRED | `GS10` → a **modelled** rolled par-bond total return | **modelled, `research_grade = False`** |
| FRED | `CPIAUCSL` | measured; ends two months before the equity series |
| AQR | `Time-Series-Momentum-Factors-Monthly.xlsx`, sheet `TSMOM Factors`, `33470930`, 1985-01…2026-05 | **vendor series, author-maintained, reconstructed on every update** |
| AQR | `Betting-Against-Beta-Equity-Factors-Monthly.xlsx`, sheet `BAB Factors`, `b0b1a214`, 1930-12…2026-05 | same flags, **and self-financing**: it borrows to lever the low-beta leg and states no financing rate |
| AQR | `Quality-Minus-Junk-Factors-Monthly.xlsx`, sheet `QMJ Factors`, `4eedd523`, 1957-07…2026-05 | same flags; **overlaps RMW at ρ = 0.72** and is not a separate engine from it |
| AQR | `Value-and-Momentum-Everywhere-Factors-Monthly.xlsx`, sheet `VME Factors`, `a2351d03`, 1972-01…2026-05 | same flags. **The asset-allocation legs stop at 2025-01, sixteen months before the file's last row, and their volatility falls from 13.1% to 4.2% after 2014** — a construction change, so nothing may be quoted from them |

Two warnings that have already cost time. **AQR ships its methodology as embedded
pictures** — the Definitions, Data Sources and Disclosures sheets carry 2, 1 and 0
substantive text cells; the reader recovers text from the EMF record stream, and what it
recovers documents a 60-day volatility centre of mass, a 40% per-position volatility
target and a 58-instrument universe, and **states no fee, transaction-cost, slippage or
financing basis anywhere**. And **the sheet name must be pinned as well as the hash**:
AQR changes URLs, workbook names and sheet names, and a manifest without a sheet is not
reproducible.

**There is no investable bond total-return history in this repository.** The `GS10`
proxy stands in for one everywhere a bond appears, and every bond figure inherits its
absence of on-the-run premium, bid/ask, tax and index roll rules.

### Gold — acquired 2026-08-17, and the first asset held outside equity and cash

Two samplings of one regulated benchmark. Adapters, unit tests and manifests are in
`research/src/portfolio_edge/data/{worldbank,lbma}.py`.

| Source | Coverage | sha256 (prefix) | Licence | What it is |
| --- | --- | --- | --- | --- |
| **World Bank Pink Sheet**, `Gold` ([landing page](https://www.worldbank.org/en/research/commodity-markets)) | monthly, 1960-01…2026-07, 799 rows | `7902a775` | **CC BY 4.0** | USD per troy ounce. The source's own definition: *"spot average of daily rates, from June 2025; previously (UK), 99.5% fine, **London afternoon fixing, average of daily rates**"* |
| **LBMA Gold Price PM** | daily, 1968-04-01…2026-08-14, 14,662 rows | `fa986c0a` | **licence required from IBA** | The month-end auction fix, USD/GBP/EUR. Administered by ICE Benchmark Administration, FCA-regulated under the UK Benchmarks Regulation |
| **LBMA Gold Price AM** | daily, 1968-01-02…2026-08-14, 14,814 rows | `a26883fb` | same | The 10:30 auction. **Never spliced with the PM series** |

**Why this is not a violation of [decision 0002](../decisions/0002-no-research-grade-free-price-source.md), and why it is still `exploratory`.** That decision's two named
failure modes are a silently dropped distribution and a mishandled corporate action.
Bullion has neither, so `total return = price return − carry cost` is *exact* and the only
free parameter is a carry cost the caller must state. What keeps it exploratory is
different and weaker: no vintage archive, an auction price that is not a retail execution,
and an assumed rather than measured carry. **The distinction matters because it is the
first time a price series has been admitted here at all**, and it was admitted on a
property of the asset rather than on a relaxed standard.

Four properties decide what may be quoted:

- **The Pink Sheet is a monthly AVERAGE of daily rates, not a month-end level** — the same
  trap Shiller's `P` carries. Averaging induces positive autocorrelation and understates
  volatility, so **a Sharpe ratio from it is biased upward**. Measured: AC(1) is **+0.274**
  on the average against **+0.053** on the month-end fix, and the two monthly return series
  correlate only **+0.673**. Every gold figure in this repository reports both and quotes
  the less favourable.
- **The LBMA data are licence-restricted and the restriction is enforced.** LBMA: *"A
  licence from IBA is required in order to obtain, use or redistribute real-time or
  historical benchmark data."* IBA: *"None of IBA's benchmark and other information may be
  used without a written licence from IBA."* In March 2025 IBA had the World Gold Council
  remove its historical LBMA series. **The bytes stay in the uncommitted cache and only
  hashes are manifested**, which is the treatment `fred.BAMLCC0A0CMTRIV` already gets from
  the same administrator. The Pink Sheet is primary precisely because it is redistributable.
- **There is no market price before 1971-08-15.** The dollar price was an administered peg;
  the par value was reset by PL 92-268 (86 Stat. 116) and PL 93-110 (87 Stat. 352), and
  **private US gold ownership was illegal until 1974-12-31** (PL 93-373, 88 Stat. 445).
  `lbma.BRETTON_WOODS_END` exists so a study cannot pick the cut-off by eye.
- **The Pink Sheet's URL is release-specific and a stale one serves a stale vintage with
  HTTP 200.** The path this repository first fetched was stamped January 2025 and is no
  longer linked from the landing page. The parser therefore compares the sheet's own
  `"Updated on ..."` stamp against the registry verbatim, and a network test fails on a
  mismatch. **This is the only source here where a wrong URL is silent rather than a 404.**

### Long-horizon and multi-country — acquired 2026-08-16

Three sources this page previously listed as *failed acquisitions*. None of them was
gone; all three had moved. Adapters, unit tests and manifests are in
`research/src/portfolio_edge/data/{macrohistory,shiller,goyal_welch}.py`.

| Source | Coverage | sha256 (prefix) | What it is |
| --- | --- | --- | --- |
| **Jordà–Schularick–Taylor Macrohistory, release R6** ([macrohistory.net/database](https://www.macrohistory.net/database/)) | annual, 1870–2020 | `c1bb91fe` | **Nominal, local-currency** total returns on equity, long-term government bonds, bills and housing, plus a consumer price index (1990 = 100). CC BY-NC-SA 4.0, citation required |
| **Shiller `ie_data`** ([shillerdata.com](https://shillerdata.com/)) | monthly, 1871-01–2026-08 | `71c3636d` | US S&P price, dividend, earnings, CPI, GS10, CAPE, TR CAPE, excess CAPE yield, and a real total-return index |
| **Goyal–Welch `PredictorData2025`** ([Amit Goyal's page](https://sites.google.com/view/agoyal145)) | monthly/quarterly/annual, 1871–2025 | `1e4b6527` | The Welch and Goyal (2008) predictor set, annually updated |
| **Goyal–Welch–Zafirov `Data2025`**, same page | monthly/quarterly/annual, 1871–2025 | `bbd61678` | The 56-predictor extension behind Goyal, Welch and Zafirov (2024) |

**The panel is 16 countries, not the 18 the landing page advertises.** Canada and Ireland
appear in JST for their macro series only and carry no equity, bond, bill or housing
return at all.

Four properties decide what may be quoted from these, and each is attached to the
manifests as a warning rather than left in prose:

- **JST is annual and nominal.** A drawdown from it cannot see an intra-year peak or
  trough, so it is a **lower bound**, and it is not comparable with a monthly figure.
  Real returns require deflating by the `cpi` table — `macrohistory.real_total_return`
  is where that is written down.
- **Exchange closures are filled, and the source says which.** `eq_tr_interp = 1` marks
  Portugal 1975–1977 (Carnation Revolution) and Spain 1937–1940 (Civil War). Portugal's
  published `eq_tr` is *literally the same number* in 1975 and 1976. Japan's 1946–1947
  are simply **absent** ("stock exchange closed; no data") — and that hole sits inside
  the largest loss in the panel. Two one-year returns span more than a year: the
  Netherlands' 1945 covers August 1944 to April 1946, Switzerland's 1915 covers July 1914
  to July 1916.
- **Germany 1922–1923 is hyperinflation arithmetic**, not a realisable return: `eq_tr`
  1923 is 2.6e9 against consumer-price inflation of 1.06e9, and the 1948 currency reform
  then shows as a −88% nominal equity return.
- **Goyal–Welch carries seven columns the source itself marks as full-sample estimates**
  — `cay`, `pce`, `ogap`, `sntm`, `fbm`, `tchi`, `shtint` — written back over history.
  Predicting with any of them is look-ahead by construction, and **no hash or
  availability timestamp can catch it**: the file is honest and the column is not. The
  Google Drive endpoint also returns **no `Last-Modified` header**, so these are the only
  datasets here whose sole availability bound is the retrieval timestamp.

### Read by hand, dated, not automated

Vendor and statutory sources behind the cost, tax and structure work, each with its URL
and retrieval date recorded beside the claim it supports: Morningstar's 2026 fee study
and *Mind the Gap 2026*; ICI's expense trends; Vanguard's 2025 foreign tax credit
worksheet and published fund endpoints; the iShares tax supplement; MSCI index dividend
yields; a dealer republication of the MMD municipal curve; and the US Code, Treasury
Regulations and Revenue Rulings cited in
[structural and tax-aware edges](structural-and-tax-edges.md). These decay on a
timescale of months and carry review triggers rather than a promise of currency.

---

## 3. What was tried and does not work

Named so nobody re-spends the budget discovering it.

**No free price source is research-grade** — this is
[decision 0002](../decisions/0002-no-research-grade-free-price-source.md), and
reachability was never the real problem. Stooq returns a JavaScript proof-of-work
interstitial to `curl` and HTTP 404 to `requests` for the same URL; the Yahoo chart API
answers `curl` and returns HTTP 429 to `requests` under every header combination (the
difference is TLS fingerprinting, not headers); `yfinance` is the same source behind a
parser. None of them publishes a documented total-return contract, corporate-action
treatment, delisting coverage or revision history, which is what a product audit needs.
The adapters are kept rather than deleted because the refusal is the finding: the Stooq
adapter detects the interstitial and raises rather than parsing HTML into prices.

**That decision is scoped to its own reasoning, and gold falls outside it.** Its two named
failure modes are a dropped distribution and a mishandled corporate action; bullion has
neither, so a gold price plus a stated carry cost *is* a total return. See the gold section
above. **This is not a general licence to admit price feeds** — it turns on a property of
the asset that no fund, index or equity shares.


**A 404 is not evidence of absence.** Goyal–Welch and Shiller `ie_data` were both recorded
here as failed acquisitions on the strength of an HTTP 404. Neither dataset had gone
anywhere: Goyal–Welch moved to Google Drive and Shiller moved to `shillerdata.com`, and
both were landed on 2026-08-16 by re-reading the author's own page. The old Yale path for
`ie_data.xls` still answers, which is worse than a 404 — on 2026-08-16 it served a file
last modified in October 2023. **Re-read the publisher's landing page before recording a
source as gone, and check `Last-Modified` before trusting one that answers.**

**Other acquisitions that failed:**

| Target | Result |
| --- | --- |
| Ken French 2013–14 vintage of the 5-factor file | Does not exist publicly. It is the single observation that would settle the Phase 1 band, and it changes no conclusion anywhere |
| Dimson–Marsh–Staunton (Global Investment Returns Yearbook) | Not free and not chased. The underlying series are licensed through Morningstar; only summary tables are public |
| Barro–Ursúa macroeconomic data at `barro.scholars.harvard.edu` | HTTP 403 to every client tried on 2026-08-16. Recorded as blocked, not circumvented ([decision 0002](../decisions/0002-no-research-grade-free-price-source.md)). It would have added consumption and GDP disasters, not equity total returns — its return series come from Global Financial Data and are not redistributable |
| Goyal–Welch zipped-CSV and MATLAB copies | Behind Google Drive's large-file confirmation interstitial. Not needed: the spreadsheet holds the same data and was landed |
| Cross-source check on every ETF return | HTTP error for 44 of 44 and 25 of 25. **Item B.5 is the sole measurement of every fund return here** |
| Jensen–Kelly–Pedersen internet appendix | Not publicly reachable. Without it the +20.6pp construction step in their replication decomposition cannot be attributed |
| A Hou–Xue–Zhang reply to JKP; a rebuttal to Huang et al. on time-series momentum | Searched for and absent, not merely uncited |
| CME Group; congress.gov; MSRB EMMA; Berkeley CDAR; Parametric | IP-blocked, 403, JS-only, or DNS failure |
| ~15 paywalled papers | Named individually on the pages that wanted them, with the version actually used stated |

---

## 4. What a next round would have to acquire

Stated now so the specification exists before the budget does.

**The single unlock for anything investable** is a licensed, survivorship-free,
point-in-time total-return source. Its required contents:

- fund and share-class total returns net of fees, monthly or finer, covering the listed
  shelf **from at least 2003 so the window is 240 months rather than 72**;
- post-delisting observations and a **coded exit reason**;
- stable economic fund identity across share class, ticker change, merger and vendor
  migration;
- inception, first-trade and vendor first-seen dates, so backfill is detectable;
- point-in-time expense ratios, net assets and index-mandate history;
- documented total-return, distribution and corporate-action treatment;
- a stated revision policy with retrievable vintages.

A source supplying returns but not exit reasons or vintages does not lift fund-level
work above `exploratory`, and paying for one that does not would be the most expensive
way to learn nothing.

**Three cheaper acquisitions would each open a question that is currently closed by
absence rather than by evidence**, and none of them is a price feed:

**All three of the cheaper acquisitions named here have since been made or partly made** —
see the two acquisition sections above. What they open is now an experiment backlog rather
than a budget question:

| Acquisition | Status | Opens |
| --- | --- | --- |
| A documented total-return series for bonds, gold, commodities and REITs | **gold landed 2026-08-17**; commodities were already held via AQR CLR; **bonds and REITs still absent** | Gold is tested and the result is in [marginal sleeve value § Gold, tested](marginal-sleeve-value.md#gold-tested). **The stated bias was real and the sentence it defended is falsified in form and confirmed in substance**: gold reaches the credit ceiling exactly, and the ceiling was never the binding term. What is still blocked is an investable **bond** sleeve, where the `GS10` proxy still stands in |
| Long-horizon non-US equity histories | **landed 2026-08-16** (JST R6) | The drawdown ladder underneath the equity-share decision was **one country**. It is now sixteen, and −50.3% is measurably not a bound |
| Goyal–Welch at its current URL, and an inflation series | **landed 2026-08-16** (Goyal–Welch, Shiller, and JST's 18-country CPI) | Any conditional or valuation-dependent allocation, none of which has ever been tested here |

The ranked case for spending on any of these is in
[search coverage](search-coverage.md), which is also where the argument sits that the
repository's null result is partly a property of where it has looked.

---

## Consequence for this repository

1. **Check the resolution table before freezing a specification.** If the question's
   floor exceeds its bar, the experiment will return a null result that means nothing,
   and the honest move is to change the instrument or not run it.
2. **Every alpha carries its pedestal.** −0.55 pp/yr in the US, −0.31 developed ex-US,
   **+1.50 emerging**. An alpha quoted as a distance from zero is overstated by that much.
3. **Any ex-US factor loading names its panel.** Substituting the US panel puts 16 of 25
   ex-US funds below the 0.15 bar rather than 5, and moves individual loadings by up to
   0.480. A loading without its panel is not a number.
4. **The HML/RMW volatility band propagates, and five series carry no band at all.**
   Anything that divides by one of those volatilities states the band or states that it
   did not.
5. **Nothing here is point-in-time.** A sha256 proves which file was used, never what was
   available at an earlier date.
