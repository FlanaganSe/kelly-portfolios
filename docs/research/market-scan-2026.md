# Market scan, August 2026

**Purpose.** An outside-in check on what has changed in the real world, and what this
repository's audited shelf and research corpus would now get wrong. Written for the public
website rewrite.

**Read date for everything below is 2026-08-22 or 2026-08-23** unless a line says otherwise.
Where a figure was computed rather than quoted, the computation is stated.

**Headline finding, stated up front so the rest is read correctly.** This repository is
*not* stale. The shelf's `asOf` dates are 2026-08-17 to 2026-08-23, and independent
verification of all 59 shelf entries' expense ratios found **two** discrepancies, both under
3 bp. The pricing page's FRED figures reproduce to the decimal. The tax page's 2026 limits
match the IRS notices. What the repository is missing is not accuracy — it is **coverage**:
products that exist and are not on the shelf, costs that are not in the cost model, and two
term-premium series it declared unavailable that are in fact available.

---

## Section 0 — What the repository already covers

### The shelf, as committed (`src/content/shelf.ts`, 59 entries)

| Category | Tickers |
| --- | --- |
| us-core | VTI, VOO, ITOT, SPY |
| us-value | VTV, AVUV, DFUV, DFLV, DFSV, DFAT, RPV, VBR, AVLV, QVAL |
| us-small | AVSC, DFAS, VB |
| us-momentum | MTUM, SPMO |
| us-quality | QUAL, SPHQ, DUHP |
| intl-core | VEA, SPDW, IEFA, VXUS, SCZ, GWX |
| intl-value | DFIV, AVIV, IVLU, EFV |
| intl-small-value | AVDV, DISV |
| intl-momentum | IDMO, IMTM |
| emerging-core | VWO, IEMG |
| emerging-value | AVES, DFEV |
| bonds | BND, SPAB |
| managed-futures | DBMF, SDMF, CTA, KMLM, FMF, WTMF |
| capital-efficient | RSST, CTAP, RSSB, NTSX, GDE, MATE, JPFP |
| alternative | SCHD, VNQ, TIP, SCHP |

Also priced or discussed in prose but **not** on the typed shelf: the eight US spot bitcoin
ETPs (BTC, EZBC, BITB, HODL, ARKB, IBIT, FBTC, GBTC), the ether staking trusts (ETHE, ETH,
ETHB, ETHA), and the cat bond ETF.

### Docs read before searching

`factor-products.md`, `alternative-sleeves-audit.md`, `capital-efficiency-and-breadth.md`,
`live-managed-futures.md`, `untested-tilt-candidates.md`, `current-regime-and-pricing.md`,
`valuation-and-the-allocation.md`, `structural-and-tax-edges.md`,
`harvesting-and-direct-indexing.md`, `src/content/placement.ts`.

---

## Section 1 — Fee and product changes to funds already on the shelf

Verified against issuer pages and StockAnalysis fund pages, read 2026-08-22/23. Fees are net
expense ratios. AUM is the figure each source displays; the shelf carries **no AUM field at
all**, which is itself a gap (§CORRECTIONS C-9).

### Priority holdings

| Ticker | Shelf fee (bp) | Verified fee | AUM (2026-08-22) | Verdict |
| --- | ---: | ---: | ---: | --- |
| VTI | 3 | **0.03%** as of 2026-07-31 | $690.75bn | OK — but see the name change below |
| VTV | 3 | 0.03% | $194.26bn | OK |
| VXUS | 5 | 0.05% | $162.90bn | OK |
| AVUV | 25 | **0.25%** as of 2026-01-01 | $31.32bn | OK |
| AVDV | 36 | **0.36%** as of 2026-01-01 | $19.98bn | OK |
| AVLV | 15 | 0.15% | $19.11bn | OK |
| AVES | 36 | 0.36% | $1.50bn | OK |
| DFIV | 27 | 0.27% | $21.80bn | OK |
| SPMO | 13 | 0.13% | $22.27bn | OK |
| MTUM | 15 | 0.15% | $24.86bn | OK |
| RPV | 35 | 0.35% | $1.73bn | OK |
| IVLU | 31 | **0.30%** | $4.61bn | **1 bp low — shelf says 31** |
| EFV | 31 | **0.33%** | $31.74bn | **2 bp high — shelf says 31** |
| RSST | 99 | 0.99% gross, net assets $504.95m as of 2026-08-20 | $510.98m | OK |
| RSSB | 39 | 0.39% | $522.54m | OK |
| MATE | 97 | 0.97% | $39.76m | OK — inception 2025-12-16, still sub-scale |
| JPFP | 59 | 0.59% | $32.75m | OK |
| DBMF | 85 | 0.85% | $4.00bn (issuer deck: $4.16bn at 2026-08-19) | OK |
| CTAP | 28 gross | **0.10% net** displayed; waiver to management fee 0.07% **through at least 2026-12-04** | $157.88m | OK — waiver date confirmed |
| KMLM | 90 | 0.90% | $388.90m | OK |
| SDMF | 35 | 0.35% | $39.16m | OK |
| CTA | 75 | 0.75% | $1.61bn | OK |

Sources: [Vanguard VTI](https://investor.vanguard.com/investment-products/etfs/profile/vti),
[Avantis AVUV](https://www.avantisinvestors.com/avantis-investments/avantis-us-small-cap-value-etf/),
[Avantis AVDV](https://www.avantisinvestors.com/avantis-investments/avantis-international-small-cap-value-etf/),
[Return Stacked RSST](https://www.returnstackedetfs.com/rsst-return-stacked-us-stocks-managed-futures/),
[Simplify CTAP](https://www.simplify.us/etfs/ctap-simplify-us-equity-plus-managed-futures-strategy-etf),
[Simplify CTAP summary prospectus](https://www.simplify.us/sites/default/files/etf/2025-12/CTAP-Summary-Prospectus.pdf),
[iMGP DBMF factsheet](https://www.imgp.com/wp-content/uploads/2026/04/DBMF_FACTSHEET_EN.pdf),
[Man MATE](https://www.man.com/products/man-active-trend-enhanced-etf), StockAnalysis fund
pages (e.g. [AVUV](https://stockanalysis.com/etf/avuv/)), all read 2026-08-22/23.

### Second tier — all verified, all matching

VOO 0.03% / $1.04tn · ITOT 0.03% / $97.17bn · SPY 0.09% / $820.19bn · DFUV 0.21% / $15.89bn ·
DFLV 0.21% / $7.23bn · DFSV 0.30% / $8.40bn · DFAT 0.28% / $14.65bn · VBR 0.05% / $38.19bn ·
QVAL 0.28% / $631.54m · AVSC 0.25% / $3.21bn · DFAS 0.26% / $15.79bn · VB 0.03% / $82.69bn ·
QUAL 0.15% / $47.68bn · SPHQ 0.15% / $19.10bn · DUHP 0.20% / $12.75bn · VEA 0.03% / $236.45bn ·
SPDW 0.03% / $41.92bn · IEFA 0.07% / $195.14bn · AVIV 0.25% / $2.10bn · DISV 0.42% / $5.17bn ·
SCZ 0.40% / $13.28bn · GWX 0.40% / $932.41m · IDMO 0.25% / $4.33bn · IMTM 0.30% / $4.31bn ·
VWO 0.06% / $125.07bn · IEMG 0.09% / $160.00bn · DFEV 0.43% / $2.07bn · BND 0.03% / $162.86bn ·
SPAB 0.03% / $10.28bn · FMF 0.98% / $263.27m · WTMF 0.66% / $258.43m · NTSX 0.20% / $1.39bn ·
GDE 0.20% / $481.87m · SCHD 0.06% / $112.00bn · VNQ 0.13% / $39.05bn · TIP 0.18% / $15.07bn ·
SCHP 0.03% / $16.50bn.

**No closures, liquidations or mergers were found among the 59.**

### The one real product change: Vanguard's funds were renamed

The shelf's odd-looking names — "Vanguard **Morningstar** Total Stock Market ETF",
"Vanguard **Morningstar** Small-Cap Value ETF" — are **correct**, and this was worth
verifying because it looks like an error.

- Morningstar completed its **$375m acquisition of CRSP in February 2026** and rebranded the
  CRSP Market Indexes as Morningstar Indexes
  ([Morningstar newsroom](https://newsroom.morningstar.com/news/news-details/2026/Morningstar-Reaches-New-Milestone-in-the-CRSP-Acquisition-Rebranding-CRSP-Market-Indexes-to-Morningstar-Indexes/default.aspx),
  read 2026-08-22).
- Vanguard announced on **2026-04-29** that it would update the names of **13 US equity index
  funds** (all share classes, mutual fund and ETF) tracking those indexes
  ([Vanguard press release](https://corporate.vanguard.com/content/corporatesite/us/en/corp/who-we-are/pressroom/press-release-vanguard-to-update-names-of-us-equity-index-funds-tracking-morningstar-indexes-042926.html)).
- The renaming took effect **2026-07-29**. Vanguard's own VTI profile page now reads
  "VTI — Vanguard Morningstar Total Stock Market ETF".
- **Methodology, holdings, fee and ticker are unchanged.** This is a branding event, not an
  index change. The shelf is right and its `verdict` prose is right.

**Caveat the shelf should carry anyway:** three shelf names now embed a benchmark-provider
brand that could change again. A fund's identity is its ticker and its CIK, not its
marketing name.

### JPFP's first Form N-PORT is still not filed

Checked EDGAR directly (J.P. Morgan Exchange-Traded Fund Trust, CIK 0001485894). The trust's
most recent N-PORT-P batches were filed **2026-06-26** and **2026-07-28** (24 filings), and
filings run through 2026-08-18 with no JPFP series report. `capital-efficiency-and-breadth.md`
predicted the first filing is due **2026-08-29 or 2026-09-29**; that is still the state, and
the earlier of those two dates is **six days away**. `delta` for JPFP remains uncomputable.
This is the single cheapest open item in the whole corpus and it resolves within a month.

---

## Section 2 — New products since roughly mid-2025

### 2.1 The Return Stacked family has grown to eight funds; the shelf carries two

This is the largest single coverage gap. From
[returnstackedetfs.com](https://www.returnstackedetfs.com/), read 2026-08-22, AUM as of
2026-08-20:

| Ticker | Name | Inception | Fee | AUM | 30-day median spread | Verdict |
| --- | --- | --- | ---: | ---: | ---: | --- |
| RSST | US Stocks & Managed Futures | 2023-09-05 | 0.99% | $504.95m | **0.09%** | On shelf |
| **RSIT** | **International Stocks & Managed Futures** | **2026-05-06** | **0.98%** | **$68.53m** | **0.15%** | **Not on shelf. Genuinely new for this investor.** |
| RSSY | US Stocks & Futures Yield | 2024-05-28 | 0.99% | $94.46m | — | Not on shelf |
| **RSSX** | **US Stocks & Gold/Bitcoin** | **2025-05-29** | **0.67%** | **$70.59m** | **0.28%** | **Not on shelf. Directly relevant to the crypto and gold questions.** |
| RSBT | Bonds & Managed Futures | 2023-02-07 | 1.01% | $147.27m | — | Not on shelf |
| RSBY | Bonds & Futures Yield | 2024-08-20 | 1.01% | $55.63m | — | Not on shelf |
| RSBA | Bonds & Merger Arbitrage | 2024-12-17 | 1.01% | $52.33m | — | Not on shelf |
| RSSB | Global Stocks & Bonds | 2023-12-04 | 0.39% | $521.01m | — | On shelf |

Partner funds on the same page: BTGD (STKd 100% Bitcoin & 100% Gold, 2024-10-15, 0.99%,
$51.05m), ISBG and ISSB (IncomeSTKd, both 2026-01-20, 1.14% net, $6.98m and $1.97m).

**RSIT is the one that matters and it is three and a half months old.** Per the issuer page,
the equity leg holds roughly **75% SPDW plus 25% MSCI EAFE index futures** — a base leg of
approximately 1.00 per dollar of capital and a trend leg of 1.00, which puts
`delta = (1 − b)/d ≈ 0.00` and makes it structurally the international twin of RSST: it keeps
the entire funding-rule gap. This repository has just recommended adding AVDV
(`untested-tilt-candidates.md` §"AVDV: add it") and separately finds trend to be the
best-supported financed diversifier. RSIT is the first vehicle that stacks those two legs in
one wrapper. It has no N-PORT and no measurable loading, so nothing can be promoted from it —
but it belongs on the shelf as `not filed`, exactly as JPFP does.

**RSSX** matters for a different reason: it is a *financed* gold-and-bitcoin sleeve on top of
US equity, obtained through IBIT and CME bitcoin futures. `alternative-sleeves-audit.md`
concludes bitcoin should be funded from the speculation budget by *selling* equity; RSSX is
the construction in which it is not. That does not make the sleeve better — the funding
algebra improves the hurdle, it does not create a premium where the return evidence is a
price expectation — and the financed construction has since been measured: the funding
rule is worth its algebra and nothing else, and the verdict stands
([audit](alternative-sleeves-audit.md) §3.1).

### 2.2 Managed futures and trend

- **FFUT — Fidelity Managed Futures ETF.** Inception **2025-06-05**, **$346.23m**, and
  **0.80%** — which is an expense cap running to **2027-05-31**, not a fee: the table reads
  0.80% management plus 0.02% other expenses for 0.82% gross, and FDS may recoup within the
  fiscal year what it reimburses (summary prospectus dated 2026-05-30, read 2026-08-24).
  Trend-following across equity, rates, FX and commodities.
  ([etf.com](https://www.etf.com/sections/etf-watch/fidelity-adds-managed-futures-etf-growing-lineup),
  [StockAnalysis](https://stockanalysis.com/etf/ffut/), read 2026-08-22.) **Not on the shelf,
  and it is now the fourth- or fifth-largest managed-futures ETF.** Verdict: repackaging of a
  known mechanism, but from an issuer with distribution — its survival probability is higher
  than most of the shelf's small trend funds, which is the variable
  `live-managed-futures.md` shows actually decides outcomes (52% of the 2019 cohort stopped
  filing inside 6.5 years).
- **JPFP — JPMorgan Managed Futures Plus.** Inception 2026-05-27, 0.59%, $32.75m. Already on
  the shelf.
- **MATE — Man Active Trend Enhanced.** Inception 2025-12-16, 0.97%, $39.76m. Already on the
  shelf.
- **Category size.** Managed-futures ETFs reached roughly **$6bn by March 2026** across
  about 13 funds, against a CTA industry above $300bn
  ([HedgeNordic](https://hedgenordic.com/2026/04/muddling-through-the-mess-managed-futures-etfs/),
  read 2026-08-22). The category is **growing, not consolidating** — but DBMF alone is
  $4.0bn of the $6bn, so the rest of the shelf's trend funds are competing for about $2bn.
  Concentration risk in a category whose main failure mode is closure.

### 2.3 Systematic value, momentum, quality

Nothing that changes an allocation. Avantis has continued to ship one-ticker
fund-of-funds solutions rather than new engines: **AVGV** (All Equity Markets Value, 0.26%,
$458.26m), **AVNV** (All International Markets Value, 0.34%, $69.28m), **AVNM** (All
International Markets Equity, 0.31%, $742.86m), **AVMA** (Moderate Allocation, 0.21%,
$86.52m). Verdict: repackaging — they hold the same underlying Avantis sleeves the shelf
already prices, at a wrapper fee. They are worth a line on the shelf only as an
implementation convenience for a small taxable account, not as candidates.

### 2.4 Defensive, tail-risk, options-based

No launch found that changes `alternative-sleeves-audit.md` §4's conclusion (reject explicit
tail hedges; the cheaper substitutes win). I could not run an exhaustive census of the
buffered/derivative-income category within the search budget available — **this is a stated
coverage gap, not a null result.**

### 2.5 Catastrophe bonds — the vehicle is now three times the size the audit recorded

The Brookmont Catastrophic Bond ETF trades as **`ILS`**, which is the ticker
[`alternative-sleeves-audit.md` §5](alternative-sleeves-audit.md#5-catastrophe-bonds-the-vehicle-problem-is-solved-and-a-price-problem-has-replaced-it)
already uses throughout. `ROAR` appeared in pre-launch coverage and was never used; it is
recorded here only so that a reader who meets it in an article knows which fund it means.
The fund listed on NYSE in **April 2025**, the first US-listed cat bond fund, advised by
Brookmont with King Ridge Capital Advisors as sub-adviser
([ETFGI](https://etfgi.com/news/stories/2025/04/brookmont-capital-management-launches-first-us-listed-catastrophe-bond-etf),
[ilsetf.com](https://ilsetf.com/)).

**What is new here is the size, and only the size.**

- AUM was **~$12m in August 2025**, **$25.3m at 2025-11-26**
  ([Artemis](https://www.artemis.bm/news/brookmont-cat-bond-etf-gains-momentum-as-trading-volume-rises-assets-surpass-25m/)),
  and **$88.44m at 2026-08-22** ([StockAnalysis](https://stockanalysis.com/etf/ils/)). The
  audit's $88.2m is dated 2026-08-20; the two readings are two days apart and both are
  current for their date.
- Average daily trading volume rose ~672% between September and November 2025.

**The fee belongs to the audit and is not restated here.** The audit's figure is not a flat
1.58%: it is **2.65% gross and 1.58% net under a cap running to 2027-04-30**, against
**costs actually paid of 2.00% annualised** in the fund's own tailored shareholder report.
Three numbers, all of them true at once, and quoting the middle one alone understates what
a holder has actually paid. Nothing in this scan revises any of them.

The audit's access finding is now understated: the vehicle has survived eighteen months and
tripled in nine. That does not touch the audit's actual objection, which is **price** — the
risk spread has compressed by roughly half since 2023 — and the reopening condition there is
a spread level, not an AUM level. But "the retail history is short" is nine months shorter
than it was.

### 2.6 Crypto ETPs

**The regulatory change is the story, not any individual fund.** In **September 2025** the SEC
approved **generic listing standards for commodity-based trust shares**, replacing
case-by-case 19b-4 review with a rules-based path and cutting time-to-list from 240+ days to
roughly 75. An asset qualifies if it trades on a regulated market, has had CFTC-regulated
futures for six months, or an existing ETF already holds 40% of its assets in it
([CNBC](https://www.cnbc.com/2025/09/30/crypto-etfs-sec-generic-listing-new-boom-solana-xrp.html),
read 2026-08-22). Spot **Solana** and **XRP** ETPs reached the market from **November 2025**.

Current fees and net assets, from StockAnalysis fund pages read 2026-08-22 — except HODL's and
EZBC's fees, which are from those trusts' own Q2-2026 Forms 10-Q, read 2026-08-24, because the
aggregator's readings for both were wrong:

| Ticker | Asset | Fee | AUM |
| --- | --- | ---: | ---: |
| IBIT | BTC | 0.25% | **$58.78bn** |
| FBTC | BTC | 0.25% | $13.43bn |
| GBTC | BTC | 1.50% | $10.13bn |
| BTC (Grayscale Mini) | BTC | 0.15% | $4.12bn |
| BITB | BTC | 0.20% | $2.91bn |
| ARKB | BTC | 0.21% | $2.70bn |
| HODL | BTC | **0.20%** | $1.18bn |
| BRRR | BTC | 0.25% | $443.27m |
| EZBC | BTC | **0.19%** | $423.22m |
| ETHA | ETH | 0.25% | $7.68bn |
| ETHE | ETH | 2.50% | $1.84bn |
| ETHB (BlackRock staked) | ETH | 0.25% | $795.50m |
| ETHW | ETH | 0.20% | $262.47m |
| BSOL (Bitwise) | SOL | n/a | $761.07m |
| GSOL (Grayscale) | SOL | 0.35% | $123.22m |
| XRPC (Canary) | XRP | 0.50% | $319.03m |

**The two divergences from the audit's Q2-2026 10-Q table are the aggregator's, not the
audit's.** The table above shows HODL at 0.25% and EZBC at 0.29%; both trusts' own Q2-2026
Forms 10-Q, read 2026-08-24, say **0.20%** and **0.19%** respectively, and HODL's filing states
in terms that after 2026-07-31 — the waiver expiry the audit already flagged — "the Sponsor Fee
will be 0.20%". The audit's figures stand, the table above carries the filed ones, and the
aggregator's 0.25% and 0.29% appear nowhere in either trust's filings; see **C-16**. The
generalisation is the useful part: a spot-ETP sponsor fee under waiver is the single field a
data aggregator here got wrong twice out of sixteen, and it is cheap to check in the trust's
own quarterly filing.

**IBIT went from $43.4bn at 2026-06-30 to $58.78bn** — roughly +35%, against bitcoin's
+31.6% price move over the same stretch, so most of that is mark-to-market rather than flow.

**Verdict on the new altcoin ETPs: repackaging with worse economics.** Solana and XRP ETPs are
the same 1933-Act grantor-trust wrapper around an asset with a shorter history, thinner
benchmark infrastructure, and no cash-flow claim. Nothing in the repository's crypto argument
turns on which coin is in the trust.

### 2.7 Structural changes to what is buyable

- **ETF share classes of mutual funds.** The SEC granted Dimensional's exemptive relief on
  **2025-11-17**, the first for an active manager and the second ever after Vanguard's expired
  patent ([Dimensional](https://www.dimensional.com/us-en/newsroom/dimensional-receives-sec-approval-for-etf-share-classes),
  [Seward & Kissel 40 Act Blog](https://40actblog.sewkis.com/blog/sec-issues-order-for-dfa-exemptive-application-opening-the-door-to-etf-share-classes)).
  Substantially identical applications from other managers follow. **Why it matters to this
  repository:** the tax-efficiency argument in `structural-and-tax-edges.md` and
  `placement.ts` rests partly on the ETF in-kind shield. If a Dimensional *mutual fund*
  acquires an ETF share class, the mutual fund's capital-gain distributions fall toward the
  ETF's. That changes the placement arithmetic for anyone holding DFA mutual funds in a
  taxable account, and it changes the "ETF or mutual fund" question from a structural one to
  an empirical one. No shelf fund is affected yet.
- **Generic crypto listing standards** (September 2025) — above.

---

## Section 3 — The current pricing environment

Every FRED figure below was **refetched directly from `fredgraph.csv` on 2026-08-23** for this
scan, independently of the repository's cache. **All of them reproduce the values in
`current-regime-and-pricing.md` exactly.** That page is correct as written.

### 3.1 Rates and inflation

| Measure | Value | As of | Source |
| --- | ---: | --- | --- |
| 10y nominal Treasury | **4.69%** | 2026-08-20 | [FRED DGS10](https://fred.stlouisfed.org/series/DGS10) |
| 30y nominal | 5.23% | 2026-08-20 | [FRED DGS30](https://fred.stlouisfed.org/series/DGS30) |
| 2y nominal | 4.19% | 2026-08-20 | [FRED DGS2](https://fred.stlouisfed.org/series/DGS2) |
| 3m bill | 3.71% | 2026-08-20 | [FRED DTB3](https://fred.stlouisfed.org/series/DTB3) |
| **10y TIPS real** | **2.35%** | 2026-08-20 | [FRED DFII10](https://fred.stlouisfed.org/series/DFII10) |
| **30y TIPS real** | **2.95%** | 2026-08-20 | [FRED DFII30](https://fred.stlouisfed.org/series/DFII30) |
| 10y breakeven | 2.34% | 2026-08-21 | [FRED T10YIE](https://fred.stlouisfed.org/series/T10YIE) |
| 5y5y forward breakeven | **2.34%** | 2026-08-21 | [FRED T5YIFR](https://fred.stlouisfed.org/series/T5YIFR) |
| Fed funds effective | 3.63% | 2026-08-20 | [FRED DFF](https://fred.stlouisfed.org/series/DFF) |
| CPI YoY | **+3.30%** | 2026-07 | computed from [FRED CPIAUCSL](https://fred.stlouisfed.org/series/CPIAUCSL) |
| Core CPI YoY | **+2.47%** | 2026-07 | computed from [FRED CPILFESL](https://fred.stlouisfed.org/series/CPILFESL) |
| Core PCE YoY | **+3.29%** | 2026-06 | computed from [FRED PCEPILFE](https://fred.stlouisfed.org/series/PCEPILFE) |
| Headline PCE YoY | +3.67% | 2026-06 | computed from [FRED PCEPI](https://fred.stlouisfed.org/series/PCEPI) |
| Unemployment | **4.1%** | 2026-07 | [FRED UNRATE](https://fred.stlouisfed.org/series/UNRATE) |

**A wrinkle worth noting that the repository's page does not:** headline CPI YoY is 3.30%
while **core** CPI YoY is 2.47%. Headline is running *above* core, which is the reverse of the
usual configuration and means the 3.54% trailing-CPI figure the pricing page uses for the
ex-post real bill is being driven by non-core components. The real-cash-rate conclusion does
not change, but the "+0.19 pp real bill" is more volatile than it looks.

### 3.2 Term premium — the repository says this is unavailable; it is not

`current-regime-and-pricing.md` §1.3 states: *"No term-premium estimate is supported by this
cache. The Adrian–Crump–Moench and Kim–Wright decompositions are not in it… `unresolved`, and
honestly so."*

Both are obtainable:

- **Kim–Wright 10-year term premium: +0.8393%, as of 2026-08-14**, from
  [FRED THREEFYTP10](https://fred.stlouisfed.org/series/THREEFYTP10) — 9,555 daily rows back
  to 1990-01-02, fetched 2026-08-23. This is a Federal Reserve Board series distributed on
  FRED. **It is in the same data contract the pricing page already uses.**
- **NY Fed ACM 10-year term premium: approximately +0.80% as of 2026-08-13**, against 0.513%
  in June 2026 and 0.667% in May 2026 (secondary aggregators citing the NY Fed release;
  primary table at
  [newyorkfed.org term premia](https://www.newyorkfed.org/research/data_indicators/term-premia-tabs)).
  Treat the ACM figure as **medium confidence** — I read it from aggregators, not from the
  NY Fed's own CSV.

The two estimates agree at roughly **+0.8 pp**, which is materially positive for the first
time in about five years. That is a *substantive* addition, not a bookkeeping one: it says the
+0.82 pp 10y−3m slope is roughly **all term premium and roughly no expected rate change**,
which the pricing page explicitly declines to conclude because it lacked the decomposition.
The honest label moves from `unresolved` to `measured, two independent estimates, both ≈+0.8`.

### 3.3 Credit — the data-contract finding is confirmed and still binding

Fetched 2026-08-23:

- **ICE BofA US High Yield OAS = 2.75%**, latest 2026-08-20. **796 daily rows, series begins
  2023-08-22.** ([FRED BAMLH0A0HYM2](https://fred.stlouisfed.org/series/BAMLH0A0HYM2))
- **ICE BofA US Corporate (IG) OAS = 0.82%**, latest 2026-08-20. **796 daily rows, begins
  2023-08-22.** ([FRED BAMLC0A0CM](https://fred.stlouisfed.org/series/BAMLC0A0CM))

**The truncation is real and current.** The pricing page's finding — that no percentile of a
current OAS against its own history can be computed from FRED — reproduces exactly, three
years to the day. Anyone rewriting the public site should not quietly quote a "high yield
spreads are in the Nth percentile since 1997" line, because the underlying series no longer
supports it from this source.

### 3.4 US equity valuation

| Measure | Value | As of | Source |
| --- | ---: | --- | --- |
| Shiller CAPE | **41.2×** (aggregators span 40.4–41.58) | Aug 2026 | [GuruFocus](https://www.gurufocus.com/economic_indicators/56/sp-500-shiller-cape-ratio), [thetrading.tools](https://www.thetrading.tools/shiller-cape) |
| Repo's own CAPE | 41.18 | 2026-08-01 | `current-regime-and-pricing.md` |
| S&P 500 forward 12m P/E | **20.0** | 2026-08-07 | [FactSet Earnings Insight, 2026-08-07](https://insight.factset.com/sp-500-earnings-season-update-august-7-2026) |
| 5-year average forward P/E | 19.9 | 2026-08-07 | same |
| 10-year average forward P/E | 19.0 | 2026-08-07 | same |
| Forward P/E at 2026-06-30 | 20.4 | 2026-06-30 | same |
| CY2026 consensus EPS growth | +30.0% | 2026-08-07 | same |

**The repository's CAPE of 41.18 and forward P/E of 20.0 are both current and both correctly
sourced.** `shillerdata.com` itself does not display the value — it only serves `ie_data.xls`
— so the repository's practice of reading it from its own cache and cross-checking against
aggregators is the right one.

The FactSet detail worth carrying into the site rewrite: **a forward P/E of 20.0 that is only
0.1 above its own five-year average, resting on +30% consensus CY2026 earnings growth.** The
multiple is not the extreme; the earnings denominator is. A CAPE of 41 at the 98.9th
percentile and a forward P/E of 20 at roughly the 55th percentile of five years are both true,
and the pricing page is right to call the tension unresolved.

### 3.5 US versus international — this is where the year actually happened

Computed from [FRED SP500](https://fred.stlouisfed.org/series/SP500), fetched 2026-08-23
(price return, dividends excluded):

- **S&P 500 calendar 2025: +16.4% price** (≈+17.9% total return).
- **S&P 500 2026 YTD to 2026-08-21: +12.1%** (6,845.50 → 7,674.37).
- S&P 500 first half 2026: +9.6%.

Against that:

- **MSCI EAFE returned ~+31.2% and MSCI EM ~+33.6% in calendar 2025**, against the S&P 500's
  +17.9% — roughly **13 to 16 percentage points of international outperformance in one year**,
  of which **a little over 10 pp came from dollar weakness**
  ([Yahoo Finance / MSCI coverage](https://finance.yahoo.com/news/international-stocks-pummelled-p-500-180000221.html),
  [The London Company](https://www.tlcadvisory.com/fy-international-equity-2025-vs-msci-eafe/), read 2026-08-22).
- 2026 has been closer. Some coverage claims the S&P 500 "slipped about 2% in 2026" — **that
  is stale or wrong**; the index is **+12.1% YTD** on primary data. Treat mid-year commentary
  on 2026 relative performance as unreliable and re-measure it.

**Valuation gap** (repository's own figures, Siblis Research at 2026-06-30, read 2026-08-22):
US CAPE 35.82, global ex-US 21.02, EM 19.36 — a **1.70× US premium over developed ex-US** and
**1.85× over EM**. Secondary coverage puts developed international and EM at roughly 19× and
18× forward earnings against the S&P 500 near 29× trailing.

**The dollar.** Fetched 2026-08-23 from
[FRED DTWEXBGS](https://fred.stlouisfed.org/series/DTWEXBGS):

- Broad trade-weighted dollar index **118.9028 at 2026-08-14**.
- **−1.44% over one year**, **−0.97% over three years**.
- **57th percentile of its own ten-year range** (10y min 106.49, max 130.04).

That last line is the one that should temper the story. The dollar delivered 10 pp of EAFE's
2025 return, and it is still at the **57th percentile of the last decade** — mid-range, not
cheap. The currency tailwind is not obviously spent, and it is not obviously repeatable.
`currency-and-the-international-sleeve.md` owns this; **the repository does not currently
carry a dollar level anywhere I could find**, and given that a tenth of last year's
international outperformance was currency, it should.

### 3.6 Gold

- **Spot ~$4,587/oz at 2026-08-21**; another read $4,607.35 the same day
  ([Fortune, 2026-08-21](https://fortune.com/article/current-price-of-gold-08-21-2026/)).
  The repository's "2026-08-21 fix of $4,582" is consistent.
- **But gold peaked in January.** Gold futures hit a **record $5,542.40 on 2026-01-29**. Gold
  is therefore roughly **−17% from its high** while sitting at the **98.5th percentile of its
  own real price since 1975**.

Both facts are true and the pricing page carries only the second. "Most expensive thing on the
page relative to its own history, and 17% below its own January high" is a more complete and
more useful sentence than either half.

### 3.7 Capital market assumptions

**Vanguard Capital Markets Model, 10-year annualised nominal, June 30 2026 running**
([Vanguard VEMO return forecasts](https://corporate.vanguard.com/content/corporatesite/us/en/corp/vemo/vemo-return-forecasts.html),
read 2026-08-23):

| Asset | 2026-06-30 range | Prior (2026-03-31) |
| --- | --- | --- |
| US equities | **4.2%–6.2%** | 4.9%–6.9% |
| Developed markets ex-US | **4.5%–6.5%** | 5.4%–7.4% |
| Emerging markets | **2.0%–4.0%** | 3.6%–5.6% |

Vanguard notes value stocks continue to offer the most attractive expected-return profile
within US equities. I could not extract the bond, small-cap or REIT rows from the page.

**Read this carefully, because it cuts against the obvious story.** Vanguard now forecasts
**emerging markets below US equities** — 2.0–4.0% against 4.2–6.2% — after EM returned +33.6%
in 2025. Developed ex-US retains only a **0.3 pp** median edge over the US. A model that
conditions on valuation has *already priced in* most of the 2025 international rally and cut
its forward EM number by 1.6 pp in a single quarter. The valuation gap is 1.70×; the
model-implied return gap is 0.3 pp. **Anyone rewriting the site should not present the
valuation gap as though it were an expected-return gap.**

I could not reach GMO's or Research Affiliates' current vintages within the search budget.
**Stated gap.**

### 3.8 Does the evidence support changing an allocation on valuation? Yes to the framing the
repository already uses, and the last twelve months are a live test of it

I could not complete a fresh literature sweep — the session's search budget was exhausted
before Task B. What I *can* do is check the repository's position against what actually
happened, which is the more informative test.

`valuation-and-the-allocation.md`'s position, as written: CAPE's out-of-sample record does not
support timing the equity share; the **relative** US/international call is "a different and
better-posed question"; the cross-country relation is undetectable after 1990; and the
recommendation is a fixed split with the decision framed as regret rather than forecast.
`current-regime-and-pricing.md` reinforces it: of twenty-seven conditioning relations, none
predicts the equity premium out of sample, and the term spread's five-year equity regression
carries a Hodrick *t* of 2.32 with an **out-of-sample R² of −0.175**.

Three checks against 2025–2026:

1. **The relative call paid, once.** International beat the US by 13–16 pp in 2025. A
   valuation-motivated tilt would have been rewarded. **One year is one observation**, and the
   repository's own §5.2 already measures the confounds.
2. **Ten pp of the 13–16 was currency, not re-rating.** That is the confound the repository
   names and it dominated the result. The valuation gap barely closed: US CAPE 35.82 vs ex-US
   21.02 at 2026-06-30 is still a 1.70× premium.
3. **The forward-looking models did not extrapolate.** Vanguard cut its EM forecast to
   2.0–4.0% and left developed ex-US only 0.3 pp ahead of the US. A model that both conditions
   on valuation and is disciplined about it says the gap is *mostly already collected*.

**The repository's view holds.** Nothing in the last twelve months supports moving the equity
share on CAPE, and the relative call — which the repository already treats as better-posed —
delivered its payoff in a form (currency) that its own currency page identifies as the least
persistent driver. The one thing I would add to the page: **a dollar level with a percentile**,
because the 2025 result is unreadable without it.

**Not verified in this scan (stated gaps):** Goyal, Welch & Zafirov's updated paper; the
Siegel / Straehl–Ibbotson / Philosophical Economics accounting-comparability arguments; the
post-publication out-of-sample record of valuation-timing rules. The repository's own §2.3 and
§2.4 already cover the last two and were not contradicted by anything found here.

---

## Section 4 — Crypto, honestly

**All correlation, beta, drawdown and worst-decile figures in this section were computed by me
on 2026-08-23** from [FRED CBBTCUSD](https://fred.stlouisfed.org/series/CBBTCUSD) (Coinbase
BTC/USD) and [FRED SP500](https://fred.stlouisfed.org/series/SP500), using log returns. The
SP500 series is limited to ten years, so the monthly panel is 120 months (2016-08 to 2026-08),
not the repository's 137.

### 4.1 Is the repository's verdict still true?

**Substantially yes, and one figure has moved in bitcoin's favour.**

| Repository claim | My independent measurement | Verdict |
| --- | --- | --- |
| Up-beta 1.526, down-beta 1.616, no convexity | Monthly beta to SPX: **+1.77 (5y)**, **+1.37 (3y)**, **+1.41 (1y)**. I did not decompose up/down. | Consistent — beta is large and positive |
| Positive in **1 of 13** worst-decile equity months, mean −7.51% | Positive in **2 of 12**; mean **−5.0%** | **Slightly better than the repo states**, and the new observation is 2026-03 |
| ρ to equity +0.342 over 137 months; +0.531 on the 81-month sub-window | Monthly ρ: **+0.510 (5y)**, **+0.363 (3y)**, **+0.383 (1y)**. Daily ρ: **+0.326 (5y)**, **+0.170 (3y)**, **+0.384 (1y)** | Consistent. **Correlation has stopped rising** — the 3y daily reading of +0.170 is the lowest on the panel |
| Max drawdown −75.9% | Now **−38.2% from the all-time high** of $124,720 on 2025-10-05 | Current drawdown, not max |
| H1 2026: bitcoin −33.2% while equity +9.9% | **Exactly reproduced**: $87,696 (2025-12-31) → $58,586 (2026-06-30) = **−33.2%**; SPX +9.6% | Confirmed |
| "Since recovered to $77,338" | **$77,117.73 at 2026-08-22** | Confirmed |

**The full worst-decile table** (worst 12 of 120 months by S&P 500 return):

| Month | S&P 500 | Bitcoin |
| --- | ---: | ---: |
| 2020-03 | −12.5% | −24.8% |
| 2022-09 | −9.3% | −3.0% |
| 2018-12 | −9.2% | −7.1% |
| 2022-04 | −8.8% | −17.2% |
| 2020-02 | −8.4% | −8.5% |
| 2022-06 | −8.4% | −37.6% |
| 2018-10 | −6.9% | −4.6% |
| **2019-05** | −6.6% | **+62.2%** |
| 2022-12 | −5.9% | −3.8% |
| 2025-03 | −5.8% | −1.0% |
| 2022-01 | −5.3% | −16.9% |
| **2026-03** | −5.1% | **+2.2%** |

Two positives in twelve, and one of them (+62.2% in May 2019) is a bull-market month that
happened to coincide with an equity dip. **The 2026-03 observation is new since the audit was
written and it is a genuine, if small, point in bitcoin's favour.**

### 4.2 Trailing returns, which are the part that has genuinely changed

Computed 2026-08-23:

| Horizon | Bitcoin | S&P 500 (price) |
| --- | ---: | ---: |
| 1 year (from 2025-08-22) | **−33.2%** ($115,384 → $77,118) | **+18.7%** |
| 3 years (from 2023-08-22) | +196.2% ($26,038 → $77,118) | +74.9% |
| 5 years (from 2021-08-22) | **+56.3%** ($49,328 → $77,118) | **+72.8%** |

**Over five years, bitcoin has underperformed the S&P 500 at roughly four times the
volatility** (42.2% realised over the last year against the index's 12.9%). That is not a
selective window: it is the longest horizon the daily panel supports cleanly, and it covers
the spot-ETF launch, the 2024 halving, and the entire institutional-adoption story.

### 4.3 What has structurally changed, and whether it matters

**Genuinely changed:**

- **Flows are large and institutional.** IBIT alone holds **$58.78bn**. US spot bitcoin ETFs
  took **$517m in a single day on 2026-08-19**, the largest since early May, and about $853m
  in the strongest week since April 2026
  ([CoinDesk, 2026-08-20](https://www.coindesk.com/tech/2026/08/20/live-updates-bitcoin-etfs-draw-usd517-million-ether-pulls-usd189-million-in-biggest-inflows-in-months)).
- **Volatility has collapsed.** 30-day realised volatility fell to an annualised **42%**,
  the narrowest volatility gap to the S&P 500 on record
  ([Coincall market note, 2026-08-19](https://support.coincall.com/hc/en-us/articles/61315330793369-August-19-2026-ETF-Demand-Rebounds-Bitcoin-Volatility-Hits-a-Cycle-Low-U-S-Crypto-Rules-Advance)).
- **Regulation opened up.** Generic listing standards (September 2025); Rev. Proc. 2025-31's
  staking safe harbour, which the repository already documents.
- **A financed vehicle now exists**: RSSX (§2.1).

**What that does to the argument: less than it sounds.**

Every one of those changes makes bitcoin *more like a financial asset* — more correlated,
better arbitraged, lower-vol, more owned by the same institutions that own equity. The
repository's stated reopening trigger is **"a correlation to equity back below +0.2 on a
window containing a recession."** The 3-year *daily* correlation is +0.170, which is under the
threshold — but the window contains no recession, and the 3-year *monthly* reading is +0.363.
**The trigger is not met.** Financialisation is the mechanism that removes the diversification
case, not the one that establishes it. A short-term correlation of 83.6% to the S&P 500 in
early August 2026 is the same point from the other side.

### 4.4 The fair hearing

What can honestly be said for a small position, and what cannot:

- **Cannot:** that it is a diversifier. Five of the last five years of evidence, including the
  ETF era, say it is high-beta equity with idiosyncratic risk on top. It has now
  *underperformed* equity over five years while doing that.
- **Cannot:** that a cash-flow claim has arrived for bitcoin. Ether staking is a real
  contractual payer and it is **not bitcoin** — the repository already has this exactly right.
- **Can:** that the loss from a 1–2% position going to zero is 1–2%; that the investor asked
  for it; and that a holding one wants is easier to keep than one one resents. That is a
  preference argument, and the repository already labels it as one.
- **Can, and is new:** that if it is held, the **financed** construction (RSSX at 0.67%) has a
  better hurdle than selling equity to fund it, because the funding-rule gap is real
  arithmetic independent of any premium. This does not make the sleeve good. It makes the
  *worst* version of holding it less bad.

**Bottom line: the repository's verdict — at most 1–2%, from the speculation budget, in
taxable, labelled a speculation — survives everything measured here, and one of its
supporting figures (1 of 13) should be updated to 2 of 12.**

---

## Section 5 — Tax and account rules for 2026

Verified against IRS primary sources. **The repository's figures are correct.** The one gap is
a rule it does not appear to mention at all.

### 5.1 Retirement limits — IRS Notice 2025-67

Extracted directly from [Notice 2025-67 (PDF)](https://www.irs.gov/pub/irs-drop/n-25-67.pdf),
read 2026-08-23, and cross-checked against the
[IRS newsroom release](https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500):

| Item | 2026 | 2025 |
| --- | ---: | ---: |
| §402(g) elective deferral | **$24,500** | $23,500 |
| §414(v) age-50 catch-up | **$8,000** | $7,500 |
| Age 60–63 "super" catch-up | **$11,250** | $11,250 |
| IRA contribution | **$7,500** | $7,000 |
| IRA age-50 catch-up | **$1,100** | $1,000 |
| **§415(c) annual additions (the mega-backdoor ceiling)** | **$72,000** | $70,000 |
| §415(b)(1)(A) DB limit | $290,000 | $280,000 |
| §401(a)(17) compensation limit | $360,000 | $350,000 |
| §414(q) HCE threshold | $160,000 | $160,000 |
| Roth IRA phase-out, MFJ | **$242,000–$252,000** | — |
| Roth IRA phase-out, single/HoH | **$153,000–$168,000** | — |
| Traditional IRA deduction, single (covered) | $81,000–$91,000 | — |
| Traditional IRA deduction, MFJ (covered) | $129,000–$149,000 | — |
| Traditional IRA deduction, non-covered spouse | $242,000–$252,000 | — |
| SIMPLE 401(k) | $17,000 (or $18,100 under SECURE 2.0) | $16,500 |

The repository's `structural-and-tax-edges.md` §1264 and `placement.ts` carry the deferral,
catch-up, IRA and Roth phase-out figures correctly. **They do not carry §415(c) = $72,000**,
which is the number that bounds the mega-backdoor Roth.

### 5.2 The rule the repository does not mention: mandatory Roth catch-up

**SECURE 2.0 §603, effective for taxable years beginning in 2026.** Notice 2025-67 line 41–44:
the §414(v)(7)(A) wage threshold *"used to determine whether catch-up contributions must be
designated as Roth contributions, is increased from $145,000 to $150,000."*

Concretely: **if your 2025 Social Security (FICA) wages from the employer sponsoring the plan
exceeded $150,000, then every catch-up dollar in 2026 — the $8,000 age-50 catch-up or the
$11,250 age 60–63 catch-up — must be a designated Roth contribution.** No pre-tax option.

**Why this matters here specifically.** `capital-efficiency-and-breadth.md` reaches a placement
conclusion — a stacked trend wrapper belongs in the **pre-tax** account, not the Roth and not
taxable — and then notes that a 30%-of-portfolio wrapper *"consumes roughly nine tenths of a
one-third pre-tax account."* This rule makes the pre-tax account **smaller** for exactly the
investor the page is written for: a high earner over 50 loses the ability to add $8,000–$11,250
of *pre-tax* space per year and gains Roth space instead. The scarce shelter the wrapper needs
is now scarcer, and it gets scarcer every year. **That is a real, dated, decision-relevant
change to a conclusion the repository has already reached.**

### 5.3 Capital gains, NIIT, and the loss cap

From [Rev. Proc. 2025-32 (PDF)](https://www.irs.gov/pub/irs-drop/rp-25-32.pdf) §3.03 and
§3.14, extracted 2026-08-23:

**2026 long-term capital gain / qualified dividend thresholds:**

| Filing status | Max 0% rate amount | Max 15% rate amount |
| --- | ---: | ---: |
| MFJ / surviving spouse | $98,900 | **$613,700** |
| MFS | $49,450 | $306,850 |
| Head of household | $66,200 | $579,600 |
| All other individuals | $49,450 | $545,500 |
| Estates and trusts | $3,300 | $16,250 |

**2026 standard deduction:** MFJ $32,200 · HoH $24,150 · single $16,100 · MFS $16,100 ·
additional for aged/blind $1,650 ($2,050 if unmarried and not a surviving spouse).

The repository already cites Rev. Proc. 2025-32 §3.03 and the $613,700 figure. Correct.

**§1411 NIIT: 3.8%, on modified AGI above an unindexed $250,000 (MFJ) / $200,000 (single).**
Unchanged; the threshold has never been indexed. The repository states this correctly and
correctly observes that any investor in the 18.8% or 23.8% column is at or past the Roth IRA
phase-out.

**§1211(b): still $3,000, still not indexed.** Congressional Research Service analysis and
2026 practitioner guidance confirm that **the One Big Beautiful Bill Act made no change to
§1211, §1212, or the wash-sale rule in §1091**
([CRS RL31562](https://www.congress.gov/crs-product/RL31562)). Indexing from 1978 would put
the cap near $13,000. `harvesting-and-direct-indexing.md`'s entire argument — that the $3,000
cap, not the harvest yield, is the binding constraint — is **intact and current.**

### 5.4 Wash sales and crypto

**No change.** §1091 applies to "stocks or securities," digital assets are not securities for
this purpose, and no 2025–2026 legislation altered that. Proposals to extend §1091 to digital
assets have appeared repeatedly in budget documents and have not been enacted. The OBBBA did
not do it.

**Medium confidence.** I confirmed the OBBBA point from CRS and practitioner sources but could
not run a fresh check on 2026 crypto market-structure legislation before the search budget
ran out. **Re-verify before publishing any claim that crypto tax-loss harvesting is
unrestricted.**

### 5.5 Backdoor and mega-backdoor Roth

Both remain available. No 2025–2026 legislation eliminated either. The mega-backdoor ceiling
is the §415(c) limit, **$72,000 for 2026** (less elective deferrals and employer
contributions), and requires a plan that permits after-tax contributions plus either in-plan
Roth conversion or in-service withdrawal. The backdoor Roth remains subject to the pro-rata
rule of §408(d)(2) across all traditional/SEP/SIMPLE IRAs.

### 5.6 Qualified dividends and the foreign tax credit

- **Qualified dividend treatment** is unchanged: the LTCG rate schedule above, subject to the
  §1(h)(11) holding-period requirement.
- **Foreign tax credit through funds:** §853(a)(1) requires **more than 50% of a fund's total
  assets at year end to be foreign securities** for it to elect to pass foreign taxes through
  to shareholders. `currency-and-the-international-sleeve.md` line 507 has this right. The
  practical consequence the repository already draws — the credit is lost in a tax-deferred
  account — is unchanged.

---

## Section 6 — Costs an investor actually pays

### 6.1 Two brokers are changing their fee structure, and this is the most decision-relevant
item in the scan after RSIT

**Fidelity, effective 2026-06-01:** Fidelity issued a notice on **2026-03-16** requiring ETF
issuers to pay asset-based platform fees to remain accessible. Issuers that refused were placed
on a **"service fee eligible" list**, and purchases of their ETFs now carry **$100 per trade**
(described as roughly 5% of trade value, **capped at $100**)
([ETF Investments, read 2026-08-23](https://etfinvestments.substack.com/p/fidelity-just-added-100-fees-to-120);
[RIABiz, 2026-05-07](https://riabiz.com/a/2026/5/7/schwab-is-joining-fidelity-in-law-of-the-jungle-shakedown-of-etfs-with-vanguard-not-immune-to-claim-up-to-15-of-fee-revenues-and-charge-investors-100-per-trade-for-using-non-compliant-etf-managers)).

**Schwab:** CEO Rick Wurster said on the Q1 2026 call (2026-04-16) that an issuer platform-fee
programme would be "in place and live" by the end of 2026; a spokesperson later gave "no later
than Q1 2027"; the Q2 call (2026-07-21) added nothing. The reported terms — about 15% of ETF
fee revenue, or a $100 ticket charge on non-paying issuers — are press anticipation, not a
Schwab statement. **Announced, not in effect, and no issuer list exists** (`as of 2026-09-01`;
Schwab's pricing pages carry no per-trade ETF fee).

**Vanguard:** reportedly reached an undisclosed agreement with Fidelity by May 2026, while
maintaining it does not pay distribution fees that incentivise sales.

**Scale:** combined Schwab and Fidelity assets of $26tn, of which about **$3.8tn of ETF assets
are liable**.

**Issuers named as penalised as of June 2026:** Roundhill (40+ funds), Kurv, Renaissance,
XOVR, IVES, Inspire, Hedgeye, Rareview, Polen, Brandes, WEBs Defined Volatility, Cyber Hornet,
Guinness Atkinson, Strategy Shares, Faith Investor Services.

**Resolved 2026-09-01.** Fidelity's own PDF, "ETFs Subject to Service Fee, as of August 15,
2026" (`fidelity.com/bin-public/…/service-fee-eligible-ETFs.pdf`), lists **84 tickers** (press
counts run to about 108) from AltShares, American Conservative Values, Atlas, CrossingBridge,
Cultivar, Wedbush, ERShares, Formidable, Fortuna, Hedgeye, Kingsbarn, Miller Value, Point
Bridge, Rareview, Renaissance, Roundhill, Siren, Spear and WealthTrust. **None of
Tidal/Return Stacked, Simplify, Pacer, J.P. Morgan, Invesco, Avantis or Dimensional appears,
and no shelf ticker appears.** The list is "subject to change without notice", so it is a
reading, not a clearance. The exposure it would have created is still worth stating, because
the list can grow:

- A **$100 flat fee on a $10,000 purchase is 100 bp** — larger than the entire expense ratio of
  every fund on the shelf except the trend wrappers, and roughly **four times AVDV's 36 bp
  annual fee, paid on day one**.
- The exposed issuers are structurally the **small ones**: Simplify ($39m–$1.6bn per fund),
  Tidal/Return Stacked ($52m–$523m per fund), Brookmont ($88m), Man ($40m), iMGP. These are
  precisely the boutiques with the least fee revenue to hand over. Avantis (American Century),
  Dimensional, iShares, Invesco, Vanguard, SSGA, WisdomTree, Schwab and JPMorgan are not
  plausibly at risk; **Simplify, Tidal, Brookmont, Man Group and KraneShares plausibly are.**
- A conclusion that a wrapper is buyable is a conclusion about a **broker**, not only a fund.
  `capital-efficiency-and-breadth.md` compares CTAP, RSST and MATE at 0.81%–0.99%; a $100 entry
  fee at the investor's actual broker would reorder that comparison, and none of the three is
  large enough to be safe from the list.

**Commissions themselves are unchanged:** Fidelity, Schwab and Vanguard all remain **$0 on
online stock and ETF trades**. Options differ — Schwab $0.65/contract; **Vanguard restructured
its schedule on 2026-07-10** into tiers based on "Qualifying Assets," replacing its previous
$1.00/contract flat rate.

**Addendum, read 2026-09-01.** Three fund facts that bear on the stacked-fund comparisons:

- **RSSB's fee is 0.39% with no expiry.** The 485BPOS of 2026-04-27 records that the waiver to
  0.35% "was terminated by the Board and the Fund's management fee was reduced to 0.35%"
  (plus 0.04% AFFE); the 497K's "reflected only through May 31, 2026" line is the old waiver
  language. The waiver question in §2.1 is closed.
- **GDT** (WisdomTree Efficient TIPS Plus Gold, 2026-01-22, 0.20% after a cut from 0.30%
  effective about 2026-04-20): roughly a dollar of short TIPS plus a dollar of gold futures,
  $11.8m; a TIPS-and-gold stack, not a Treasury one.
- **NTSD** (WisdomTree Efficient U.S. Plus International Equity, 2026-03-19, 0.35%): 90%
  US large cap plus about 60% developed-international index futures, $46.7m; Treasuries only
  as collateral, so not a bond stack.
- **SDMF** (Simplify DBi CTA Managed Futures Index, 2026-02-17, 0.35% net): replicates DBi's
  CTA index through swaps and futures with a weekly rebalance, $39m; a cheaper cousin of
  DBMF with no track record, `not filed` for loading purposes.

### 6.2 Bid-ask spreads — the number the shelf's cost model omits

Every ETF must publish its 30-day median bid-ask spread under **Rule 6c-11(c)(1)(v)**. Read
from issuer pages, 2026-08-22/23:

| Ticker | 30-day median spread | Annual net cost on the shelf | Comment |
| --- | ---: | ---: | --- |
| **CTAP** | **0.33%** | 0.10% net fee (0.81% all-in per the repo) | **Spread is 3.3× the displayed net fee** |
| **RSSX** | 0.28% | 0.67% | New fund, thin |
| **SDMF** | 0.24% | 0.35% | Spread is 69% of the annual fee |
| **RSIT** | 0.15% | 0.98% | 3½ months old |
| CTA | 0.14% | 0.75% | |
| RSST | 0.09% | 0.99% | Reasonable for the category |
| MTUM | 0.03% | 0.15% | |
| QUAL | 0.03% | 0.15% | |
| IVLU | 0.02% | 0.30% | |
| SCZ | 0.01% | 0.40% | |
| IEMG | 0.01% | 0.09% | |

Sources: [Simplify CTAP](https://www.simplify.us/etfs/ctap-simplify-us-equity-plus-managed-futures-strategy-etf),
[Simplify SDMF](https://www.simplify.us/etfs/sdmf-simplify-dbi-cta-managed-futures-index-etf),
[Simplify CTA](https://www.simplify.us/etfs/cta-simplify-managed-futures-strategy-etf),
[Return Stacked RSST](https://www.returnstackedetfs.com/rsst-return-stacked-us-stocks-managed-futures/),
[RSIT](https://www.returnstackedetfs.com/rsit-international-stocks-managed-futures/),
[RSSX](https://www.returnstackedetfs.com/rssx-return-stacked-us-stocks-gold-bitcoin/),
iShares product pages.

**The CTAP finding is material and it changes a conclusion.**
`capital-efficiency-and-breadth.md` runs a careful, correct argument that CTAP's fee table
understates its true cost — the swap on affiliated CTA hides a 0.75% expense ratio, taking
all-in from a headline 0.10% to about 0.81%, and to about 0.99% once the waiver lapses on
2026-12-04. That argument is right and it stops one step early. **CTAP also has a 33 bp median
bid-ask spread.** A round trip costs about **66 bp**, and even a one-way purchase held for a
year adds 33 bp to a first-year all-in cost of roughly 0.81%. The page's conclusion — *"neither
the funding rule nor the fee table separates the candidates"* — is drawn from `delta` and the
fee table. **The spread does separate them: 33 bp against RSST's 9 bp is a 24 bp/yr difference
on a one-year hold, on a shelf where the entire fee dispersion among the three wrappers is
18 bp.** For any investor who rebalances, CTAP is the most expensive of the three, not the
cheapest. `src/content/shelf.ts` now carries a `spread` field, populated for the funds whose
Rule 6c-11 disclosure was read here and absent for the rest.

The general point for the site rewrite: **the shelf models `fee − securities lending` and calls
it net cost.** For a fund with a 1 bp spread that is nearly complete. For a fund with a 33 bp
spread and an annual rebalance it is missing the largest term.

---

## CORRECTIONS

Specific things in this repository that are now stale, wrong, or incomplete, with the correct
current value. Ordered by how much they change a decision.

**C-1 — `docs/research/capital-efficiency-and-breadth.md`: CTAP's cost is understated by its
bid-ask spread, and the "no candidate is separated" conclusion does not survive it.**
The page compares CTAP (~0.81% all-in, rising to ~0.99% on 2026-12-04), RSST (0.99%) and MATE
(0.97%) and concludes the fee table does not separate them. **CTAP's 30-day median bid-ask
spread is 0.33%; RSST's is 0.09%** ([Simplify](https://www.simplify.us/etfs/ctap-simplify-us-equity-plus-managed-futures-strategy-etf),
[Return Stacked](https://www.returnstackedetfs.com/rsst-return-stacked-us-stocks-managed-futures/),
read 2026-08-22). A one-way purchase adds 33 bp to CTAP's first-year cost; a round trip adds
66 bp. **The candidates are separated, and CTAP is the dearest of the three, not the
cheapest.** SDMF's spread is 0.24% against a 0.35% fee. Add a spread field to the shelf.

**C-2 — `src/content/shelf.ts`: the Return Stacked shelf is 2 of 8, and the missing one that
matters is RSIT.** **RSIT — Return Stacked International Stocks & Managed Futures ETF**,
inception **2026-05-06**, **0.98%**, **$68.53m**, median spread **0.15%**, equity leg roughly
75% SPDW + 25% MSCI EAFE futures (so a base leg near 1.00 and `delta ≈ 0.00`). It is the
international twin of RSST and it lands directly on the intersection of two live repository
recommendations (add AVDV; trend is the best-supported financed diversifier). Also missing:
**RSSX** (US Stocks & Gold/Bitcoin, 2025-05-29, 0.67%, $70.59m, spread 0.28%), RSSY, RSBT,
RSBY, RSBA. All six are now on the shelf, at the fees their own Forms 497K dated 2026-04-27
(RSIT 2026-05-05) print, and none carries a measured structure. Source:
[returnstackedetfs.com](https://www.returnstackedetfs.com/), read 2026-08-22.

**C-3 — Section 6 of everything: two brokers are introducing a $100-per-trade fee and the
repository's cost model has no broker in it.** Fidelity began charging **$100 per purchase**
on ETFs from non-participating issuers on **2026-06-01**; Schwab has confirmed a comparable
programme for **year-end 2026** claiming up to 15% of issuer fee revenue. On a $10,000
purchase that is **100 bp**. The issuers most exposed are the small ones — Simplify, Tidal
(Return Stacked), Brookmont, Man, iMGP — which is most of the diversifier shelf.
**I could not read Fidelity's live list (HTTP 403); verify before publishing.** Sources:
[RIABiz 2026-05-07](https://riabiz.com/a/2026/5/7/schwab-is-joining-fidelity-in-law-of-the-jungle-shakedown-of-etfs-with-vanguard-not-immune-to-claim-up-to-15-of-fee-revenues-and-charge-investors-100-per-trade-for-using-non-compliant-etf-managers),
[ETF Investments](https://etfinvestments.substack.com/p/fidelity-just-added-100-fees-to-120).

**C-4 — `docs/research/current-regime-and-pricing.md` §1.3: "No term-premium estimate is
supported by this cache" is wrong.** Two estimates exist and agree. **Kim–Wright 10-year term
premium = +0.8393% at 2026-08-14**, from
[FRED THREEFYTP10](https://fred.stlouisfed.org/series/THREEFYTP10) — 9,555 daily rows from
1990-01-02, fetched 2026-08-23, in the same FRED contract the page already uses.
**NY Fed ACM ≈ +0.80% at 2026-08-13.** Both are materially positive for the first time in
about five years, which means the page's +0.82 pp 10y−3m slope is **nearly all term premium**
— a conclusion it currently declines to draw. Change the label from `unresolved` to measured.

**C-5 — `docs/research/structural-and-tax-edges.md` and `src/content/placement.ts`: the
mandatory Roth catch-up rule for 2026 is missing, and it shrinks the account the trend
wrapper is supposed to live in.** SECURE 2.0 §603 is effective for taxable years beginning in
**2026**: per [IRS Notice 2025-67](https://www.irs.gov/pub/irs-drop/n-25-67.pdf), the
§414(v)(7)(A) threshold rose from $145,000 to **$150,000**, and a participant whose **2025 FICA
wages from the sponsoring employer exceeded $150,000 must make every 2026 catch-up dollar as
designated Roth**. That removes $8,000–$11,250/yr of *pre-tax* capacity for a high earner over
50. `capital-efficiency-and-breadth.md` places the stacked wrapper in the pre-tax account and
already warns that a 30% wrapper consumes nine tenths of a one-third pre-tax account; this rule
makes that account grow more slowly, every year, for exactly this investor.

**C-6 — `docs/research/structural-and-tax-edges.md`: the §415(c) limit is not recorded.**
**$72,000 for 2026**, up from $70,000 (Notice 2025-67, line 21–22). It is the ceiling on the
mega-backdoor Roth and the repository discusses shelter capacity extensively without carrying
it.

**C-7 — `docs/research/alternative-sleeves-audit.md` §3: "positive in 1 of 13 worst-decile
equity months" should be 2 of 12 on data through 2026-08.** On the 120-month
CBBTCUSD/SP500 panel I computed 2026-08-23, bitcoin was positive in **2 of the 12** worst
equity months (2019-05 at +62.2%, and **2026-03 at +2.2%** against the S&P 500's −5.1%), with a
mean of **−5.0%**, not −7.51%. **The 2026-03 observation is new and it is a point in bitcoin's
favour.** The verdict does not change — but a page that measures this precisely should carry
the updated count. Related: the 3-year *daily* correlation is now **+0.170**, the lowest on the
panel, which is below the page's own +0.2 reopening threshold; the trigger is still not met
because the window contains no recession and the 3-year monthly reading is +0.363.

**C-8 — `docs/research/alternative-sleeves-audit.md` §5: the cat bond ETF is now $88.44m, and
that is the only figure in that section this scan changes.** AUM went ~$12m (Aug 2025) →
$25.3m (2025-11-26) → **$88.44m (2026-08-22)**, against the audit's $88.2m at 2026-08-20 —
two readings two days apart, both current for their date. Average daily volume was up ~672%
Sept–Nov 2025. The ticker is `ILS`, which is what the audit already uses; `ROAR` was
pre-launch coverage only and is worth recording just so a reader who meets it can place it.
The fee is the audit's and is not restated: 2.65% gross, 1.58% net under a cap to
2027-04-30, and 2.00% actually paid. The price objection is untouched and the reopening
condition is still a spread level, but "retail history is short" is nine months shorter.
Sources:
[ETFGI](https://etfgi.com/news/stories/2025/04/brookmont-capital-management-launches-first-us-listed-catastrophe-bond-etf),
[Artemis](https://www.artemis.bm/news/brookmont-cat-bond-etf-gains-momentum-as-trading-volume-rises-assets-surpass-25m/),
[StockAnalysis](https://stockanalysis.com/etf/ils/).

**C-9 — `src/content/shelf.ts` carries no AUM field and no inception date field.** For a shelf
whose own `live-managed-futures.md` measures **52% attrition of the 2019 managed-futures cohort
inside 6.5 years**, size and age are the two variables most predictive of the failure mode the
repository has actually documented. Four shelf funds are under $50m: **MATE $39.76m**,
**SDMF $39.16m**, **JPFP $32.75m**, and (off-shelf but discussed) **ILS $88.44m**. A verdict
that a fund is a candidate should print its size.

**C-10 — IVLU and EFV: the shelf's 31 bp is right for both, and an aggregator reading is not.**
Read from the funds' own summary prospectuses, both dated 2025-11-28, on 2026-08-24:
**IVLU** files 0.30% management, 0.01% other expenses, **0.31% total**
([Form 497K](https://www.sec.gov/Archives/edgar/data/1100663/000119312525302146/d90140d497k.htm));
**EFV** files 0.31% management, 0.00% other expenses, **0.31% total**
([Form 497K](https://www.sec.gov/Archives/edgar/data/1100663/000119312525302176/d949816d497k.htm)).
Neither has a waiver line. A 0.30% quote for IVLU is its management fee with the other-expenses
line dropped, and 0.33% is not a number in EFV's fee table at all. **Do not amend the shelf on
either.** The general lesson is worth more than the two numbers: an aggregator's "expense ratio"
and a fee table's total annual fund operating expenses are different fields, and they diverge by
exactly the other-expenses line. Every other fee among the 59 verified exactly.

**C-11 — `src/content/shelf.ts`: three funds carried `null` where a public fee exists.** All
three were read from the funds' own summary prospectuses on 2026-08-24 and are now on the shelf.
**GWX = 0.40%** total, no waiver, per its 497K dated 2026-01-31
([filing](https://www.sec.gov/Archives/edgar/data/1168164/000119312526031217/d833468d497k.htm)) —
the registrant now styles it *State Street* SPDR S&P International Small Cap ETF.
**DFEV = 0.46% gross less a 0.03% waiver = 0.43% net**, the waiver running only to **2027-02-28**,
per its 497K dated 2026-02-28
([filing](https://www.sec.gov/Archives/edgar/data/1816125/000181612526000066/c497k.htm)); a bare
0.43% hides an expiry date. **TIP = 0.18%** total, per its 497K dated 2026-02-27
([filing](https://www.sec.gov/Archives/edgar/data/1100663/000119312526081826/d191245d497k.htm)).
One arithmetic loose end travels with the last of these: TIP's `netCostBp` is 17.92 against an
18 bp fee, which implies 0.08 bp of securities lending nobody has read. The gap is the size of
the unread term, not a measurement of it, and `securitiesLendingBp` stays null rather than
carrying a number obtained by subtraction.

**C-12 — `docs/research/current-regime-and-pricing.md` §1.7: gold is at the 98.5th percentile
of its real price *and* 17% below its own January high.** Gold futures set a record
**$5,542.40 on 2026-01-29**; spot was **~$4,587/oz on 2026-08-21**
([Fortune](https://fortune.com/article/current-price-of-gold-08-21-2026/)). The page's
percentile is correct and its price is correct; the drawdown is missing, and "expensive and
falling" is a different sentence from "expensive."

**C-13 — Nothing in the repository carries a dollar level, and a tenth of 2025's international
outperformance was the dollar.** Broad trade-weighted dollar index
([FRED DTWEXBGS](https://fred.stlouisfed.org/series/DTWEXBGS)) = **118.9028 at 2026-08-14**,
**−1.44% over one year**, **−0.97% over three**, at the **57th percentile of its ten-year
range** (min 106.49, max 130.04), computed 2026-08-23. MSCI EAFE beat the S&P 500 by ~13 pp in
2025 and **roughly 10 pp of that was currency**. `currency-and-the-international-sleeve.md`
should carry the level and the percentile, because the 2025 result is unreadable without them.

**C-14 — `docs/research/valuation-and-the-allocation.md` should carry the fact that
forward-looking models have already collected the international gap.** Vanguard's VCMM at
**2026-06-30** puts US equities at **4.2–6.2%**, developed ex-US at **4.5–6.5%**, and
**emerging markets at 2.0–4.0%** — EM *below* the US, cut by 1.6 pp in one quarter after EM
returned +33.6% in 2025
([Vanguard VEMO](https://corporate.vanguard.com/content/corporatesite/us/en/corp/vemo/vemo-return-forecasts.html),
read 2026-08-23). A 1.70× valuation gap and a 0.3 pp expected-return gap are both true, and the
site rewrite must not present the first as though it were the second. This *supports* the
page's existing conclusion; it is missing evidence, not a contradiction.

**C-15 — `docs/research/factor-products.md` and the managed-futures shelf: FFUT is missing and
it is now among the largest funds in the category.** **Fidelity Managed Futures ETF**,
inception **2025-06-05**, **$346.23m**
([etf.com](https://www.etf.com/sections/etf-watch/fidelity-adds-managed-futures-etf-growing-lineup),
[StockAnalysis](https://stockanalysis.com/etf/ffut/)). Its current fee table, read from the
summary prospectus dated 2026-05-30 on 2026-08-24, is **0.80% management plus 0.02% other
expenses = 0.82% gross, less a 0.02% reimbursement, for 0.80% net**
([Form 497K](https://www.sec.gov/Archives/edgar/data/1898391/000189839126000077/filing11811.htm)).
The 0.80% is an **expense cap running to 2027-05-31**, not a plain waiver, and FDS may recoup
within the fiscal year anything it reimbursed. Two net-asset figures for this fund are in the
repository and both are current for their date: **$255.9m at 2026Q2**
(`trend-marginal-value.md`, second census table) and **$346.23m at 2026-08-22**.
Category context the shelf also lacks:
managed-futures ETFs total roughly **$6bn across ~13 funds as of March 2026**, of which DBMF
alone is $4.0bn — so the rest of the shelf's trend funds are competing for about $2bn, in a
category whose documented failure mode is closure.

**C-16 — the crypto table's fees did not move, and the aggregator readings that said they had
are wrong.** StockAnalysis showed HODL at 0.25% and EZBC at 0.29% on 2026-08-22. Both trusts'
own Q2-2026 Forms 10-Q, read on 2026-08-24, say otherwise. **HODL's Sponsor Fee is 0.20%**, and
the filing states the waiver of that fee on the first $2.5bn ran "from November 25, 2024 through
July 31, 2026" and that "[a]fter July 31, 2026, the Sponsor Fee will be 0.20%"
([10-Q filed 2026-08-13](https://www.sec.gov/Archives/edgar/data/1838028/000093041326002505/c117299_10q-ixbrl.htm)) —
so the waiver expiry the audit already flagged takes the fee from an effective zero to 0.20%,
not to 0.25%. **EZBC's Sponsor fee accrues "at an annualized rate equal to 0.19%"**
([10-Q filed 2026-08-14](https://www.sec.gov/Archives/edgar/data/1992870/000114036126033208/ef20077161_10q.htm)).
**The audit's table stands unamended.** What is genuinely new is **IBIT at $58.78bn** against the
$43.4bn the audit records at 2026-06-30 — a different date, not a different fact, and mostly
mark-to-market. The rule this entry earns: a 1933-Act trust's fee is in its own 10-Q, and a
sponsor-fee waiver is the field an aggregator is most likely to get wrong.

**C-17 — `src/content/shelf.ts` name fields now embed a benchmark-provider brand that changed
once and could change again.** The "Vanguard Morningstar …" names are **correct** — Morningstar
completed its $375m acquisition of CRSP in February 2026, Vanguard announced the renaming of 13
US equity index funds on 2026-04-29, and it took effect **2026-07-29** with no change to
methodology, holdings, fee or ticker
([Vanguard](https://corporate.vanguard.com/content/corporatesite/us/en/corp/who-we-are/pressroom/press-release-vanguard-to-update-names-of-us-equity-index-funds-tracking-morningstar-indexes-042926.html),
[Morningstar](https://newsroom.morningstar.com/news/news-details/2026/Morningstar-Reaches-New-Milestone-in-the-CRSP-Acquisition-Rebranding-CRSP-Market-Indexes-to-Morningstar-Indexes/default.aspx)).
This is not an error to fix; it is a note to add, because a reader will assume it is one.

**C-18 — Structural change the repository has not registered: Dimensional can now issue ETF
share classes of its mutual funds** (SEC exemptive order, **2025-11-17**; first active manager,
second ever). Substantially identical applications from other managers will follow. If a DFA
mutual fund gains an ETF share class, its capital-gain distributions fall toward the ETF's, and
the ETF-versus-mutual-fund placement arithmetic in `structural-and-tax-edges.md` and
`placement.ts` becomes an empirical question rather than a structural one. No shelf fund is
affected yet. Sources:
[Dimensional](https://www.dimensional.com/us-en/newsroom/dimensional-receives-sec-approval-for-etf-share-classes),
[40 Act Blog](https://40actblog.sewkis.com/blog/sec-issues-order-for-dfa-exemptive-application-opening-the-door-to-etf-share-classes).

**C-19 — Open item with a date attached: JPFP's first Form N-PORT is still not filed as of
2026-08-23.** EDGAR shows J.P. Morgan Exchange-Traded Fund Trust (CIK 0001485894) filing
N-PORT-P batches on 2026-06-26 and 2026-07-28, with filings through 2026-08-18 and no JPFP
series report. `capital-efficiency-and-breadth.md`'s stated due dates of **2026-08-29 or
2026-09-29** stand, and the earlier is six days away. `delta` remains uncomputable. This is the
cheapest open item in the corpus.

---

## What could not be verified

Stated plainly so nothing here is read as more complete than it is.

1. **Fidelity's live service-fee ETF list** — `fidelity.com/trading/etfs/service-fee-etfs`
   returns HTTP 403 to automated fetches. Whether any shelf issuer is on it is **unknown**, and
   it is the highest-value open question in this scan.
2. **A fresh literature sweep on valuation timing** (Goyal–Welch–Zafirov II; Siegel;
   Straehl–Ibbotson). The session's web-search budget was exhausted. The repository's own §2.3
   and §2.4 cover this ground and nothing found here contradicts them.
3. **GMO and Research Affiliates current CMA vintages** — GMO's public forecast page returned
   404. Only Vanguard's June 2026 VCMM running was obtained.
4. **An exhaustive census of buffered / defined-outcome / derivative-income launches** since
   mid-2025. Not attempted at depth. The absence of a finding in §2.4 is a coverage gap, not a
   null result.
5. **NY Fed ACM term premium from the NY Fed's own file** — read from aggregators citing the
   release, not from the primary CSV. Medium confidence. Kim–Wright is primary.
6. **2026 crypto market-structure legislation** and any wash-sale extension to digital assets.
   Confirmed the OBBBA made no change; did not confirm nothing else did.
7. **Bid-ask spreads for KMLM, MATE, JPFP, NTSX, GDE, ILS, and the Avantis and Dimensional
   funds** — their issuer pages did not yield the Rule 6c-11 field to automated parsing. Every
   one of these publishes it and it is worth collecting properly.
8. **The six Return Stacked funds' and FFUT's holdings.** Their fees and sizes are filed or
   issuer-published and are now on the shelf; not one of them has had a Form N-PORT read here,
   so none has a computed `delta`, and RSIT's "75% SPDW + 25% MSCI EAFE futures" is an
   issuer-page description rather than a filed measurement. **No structure claim about any of
   the seven is verified.**
