# Discovery sweep, September 2026: what has not been screened

**Question.** Which return sources, products and constructions that this repository has not
screened exist as of 2026-09-02, and which of them could change the published position of
RSST 30 / VTI 19 / VTV 15 / VXUS 16 / AVDV 10 / IDMO 5 / AVES 5?

**Decision it informs.** Which candidates deserve a frozen specification next, and which
can be set aside with the reason attached. Out of scope: re-testing anything the
[alternative sources audit](alternative-sleeves-audit.md) or the
[market scan](market-scan-2026.md) already measured, and the equity share itself.

**Status: `exploratory`.** Product facts were read on 2026-09-02 from issuer pages and SEC
filings unless a line says otherwise. The measured figures below come from each fund's own
Form N-PORT Item B.5 monthly total return through the repository's
[`data/nport.py`](../../research/src/portfolio_edge/data/nport.py); no specification was
frozen before the numbers were seen, the windows are the funds' whole filed lives, and the
comparisons are hypothesis-bearing choices that owe a ledger entry. Nothing here is
promoted.

## Conclusion

The sweep found one genuinely new financed return source with a filed record, one value
definition the held value funds do not span, and one financing fact the repository has
been treating as unobservable. Everything else launched since mid-2025 is a known mechanism
in a new box, a speculation with a dividend attached, or a product whose live record has
already answered the question.

1. **Cross-asset carry is the only new candidate that meets all three conditions**: it is
   economically distinct from equity, value, momentum and trend; it is financed on top of
   equity or bonds in RSSY and RSBY at 99 to 101 bp; and its payer, anyone who wants price
   certainty or borrows in a low-rate currency, has a reason to keep paying. Its live record
   is the problem. The carry position inside RSSY, read as RSSY minus VTI, returned −5.3%
   a year at 13.3% volatility over its 22 full filed months (2024-06 to 2026-03), with a
   correlation of +0.31 [−0.13, +0.65] to the trend position inside RSST and +0.21
   [−0.23, +0.58] to DBMF. That is a good correlation and a bad return, and at this
   sample the smallest premium a t-statistic of 2 could confirm is 19.6% a year, so the
   record cannot sign it either way. Admit for measurement with the premium carried as an
   input, exactly as the [stacking page](stacking-and-effective-breadth.md) does for trend.
2. **Intangible-adjusted value (Sparkline ITAN, 50 bp, five filed years)** is the one
   equity idea that could raise the effective number of bets rather than add a sixth
   correlated value fund. Its exposure to the held value funds is unmeasured and is the
   whole question.
3. **Box spreads make the financing rate observable.** BOXX holds $14.6bn of them at 19 bp,
   returned 4.70% a year since 2022-12 with a correlation of 0.00 to VTI, and pays it as
   price rather than as interest. The same market lets a margin account borrow near the
   Treasury rate. The recommendation says no issuer discloses fund-level financing; a box
   rate does not disclose RSST's, but it prices the alternative to it, which is the number
   that decides whether a 99 bp stacked fund or a self-built one is cheaper.

Three things the sweep closes. **Bank quantitative-strategy baskets** (Simplify QIS) lost
57% in three years, with six monthly losses above 8% since 2025-07; the audit called
the cost stack the finding, and this is worse: the strategies themselves failed together.
**Defensive equity** (USMV) is a beta of 0.62 with a fee, and cash does the same job for
nothing. **Bitcoin yield products** (covered calls at 27% distribution rates, staking at
about 2.6%, a futures basis now below the two-year Treasury) attach an income line to a
speculation without changing what it is.

No AQR ETF exists as of the read date. The 2025 to 2026 launches from Dimensional, Avantis,
Alpha Architect, Cambria, Simplify, Fidelity and JPMorgan are cost cuts, tax structures and
new boxes for held mechanisms; the two that touch a live decision are Fidelity's AAA CLO
fund at 20 bp and PIMCO's stocks-plus-bonds fund at 18 bp.

## Verified facts, measured figures and interpretation, kept apart

**Verified on the issuer page or in a filing (read 2026-09-02).**

| Fund | Fee | Inception | Net assets (date) | Issuer-published return | Source |
| --- | ---: | --- | --- | --- | --- |
| RSSY, US Stocks & Futures Yield | 0.99% | 2024-05-28 | $94.72m (2026-08-31); spread 0.12% | NAV 1y +36.30%, since inception +12.86%/yr vs S&P 500 TR +20.38% / +19.31%, to 2026-08-31 | [issuer](https://www.returnstackedetfs.com/rssy-return-stacked-us-stocks-futures-yield/) |
| RSBY, Bonds & Futures Yield | 1.01% | 2024-08-20 | $56.29m (2026-08-31); spread 0.22% | NAV 1y +14.13%, since inception −3.00%/yr (cumulative −6.00%) vs Bloomberg US Aggregate +1.89% / +2.33%, to 2026-08-31 | [issuer](https://www.returnstackedetfs.com/rsby-return-stacked-bonds-futures-yield/) |
| USMV, MSCI USA Min Vol | 0.15% | 2011-10-18 | $23,007.75m (2026-06-30) | NAV 10y 9.59%/yr vs index 9.70%; 2022 −9.35%; 3y beta 0.49, 3y standard deviation 9.31% | [fact sheet](https://www.ishares.com/us/literature/fact-sheet/usmv-ishares-msci-usa-min-vol-factor-etf-fund-fact-sheet-en-us.pdf) |
| PRIV, SPDR SSGA IG Public & Private Credit | 0.70% gross (FAQ); the product page shows 0.55%, and which is the current net figure is not stated | 2025-02-26 | $816.10m (2026-09-01) | NAV 1y 3.40%, since inception 3.59%/yr to 2026-07-31; 30-day SEC yield 4.64%; option-adjusted duration 5.86y; Apollo-sourced private paper 21.4% (13.33% asset-backed, 8.09% corporate) at 2026-08-31; the FAQ's target range is 10 to 35% | [product page](https://www.ssga.com/us/en/individual/etfs/spdr-ssga-ig-public-private-credit-etf-priv), [FAQ](https://d1e00ek4ebabms.cloudfront.net/production/uploaded-files/priv-faq-f6b152e6-a43e-4337-a805-93134472889b.pdf) |
| BIZD, VanEck BDC Income | management 0.40% + other 0.02% + acquired fund fees 10.75% = 11.17% total (latest fee table located, June 2024 497K) | 2013-02-11 | not verified today | not verified today | [497K](https://www.sec.gov/Archives/edgar/data/1137360/000113736024000444/vebdcincomeetfsumprobizdju.htm) |
| ILS, Brookmont Catastrophic Bond | 1.58% net (the audit's 2.65% gross under a cap to 2027-04-30 stands) | listed 2025-04 | $95.91m (2026-09-01, aggregator; a second aggregator shows $34.9m and is wrong) | issuer page carries no performance table | [ilsetf.com](https://ilsetf.com/), [aggregator](https://stockanalysis.com/etf/ils/) |
| BOXX, Alpha Architect 1-3 Month Box | 0.2449% gross, 0.1949% net | 2022-12-27 | $14,604.84m (2026-09-01) | NAV since inception 4.70%/yr, 1y 4.06% to 2026-08-31; distributions: none 2023, $0.29 in 2024-08, none 2025-12 | [issuer](https://funds.alphaarchitect.com/boxetf/) |
| SVOL, Simplify Volatility Premium | 0.66% | 2021-05-12 | $531.3m (2026-08-31) | NAV since inception 8.04%/yr, 1y 16.02%, 3y 5.81% to 2026-08-31; distribution yield 21.22%; −0.2x to −0.3x VIX with a VIX-call budget | [issuer](https://www.simplify.us/etfs/svol-simplify-volatility-premium-etf) |
| QIS, Simplify Multi-QIS Alternative | 1.21% | 2023-07-10 | $42.07m (2026-08-31); spread 0.88% | NAV since inception −56.99% cumulative, 1y −50.08%, to 2026-07-31 | [issuer](https://www.simplify.us/etfs/qis-simplify-multi-qis-alternative-etf) |
| ITAN, Sparkline Intangible Value | 0.50% | 2021-06-28 | $117.45m (2026-09-01) | NAV since inception 12.95%/yr, 1y 33.82%, 3y 23.55%/yr to 2026-08-31 | [issuer](https://etf.sparklinecapital.com/itan/) |
| DTAN, Sparkline International Intangible Value | 0.55% | 2024-09-09 | $22.18m (2026-09-01) | NAV since inception 19.74%/yr, 1y 18.07% to 2026-08-31 | [issuer](https://etf.sparklinecapital.com/dtan/) |
| EMXC, MSCI Emerging Markets ex China | 0.25% | 2017-07-18 | $26,057.40m (2026-06-30) | NAV 1y 66.23% vs index 63.11%; 2025 +34.93%; 3y beta 0.96 | [fact sheet](https://www.ishares.com/us/literature/fact-sheet/emxc-ishares-msci-emerging-markets-ex-china-etf-fund-fact-sheet-en-us.pdf) |
| MEMA, Man Active Emerging Markets Alternative | 0.85% unitary (497K) | 2025-12-16 | about $11.9m (aggregator, unverified) | issuer page: YTD +22.52% at 2026-09-01; a 130/30 EM equity long-short built with machine-learning models | [497K](https://www.sec.gov/Archives/edgar/data/2065379/000119312525317205/d92531d497k.htm), [issuer](https://www.man.com/products/man-active-emerging-markets-alternative-etf) |
| BTCI, NEOS Bitcoin High Income | 0.99% total | 2024-10-16 | $1,299.76m (2026-08-31) | NAV since inception +5.58%/yr (cumulative +10.70%) to 2026-08-31; 1y −40.91% to 2026-06-30; distribution rate 26.73% | [issuer](https://neosfunds.com/btci/) |
| ETHB, iShares Staked Ethereum Trust | 0.25% sponsor fee, waived to 0.12% on the first $2.5bn for twelve months from 2026-03-12; staking rewards carry an 18% service fee | 2026-03-12 | $795.5m (market scan, 2026-08-22) | staking rewards earned to 2026-06-30: $1,194,785 (10-Q) | [424B3](https://www.sec.gov/Archives/edgar/data/2099103/000143774926007771/iset20260311_424b3.htm) |
| SPLS, PIMCO US Stocks PLUS Active Bond | 0.18% | 2026-01-15 | $45.50m (2026-09-01, aggregator) | structure per aggregator: about 98% in IVV plus bond exposure through derivatives; not read from a filing | [PIMCO release](https://www.pimco.com/us/en/about-us/press-release/2026/pimco-launches-new-active-etf) (release page returned 403; facts from [aggregator](https://stockanalysis.com/etf/spls/)) |
| FAAA, Fidelity AAA CLO | 0.20% gross, management fee waived for the first twelve months | 2026-02-12 | not verified | at least 80% in AAA CLOs | [Fidelity](https://newsroom.fidelity.com/pressreleases/fidelity-investments-expands-active-etf-lineup-with-two-clo-etfs-faaa-fclo/s/56c6cef7-ac3f-49e3-b4ee-37fefba11371) |

Other facts read today. The Return Stacked family is still ten funds; RSST holds $528.93m,
RSIT $73.39m, RSSX $75.61m, RSBT $152.57m and RSBA $52.15m at 2026-08-31
([issuer](https://www.returnstackedetfs.com/)). AQR's fund site lists no ETF and its
only launch item is the June 2025 Fusion mutual-fund series ([funds.aqr.com](https://funds.aqr.com/)).
Dimensional listed DFMC as the first active ETF share class in March 2026 and announced
fee cuts of 9% asset-weighted from 2026-11-01. Fidelity's $100 purchase fee list names
Roundhill, Renaissance, Convergence, Hedgeye and similar issuers in an article of 2026-08-31;
the live list itself still could not be read.

**Catastrophe bond pricing, from the Artemis Q2 2026 report (PDF read 2026-09-02).** The
average multiple of Q2 2026 issuance was 2.29, down 0.32 on the quarter and 0.85 on Q2
2025's 3.14, against the Q2 record of 4.82 in 2023; the average spread above expected loss
was 3.74%, the first reading under 4% in twenty quarters, and the average spread 6.63%.
The multiple has sat below 3 for four consecutive quarters. Plenum's market yield was
9.29% at 2026-07-31 against 10.81% a year earlier (via Artemis); the August figure was not
yet published at the read date. The audit's reopening boundary of 3.5x is farther away
than when it was written.

**Measured here, from Item B.5 monthly returns.** Exploratory, whole filed life, monthly
resolution.

| Measurement | Window | Result |
| --- | --- | --- |
| Carry position, RSSY minus VTI | 2024-06 to 2026-03, 22 months | −5.3%/yr arithmetic, 13.3% vol, t −0.54, cumulative −10.6% |
| Trend position, RSST minus VTI, same window | same | −1.7%/yr, 11.2% vol; DBMF +7.35%/yr; VTI +13.4%/yr |
| Correlation of the carry position with the trend position | same | +0.31 [−0.13, +0.65] |
| Correlation of the carry position with DBMF; with VTI | same | +0.21 [−0.23, +0.58]; −0.19 [−0.57, +0.25] |
| Correlation of the trend position with DBMF (control) | same | +0.84 [+0.64, +0.93] |
| Bond-stack carry position, RSBY minus RSBT plus the trend position, against the equity-stack carry position | 2024-09 to 2026-03, 20 months | +0.999: one carry model sits inside both funds, so RSBY adds no second reading |
| Carry in the three stress months | 2025-03, 2025-04, 2026-03 | −3.6%, −6.3%, +12.1% while VTI did −5.9%, −0.7%, −5.0% and the trend position −1.8%, −5.4%, −2.7% |
| USMV against VTI | 2022-03 to 2026-03, 49 months | beta 0.62, up-beta 0.56, down-beta 0.65; cumulative +34.9% vs +54.2% |
| QUAL; DUHP against VTI | same | QUAL beta 0.98, down-beta 1.07, 2022-01 to 09 −27.7% vs VTI −24.9%; DUHP beta 0.94, down-beta 0.95 |
| USMV in 2022-01 to 2022-09; in 2020 Q1 | | −17.4% vs VTI −24.9%; −17.2% vs −20.9% |
| ILS | 2025-04 to 2026-06, 15 months | +6.9%/yr, 1.1% vol, no negative month; correlation with VTI +0.45 [−0.17, +0.81] on 12 overlapping months |
| SVOL against VTI | 2021-06 to 2026-03, 59 months | correlation +0.74 [+0.59, +0.83], beta 0.67; 8.8%/yr at 14.1% vol |
| QIS | 2023-07 to 2026-06, 36 months | cumulative −56.6%, matching the issuer; beta 0.37 to VTI; monthly −12.1%, −9.9%, −14.1%, +13.9%, −16.3%, −12.2% from 2025-11 to 2026-06 |
| BOXX | 2022-10 to 2026-06, 44 months | 4.28%/yr, 0.39% vol, correlation with VTI 0.00 |

**Interpretation.** The carry correlation is the useful number and the carry return is
noise: a 22-month mean at 13% volatility resolves nothing under about 20% a year. The
0.999 between the two Return Stacked carry positions is a consistency check on the reading,
and a warning that buying both funds buys one bet. USMV's protection is a beta cut, and a
down-beta above its up-beta is the concave shape the audit measured for low-volatility
strategies. ILS's 1.1% volatility is the mark, not the risk; a fund of hurricane bonds
whose worst month is +0.32% has not yet met a hurricane, and its correlation to anything is
uninformative until it does. QIS's record is the strongest evidence in this sweep about
bank-sourced alternative premiums: they were crowded, correlated and sold to retail at the
top.

## Classified table

Read date 2026-09-02 for every fee, inception and net-asset figure; sources are in the
table above.

| Mechanism | Who pays and why they keep paying | Access vehicle | Distinct from what is held | Plausible net return and how | Shared failure mode | Verdict | Instrument a measurement needs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Cross-asset carry (long high-yielding, short low-yielding futures across rates, FX, commodities, equity indices) | Hedgers who want price certainty and borrowers in low-rate currencies; the payment is the roll, and it persists because hedging demand is structural | RSSY (0.99%, 2024-05-28, $94.72m); RSBY (1.01%, 2024-08-20, $56.29m) | Yes: correlation +0.31 to the trend position, +0.21 to DBMF, −0.19 to VTI, measured | Published diversified carry Sharpe ratios above 1 in sample ([Koijen, Moskowitz, Pedersen, Vrugt 2018](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2298565)); halve for publication decay and costs gives 3 to 5% a year at 10% vol before a 99 bp fee; the live fund shows −5.3% a year and cannot sign it | Currency carry is short volatility; it lost with equity in 2025-04 and with trend in the same month. Fund closure at $95m | Admit for measurement, premium as an input | 36 or more filed months of RSSY, RSST, RSBT, VTI, BND from N-PORT; a long carry series (KMPV replication needs futures data the repository does not hold) |
| Carry-conditioned trend | Same payers as trend and carry | None dedicated; RSSY plus RSST approximates it | Partly: it is a signal rule, not a source | [Research Affiliates 2026](https://www.researchaffiliates.com/insights/publications/articles/1107-should-trend-follow-carry-lessons-from-bonds-gold-and-2022) on 83 contracts 1989 to 2025 reports carry filtering improved plain trend in the last decade; [Tzotchev 2024](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4726362) reports strong diversification between market-neutral carry and trend | A filter fitted to the decade that included 2022 | Unresolved: no vehicle, no independent series | Futures data |
| Intangible-adjusted value ([Eisfeldt, Kim, Papanikolaou 2022](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3720983)) | The same investors who overpay for glamour, if value is real; the payment is the book-value error on intangible-heavy firms | ITAN (0.50%, 2021-06-28, $117.45m); DTAN (0.55%, 2024-09-09, $22.18m) | Unmeasured, and the question: it reclassifies technology as value, so its exposure to VTV and AVDV may be low or negative | 3y NAV 23.55%/yr against a market that did about the same; no factor decomposition exists here, so no figure | It may be growth exposure under a value label; capacity at $117m | Admit for measurement | N-PORT 2021-07 to 2026-06 for ITAN and VTV; French five factors plus momentum |
| Machine-learning return prediction ([Kelly, Malamud, Zhou 2024](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13298)) | Slow information processing, if it exists | AIEQ (0.75%, 2017-10) is the only long-lived retail product | The paper's timing model is distinct; the product is equity | AIEQ about +100% since inception against about +200% for the S&P 500 (aggregator); no retail product has beaten its index over its life | Complexity fits history | Reject as implementable now | A live product with five filed years |
| Seasonality; betting against correlation ([Keloharju, Linnainmaa, Nyberg 2016](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12398); [Asness, Frazzini, Gormsen, Pedersen 2020](https://www.sciencedirect.com/science/article/abs/pii/S0304405X1930176X)) | Institutional calendar flows; borrowing-constrained investors | None retail; both are long-short | Yes on paper | Unquotable without a vehicle | Long-short costs | Reject on access; a missing vehicle is an implementation finding, not evidence of absence | A retail long-short vehicle |
| Trend on alternative data | Unclear | Nothing found in 2024 to 2026 | | | | Not found | |
| Defensive equity, minimum volatility | Nobody pays; it is a beta cut | USMV (0.15%, 2011-10-18, $23.0bn) | No: beta 0.62 to VTI, down-beta 0.65 above up-beta 0.56 | Index minus 0.15%, times 0.6 | Same drawdown state as equity, smaller; gave up 19 pp of 54 over 49 months for 7.5 pp less loss in 2022 | Reject as a valuation hedge: cash does the same for nothing | None |
| Quality / profitability as a hedge | Rejected premium (decision 0005) | QUAL (0.15%), DUHP (0.20%), both on the fund list | No: down-betas 1.07 and 0.95 | Not a hedge at any price | Lost more than VTI in 2022 | Reject as defensive; unchanged as a factor | None |
| Private credit, IG blend | Borrowers outside bank appetite; rating-constrained holders | PRIV (0.70% gross, 2025-02-26, $816m) | No: 79% public IG with 5.9y duration, the instrument the audit rejected; 21% dealer-marked paper | 30-day SEC yield 4.64%; 1y NAV 3.40% | Duration plus credit; marks supplied by the seller of the paper under a firm-bid contract | Reject as repackaging; reopen if private share passes 50% and duration is hedged | Holdings-level marks against a public-loan index |
| BDC equity | Middle-market borrowers, through 1x to 2x financed loan books | BIZD (11.17% all-in including 10.75% acquired fees) | Unmeasured here; listed BDCs are credit with equity beta | Loan yield minus two fee layers minus loss rate | Credit default state, with a listed-equity discount on top | Reject on cost stack; unmeasured on correlation | N-PORT 2019 to 2026 against VTI and a loan index |
| AAA CLO | Rating-constrained holders (audit §6) | FAAA (0.20%, 2026-02-12, fee waived twelve months); JAAA on the audit | Already admitted by the audit | Audit's figures | No liquidity-crisis record | Note for the fund list: the first 20 bp large-issuer product | The audit's next test |
| Catastrophe risk | Insurers with statutory capital constraints | ILS (1.58% net, 2.65% gross, $95.9m) | Yes in mechanism; 1.1% measured vol is a pricing artefact | Multiple 2.29x, spread over expected loss 3.74%, market yield 9.29% at 2026-07-31; net of 1.58% and a 2% actual cost, about 1 to 2% over cash before a loss year | Hurricane; the fund has not met one | Unchanged: wait; the audit's 3.5x boundary stands and is farther off | Weekly multiple; a hurricane season |
| Box-spread yield and financing | Option market makers and hedgers borrowing against collateral pay a little over the Treasury rate | BOXX (0.19%, 2022-12-27, $14.6bn); selling an SPX box in a margin account | It is cash, and a financing rate; not a return source | 4.70%/yr since inception, paid as price and taxed at sale; N-PORT 4.28%/yr at 0.39% vol | Tax treatment of the structure changing; SPX option liquidity | Admit as implementation, taxable third's cash and as the financing benchmark | Implied box rate series against 3-month bills and against RSST's implied financing from its filed returns |
| Volatility premium, short VIX | Buyers of crash insurance | SVOL (0.66%, 2021-05-12, $531m) | No: +0.74 to VTI, beta 0.67 | 8.0%/yr since inception at 14% vol, most of it equity | Equity crash | Reject on overlap, now measured on the live product | None |
| Dispersion, single-stock volatility | Structured-note issuers hedging autocallables | No dispersion ETF; DSPX is an index (2023-09); Calamos CAIE/CAIQ sell the autocallable side (about $1bn in ten months) | The autocallable side is short single-name crash risk | The JPMorgan dispersion index lost 4.9% in 2026-03 (secondary source) | Same crash as equity, concentrated | Reject the autocallable side on overlap; unresolved on the long-dispersion side for lack of a vehicle | A vehicle |
| Bank quantitative-strategy baskets | Various, sold by dealers | QIS (1.21%, 2023-07-10, $42m) | Beta 0.37 to VTI; the rest correlated with itself | −57% in three years | Crowded strategies unwind together | Reject, and reclassify the audit's grounds from cost to failure | None |
| EM ex-China; frontier | Country risk premiums | EMXC (0.25%, $26.1bn); FM (about 0.79%, $195m, aggregator, unverified) | No: a country-weight choice inside VXUS and AVES, beta 0.96 | Index return; +66% in the year to 2026-06 | Emerging-market equity | Reject as a mechanism; a China-exclusion policy is a risk view, not a premium | None |
| EM long-short equity, machine-learning | Slower information in emerging markets | MEMA (0.85%, 2025-12-16, about $12m) | Adds a short leg the held EM funds lack | Unquotable at nine months | Closure at $12m; model risk | Unresolved, too young; review at 24 filed months against AVES | N-PORT against MSCI EM and AVES |
| Financed stocks plus bonds, cheaper | Bond term premium, financed | SPLS (0.18%, 2026-01-15, $45.5m) against RSSB 0.39% | Same construction as RSSB and NTSX | Bond return minus financing at 18 bp | Structure unverified: no N-PORT yet | Admit to the fund list as `not filed`; nothing in the vector holds RSSB | First N-PORT, due about 2026-09 |
| Bitcoin covered calls | Buyers of bitcoin upside | BTCI (0.99%, 2024-10-16, $1.30bn) | No: short bitcoin volatility on a spot position | +5.58%/yr since inception; 1y −40.91%; a 26.73% distribution rate paid from the position | Bitcoin drawdown, with the upside sold | Reject on overlap with the audit's bitcoin verdict | None |
| Ether staking | Ethereum protocol issuance, paid to validators | ETHB (0.25%, waived to 0.12%; 18% of rewards to the sponsor and custodian) | No: spot ether with a coupon | Base staking about 2.6% (aggregators, 2026-08) on 70 to 95% staked, less 18%, less fee: about 1.3 to 1.8% a year | Ether price | Reject as a mechanism; it is a dividend on a speculation | None |
| Bitcoin futures basis | Financed longs paying to hold futures | None dedicated; BITO's distributions were this | Yes when it pays | Three-month basis below the two-year Treasury since 2026-02 (Glassnode via CoinDesk, secondary) | It pays only in bull markets | Reject on price; reopen above bills plus 5 pp | Glassnode or CME basis series |
| Gold and bitcoin financed on equity | None; audit §3 and §8 | RSSX (0.67%, 2025-05-29, $75.6m), on the fund list | Funding rule only | Audit's figures | Audit's | Unchanged | N-PORT |
| Section 351 and tax-aware launches (Alpha Architect AAUS/AAEQ/AAUA, Cambria GEQ/GEX, Simplify LQ/DINE) | The Treasury, statutorily | Various, 2025 to 2026 | Not return sources | Deferral, not return | Rule change | Implementation only; belongs with [structural edges](structural-and-tax-edges.md) | None |
| Dimensional and Fidelity ETF share classes; Avantis AVTM; DFMC | Cost | 2026 | Repackaging | Fee cut of 9% asset-weighted at Dimensional from 2026-11-01 | None | Note for the fund list | None |

## The three candidates most capable of changing the vector

**1. Financed cross-asset carry beside the trend position: RSST 30 becomes RSST 20 plus
RSSY 10.** The change is decided by two numbers, and the second is the one to measure. The
premium cannot be measured on any series available here, so carry it as an input across the
same four scenarios the stacking page uses for trend. The measurement is the correlation of
the carry position to the trend position and to the equity core on at least 36 filed months,
with a confidence interval narrower than ±0.25, and the sign of the carry position in months
when VTI falls more than 3%. If the correlation to trend holds below 0.4 and the crisis
months split, the same arithmetic that gives one financed diversifier +0.58 pp a year at 10%
gives a second uncorrelated one most of that again; if the correlation sits above 0.6, the
two are one bet at double the fee. Data: N-PORT Item B.5 for RSSY, RSBY, RSST, RSBT, VTI and
BND through 2027-07, which arrives without a licence; a long carry series would need futures
data the repository does not hold, and the ReSolve model history is not public.

**2. Intangible-adjusted value beside the held value: VTV 15 becomes VTV 10 plus ITAN 5.**
The stacking page shows the whole gain from adding a fund is governed by the correlation of
its excess return to the excess returns already held, measured at 0.435 among the value
funds. The measurement is that correlation for ITAN against VTV, AVDV and IDMO on 60 filed
months (2021-07 to 2026-06), and a regression of ITAN on the French five factors plus
momentum to see whether its value exposure is positive at all or whether the label covers
growth. A value exposure near VTV's with an excess-return correlation below 0.2 raises the
effective number of bets; a negative value exposure makes it a growth fund and the change
is withdrawn. Data: N-PORT for ITAN and VTV; the French library already in the repository.

**3. Self-built financing against the 99 bp fund: RSST 30 becomes VTI plus DBMF plus a box
loan, or stays.** The recommendation lists the fund-level financing spread as the input that
decides the sign of a financed position's contribution and says no issuer discloses it. The
measurement has two halves. First, RSST's implied financing: regress its filed monthly return
on one unit of the S&P 500 total return and one unit of a trend index, and read the intercept
plus the fee as the cost of the structure. Second, the retail alternative: the implied rate on
a sold SPX box spread, which is public daily, against the 3-month bill. If the box rate plus
DBMF's 85 bp is more than 50 bp a year below RSST's implied all-in cost, a margin account can
hold the same exposure cheaper, in the taxable third, with the loan interest deductible
against investment income. If not, the fund is the cheaper structure and the question closes.
Data: end-of-day SPX option chains (CBOE) or the boxtrades.com history, FRED DTB3, N-PORT for
RSST, and the AQR trend index already used by the [trend-weight page](trend-weight-under-uncertainty.md).

## What this sweep could not verify

The Fidelity $100 purchase-fee list (HTTP 403 again); the current PRIV net fee, where the
FAQ and the product page disagree by 15 bp; the FM fee and size (aggregator only); the
August 2026 catastrophe bond yield (July is the latest published); a numeric bitcoin basis
(the CoinDesk source returned 403, the secondary carried no figure); SPLS's structure
(release page 403, no N-PORT filed); BIZD's 2026 fee table (the June 2024 497K is the latest
located; an aggregator reads 9.69% for 2026); MEMA's net assets. Stooq, Yahoo and Alpha
Vantage all refused automated price requests, which is why every measured figure here comes
from N-PORT rather than from prices, and why RSSY's April 2026 month could not be paired with
VTI, whose filing for that quarter was not yet in the cache.
